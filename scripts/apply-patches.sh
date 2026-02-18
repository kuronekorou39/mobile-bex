#!/bin/bash
# mobile-bex: Chromiumソースへのパッチ適用スクリプト
# Usage: ./scripts/apply-patches.sh [--phase 1|2|3] [--dry-run] [--reverse]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PATCHES_DIR="$PROJECT_ROOT/patches"
CHROMIUM_DIR="${CHROMIUM_DIR:-$HOME/chromium}"
CHROMIUM_SRC="$CHROMIUM_DIR/src"

PHASE="1"
DRY_RUN=""
REVERSE=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --phase) PHASE="$2"; shift 2 ;;
    --dry-run) DRY_RUN="--dry-run"; shift ;;
    --reverse) REVERSE="--reverse"; shift ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

if [[ ! -d "$CHROMIUM_SRC" ]]; then
  echo "ERROR: Chromiumソースが見つかりません: $CHROMIUM_SRC"
  echo "先に ./scripts/setup.sh を実行してください"
  exit 1
fi

echo "=== mobile-bex: パッチ適用 (Phase $PHASE) ==="
echo "Chromium src: $CHROMIUM_SRC"
echo ""

apply_phase() {
  local phase_num="$1"
  local phase_dir="$PATCHES_DIR/phase${phase_num}"

  if [[ ! -d "$phase_dir" ]]; then
    echo "WARNING: パッチディレクトリが存在しません: $phase_dir"
    return 0
  fi

  local patch_count=0
  local fail_count=0

  # パッチファイルを番号順にソートして適用
  for patch_file in $(find "$phase_dir" -name "*.patch" -type f | sort); do
    patch_name="$(basename "$patch_file")"
    echo -n "  Applying: $patch_name ... "

    if git -C "$CHROMIUM_SRC" apply $DRY_RUN $REVERSE --check "$patch_file" 2>/dev/null; then
      if [[ -z "$DRY_RUN" ]]; then
        git -C "$CHROMIUM_SRC" apply $REVERSE "$patch_file"
        echo "OK"
      else
        echo "OK (dry-run)"
      fi
      ((patch_count++))
    else
      echo "FAILED"
      ((fail_count++))
      echo "    git apply で失敗しました。手動での適用が必要です:"
      echo "    cd $CHROMIUM_SRC && git apply --3way $patch_file"
    fi
  done

  echo ""
  echo "  Phase $phase_num: $patch_count 適用成功, $fail_count 失敗"
}

# Apply patches for specified phase(s)
case "$PHASE" in
  1)
    apply_phase 1
    ;;
  2)
    apply_phase 1
    apply_phase 2
    ;;
  3)
    apply_phase 1
    apply_phase 2
    apply_phase 3
    ;;
  *)
    echo "ERROR: 無効なフェーズ: $PHASE (1, 2, 3 のいずれかを指定)"
    exit 1
    ;;
esac

echo ""
if [[ -n "$DRY_RUN" ]]; then
  echo "=== ドライラン完了（実際の変更はありません） ==="
else
  echo "=== パッチ適用完了 ==="
fi
