# mobile-bex パッチ

Chromium Android に拡張機能サポートを追加するためのパッチ群。

## ディレクトリ構成

```
patches/
├── phase1/    # 空: PoC はパッチ不要だった（下記参照）
├── phase2/    # 空: API 検証もパッチ不要だった
└── phase3/    # UX最適化: ツールバー・ポップアップ・sidePanel・omnibox 等（01〜26）
```

## Phase 1 / Phase 2 について

当初は buildflags 修正など8本程度のパッチを想定していたが、**Phase 1 の実測で
`is_desktop_android = true` を指定するだけで拡張機能の基盤（chrome://extensions、
Content Script 注入、権限UI、主要API）が動作することが判明した**。
そのため phase1/ と phase2/ にパッチは存在しない。
経緯は `docs/phase1-results.md` / `docs/phase2-results.md` を参照。

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

# パッチを元に戻す（26→01 の逆順で剥がされる）
./scripts/apply-patches.sh --reverse
```

## パッチ作成規則

- ファイル名は `NN-short-description.patch` 形式（NNは適用順序）
- **必ず適用対象の状態のツリーから `git diff` で生成する**（hunk ヘッダの手編集は
  corrupt patch の原因になるため禁止。過去に 09/10/13/14 で発生）
- 累積 diff にしない: パッチ NN は 01〜(NN-1) 適用後のツリーとの差分にする
- パッチ先頭にコメントで目的と変更概要を記載
- 生成後は clean なツリーで `./scripts/apply-patches.sh --dry-run` が全件 OK に
  なることを確認する
