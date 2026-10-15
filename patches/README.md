# mobile-bex パッチ

Chromium Android に拡張機能サポートを追加するためのパッチ群。

## ディレクトリ構成

```
patches/
├── phase1/    # 空: PoC はパッチ不要だった（下記参照）
├── phase2/    # 空: API 検証もパッチ不要だった
└── phase3/    # UX最適化: ツールバー・ポップアップ・sidePanel・omnibox 等（01〜48）
```

## Phase 1 / Phase 2 について

当初は buildflags 修正など8本程度のパッチを想定していたが、**Phase 1 の実測で
`is_desktop_android = true` を指定するだけで拡張機能の基盤（chrome://extensions、
Content Script 注入、権限UI、主要API）が動作することが判明した**。
そのため phase1/ と phase2/ にパッチは存在しない。
経緯は `docs/history/phase1-results.md` / `docs/history/phase2-results.md` を参照。

## Phase 3 パッチ一覧 (UX最適化)

全パッチは clean な Chromium 155.0.8059.40 への番号順フル適用で作業ツリーと
完全一致することを検証済み（`python3 scripts/regen-patches.py`）。
欠番があるのは、上流が同じ修正を取り込んだか、作り直しのため一時的に外した
パッチがあるため（下記「欠番について」を参照）。

| # | ファイル名 | 内容 |
|---|-----------|------|
| 01 | `01-toolbar-phone-extension-stub.patch` | toolbar_phone.xml に拡張機能ツールバー用の ViewStub を追加 |
| 02 | `02-toolbar-phone-extension-coordinator.patch` | 拡張機能ツールバーの生成をタブレット限定にしない（キャストを外す） |
| 14 | `14-omnibox-input-entered.patch` | omnibox onInputEntered 発火 + サジェスト閉じ修正 |
| 15 | `15-extensions-webui-mobile.patch` | chrome://extensions のスマホ幅表示対応 |
| 17 | `17-newtab-native-url-overriding.patch` | NTPオーバーライド用フラグ有効化 |
| 19 | `19-app-icon.patch` | アプリアイコンを BEX（ネオンウサギ）に変更（適応型/legacy/テーマ） |
| 20 | `20-app-name.patch` | アプリ表示名を BEX に変更 |
| 21 | `21-signin-add-account-no-crash.patch` | 「アカウントを追加」のクラッシュ防止と、サインイン導線の非表示 |
| 22 | `22-selectfiledialog-tree-uri.patch` | Android 15+ でフォルダ選択が常に失敗する問題を修正 |
| 23 | `23-unpacked-extension-copy.patch` | 未パッケージ拡張機能をプロファイル配下にコピーしてから読み込む |
| 24 | `24-load-unpacked-progress.patch` | 読み込み中の進捗プレースホルダ（点線枠＋スピナー）を表示 |
| 26 | `26-webstore-desktop-site.patch` | Chrome ウェブストアを既定でデスクトップ表示にする |
| 27 | `27-pip-menu.patch` | 三点メニューに「小窓表示」(PiP) を追加。PiP 中はツールバーを隠す |
| 28 | `28-ntp-hide-unusable.patch` | 新規タブの「AI モード」ボタンとおすすめ記事フィードを消す |
| 29 | `29-link-capturing.patch` | リンクで勝手にアプリへ飛ばさない（開くのはメニューからの明示操作のみ） |
| 30 | `30-background-playback.patch` | 画面を消しても再生を続ける（バックグラウンド再生） |
| 31 | `31-new-window-on-phones.patch` | スマホでも「新しいウィンドウ」を出す（上限は画面幅で決めない） |
| 32 | `32-extensions-ui-no-logo.patch` | chrome://extensions の Chromium ロゴを消す |
| 33 | `33-product-name-bex.patch` | UI 中の製品名を BEX にする（設定・通知・拡張機能のダイアログ） |
| 34 | `34-github-update-check.patch` | GitHub のリリースを見て更新を知らせる（Omaha の UI に載せる） |
| 36 | `36-incognito-extensions.patch` | シークレットモードで拡張機能を動くようにする |
| 37 | `37-extensions-detail-width.patch` | chrome://extensions の詳細ページが横に見切れるのを直す |
| 41 | `41-omnibox-no-multimodal-input.patch` | アドレスバーを普通の編集できる形に戻す（実験機能 Fusebox を無効化） |
| 42 | `42-omnibox-wrap-url.patch` | 長い URL をアドレスバーで折り返して編集できるようにする |
| 43 | `43-hard-reload-menu.patch` | 三点メニューに「ハードリロード」（キャッシュを無視して再読み込み）を追加 |
| 44 | `44-bex-menu-icons.patch` | 「小窓表示」「ハードリロード」にアイコンを付け、他の項目と行頭を揃える |
| 45 | `45-update-menu-product-name.patch` | 更新の案内の製品名を BEX にする（「Chrome を更新」→「BEX を更新」） |
| 46 | `46-extension-action-null-guards.patch` | 拡張機能アクションの null 参照でブラウザが落ちるのを防ぐ |
| 47 | `47-sidepanel-overlay-narrow-window.patch` | 幅の狭いウィンドウ（スマホの縦画面）ではサイドパネルをページに重ねて出す |
| 48 | `48-popup-autosize-ceil.patch` | 拡張機能ポップアップを開くたびにスクロールバーが一瞬出るのを直す（自動リサイズの端数を切り上げる） |

### 欠番について

**05 / 06** (popup-max-width / popup-open-as-tab): ポップアップ表示の中間形態。
09 の BottomSheet 方式で置き換えられたため削除。

