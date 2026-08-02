#!/bin/bash
# mobile-bex: Chromiumソースへのパッチ適用スクリプト
# Usage: ./scripts/apply-patches.sh [--phase 1|2|3] [--dry-run] [--reverse]
# 注: Phase 1/2 はパッチ不要（is_desktop_android=true のみで動作）のためディレクトリは空。
#     実体があるのは phase3 のみで、デフォルトの --phase 3 は 1→2→3 の順に走査する。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PATCHES_DIR="$PROJECT_ROOT/patches"
CHROMIUM_DIR="${CHROMIUM_DIR:-$HOME/chromium}"
CHROMIUM_SRC="$CHROMIUM_DIR/src"

PHASE="3"
DRY_RUN=""
REVERSE=""
TOTAL_APPLIED=0
TOTAL_FAILED=0

while [[ $# -gt 0 ]]; do
  case $1 in
    --phase) PHASE="$2"; shift 2 ;;
    --dry-run) DRY_RUN="1"; shift ;;
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

  # ゼロ埋め番号付きファイル名なので glob のソート順 = 適用順
  local patch_files=("$phase_dir"/*.patch)
  if [[ ! -e "${patch_files[0]}" ]]; then
    echo "  Phase $phase_num: パッチなし（スキップ）"
    return 0
  fi

  # 逆適用時は後のパッチから剥がす（08→11→12 等の依存関係があるため）
  if [[ -n "$REVERSE" ]]; then
    local reversed=()
    local i
    for ((i = ${#patch_files[@]} - 1; i >= 0; i--)); do
      reversed+=("${patch_files[i]}")
    done
    patch_files=("${reversed[@]}")
  fi

  local patch_file patch_name apply_err
  for patch_file in "${patch_files[@]}"; do
    patch_name="$(basename "$patch_file")"
    echo -n "  Applying: $patch_name ... "

    if apply_err=$(git -C "$CHROMIUM_SRC" apply $REVERSE --check "$patch_file" 2>&1); then
      if [[ -z "$DRY_RUN" ]]; then
        git -C "$CHROMIUM_SRC" apply $REVERSE "$patch_file"
        echo "OK"
      else
        echo "OK (dry-run)"
      fi
      patch_count=$((patch_count + 1))
    else
      echo "FAILED"
      fail_count=$((fail_count + 1))
      # git apply のエラーをそのまま表示（already applied か context 不一致かを判別できるように）
      sed 's/^/    | /' <<< "$apply_err"
    fi
  done

  echo ""
  echo "  Phase $phase_num: $patch_count 適用成功, $fail_count 失敗"
  TOTAL_APPLIED=$((TOTAL_APPLIED + patch_count))
  TOTAL_FAILED=$((TOTAL_FAILED + fail_count))
}

# Apply patches for specified phase(s)
case "$PHASE" in
  1)
    apply_phase 1
    ;;
  2)
    if [[ -n "$REVERSE" ]]; then
      apply_phase 2
      apply_phase 1
    else
      apply_phase 1
      apply_phase 2
    fi
    ;;
  3)
    if [[ -n "$REVERSE" ]]; then
      apply_phase 3
      apply_phase 2
      apply_phase 1
    else
      apply_phase 1
      apply_phase 2
      apply_phase 3
    fi
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

if [[ "$TOTAL_FAILED" -gt 0 ]]; then
  echo "WARNING: $TOTAL_FAILED 件のパッチが適用できませんでした。上記エラーを確認してください。"
  exit 1
fi
