#!/bin/bash
# mobile-bex: Chromium Android ビルドスクリプト
# Usage: ./scripts/build.sh [--setup] [--target TARGET] [--cpu CPU] [--release] [--out DIR]
#   --out は src からの相対パス（デフォルト: out/MobileBex）
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

if [[ "$OUT_DIR" == /* ]]; then
  echo "ERROR: --out は src からの相対パスで指定してください (例: out/MobileBex)"
  exit 1
fi

if [[ ! -d "$CHROMIUM_SRC" ]]; then
  echo "ERROR: Chromiumソースが見つかりません: $CHROMIUM_SRC"
  exit 1
fi

# 非対話シェル（wsl -e bash 等）では ~/.profile が読まれず depot_tools が
# PATH に無いことがあるため、ここで補う
if ! command -v gn &>/dev/null && [[ -d "$HOME/depot_tools" ]]; then
  export PATH="$PATH:$HOME/depot_tools"
fi

cd "$CHROMIUM_SRC"

# --- Generate args.gn ---
# 第1引数に出力先を指定できる（省略時は $OUT_DIR/args.gn）。
generate_args() {
  local args_file="${1:-$CHROMIUM_SRC/$OUT_DIR/args.gn}"
  mkdir -p "$(dirname "$args_file")"

  if [[ "$args_file" == "$CHROMIUM_SRC/$OUT_DIR/args.gn" ]]; then
    echo ">>> args.gn を生成中: $args_file"
  fi

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

# 非officialビルドはデフォルトで DCHECK / Java assert が有効になり、
# 上流の実験的コード (desktop-android) の assert を踏むたびにクラッシュする
# (実例: GPU watchdog の !is_backgrounded_ DCHECK、FrozenNativePage.getView の
#  AssertionError)。日常使用に耐えるようリリース版 Chrome 相当に無効化する。
dcheck_always_on = false
enable_java_asserts = false
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
  local args_file="$CHROMIUM_SRC/$OUT_DIR/args.gn"
  if [[ ! -f "$args_file" ]]; then
    echo "ビルド設定が見つかりません。先にセットアップします..."
    setup_build
  else
    # 既存 args.gn が build.sh の生成内容と一致するか検証する。
    # (build.sh を更新しても --setup を実行し忘れると、設定が反映されないまま
    #  ビルドが通ってしまい原因究明が極めて困難になる。実際に
    #  dcheck_always_on=false の反映漏れでレンダラークラッシュを追う羽目になった)
    local expected_args
    expected_args="$(mktemp)"
    generate_args "$expected_args" > /dev/null
    if ! diff -q "$expected_args" "$args_file" > /dev/null 2>&1; then
      echo "ERROR: $OUT_DIR/args.gn が build.sh の生成内容と一致しません。"
      echo "       差分 (左: 期待値 / 右: 現在):"
      diff "$expected_args" "$args_file" | sed 's/^/         /' || true
      echo ""
      echo "       次を実行して設定を反映してください（全体の再ビルドになります）:"
      echo "         ./scripts/build.sh --setup"
      rm -f "$expected_args"
      exit 1
    fi
    rm -f "$expected_args"
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
