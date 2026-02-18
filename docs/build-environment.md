# Android版Chromium ビルド環境構築ガイド

## 1. システム要件

| 項目 | 最低要件 | 推奨 |
|------|---------|------|
| OS | Ubuntu 22.04 LTS | Ubuntu 22.04 LTS (ネイティブ) |
| CPU | 4コア | 16コア以上 |
| RAM | 8GB (+32GB swap) | 32GB以上 |
| ディスク | 100GB SSD | 200GB以上 SSD |
| WSL2 | 可能（非公式） | ext4上で作業必須 |

**重要**: Windows/macOSから直接のAndroid Chromiumビルドは不可。Linux (Ubuntu 22.04) が必須。

## 2. depot_tools セットアップ

```bash
git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git
export PATH="$PATH:$(pwd)/depot_tools"
# ~/.bashrc に追記推奨
echo 'export PATH="$PATH:$HOME/depot_tools"' >> ~/.bashrc
```

## 3. Chromiumソース取得

```bash
mkdir ~/chromium && cd ~/chromium

# Android向けソースの取得（履歴なしで高速化）
fetch --nohooks --no-history android

cd src

# 依存パッケージのインストール
build/install-build-deps.sh
build/install-build-deps-android.sh

# フック実行
gclient runhooks
```

### 特定バージョンのチェックアウト

```bash
git checkout tags/145.0.7632.45
gclient sync
```

## 4. Android SDK/NDK

Chromiumは独自のSDK/NDKを `third_party/` 以下に自動管理。
手動インストール不要（`gclient sync` で自動取得）。

## 5. args.gn 設定

### 開発用（高速ビルド優先）

```gn
# out/Default/args.gn
target_os = "android"
target_cpu = "arm64"
is_debug = false
symbol_level = 0
is_component_build = false
is_official_build = false
is_chrome_branded = false
is_java_debug = true
cc_wrapper = "ccache"

# 拡張機能サポート（パッチ適用後）
enable_extensions = true
```

### リリース用

```gn
target_os = "android"
target_cpu = "arm64"
is_debug = false
symbol_level = 0
is_component_build = false
is_official_build = true
is_chrome_branded = false
```

## 6. ビルドコマンド

```bash
# GN設定生成
gn gen out/Default

# Chrome APK ビルド
autoninja -C out/Default chrome_public_apk

# インストール & 起動
out/Default/bin/chrome_public_apk install
out/Default/bin/chrome_public_apk launch http://example.com
```

### ビルド時間目安

| CPUコア数 | クリーンビルド |
|----------|--------------|
| 4コア | 6-10時間 |
| 8コア | 3-6時間 |
| 16コア | 1.5-3時間 |
| 32コア | 45分-1.5時間 |

## 7. キャッシュ戦略（ccache）

```bash
sudo apt install ccache
export CCACHE_CPP2=yes
export CCACHE_SLOPPINESS=time_macros
ccache -M 50G
```

ホットキャッシュ時、リビルド時間を約50-70%短縮。

## 8. GitHub Actions CI

### Standard Runner: 不可

| 項目 | Standard Runner | Chromium要件 |
|------|----------------|-------------|
| ディスク | 14GB | 100GB+ |
| RAM | 16GB | 16GB+ |
| CPU | 2-4コア | 8コア以上推奨 |

### 推奨: Self-hosted Runner または Larger Runner

| 方式 | 費用 | スペック |
|------|------|---------|
| Self-hosted | 自前マシン費用のみ | 自由に設定可能 |
| Larger (16-core) | ~$7.56/ビルド | 16コア, 64GB RAM, 600GB SSD |
| Larger (32-core) | ~$14.76/ビルド | 32コア, 128GB RAM, 1200GB SSD |

## 9. 対象Chromiumバージョン

- **Stable最新**: Chrome 145 (145.0.7632.45) — 2026年2月
- パッチ対象としてstableブランチを使用
