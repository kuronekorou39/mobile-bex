#!/bin/bash
set -euo pipefail
export PATH="$HOME/depot_tools:$PATH"

mkdir -p ~/chromium
cd ~/chromium

echo "=== Chromiumソース取得開始: $(date) ==="
echo "fetch --nohooks --no-history android を実行中..."
echo "(30分〜数時間かかります)"

fetch --nohooks --no-history android 2>&1 | tee ~/chromium-fetch.log

echo "=== fetch完了: $(date) ==="

cd src

echo ">>> ビルド依存パッケージをインストール中..."
sudo apt-get update -y
./build/install-build-deps.sh --no-prompt --no-chromeos-fonts
./build/install-build-deps-android.sh

echo ">>> gclient runhooks を実行中..."
gclient runhooks

echo ">>> ccache をセットアップ中..."
sudo apt-get install -y ccache
ccache -M 50G

echo "=== セットアップ完了: $(date) ==="
echo "Chromium src: $(pwd)"
du -sh ~/chromium/
