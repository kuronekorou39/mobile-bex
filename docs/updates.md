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

### 現在: 手動 + Obtainium (推奨)

利用者側の選択肢:

1. **GitHub のリリースページを見る** — 何も実装しなくてよい。リリースノートで
   変更点を伝える
2. **[Obtainium](https://github.com/ImranR98/Obtainium) を使う** — GitHub の
   リリースを監視して、サイドロードしたアプリを自動更新してくれる Android アプリ。
   BEX 側の実装は不要で、利用者がリポジトリの URL を登録するだけ

サイドロード配布ではこの2つが実用的な落としどころ。README に Obtainium での
登録方法を書いておけば、実質的に自動更新が実現できる。

### 将来の選択肢: アプリ内で更新を確認する

GitHub の API (`https://api.github.com/repos/<owner>/<repo>/releases/latest`) を
定期的に叩き、`tag_name` を現在の版数と比べて、新しければ通知やバナーを出す。

- 利点: 利用者が Obtainium を知らなくても気づける
- 注意: API のレート制限（未認証で 60 req/hour/IP）があるため、確認は1日1回程度に
  絞る。またネットワークアクセスが増えるので、既定で有効にするかは要検討

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
