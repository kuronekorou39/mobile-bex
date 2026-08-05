#!/usr/bin/env python3
"""Chromium 作業ツリーに対して patches/phase3/*.patch を検証・再生成する。

パッチは「クリーンな Chromium に番号順で全適用すると作業ツリーと完全一致する」
状態を常に保つ。このスクリプトがその保証を担う。

パッチは順番に重ねる差分なので、同じファイルを複数のパッチが触ることがある
(例: 04 が作ったクラスを 09 が変更する)。そのため再生成では「どのパッチを
作り直すか」を明示し、それ以外は既存のパッチをそのまま適用して土台を作る。

使い方 (WSL 上で実行):
    python3 scripts/regen-patches.py                 # 検証のみ
    python3 scripts/regen-patches.py --regen 09,25   # 09 と 25 を作り直して検証

新しいパッチを足すときは、コメント行だけを書いたパッチファイルを置き、
担当ファイルを --files で教えて一度だけ生成する (以降は --regen だけでよい):
    printf '# Patch 28: ...\\n' > patches/phase3/28-foo.patch
    python3 scripts/regen-patches.py --regen 28 --files path/a.java,path/b.cc

環境変数:
    CHROMIUM_SRC   Chromium のソース (既定: ~/chromium/src)
"""
import argparse
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

REPO = pathlib.Path(__file__).resolve().parent.parent
PATCH_DIR = REPO / "patches" / "phase3"
SRC = pathlib.Path(os.environ.get("CHROMIUM_SRC", os.path.expanduser("~/chromium/src")))


def run(*args, cwd=None, check=True):
    r = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    if check and r.returncode != 0:
        sys.exit(f"コマンド失敗: {' '.join(args)}\n{r.stdout}\n{r.stderr}")
    return r


def parse_patch(path):
    """パッチから (ヘッダコメント, 担当ファイル一覧) を取り出す。"""
    header, files = [], []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("diff --git"):
            m = re.match(r"diff --git a/(\S+)", line)
            if m:
                files.append(m.group(1))
        elif not files and line.startswith("#"):
            header.append(line)
    return "\n".join(header), files


def load_patches():
    patches = []
    for p in sorted(PATCH_DIR.glob("*.patch")):
        header, files = parse_patch(p)
        patches.append((p, header, files))
    return patches


def tree_files():
    out = run("git", "-C", str(SRC), "status", "--porcelain").stdout
    return [line[3:].strip() for line in out.splitlines() if line.strip()]


def make_sandbox(files):
    """変更対象ファイルの「変更前の状態」だけを持つ git リポジトリを作る。"""
    sb = pathlib.Path(tempfile.mkdtemp(prefix="bex-patch-"))
    run("git", "init", "-q", str(sb))
    run("git", "-C", str(sb), "config", "user.email", "bex@local")
    run("git", "-C", str(sb), "config", "user.name", "bex")
    for f in files:
        if run("git", "-C", str(SRC), "cat-file", "-e", f"HEAD:{f}", check=False).returncode:
            continue  # 新規追加ファイルは変更前が存在しない
        dest = sb / f
        dest.parent.mkdir(parents=True, exist_ok=True)
        blob = subprocess.run(["git", "-C", str(SRC), "show", f"HEAD:{f}"],
                              capture_output=True)
        dest.write_bytes(blob.stdout)
    run("git", "-C", str(sb), "add", "-A")
    run("git", "-C", str(sb), "commit", "-qm", "pristine")
    return sb


def check_regen_targets(patches, targets):
    """再生成するパッチ同士が同じファイルを持っていないか確かめる。"""
    owner = {}
    names = {p.name for p, _, _ in patches}
    for t in targets:
        if t not in names:
            sys.exit(f"そのようなパッチはありません: {t}")
    for path, _, files in patches:
        if path.name not in targets:
            continue
        for f in files:
            if f in owner:
                sys.exit(
                    f"{f} を {owner[f]} と {path.name} の両方で作り直そうとしています。\n"
                    "同時に作り直すパッチ同士は、担当ファイルが重ならないようにしてください。"
                )
            owner[f] = path.name


