# BEX — Chrome 拡張機能が動く Android ブラウザ

Android 版 Chromium を改造し、**PC 版の Chrome 拡張機能をスマートフォンで動かす**ブラウザです。
uBlock Origin による広告ブロック、Chrome ウェブストアからのインストール、
未パッケージ拡張機能の読み込みが実機で動作します。

<!-- スクリーンショットは docs/images/ に置いてここから参照する -->

## できること

- **任意の Chrome 拡張機能が動く** — 限定リストではなく、Manifest V3 の拡張機能を制限なく
- **Chrome ウェブストアからインストールできる** — 検索・インストール・起動・削除まで
- **未パッケージ拡張機能を読み込める** — 開発中の自作拡張機能をスマホで直接テストできる
- **拡張機能 UI がモバイルに最適化されている** — ツールバーのアイコン、BottomSheet 形式の
  ポップアップ、右スライドのサイドパネル、omnibox キーワード

### 動作確認済みの拡張機能

| 拡張機能 | 状態 |
|---|---|
| uBlock Origin Lite | 広告ブロックが動作 |
| 自作拡張（広告スキッパー / 通信可視化ツール等） | 動作 |

### 比較

Android で拡張機能に対応するブラウザは他にもありますが、多くは提供元が用意した
**限定的なリストからしか選べません**。BEX は任意の拡張機能を、ウェブストア経由でも
ローカルのフォルダからでも導入できます。

## 技術的な要点

Chromium 本体に 26 本のパッチを当てています（`patches/phase3/`）。主なものを挙げます。

### 上流のバグ修正

開発の過程で、Chromium の desktop-android 実装（Google が開発中の実験的構成）に
起因する問題をいくつか特定して修正しました。

- **Android 15+ でフォルダ選択が必ず失敗する**（Patch 22）
  未パッケージ拡張機能の読み込みでフォルダを選ぶと無言で失敗していた。原因は
  `checkContentUriPermission()` がツリー URI を評価できず例外を投げ、それが
  「権限なし」として握り潰されていたこと。logcat から特定。

- **`_locales` を持つ拡張機能でブラウザが落ちる**（Patch 23）
  外部ストレージのパスは通常のファイルパスと構造が異なるため、多言語対応の
  拡張機能を読み込むと `extension_l10n_util` の `NOTREACHED()` に到達して
  プロセスごと終了していた。選択されたフォルダをプロファイル配下にコピーしてから
  読み込む方式に変更し、再起動後に読み込めなくなる問題も同時に解消。

- **日常操作でのクラッシュ**
  テキスト選択後のスクロールやアプリ切替でクラッシュする問題の真因が、
  開発ビルドでのみ有効になる `DCHECK` だと特定。ビルド構成で無効化した上で、
  同種の設定反映漏れを検出する仕組みをビルドスクリプトに組み込んだ。

### モバイル向け UI の実装

- 拡張機能ポップアップの BottomSheet 表示（Patch 09）
- サイドパネルのオーバーレイ実装（Patch 11/12）— シークレットモードのプロファイル
  分離、画面回転時のリーク対策を含む
- `chrome://extensions` のスマホ幅対応（Patch 15）
- Chrome ウェブストアを既定でデスクトップ表示にする（Patch 26）—
  モバイル表示ではストアが利用できず、拡張機能を導入できないため

### パッチの再現性

パッチはすべて、**クリーンな Chromium ツリーに番号順で適用すると作業ツリーと
完全に一致する**ことを検証しています。CI（`.github/workflows/validate.yml`）で
パッチの整合性・改行コード・manifest を自動チェックしています。

## ビルド方法

環境構築の詳細は [docs/build-environment.md](docs/build-environment.md) を参照してください。

```bash
# 1. Chromium ソースの取得と環境構築
./scripts/setup.sh

# 2. パッチ適用
./scripts/apply-patches.sh

# 3. ビルド設定 + ビルド
./scripts/build.sh --setup
./scripts/build.sh
```

配布用（署名付き・非デバッグ）ビルド:

```bash
# 署名鍵を作る（初回のみ。鍵とパスワードはリポジトリに置かないこと）
keytool -genkeypair -v -keystore ~/bex-release.keystore \
  -alias bex -keyalg RSA -keysize 2048 -validity 10000

export BEX_KEYSTORE_PATH=~/bex-release.keystore
export BEX_KEYSTORE_NAME=bex
export BEX_KEYSTORE_PASSWORD=<設定したパスワード>

./scripts/build.sh --setup --release
./scripts/build.sh --release
```

## インストール

リリースページの APK をダウンロードし、端末の「提供元不明のアプリ」を許可して
インストールしてください。パッケージ名は `com.rou39.bex` で、Chrome や Chromium とは
別のアプリとして共存します。

## 注意事項

**これは実験的なビルドです。常用は推奨しません。**

- **セキュリティ更新は保証されません。** Chromium は約4週間ごとに脆弱性修正を
  公開しますが、このビルドが同じ速度で追随することはありません。既知の脆弱性が
  未修正のまま残っている可能性があります
- **パスワードやクレジットカード情報など、機微な情報の入力には使わないでください**
- ベースは Chromium の開発版スナップショットであり、安定版ではありません
- 拡張機能は自己責任で導入してください。ブラウザの全通信を読める権限を持ちます
- `devtools_page` を含む拡張機能を読み込むと、ブラウザが起動しなくなる既知の問題が
  あります（復旧手順は `scripts/strip-devtools-extension.py`）

## 既知の制限

- DevTools 拡張機能は未対応（上記の起動ハング）
- CRX / zip ファイルからの直接インストールは未対応（ウェブストア経由は可能）
- 拡張機能の自動更新は未対応
- iOS 版の予定はありません。iOS はブラウザエンジンの制約により、
  この方式を再現できません

## ライセンス

ベースとなる Chromium は BSD-3-Clause です。同梱している FFmpeg は
**LGPL v2.1+** であり、バイナリを配布する場合はそのソースの入手可能性を
確保する必要があります。third-party のライセンス表記はアプリ内の
`chrome://credits` から確認できます。

本リポジトリに含まれるパッチおよびスクリプトは Chromium と同じ BSD-3-Clause と
します。

## ドキュメント

- [ビルド環境](docs/build-environment.md)
- [パッチ一覧](patches/README.md)
- [Phase 1 結果](docs/phase1-results.md) / [Phase 2 結果](docs/phase2-results.md)
- [Phase 3 パッチ詳細](docs/phase3-patches.md) / [UI 検証結果](docs/phase3-ui-styles.md)
- [実機スモークテスト手順](docs/smoke-test.md)
