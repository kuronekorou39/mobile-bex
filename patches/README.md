# mobile-bex パッチ

Chromium Android に拡張機能サポートを追加するためのパッチ群。

## ディレクトリ構成

```
patches/
├── phase1/    # 空: PoC はパッチ不要だった（下記参照）
├── phase2/    # 空: API 検証もパッチ不要だった
└── phase3/    # UX最適化: ツールバー・ポップアップ・sidePanel・omnibox 等（01〜40）
```

## Phase 1 / Phase 2 について

当初は buildflags 修正など8本程度のパッチを想定していたが、**Phase 1 の実測で
`is_desktop_android = true` を指定するだけで拡張機能の基盤（chrome://extensions、
Content Script 注入、権限UI、主要API）が動作することが判明した**。
そのため phase1/ と phase2/ にパッチは存在しない。
経緯は `docs/history/phase1-results.md` / `docs/history/phase2-results.md` を参照。

## Phase 3 パッチ一覧 (UX最適化)

全パッチは clean な Chromium 147 (HEAD 8953804a86) への番号順フル適用で
作業ツリーと完全一致することを検証済み。05/06 は欠番（下記注記参照）。

| # | ファイル名 | 内容 |
|---|-----------|------|
| 01 | `01-toolbar-phone-extension-stub.patch` | toolbar_phone.xml に拡張機能アクション用 ViewStub 追加 |
| 02 | `02-toolbar-phone-extension-coordinator.patch` | ToolbarPhone への Coordinator 接続 |
| 03 | `03-extension-recycler-measure-fix.patch` | アクション一覧 RecyclerView の onMeasure 修正 |
| 04 | `04-menu-click-popup-trigger.patch` | メニュー行クリックでポップアップ起動 |
| 07 | `07-sidepanel-permission-allow.patch` | sidePanel パーミッション許可 |
| 08 | `08-sidepanel-api-stub.patch` | chrome.sidePanel API スタブ |
| 09 | `09-popup-bottomsheet.patch` | ポップアップの BottomSheet 表示（最終形態） |
| 10 | `10-tests.patch` | BottomSheet ポップアップの Robolectric テスト（25件） |
| 11 | `11-sidepanel-overlay.patch` | sidePanel の右スライドオーバーレイ実装 (Java/res/BUILD.gn) |
| 12 | `12-sidepanel-open-service-worker-fix.patch` | sidePanel C++ 側修正（SWからの open() / onClicked 許可） |
| 13 | `13-menu-extension-icons.patch` | 拡張機能メニュー行のアイコン表示 |
| 14 | `14-omnibox-input-entered.patch` | omnibox onInputEntered 発火 + サジェスト閉じ修正 |
| 15 | `15-extensions-webui-mobile.patch` | chrome://extensions のスマホ幅表示対応 |
| 16 | `16-runtime-open-options-page.patch` | chrome.runtime.openOptionsPage() のタブ実装 |
| 17 | `17-newtab-native-url-overriding.patch` | NTPオーバーライド用フラグ有効化 |
| 18 | `18-devtools-extensions-core-wip.patch` | DevTools buildflag 修正（**WIP: 起動ハング未解決**） |
| 19 | `19-app-icon.patch` | アプリアイコンを BEX（ネオンウサギ）に変更（適応型/legacy/テーマ） |
| 20 | `20-app-name.patch` | アプリ表示名を BEX に変更 |
| 21 | `21-signin-add-account-no-crash.patch` | 「アカウントを追加」のクラッシュ防止（null返却） |
| 22 | `22-selectfiledialog-tree-uri.patch` | Android 15+ でフォルダ選択が常に失敗する問題を修正 |
| 23 | `23-unpacked-extension-copy.patch` | 未パッケージ拡張機能をプロファイル配下にコピーしてから読み込む |
| 24 | `24-load-unpacked-progress.patch` | 読み込み中の進捗プレースホルダ（点線枠＋スピナー）を表示 |
| 25 | `25-popup-width-transparency.patch` | ポップアップの幅の扱いを改善（全幅化 / 見切れ防止） |
| 26 | `26-webstore-desktop-site.patch` | Chrome ウェブストアを既定でデスクトップ表示にする |
| 27 | `27-pip-menu.patch` | 三点メニューに「小窓表示」(PiP) を追加。PiP 中はツールバーを隠す |
| 28 | `28-ntp-hide-unusable.patch` | 新規タブの「AI モード」ボタンとおすすめ記事フィードを消す |
| 29 | `29-link-capturing.patch` | リンクで勝手にアプリへ飛ばさない。開くのはメニューからの明示操作のみ |
| 30 | `30-background-playback.patch` | 画面を消しても再生を続ける（バックグラウンド再生） |
| 31 | `31-new-window-on-phones.patch` | スマホでも「新しいウィンドウ」を出す（上限は画面幅で決めない） |
| 32 | `32-extensions-ui-no-logo.patch` | chrome://extensions の Chromium ロゴを消す |
| 33 | `33-product-name-bex.patch` | UI 中の製品名を BEX にする（設定・通知・拡張機能のダイアログ） |
| 34 | `34-github-update-check.patch` | GitHub のリリースを見て更新を知らせる（Omaha の UI に載せる） |
| 35 | `35-extension-shortcuts.patch` | 拡張機能をホーム画面のショートカットにする |
| 36 | `36-incognito-extensions.patch` | シークレットモードで拡張機能を動くようにする（落ちる／「現在のウィンドウなし」を解消） |
| 37 | `37-extensions-detail-width.patch` | chrome://extensions の詳細ページが横に見切れるのを直す |
| 38 | `38-allow-audio-capture.patch` | 画面録画に音が入るようにする（`allowAudioPlaybackCapture`） |
| 39 | `39-custom-tab-open-in-app-crash.patch` | 他アプリからのリンク（Custom Tab）が「繰り返し終了」で開けないのを直す（29 の副作用） |
| 40 | `40-pdf-fragment-restore-crash.patch` | PDF タブを開いたまま再起動すると落ちるのを直す（上流バグ: Fragment の引数なしコンストラクタ） |

### 欠番について

- **05** (popup-max-width) / **06** (popup-open-as-tab): ポップアップ表示の中間形態。
  09 の BottomSheet 方式で完全に置き換えられたため削除。
(10 は一度削除したが、2026-08-04 にテストを実際に動く状態にして復活させた。
`chrome_junit_tests` で 25 件すべて PASS することを確認済み。)

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

# パッチを元に戻す（40→01 の逆順で剥がされる）
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