def regenerate(patches, files, targets, declared=None):
    sb = make_sandbox(files)
    try:
        for path, header, owned in patches:
            if path.name in targets:
                owned = declared or owned
                if not owned:
                    sys.exit(f"{path.name}: 担当ファイルが分かりません。--files で指定してください。")
                for f in owned:
                    srcf = SRC / f
                    if not srcf.exists():
                        sys.exit(f"{path.name}: 作業ツリーにありません: {f}")
                    dest = sb / f
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(srcf, dest)
                run("git", "-C", str(sb), "add", "-A")
                diff = run("git", "-C", str(sb), "diff", "--cached", "--binary").stdout
                if not diff.strip():
                    print(f"  警告: {path.name} の差分が空です")
                    continue
                path.write_text((header + "\n" if header else "") + diff,
                                encoding="utf-8", newline="\n")
                run("git", "-C", str(sb), "commit", "-qm", path.name)
                print(f"  再生成: {path.name}")
            else:
                r = run("git", "-C", str(sb), "apply", str(path), check=False)
                if r.returncode:
                    sys.exit(f"土台の適用に失敗: {path.name}\n{r.stderr}")
                run("git", "-C", str(sb), "add", "-A")
                run("git", "-C", str(sb), "commit", "-qm", path.name, check=False)
    finally:
        shutil.rmtree(sb, ignore_errors=True)


def verify(patches, files):
    """クリーンなツリーに全適用し、作業ツリーと一致するか確かめる。"""
    sb = make_sandbox(files)
    try:
        for path, _, _ in patches:
            r = run("git", "-C", str(sb), "apply", "--check", str(path), check=False)
            if r.returncode:
                print(f"  適用できません: {path.name}\n{r.stderr}")
                return False
            run("git", "-C", str(sb), "apply", str(path))
        bad = 0
        for f in files:
            a, b = sb / f, SRC / f
            if not a.exists():
                print(f"  生成されていません: {f}")
                bad += 1
            elif a.read_bytes() != b.read_bytes():
                print(f"  内容が一致しません: {f}")
                bad += 1
        if bad:
            print(f"  {bad} 件が不一致")
            return False
        print(f"  全 {len(patches)} パッチを適用し、{len(files)} ファイルすべて一致")
        return True
    finally:
        shutil.rmtree(sb, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--regen", default="",
                    help="作り直すパッチ (番号かファイル名をカンマ区切り。例: 09,25)")
    ap.add_argument("--files", default="",
                    help="担当ファイルを明示する (新しいパッチを初めて生成するとき用。"
                         "--regen でパッチを1本だけ指定すること)")
    args = ap.parse_args()

    if not (SRC / ".git").exists():
        sys.exit(f"Chromium のソースが見つかりません: {SRC}")

    patches = load_patches()
    files = tree_files()
    print(f"パッチ {len(patches)} 本 / 変更ファイル {len(files)} 件")

    if args.regen:
        wanted = [w.strip() for w in args.regen.split(",") if w.strip()]
        targets = set()
        for w in wanted:
            hit = [p.name for p, _, _ in patches
                   if p.name == w or p.name.startswith(w + "-")]
            if not hit:
                sys.exit(f"そのようなパッチはありません: {w}")
            targets.update(hit)
        declared = [f.strip() for f in args.files.split(",") if f.strip()]
        if declared and len(targets) != 1:
            sys.exit("--files を使うときは --regen でパッチを1本だけ指定してください。")
        check_regen_targets(patches, targets)
        print("再生成:")
        regenerate(patches, files, targets, declared)

    print("検証:")
    if not verify(patches, files):
        sys.exit(1)
    print("OK")


if __name__ == "__main__":
    main()
