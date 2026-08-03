#!/usr/bin/env python3
"""デバッグ用スクリプトが共有する環境設定。

環境変数で上書きできる:
  BEX_ADB            adb の実行ファイルパス (既定: PATH 上の adb)
  BEX_DEVICE_SERIAL  対象端末のシリアル (既定: adb devices が1台だけならそれ)
  BEX_PACKAGE        アプリのパッケージ名 (既定: com.rou39.bex)
"""
import os
import pathlib
import shutil
import subprocess
import sys

# リポジトリのルート。スクリプトの位置から求めるので、どこに clone しても動く。
REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# 一時ファイルの置き場所。リポジトリを汚さないよう .work/ に隔離する。
WORK_DIR = REPO_ROOT / ".work"

PACKAGE = os.environ.get("BEX_PACKAGE", "com.rou39.bex")
REMOTE_PREFS = f"/data/data/{PACKAGE}/app_chrome/Default/Preferences"
MAIN_ACTIVITY = f"{PACKAGE}/com.google.android.apps.chrome.Main"


def find_adb():
    """adb の場所を返す。見つからなければ終了する。"""
    explicit = os.environ.get("BEX_ADB")
    if explicit:
        if not os.path.isfile(explicit):
            sys.exit(f"BEX_ADB が指すファイルがありません: {explicit}")
        return explicit

    found = shutil.which("adb") or shutil.which("adb.exe")
    if found:
        return found

    # Windows でよくある既定の場所を最後に試す
    for candidate in (
        r"C:\Android\platform-tools\adb.exe",
        os.path.expanduser(r"~\AppData\Local\Android\Sdk\platform-tools\adb.exe"),
        os.path.expanduser("~/Android/Sdk/platform-tools/adb"),
    ):
        if os.path.isfile(candidate):
            return candidate

    sys.exit("adb が見つかりません。PATH に追加するか BEX_ADB を設定してください。")


ADB = find_adb()


def find_serial():
    """対象端末のシリアルを返す。複数台つながっている場合は指定を促す。"""
    explicit = os.environ.get("BEX_DEVICE_SERIAL")
    if explicit:
        return explicit

    out = subprocess.run([ADB, "devices"], capture_output=True, text=True).stdout
    devices = [
        line.split()[0]
        for line in out.splitlines()[1:]
        if line.strip() and line.split()[-1] == "device"
    ]
    if not devices:
        sys.exit("接続されている端末がありません。")
    if len(devices) > 1:
        sys.exit(
            "端末が複数接続されています。BEX_DEVICE_SERIAL で指定してください:\n  "
            + "\n  ".join(devices)
        )
    return devices[0]


SERIAL = find_serial()


def adb(*args, capture=True, **kwargs):
    """対象端末に対して adb を実行する。"""
    return subprocess.run(
        [ADB, "-s", SERIAL, *args], capture_output=capture, **kwargs
    )


def work_path(name):
    """.work/ 配下のパスを返す (ディレクトリは自動作成)。"""
    WORK_DIR.mkdir(exist_ok=True)
    return str(WORK_DIR / name)
