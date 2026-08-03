#!/usr/bin/env python3
"""パッチファイルとテスト拡張機能の静的検証。

CI およびローカルでの事前チェック用。Chromium ソース不要で以下を検証する:
1. patches/**/*.patch の hunk ヘッダ (@@ -a,b +c,d @@) と本文の行数整合
   (過去に 09/10/13/14 で手編集による corrupt patch が発生したため)
2. .sh / .patch / .py が LF であること (CRLF だと WSL / git apply で全滅)
3. test-extensions/*/manifest.json が有効な JSON かつ Manifest V3 であること

使い方: python3 scripts/validate-patches.py  (リポジトリルートで実行)
終了コード: 問題なし=0, 問題あり=1
"""
import glob
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
errors = []


def error(path, msg):
    errors.append(f"{os.path.relpath(path, REPO)}: {msg}")


def validate_patch(path):
    with open(path, encoding="utf-8", errors="replace", newline="") as f:
        lines = f.read().split("\n")

    i = 0
    in_binary = False
    while i < len(lines):
        line = lines[i]
        if line.startswith("GIT binary patch"):
            in_binary = True
            i += 1
            continue
        if line.startswith("diff --git"):
            in_binary = False
            i += 1
            continue
        m = re.match(r"^@@ -\d+(?:,(\d+))? \+\d+(?:,(\d+))? @@", line)
        if m and not in_binary:
            expect_old = int(m.group(1)) if m.group(1) is not None else 1
            expect_new = int(m.group(2)) if m.group(2) is not None else 1
            old_count = new_count = 0
            j = i + 1
            while j < len(lines):
                body = lines[j]
                if body.startswith("\\ No newline"):
                    j += 1
                    continue
                if body.startswith("@@") or body.startswith("diff --git"):
                    break
                if body.startswith("-"):
                    old_count += 1
                elif body.startswith("+"):
                    new_count += 1
                elif body.startswith(" ") or body == "":
                    # 末尾の空行は hunk 外の可能性があるため、期待数を
                    # 超えて数えない
                    if old_count >= expect_old and new_count >= expect_new:
                        break
                    old_count += 1
                    new_count += 1
                else:
                    break
                j += 1
            if old_count != expect_old or new_count != expect_new:
                error(
                    path,
                    f"corrupt hunk at line {i + 1}: header says "
                    f"-{expect_old}/+{expect_new} but body has "
                    f"-{old_count}/+{new_count}",
                )
            i = j
            continue
        i += 1


def validate_line_endings(path):
    with open(path, "rb") as f:
        if b"\r\n" in f.read():
            error(path, "CRLF line endings (must be LF)")


def validate_manifest(path):
    try:
        with open(path, encoding="utf-8") as f:
            manifest = json.load(f)
    except json.JSONDecodeError as e:
        error(path, f"invalid JSON: {e}")
        return
    if manifest.get("manifest_version") != 3:
        error(path, "manifest_version must be 3")
    for key in ("name", "version"):
        if key not in manifest:
            error(path, f"missing required key: {key}")


def main():
    patches = glob.glob(os.path.join(REPO, "patches", "**", "*.patch"), recursive=True)
    for p in patches:
        validate_patch(p)
        validate_line_endings(p)
    print(f"patches: {len(patches)} checked")

    scripts = glob.glob(os.path.join(REPO, "scripts", "*.sh")) + glob.glob(
        os.path.join(REPO, "scripts", "*.py")
    )
    for p in scripts:
        validate_line_endings(p)
    print(f"scripts: {len(scripts)} checked (line endings)")

    manifests = glob.glob(os.path.join(REPO, "test-extensions", "*", "manifest.json"))
    for p in manifests:
        validate_manifest(p)
    print(f"manifests: {len(manifests)} checked")

    if errors:
        print(f"\n{len(errors)} error(s):")
        for e in errors:
            print(f"  ERROR {e}")
        return 1
    print("\nAll OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
