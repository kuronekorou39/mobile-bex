#!/bin/bash
# mobile-bex: Chromium Android ビルドスクリプト
# Usage: ./scripts/build.sh [--setup] [--target TARGET] [--cpu CPU] [--release]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CHROMIUM_DIR="${CHROMIUM_DIR:-$HOME/chromium}"
CHROMIUM_SRC="$CHROMIUM_DIR/src"
OUT_DIR="out/MobileBex"
TARGET="chrome_public_apk"
TARGET_CPU="arm64"
IS_RELEASE=false
SETUP_ONLY=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --setup) SETUP_ONLY=true; shift ;;
    --target) TARGET="$2"; shift 2 ;;
    --cpu) TARGET_CPU="$2"; shift 2 ;;
    --release) IS_RELEASE=true; shift ;;
    --out) OUT_DIR="$2"; shift 2 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

if [[ ! -d "$CHROMIUM_SRC" ]]; then
  echo "ERROR: Chromiumソースが見つかりません: $CHROMIUM_SRC"
  exit 1
fi

cd "$CHROMIUM_SRC"

# --- Generate args.gn ---
generate_args() {
  local args_file="$CHROMIUM_SRC/$OUT_DIR/args.gn"
  mkdir -p "$CHROMIUM_SRC/$OUT_DIR"

  echo ">>> args.gn を生成中: $args_file"

  cat > "$args_file" << 'ARGS_EOF'
# mobile-bex: Android Chromium with Extensions
target_os = "android"
ARGS_EOF

  echo "target_cpu = \"$TARGET_CPU\"" >> "$args_file"

  if $IS_RELEASE; then
    cat >> "$args_file" << 'ARGS_EOF'

# Release build
is_debug = false
symbol_level = 0
is_component_build = false
is_official_build = true
is_chrome_branded = false
ARGS_EOF
  else
    cat >> "$args_file" << 'ARGS_EOF'

# Development build
is_debug = false
symbol_level = 0
is_component_build = false
is_official_build = false
is_chrome_branded = false
is_java_debug = true
ARGS_EOF
  fi

  # ccache
  if command -v ccache &>/dev/null; then
    echo '' >> "$args_file"
    echo '# ccache' >> "$args_file"
    echo 'cc_wrapper = "ccache"' >> "$args_file"
  fi

  # Extensions support (requires patches)
  cat >> "$args_file" << 'ARGS_EOF'

# Extensions support (requires mobile-bex patches)
enable_extensions = true
ARGS_EOF

  echo ""
  echo "args.gn の内容:"
  echo "---"
  cat "$args_file"
  echo "---"
}

# --- Setup (gn gen) ---
setup_build() {
  generate_args
  echo ""
  echo ">>> gn gen を実行中..."
  gn gen "$OUT_DIR"
  echo ">>> ビルド設定完了: $OUT_DIR"
}

# --- Build ---
run_build() {
  if [[ ! -f "$CHROMIUM_SRC/$OUT_DIR/args.gn" ]]; then
    echo "ビルド設定が見つかりません。先にセットアップします..."
    setup_build
  fi

  echo ""
  echo "=== mobile-bex: ビルド開始 ==="
  echo "Target: $TARGET"
  echo "CPU: $TARGET_CPU"
  echo "Output: $OUT_DIR"
  echo ""

  local start_time=$(date +%s)

  autoninja -C "$OUT_DIR" "$TARGET"

  local end_time=$(date +%s)
  local elapsed=$(( end_time - start_time ))
  local minutes=$(( elapsed / 60 ))
  local seconds=$(( elapsed % 60 ))

  echo ""
  echo "=== ビルド完了 (${minutes}分${seconds}秒) ==="
  echo "APK: $CHROMIUM_SRC/$OUT_DIR/apks/ChromePublic.apk"
}

# --- Main ---
if $SETUP_ONLY; then
  setup_build
else
  run_build
fi
