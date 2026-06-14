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

  # Extensions support — enable the "Desktop Android" build flavor.
  cat >> "$args_file" << 'ARGS_EOF'

# Extensions support: enable Google's "Desktop Android" flavor. This flows to
# enable_desktop_android_extensions -> enable_extensions_core = true, the
# Android-capable extensions config (see docs/phase1-results.md).
# Do NOT set `enable_extensions = true` directly: on Android it pulls in
# app_shell (//extensions/shell -> //apps) and trips assert(!is_android) in
# 50+ BUILD.gn files, breaking `gn gen` (see docs/patch-research.md).
is_desktop_android = true

# Proprietary codecs (H.264/AAC) — required for live streaming.
# Without these the build defaults to Chromium branding and lacks H.264/AAC,
# so Twitch/YouTube live fail to decode (Twitch error #4000,
# MediaSource.isTypeSupported('...avc1...,mp4a...') == false). VP9/AV1 (e.g.
# YouTube VOD) still work since they ship with Chromium. H.264 video decodes
# via the Android platform MediaCodec; AAC audio uses the bundled ffmpeg.
proprietary_codecs = true
ffmpeg_branding = "Chrome"
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
