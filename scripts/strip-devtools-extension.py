#!/usr/bin/env python3
"""Strip extensions that declare devtools_page (or have 'devtools' in their path)
from Chromium's Preferences JSON, then write it back via adb run-as.
This is the recovery path when an extension with a devtools_page causes the
Chromium browser to hang on the splash screen at startup."""
import json
import subprocess
import sys
import os
import time

ADB = r'C:\Android\platform-tools\adb.exe'
# 端末シリアル。BEX_DEVICE_SERIAL で上書きできる (adb devices で確認)。
SERIAL = os.environ.get('BEX_DEVICE_SERIAL', '54231JEBF06373')
PKG = 'org.chromium.chrome'
REMOTE_PATH = f'/data/data/{PKG}/app_chrome/Default/Preferences'
# タイムスタンプ付きにして上書き破壊を防ぐ
LOCAL_BACKUP = rf'C:\projects\mobile-bex\Preferences.backup.{time.strftime("%Y%m%d-%H%M%S")}.json'
LOCAL_FIXED = r'C:\projects\mobile-bex\Preferences.fixed.json'
SDCARD_TMP = '/sdcard/Preferences.fixed.json'

def adb(*args, capture=True):
    return subprocess.run([ADB, '-s', SERIAL, *args], capture_output=capture)

print("Step 1: Pull current Preferences from device via run-as...")
result = subprocess.run(
    [ADB, '-s', SERIAL, 'exec-out', 'run-as', PKG, 'cat', REMOTE_PATH],
    capture_output=True
)
if result.returncode != 0:
    print("FAILED to read Preferences:")
    print(result.stderr.decode('utf-8', errors='replace'))
    sys.exit(1)

prefs_bytes = result.stdout
print(f"  Got {len(prefs_bytes)} bytes")

with open(LOCAL_BACKUP, 'wb') as f:
    f.write(prefs_bytes)
print(f"  Backup saved: {LOCAL_BACKUP}")

print()
print("Step 2: Parse JSON and identify extensions to remove...")
data = json.loads(prefs_bytes.decode('utf-8'))

ext_settings = data.get('extensions', {}).get('settings', {})
print(f"  Total registered extensions: {len(ext_settings)}")

to_remove = []
for ext_id, ext_info in ext_settings.items():
    manifest = ext_info.get('manifest', {}) or {}
    path = ext_info.get('path', '') or ''
    name = manifest.get('name', '<unnamed>')
    has_devtools_page = 'devtools_page' in manifest
    path_has_devtools = 'devtools' in path.lower()
    if has_devtools_page or path_has_devtools:
        to_remove.append((ext_id, name, path, has_devtools_page, path_has_devtools))

print(f"  Extensions matching devtools criteria: {len(to_remove)}")
for ext_id, name, path, has_dp, has_path in to_remove:
    print(f"    - {ext_id[:20]}... name={name}")
    print(f"        path={path}")
    print(f"        devtools_page in manifest={has_dp}, 'devtools' in path={has_path}")

if not to_remove:
    print("  Nothing to remove. Aborting.")
    sys.exit(0)

print()
print("Step 3: Remove from extensions.settings...")
for ext_id, *_ in to_remove:
    del ext_settings[ext_id]

# Clean extensions.toolbar (pinned/order list) if it references removed ids
toolbar = data.get('extensions', {}).get('toolbar', None)
if isinstance(toolbar, list):
    before = len(toolbar)
    toolbar[:] = [e for e in toolbar if e not in [t[0] for t in to_remove]]
    after = len(toolbar)
    if before != after:
        print(f"  Pruned {before - after} entries from extensions.toolbar")

# Clean pinned extensions
pinned = data.get('extensions', {}).get('pinned_extensions', None)
if isinstance(pinned, list):
    before = len(pinned)
    pinned[:] = [e for e in pinned if e not in [t[0] for t in to_remove]]
    after = len(pinned)
    if before != after:
        print(f"  Pruned {before - after} entries from extensions.pinned_extensions")

print()
print("Step 4: Write fixed JSON locally...")
with open(LOCAL_FIXED, 'w', encoding='utf-8', newline='\n') as f:
    json.dump(data, f, separators=(',', ':'), ensure_ascii=False)
size = os.path.getsize(LOCAL_FIXED)
print(f"  Wrote: {LOCAL_FIXED} ({size} bytes)")

DEVICE_TMP = '/data/local/tmp/Preferences.fixed.json'

print()
print(f"Step 5: Push fixed JSON to {DEVICE_TMP} (shell-writable)...")
r = adb('push', LOCAL_FIXED, DEVICE_TMP, capture=True)
print(f"  stdout: {r.stdout.decode('utf-8', errors='replace').strip()}")
if r.returncode != 0:
    print(f"  stderr: {r.stderr.decode('utf-8', errors='replace')}")
    sys.exit(1)

print()
print(f"Step 6: Copy from {DEVICE_TMP} to {REMOTE_PATH} via run-as...")
r = subprocess.run(
    [ADB, '-s', SERIAL, 'shell',
     f'run-as {PKG} cp {DEVICE_TMP} {REMOTE_PATH}'],
    capture_output=True
)
print(f"  stdout: {r.stdout.decode('utf-8', errors='replace').strip()}")
print(f"  stderr: {r.stderr.decode('utf-8', errors='replace').strip()}")
print(f"  return: {r.returncode}")
if r.returncode != 0:
    sys.exit(1)

print()
print("Step 7: Verify by re-reading size...")
r = subprocess.run(
    [ADB, '-s', SERIAL, 'exec-out', 'run-as', PKG, 'wc', '-c', REMOTE_PATH],
    capture_output=True
)
print(f"  wc -c: {r.stdout.decode('utf-8', errors='replace').strip()}")

print()
print(f"Step 8: Clean up {DEVICE_TMP}...")
adb('shell', 'rm', DEVICE_TMP)

print()
print("DONE. Devtools-related extensions have been removed from Preferences.")
print("Now run: adb shell am start -n org.chromium.chrome/com.google.android.apps.chrome.Main")
