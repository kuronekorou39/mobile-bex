# Android版Chromium ビルド環境構築ガイド

## 1. システム要件

| 項目 | 最低要件 | 推奨 |
|------|---------|------|
| OS | Ubuntu 22.04 LTS | Ubuntu 24.04 LTS (本プロジェクトの実績環境) |
| CPU | 4コア | 16コア以上 |
| RAM | 8GB (+32GB swap) | 32GB以上 |
| ディスク | 100GB SSD | 200GB以上 SSD |
| WSL2 | 可能（非公式） | ext4上で作業必須 |

**重要**: Windows/macOSから直接のAndroid Chromiumビルドは不可。Linux (Ubuntu) が必須。
本プロジェクトは WSL2 上の Ubuntu 24.04 でビルドしている。

## 2. depot_tools セットアップ

```bash
git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git
export PATH="$PATH:$(pwd)/depot_tools"
# ~/.profile に追記する（~/.bashrc ではない）
echo 'export PATH="$PATH:$HOME/depot_tools"' >> ~/.profile
```

**注意**: PATH の追記先は `~/.bashrc` ではなく `~/.profile`。Ubuntu の `~/.bashrc` は
冒頭の non-interactive guard で即 return するため、`wsl bash -c ...` のような
非対話シェルからのビルド実行時に `~/.bashrc` の設定が読まれない。

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

このチェックアウトは shallow（履歴1コミット）なので、タグを取るときは**そのタグだけを
depth=1 で取る**こと。`--with_tags` を付けて `gclient sync` すると全タグを取りに行き、
20GB 超の無駄なダウンロードになる（実際にやってしまった）。

```bash
git fetch --depth=1 origin refs/tags/153.0.8010.18:refs/tags/153.0.8010.18
git checkout --detach 153.0.8010.18
gclient sync -D
```

依存の取得で HTTP 429（レート制限）に当たることがある。少し置いて
`gclient sync -D` をもう一度流せば埋まる。

## 4. Android SDK/NDK

Chromiumは独自のSDK/NDKを `third_party/` 以下に自動管理。
手動インストール不要（`gclient sync` で自動取得）。

## 5. args.gn 設定

args.gn は `scripts/build.sh` が自動生成する（出力先は `out/MobileBex`）。
手で書く場合も以下と同じ内容にすること。

### 開発用（高速ビルド優先）

```gn
# out/MobileBex/args.gn
target_os = "android"
target_cpu = "arm64"

# Development build
is_debug = false
symbol_level = 0
is_component_build = false
is_official_build = false
is_chrome_branded = false
is_java_debug = true

# ccache（インストールされている場合のみ build.sh が付与）
cc_wrapper = "ccache"

# 拡張機能サポート
is_desktop_android = true

# ライブ配信に必要な proprietary codecs (H.264/AAC)
proprietary_codecs = true
ffmpeg_branding = "Chrome"
```

### リリース用

`--release` 指定時は Development build のブロックが以下に置き換わる（他は同じ）:

```gn
# Release build
is_debug = false
symbol_level = 0
is_component_build = false
is_official_build = true
is_chrome_branded = false
```

### `enable_extensions = true` を直接指定してはいけない

拡張機能の有効化は `is_desktop_android = true` だけで行う。これが
`enable_desktop_android_extensions` → `enable_extensions_core = true` という
Android 対応版の拡張機能構成に伝播する（`docs/history/phase1-results.md` 参照）。

`enable_extensions = true` を直接書くと、Android では app_shell
(`//extensions/shell` → `//apps`) を引き込み、50以上の BUILD.gn にある
`assert(!is_android)` に引っかかって `gn gen` 自体が失敗する
（`docs/history/patch-research.md` 参照）。この注意は `scripts/build.sh` の `generate_args`
内にもコメントとして残してある。

### proprietary_codecs が必要な理由

これを外すと Chromium branding のビルドになり H.264/AAC が同梱されないため、
Twitch/YouTube のライブ配信がデコードできない（Twitch はエラー #4000、
`MediaSource.isTypeSupported('...avc1...,mp4a...')` が false になる）。
VP9/AV1（YouTube の VOD 等）は Chromium 標準で入っているため影響しない。
H.264 の映像は Android プラットフォームの MediaCodec、AAC の音声は同梱 ffmpeg で処理される。

## 6. ビルドコマンド

```bash
# ビルド設定生成 + ビルド（推奨: args.gn 生成から一括で行う）
./scripts/build.sh

# 設定生成のみ
./scripts/build.sh --setup

# リリースビルド
./scripts/build.sh --release
```

`build.sh` を使わず直接叩く場合:

```bash
# GN設定生成（args.gn を上記の内容で用意しておくこと）
gn gen out/MobileBex

# Chrome APK ビルド
autoninja -C out/MobileBex chrome_public_apk
```

成果物: `out/MobileBex/apks/ChromePublic.apk`

### 実機へのインストール

WSL から `adb install` は行わず、APK を Windows 側にコピーして手動インストールする運用。

```bash
# WSL 側: APK を Windows のデスクトップへコピー
cp out/MobileBex/apks/ChromePublic.apk \
   /mnt/c/Users/<ユーザー名>/Desktop/mobile-bex-$(date +%m%d-%H%M).apk
```

コピーした APK を端末（Pixel 9a）へ転送して手動インストールする。

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

- **現在の土台**: Chromium 153.0.8010.18（Android の Stable、2026-08-26）
- 2026-09 に 147.0.7692.0 から載せ替えた。経緯と、そのとき上流に取り込まれて
  不要になったパッチは `patches/README.md` の「欠番について」を参照
- 実機検証は Pixel 9a / Android 17 で実施