**Chromium 155 へのリベース (2026-10) で外したもの**

上流 155 に Android 用の sidePanel 実装が入った（`chrome/browser/ui/android/extensions/side_panel/`、
`side_panel_api.cc` が Android でもビルド対象になった）。

| # | 元の内容 | 外した理由 |
|---|---------|-----------|
| 07 | sidePanel パーミッション許可 | 上流が `_permission_features.json` に `desktop_android` を追加した |
| 08 | chrome.sidePanel API スタブ | 上流の本物の API 実装と同じ BUILD.gn に入るため共存できない |
| 11 | sidePanel の右スライドオーバーレイ | 08 のスタブから呼ばれる UI。上流の実装をまず素の状態で使ってみる |
| 12 | sidePanel の onClicked 許可 | 08 のスタブ前提の回避策 |

**Chromium 153 へのリベース (2026-09) で外したもの**

上流が同じ問題を直したため不要になった:

| # | 元の内容 | 上流での対応 |
|---|---------|-------------|
| 03 | アクション一覧 RecyclerView の onMeasure 修正 | `ExtensionActionListRecyclerView` が書き直され、回避対象の assert が消えた |
| 04 | メニュー行クリックでポップアップ起動 | 上流が `executeAction()` を実装 |
| 13 | 拡張機能メニュー行のアイコン表示 | 上流が `ExtensionsMenuItemProperties.ICON` を実装 |
| 16 | `chrome.runtime.openOptionsPage()` のタブ実装 | 上流に Android 分岐が入った |
| 18 | DevTools の buildflag 修正 | 上流が `ENABLE_EXTENSIONS_CORE` に変更済み |
| 38 | 画面録画に音が入るようにする | 上流が `allowAudioPlaybackCapture="false"` の指定自体を削除 |
| 39 | Custom Tab が「繰り返し終了」で開けない | チップ生成が `TabbedRootUiCoordinator` に移り、落ちる経路が消えた |
| 40 | PDF タブがある状態での再起動クラッシュ | 上流が引数なしコンストラクタを追加 |

作り直しのために一時的に外したもの:

| # | 元の内容 | 外した理由 |
|---|---------|-----------|
| 09 / 10 / 25 | ポップアップの BottomSheet 表示とそのテスト | 上流のポップアップが自動リサイズ対応になったため、まず素の状態で使ってみる |
| 35 | 拡張機能のホーム画面ショートカット | 153 では `ExtensionsToolbarBridge` を作るとブラウザウィンドウに `ExtensionsContainer` として登録される。ショートカット機能が2個目を作ると二重登録で起動時に落ちるため、ツールバー側の bridge を共有する形に作り直してから戻す |

外したパッチの内容は Git 履歴に残っている（`git show 2a73135:patches/phase3/35-extension-shortcuts.patch` など）。

### 注意

- パッチは**シリーズとして番号順にフル適用**すること。中間状態は単体で
  ビルドが通るとは限らない（例: 09 が追加する Java は 11 の BUILD.gn 変更で登録される）。

## テスト

```bash
# ビルド (初回は依存が多く時間がかかる)
autoninja -C out/MobileBex chrome_junit_tests

# 実行
out/MobileBex/bin/run_chrome_junit_tests -f "*ExtensionBottomSheet*"
```

実機での確認手順は `docs/smoke-test.md` を参照。

## 適用方法

```bash
# ドライラン（実際には適用しない）
./scripts/apply-patches.sh --dry-run

# Phase 3 パッチを適用（デフォルト。phase1/2 は空なのでスキップされる）
./scripts/apply-patches.sh

# パッチを元に戻す（48→01 の逆順で剥がされる）
./scripts/apply-patches.sh --reverse
```

## パッチ作成規則

- ファイル名は `NN-short-description.patch` 形式（NNは適用順序）
- パッチ先頭にコメントで目的と変更概要を記載
- **手書きしない**。ソースツリーを編集したら `scripts/regen-patches.py` で
  生成・検証する（hunk ヘッダの手編集は corrupt patch の原因になるため禁止。
  過去に 09/10/13/14 で発生）

```bash
# 検証のみ: クリーンなツリーに 01→NN を全適用し、作業ツリーと一致するか確かめる
python3 scripts/regen-patches.py

# 既存パッチの担当ファイルを編集した後に作り直す
python3 scripts/regen-patches.py --regen 09,25

# 新しいパッチを足す（初回だけ担当ファイルを教える。以降は --regen だけでよい）
printf '# Patch 29: ...\n' > patches/phase3/29-foo.patch
python3 scripts/regen-patches.py --regen 29 --files path/to/a.java,path/to/b.cc
```

パッチは順番に重ねる差分なので、同じファイルを複数のパッチが触ることがある
（例: 04 が作ったクラスを 09 が変更する）。`--regen` で指定しなかったパッチは
そのまま適用されて土台になるため、累積 diff にはならない。

**後続のパッチが触っているファイルを、前のパッチで作り直すことはできない。**
再生成は作業ツリーの「最終形」を書き込むので、後続パッチが前提にしている中間状態が
消え、後続の適用が失敗する（例: 15 と 24 はどちらも `item_list.css` を触るため、
15 を作り直すと 24 が当たらなくなる）。この場合は末尾に新しいパッチを足す
（詳細ページの幅を 15 ではなく 37 にしたのはこの理由）。

コミット前には `scripts/validate-patches.py`（改行コードと hunk 行数の検査）も
通すこと。CI でも実行される。
