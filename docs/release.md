# 配布用ビルドの作り方

開発ビルドとの違いは次の2点。

- `debuggable_apks = false` — 開発ビルドは `android:debuggable="true"` のため、
  第三者がデバッガを接続したり `run-as` でアプリ内データを読める。配布物では落とす
  （開発ビルドで有効にしているのは、復旧スクリプトが `run-as` を使うため）
- 署名鍵 — 開発ビルドは Chromium のデバッグ鍵で署名される。配布物には自分の鍵を使う

なお `is_official_build = true` は本プロジェクトで未検証のため使っていない
（PGO プロファイル等の追加要件がある）。実績のある構成のまま、配布に不適切な
設定だけを落としている。

## 1. 署名鍵を作る（初回のみ）

```bash
keytool -genkeypair -v -keystore ~/bex-release.keystore \
  -alias bex -keyalg RSA -keysize 2048 -validity 10000
```

> [!IMPORTANT]
> 鍵とパスワードはリポジトリに置かないこと。`.gitignore` で `*.keystore` 等を
> 弾いているが、そもそもリポジトリ外に置くのが安全。
> **鍵を失うと、以後そのアプリを更新できなくなる**（署名が変わると別アプリ扱いに
> なり、上書きインストールできない）。必ずバックアップすること。

## 2. ビルド

```bash
export BEX_KEYSTORE_PATH=~/bex-release.keystore
export BEX_KEYSTORE_NAME=bex
export BEX_KEYSTORE_PASSWORD=<設定したパスワード>

./scripts/build.sh --setup --release
./scripts/build.sh --release
```

環境変数が未設定の場合はデバッグ鍵で署名される（配布不可）。`--setup` を忘れると
設定が反映されないが、その場合はビルドスクリプトがエラーで停止する。

## 3. 成果物

```
~/chromium/src/out/MobileBex/apks/ChromePublic.apk
```

## 配布時の注意

- **FFmpeg は LGPL v2.1+** のため、バイナリ配布にはソースの入手可能性を確保する
  義務がある。本リポジトリを公開していれば、使用した Chromium のバージョンと
  取得手順が README / docs から辿れる状態を保つこと
- H.264 / AAC のコーデック特許について、商用配布を行う場合は別途確認が必要
  （本ビルドは `proprietary_codecs = true`）
- リリースノートに、実験的ビルドである旨とセキュリティ更新が保証されない旨を
  明記すること
