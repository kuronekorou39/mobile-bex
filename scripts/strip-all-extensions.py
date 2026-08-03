#!/usr/bin/env python3
"""Remove ALL extensions from Chromium Preferences so the browser can boot
without trying to load any extensions. Use this when the browser hangs at
splash screen because of one or more extensions."""
import json
import os
import subprocess
import sys
import time

from bex_env import (
    ADB, MAIN_ACTIVITY, PACKAGE as PKG, REMOTE_PREFS as REMOTE_PATH,
    SERIAL, adb, work_path,
)
# タイムスタンプ付きにして上書き破壊を防ぐ（2回実行すると拡張ゼロの状態で
# バックアップが潰れ、bisect-extensions.py の比較元も失われるため）
LOCAL_BACKUP = work_path(f'Preferences.allext.backup.{time.strftime("%Y%m%d-%H%M%S")}.json')
LOCAL_FIXED = work_path('Preferences.noext.json')
DEVICE_TMP = '/data/local/tmp/Preferences.noext.json'


print("Step 1: Pull Preferences...")
result = subprocess.run(
    [ADB, '-s', SERIAL, 'exec-out', 'run-as', PKG, 'cat', REMOTE_PATH],
    capture_output=True
)
if result.returncode != 0:
    print("FAIL"); print(result.stderr.decode()); sys.exit(1)
prefs_bytes = result.stdout
print(f"  {len(prefs_bytes)} bytes")
with open(LOCAL_BACKUP, 'wb') as f:
    f.write(prefs_bytes)
print(f"  Backup: {LOCAL_BACKUP}")

print()
print("Step 2: Strip ALL extension settings...")
data = json.loads(prefs_bytes.decode('utf-8'))
ext = data.get('extensions', {})

n_settings = len(ext.get('settings', {}))
ext['settings'] = {}
print(f"  Cleared {n_settings} entries from extensions.settings")

if 'toolbar' in ext:
    n = len(ext.get('toolbar') or [])
    ext['toolbar'] = []
    print(f"  Cleared {n} entries from extensions.toolbar")

if 'pinned_extensions' in ext:
    n = len(ext.get('pinned_extensions') or [])
    ext['pinned_extensions'] = []
    print(f"  Cleared {n} entries from extensions.pinned_extensions")

# Clear any "install_signature" / autoupdate metadata that may reference removed extensions
for k in ['install_signature', 'last_chrome_version']:
    if k in ext:
        del ext[k]
        print(f"  Removed extensions.{k}")

print()
print("Step 3: Write fixed JSON locally...")
with open(LOCAL_FIXED, 'w', encoding='utf-8', newline='\n') as f:
    json.dump(data, f, separators=(',', ':'), ensure_ascii=False)
print(f"  Wrote: {LOCAL_FIXED} ({os.path.getsize(LOCAL_FIXED)} bytes)")

print()
print(f"Step 4: Push to {DEVICE_TMP}...")
r = adb('push', LOCAL_FIXED, DEVICE_TMP)
print(f"  stdout: {r.stdout.decode().strip()}")
if r.returncode != 0:
    print(r.stderr.decode()); sys.exit(1)

print()
print(f"Step 5: run-as cp to {REMOTE_PATH}...")
r = subprocess.run(
    [ADB, '-s', SERIAL, 'shell', f'run-as {PKG} cp {DEVICE_TMP} {REMOTE_PATH}'],
    capture_output=True
)
print(f"  stdout: {r.stdout.decode().strip()}")
print(f"  stderr: {r.stderr.decode().strip()}")
print(f"  return: {r.returncode}")
if r.returncode != 0:
    sys.exit(1)

print()
print("Step 6: Cleanup and verify...")
adb('shell', 'rm', DEVICE_TMP)
r = subprocess.run(
    [ADB, '-s', SERIAL, 'exec-out', 'run-as', PKG, 'wc', '-c', REMOTE_PATH],
    capture_output=True
)
print(f"  wc -c: {r.stdout.decode().strip()}")

print()
print("Step 7: force-stop + start Chromium...")
adb('shell', 'am', 'force-stop', PKG)
time.sleep(1)
r = adb('shell', 'am', 'start', '-n', MAIN_ACTIVITY)
print(f"  {r.stdout.decode().strip()}")

print()
print("DONE. Waiting 10 seconds for boot then capturing screenshot...")
time.sleep(10)
adb('shell', 'screencap', '-p', '/sdcard/bex-screen.png')
_shot = work_path('bex-screen-noext.png')
adb('pull', '/sdcard/bex-screen.png', _shot)
print(f"Screenshot saved to {_shot}")
