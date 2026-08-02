#!/bin/bash
# mobile-bex: Chromium Android ビルド環境セットアップスクリプト
# Usage: ./scripts/setup.sh [--no-history] [--chromium-version VERSION]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CHROMIUM_DIR="${CHROMIUM_DIR:-$HOME/chromium}"
CHROMIUM_VERSION="${CHROMIUM_VERSION:-}"
NO_HISTORY=""

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --no-history) NO_HISTORY="--no-history"; shift ;;
    --chromium-version) CHROMIUM_VERSION="$2"; shift 2 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

# --no-history は shallow clone のため、特定バージョンの checkout ができない
if [[ -n "$NO_HISTORY" && -n "$CHROMIUM_VERSION" ]]; then
  echo "ERROR: --no-history と --chromium-version は併用できません"
  echo "  (shallow clone にはタグの対象コミットが含まれないため checkout が失敗します)"
  exit 1
fi

echo "=== mobile-bex: Chromium Android ビルド環境セットアップ ==="
echo "Chromium directory: $CHROMIUM_DIR"
echo ""

# --- 1. OS / WSL check ---
if [[ "$(uname -s)" != "Linux" ]]; then
  echo "ERROR: Android版Chromiumのビルドには Linux が必要です"
  echo "WSL2を使用している場合は、WSL2のターミナルからこのスクリプトを実行してください"
  echo "  wsl -e bash $(realpath "${BASH_SOURCE[0]}") $*"
  exit 1
fi

if grep -qi microsoft /proc/version 2>/dev/null; then
  echo ">>> WSL2環境を検出しました"
  # /mnt/ 以下で作業していないか確認
  if [[ "$CHROMIUM_DIR" == /mnt/* ]]; then
    echo "ERROR: ChromiumソースはWSL内のファイルシステムに置いてください"
    echo "  /mnt/c/ 等はNTFS経由でI/Oが極めて遅く、ビルドが実用になりません"
    echo "  推奨: CHROMIUM_DIR=\$HOME/chromium (デフォルト)"
    exit 1
  fi
fi

# --- 2. Disk space check ---
AVAILABLE_GB=$(df -BG --output=avail "$HOME" | tail -1 | tr -dc '0-9')
if (( AVAILABLE_GB < 100 )); then
  echo "WARNING: ディスク空き容量が ${AVAILABLE_GB}GB です (推奨: 150GB以上)"
  if [[ -t 0 ]]; then
    echo "続行しますか? [y/N]"
    read -r response
    [[ "$response" =~ ^[Yy]$ ]] || exit 1
  else
    echo "非対話実行のため中断します（容量を確保するか、対話シェルから実行してください）"
    exit 1
  fi
fi

# --- 3. depot_tools ---
if [[ ! -d "$HOME/depot_tools" ]]; then
  echo ">>> depot_tools をインストール中..."
  git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git "$HOME/depot_tools"
fi
export PATH="$PATH:$HOME/depot_tools"
# PATH は ~/.profile に書く。~/.bashrc は冒頭の non-interactive guard で
# `wsl -e bash` 等の非対話シェルから読まれないため効かない。
# 追記はファイル内容で判定して冪等にする。
if ! grep -qF 'depot_tools' "$HOME/.profile" 2>/dev/null; then
  echo 'export PATH="$PATH:$HOME/depot_tools"' >> "$HOME/.profile"
  echo "depot_tools を ~/.profile の PATH に追加しました"
else
  echo ">>> depot_tools: PATH 設定済み"
fi

# --- 4. Chromium source ---
if [[ ! -d "$CHROMIUM_DIR/src" ]]; then
  echo ">>> Chromiumソースを取得中... (30分〜数時間かかる場合があります)"
  mkdir -p "$CHROMIUM_DIR"
  cd "$CHROMIUM_DIR"
  fetch --nohooks $NO_HISTORY android
else
  echo ">>> Chromiumソース: 既に取得済み ($CHROMIUM_DIR/src)"
fi

cd "$CHROMIUM_DIR/src"

# --- 5. Checkout specific version ---
if [[ -n "$CHROMIUM_VERSION" ]]; then
  echo ">>> Chromium $CHROMIUM_VERSION にチェックアウト中..."
  git fetch --tags
  git checkout "tags/$CHROMIUM_VERSION"
fi

# --- 6. Install build dependencies ---
echo ">>> ビルド依存パッケージをインストール中..."
if [[ -f "build/install-build-deps.sh" ]]; then
  sudo bash build/install-build-deps.sh --no-prompt
fi
if [[ -f "build/install-build-deps-android.sh" ]]; then
  sudo bash build/install-build-deps-android.sh
fi

# --- 7. gclient sync & hooks ---
echo ">>> gclient sync を実行中..."
gclient sync
echo ">>> gclient runhooks を実行中..."
gclient runhooks

# --- 8. ccache setup ---
if ! command -v ccache &>/dev/null; then
  echo ">>> ccache をインストール中..."
  sudo apt-get install -y ccache
fi
ccache -M 50G
export CCACHE_CPP2=yes
export CCACHE_SLOPPINESS=time_macros

# --- 9. Create symlink to project ---
LINK_PATH="$CHROMIUM_DIR/mobile-bex"
if [[ -L "$LINK_PATH" ]]; then
  : # 作成済み
elif [[ -e "$LINK_PATH" ]]; then
  # 実ディレクトリが既にあると ln -sf はその中にリンクを作ってしまう
  echo "WARNING: $LINK_PATH が既に存在します（シンボリックリンクではありません）。リンク作成をスキップ"
else
  ln -s "$PROJECT_ROOT" "$LINK_PATH"
  echo ">>> シンボリックリンク作成: $LINK_PATH -> $PROJECT_ROOT"
fi

echo ""
echo "=== セットアップ完了 ==="
echo ""
echo "次のステップ:"
echo "  1. パッチを適用: ./scripts/apply-patches.sh"
echo "  2. ビルド設定:   ./scripts/build.sh --setup"
echo "  3. ビルド実行:   ./scripts/build.sh"
echo ""
echo "Chromium directory: $CHROMIUM_DIR/src"
