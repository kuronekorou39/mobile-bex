# バージョン管理と更新

GitHub のリリースから APK を直接配布する（サイドロード）ため、Play ストア経由の
自動更新は使えない。ここでは版数の付け方と、更新をどう届けるかを整理する。

## 版数

`VERSION` ファイルで管理し、リリースのたびに更新する。

```
NAME=0.1.0      # 利用者に見える版数
CODE=26080401   # Android の versionCode (YYMMDDNN)
```

**versionCode は単調増加でなければ端末が更新を受け付けない。** Chromium 由来の
versionCode はリベースしない限り変わらないため（同じ Chromium 版で2回リリース
すると更新できない）、独自に管理している。`build.sh` が `VERSION` を読んで
`android_override_version_name` / `android_override_version_code` に反映する。

## 署名鍵

**鍵を失うと、以後そのアプリを更新できなくなる。** 署名が変われば Android は
別アプリとして扱い、上書きインストールを拒否する（利用者は一度アンインストール
する必要があり、設定と拡張機能が消える）。

鍵はリポジトリ外に置き、必ずバックアップすること。作り方は
[release.md](release.md) を参照。

## 更新をどう届けるか

### アプリ内で更新を知らせる (Patch 34)

`BexUpdateChecker` が GitHub の API
(`https://api.github.com/repos/<owner>/<repo>/releases/latest`) から最新リリースを取り、
`tag_name` を今の版数と比べる。新しければ、Omaha が使うのと同じ SharedPreferences に
書き込む。以降の判定と UI（三点メニューの「更新」項目、ツールバーのバッジ）は
上流のものがそのまま動き、押すとリリースページが開く。

- 確認は起動時に1日1回まで。API のレート制限は未認証で 60 req/hour/IP
- 設定 → BEX について → 「更新を確認」から手動でも調べられる
- 版数の取得に `ApkInfo.getPackageVersionName()` は使えない。名前に反して、
  ブラウザとして起動した経路では Chromium の版数 (153.x) を返す。
  `BexUpdateChecker.getInstalledVersion()` が PackageManager から直接取る

### 併用: Obtainium

[Obtainium](https://github.com/ImranR98/Obtainium) は GitHub のリリースを監視して、
サイドロードしたアプリを更新してくれる Android アプリ。BEX 側の実装は不要で、
利用者がリポジトリの URL を登録するだけ。ダウンロードとインストールまで任せたい
場合はこちら。

### 実装しない方針: アプリ内での自動ダウンロード・インストール

APK を自分でダウンロードしてインストール intent を投げる方式は、
`REQUEST_INSTALL_PACKAGES` 権限が必要になる。この権限は「他のアプリを
インストールできる」という強い権限で、ブラウザに持たせるのは慎重になるべき。
利用者が明示的に操作する Obtainium 方式のほうが安全と判断している。

## リリース手順

1. `VERSION` を更新する（`CODE` は必ず前回より大きく）
2. 配布用ビルドを作る（[release.md](release.md)）
3. 動作を確認する（[smoke-test.md](smoke-test.md)）
4. GitHub にリリースを作成し、APK を添付する
5. リリースノートに以下を書く
   - 変更点
   - ベースにした Chromium のバージョン
   - **実験的ビルドであり、セキュリティ更新が保証されない旨**
