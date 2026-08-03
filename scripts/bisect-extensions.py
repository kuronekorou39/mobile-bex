#!/usr/bin/env python3
"""Bisect which test extension(s) cause Chromium to hang on splash.
Starts from a 'no extensions' state, then adds extension entries one by one
into Preferences, restarting Chromium each time, and checking via logcat
whether the browser fully booted.
"""
import json
import subprocess
import sys
import time
import os

ADB = r'C:\Android\platform-tools\adb.exe'
# 端末シリアル。BEX_DEVICE_SERIAL で上書きできる (adb devices で確認)。
SERIAL = os.environ.get('BEX_DEVICE_SERIAL', '54231JEBF06373')
PKG = 'org.chromium.chrome'
REMOTE_PATH = f'/data/data/{PKG}/app_chrome/Default/Preferences'
BACKUP_FULL = r'C:\projects\mobile-bex\Preferences.allext.backup.json'
LOCAL_FIXED = r'C:\projects\mobile-bex\Preferences.bisect.json'
DEVICE_TMP = '/data/local/tmp/Preferences.bisect.json'

ORDER = [
    'test-extension',
    'test-extension-fulltab',
    'test-extension-notifications',
    'test-extension-phase2',
    'test-extension-options',
    'test-extension-newtab',
    'test-extension-contextmenu',
    'test-extension-sidepanel',
    'test-extension-omnibox',
]

BOOT_MARKER = 'cr_TopSites: Finished saving'
WAIT_SECONDS = 18

def adb(*args, capture=True, **kw):
    return subprocess.run([ADB, '-s', SERIAL, *args], capture_output=capture, **kw)

def pull_prefs():
    r = subprocess.run(
        [ADB, '-s', SERIAL, 'exec-out', 'run-as', PKG, 'cat', REMOTE_PATH],
        capture_output=True
    )
    if r.returncode != 0:
        print("FAIL pulling prefs:", r.stderr.decode())
        sys.exit(1)
    return json.loads(r.stdout.decode('utf-8'))

def push_prefs(data):
    with open(LOCAL_FIXED, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(data, f, separators=(',', ':'), ensure_ascii=False)
    r = adb('push', LOCAL_FIXED, DEVICE_TMP)
    if r.returncode != 0:
        print("FAIL push:", r.stderr.decode())
        sys.exit(1)
    r = subprocess.run(
        [ADB, '-s', SERIAL, 'shell', f'run-as {PKG} cp {DEVICE_TMP} {REMOTE_PATH}'],
        capture_output=True
    )
    if r.returncode != 0:
        print("FAIL cp:", r.stderr.decode())
        sys.exit(1)

def restart_and_wait():
    adb('shell', 'am', 'force-stop', PKG)
    time.sleep(1)
    adb('logcat', '-c')
    adb('shell', 'am', 'start', '-n', f'{PKG}/com.google.android.apps.chrome.Main')
    time.sleep(WAIT_SECONDS)

def check_booted():
    r = adb('logcat', '-d')
    log = r.stdout.decode('utf-8', errors='replace')
    has_marker = BOOT_MARKER in log
    has_died_loop = log.count('Child process died (type=6)') >= 2
    has_chrome_tabbed = 'ChromeTabbedActivity' in log and 'onResumeWithNative' in log
    return {
        'booted': has_marker or has_chrome_tabbed,
        'has_died_loop': has_died_loop,
        'marker': has_marker,
        'tabbed_resumed': has_chrome_tabbed,
    }

print("=== Loading backup (full extension list) ===")
with open(BACKUP_FULL, encoding='utf-8') as f:
    backup = json.load(f)
backup_settings = backup.get('extensions', {}).get('settings', {})
print(f"Backup contains {len(backup_settings)} extension entries")

# Map each extension name to a (ext_id, entry) tuple from the backup.
# Match against the last path segment; check longer names first so that
# 'test-extension-fulltab' wins over 'test-extension' (prefix match).
def matches_name(segment, name):
    """True if the path segment refers to exactly this extension name.
    Allow base name, ' (n)' / '-n' suffix variants from Android renames."""
    if segment == name:
        return True
    if segment.startswith(name + ' ('):
        return True
    if segment == name + '-1' or segment == name + '-2':
        return True
    return False

sorted_order = sorted(ORDER, key=lambda x: -len(x))

ext_map = {}
debug_unmatched = []
for ext_id, entry in backup_settings.items():
    path = entry.get('path', '') or ''
    decoded_path = path.replace('%2F', '/').replace('%3A', ':').replace('%20', ' ')
    segment = decoded_path.rstrip('/').split('/')[-1]
    matched = None
    for name in sorted_order:
        if matches_name(segment, name):
            matched = name
            break
    if matched:
        # Keep the entry whose path's last segment is exactly `matched`
        # (the cleanest copy). If we already have one, prefer that one.
        if matched not in ext_map:
            ext_map[matched] = (ext_id, entry, decoded_path)
        else:
            existing_seg = ext_map[matched][2].rstrip('/').split('/')[-1]
            if existing_seg != matched and segment == matched:
                ext_map[matched] = (ext_id, entry, decoded_path)
    else:
        debug_unmatched.append((ext_id, segment))

if debug_unmatched:
    print("  (debug) unmatched backup entries:")
    for ext_id, seg in debug_unmatched:
        print(f"    {ext_id[:12]}... segment='{seg}'")

print()
print("=== Extension entries matched from backup ===")
for name in ORDER:
    if name in ext_map:
        ext_id, _, decoded_path = ext_map[name]
        print(f"  {name}: id={ext_id[:16]}... path={decoded_path[-60:]}")
    else:
        print(f"  {name}: NOT FOUND in backup, skipping")

print()
print("=== Verifying baseline (no extensions, should boot) ===")
restart_and_wait()
status = check_booted()
print(f"  baseline: {status}")
if not status['booted']:
    print("  BASELINE FAILED. Cannot bisect.")
    sys.exit(1)

results = []
prefs = pull_prefs()
print()
print("=== Adding extensions one by one ===")
for name in ORDER:
    if name not in ext_map:
        results.append((name, 'SKIP', 'not in backup'))
        continue

    ext_id, entry, decoded_path = ext_map[name]
    prefs['extensions']['settings'][ext_id] = entry
    push_prefs(prefs)
    restart_and_wait()
    status = check_booted()

    if status['booted'] and not status['has_died_loop']:
        results.append((name, 'OK', f"id={ext_id[:8]}"))
        print(f"  [OK]   {name} (id={ext_id[:8]}...)")
    else:
        verdict = 'CULPRIT' if status['has_died_loop'] else 'HUNG'
        results.append((name, verdict, f"id={ext_id[:8]} died_loop={status['has_died_loop']} marker={status['marker']}"))
        print(f"  [{verdict}] {name} (id={ext_id[:8]}...): died_loop={status['has_died_loop']}, marker={status['marker']}")
        # Remove this entry and continue to check the rest
        del prefs['extensions']['settings'][ext_id]
        push_prefs(prefs)
        restart_and_wait()
        recovery = check_booted()
        print(f"     recovery after removal: booted={recovery['booted']}")

print()
print("=== FINAL RESULTS ===")
for name, verdict, detail in results:
    print(f"  {verdict:8s} {name}  ({detail})")

culprits = [n for n, v, _ in results if v in ('CULPRIT', 'HUNG')]
oks = [n for n, v, _ in results if v == 'OK']
print()
print(f"  Culprits: {culprits}")
print(f"  Innocent: {oks}")
