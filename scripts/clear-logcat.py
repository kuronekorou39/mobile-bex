import os
import subprocess
ADB = r'C:\Android\platform-tools\adb.exe'
# 端末シリアル。BEX_DEVICE_SERIAL で上書きできる (adb devices で確認)。
SERIAL = os.environ.get('BEX_DEVICE_SERIAL', '54231JEBF06373')

try:
    r = subprocess.run([ADB, '-s', SERIAL, 'logcat', '-c'], capture_output=True, timeout=15)
    print(f"logcat -c return: {r.returncode}")
    if r.stderr:
        print(f"stderr: {r.stderr.decode(errors='replace')}")
    print("OK: buffer cleared")
except subprocess.TimeoutExpired:
    print("TIMEOUT. May need to kill and restart adb-server.")
    subprocess.run([ADB, 'kill-server'], timeout=10)
    subprocess.run([ADB, 'start-server'], timeout=10)
    print("adb-server restarted. Try the script again.")
