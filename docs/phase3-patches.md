# Phase 3 パッチ — 拡張機能メニュー & ポップアップ表示

## 概要

Phase 2 で全APIが動作確認済みだが、以下のUIが未実装だった:
- ツールバーに拡張機能アイコンが表示されない
- 三点メニューに「拡張機能」項目がない
- 拡張機能ポップアップが表示されない（ツールバーのアイコンタップ時）

## 原因

Google は Desktop Android 向けに拡張機能UIを**ほぼ完全に実装済み**（30+ Java ファイル）だが、
**phone 用ツールバーレイアウトに `extension_toolbar_container_stub` が含まれていない**。
タブレット用レイアウト (`toolbar_tablet.xml`) にのみ存在する。

### コードフロー

```
ToolbarManager.initializeWithNative()
  → mControlContainer.findViewById(R.id.extension_toolbar_container_stub)
  → null (phone) / ViewStub (tablet)
  → null の場合、ExtensionToolbarCoordinator が作成されない
  → ツールバーに拡張機能アイコンが表示されない
```

### 三点メニュー

三点メニューの拡張機能項目は `TabbedAppMenuPropertiesDelegate.shouldShowExtensionsItem()` で制御:
```java
private boolean shouldShowExtensionsItem() {
    return ExtensionUi.isEnabled(getProfileFromTabModel());
}
```
→ `ExtensionUi.isEnabled()` → `ExtensionActionsBridge.extensionsEnabled()` → C++ `ExtensionsEnabledForDesktopAndroid()` → 非Google管理アカウントは `true`

## パッチ一覧

> **2026-08-02 再編**: 全パッチを WSL 作業ツリーから再生成し、clean な Chromium 147 への
> フル適用で作業ツリーと完全一致することを検証した。この際に **05/06/10 は削除**（05/06 は
> BottomSheet 方式で置き換えられた中間形態、10 はテストファイルが実在しなかったため）。
> また、パッチ化されずツリーにだけ存在していた変更を **16（openOptionsPage 実装）/
> 17（NTPオーバーライド用フラグ）/ 18（DevTools buildflag、WIP）** として追加した。
> 最新の一覧は `patches/README.md` を参照。以下の Patch 5/6/10 の節は経緯の記録として残す。

### Patch 1: `01-toolbar-phone-extension-stub.patch`
**ファイル**: `chrome/browser/ui/android/toolbar/java/res/layout/toolbar_phone.xml`

phone用ツールバーレイアウトに `extension_toolbar_container_stub` ViewStub を追加。
ToolbarManager がこの stub を見つけると、ExtensionToolbarCoordinator を作成し、
`extension_toolbar_container.xml` をインフレートして以下を表示:
- 拡張機能アクションボタン (RecyclerView)
- パズルアイコンメニューボタン
- 区切り線

### Patch 2: `02-toolbar-phone-extension-coordinator.patch`
**ファイル**: `chrome/browser/ui/android/toolbar/java/src/org/chromium/chrome/browser/toolbar/top/ToolbarPhone.java`

- `ExtensionToolbarCoordinator` の import 追加
- フィールド `mExtensionToolbarCoordinator` 追加
- `setExtensionToolbarCoordinator()` オーバーライド追加
- インコグニートモード切り替え時のテーマ更新対応

### Patch 3: `03-extension-recycler-measure-fix.patch`
**ファイル**: `chrome/browser/ui/android/toolbar/java/src/org/chromium/chrome/browser/toolbar/extensions/ExtensionActionListRecyclerView.java`

phone ツールバーでの起動クラッシュを修正。
`onMeasure()` の `MeasureSpec.AT_MOST` アサーションが phone レイアウトの
`wrap_content` 親で失敗する問題を回避。

### Patch 4: `04-menu-click-popup-trigger.patch`
**ファイル**: 8ファイル（ExtensionsMenu*, ExtensionActionList*, ExtensionToolbarCoordinatorImpl）

拡張機能メニューの行クリックでポップアップをトリガーする仕組みを実装:
- `ROW_CLICK_LISTENER` プロパティを追加
- メニュー行クリック → `executeUserAction()` → `triggerPopup()` のフロー
- ツールバーに固定されていない拡張機能のフォールバックアンカービュー

### Patch 5: `05-popup-max-width-constraint.patch` (Patch 6 で置き換え)
**ファイル**: `ExtensionActionPopup.java`

~~ポップアップの最大幅をスクリーンサイズに制約。~~
→ Patch 6 でリバート。スクロールなしでコンテンツが見切れる問題があった。

### Patch 6: `06-popup-open-as-tab.patch`
**ファイル**: 7ファイル（C++ 2 + Java 5）

> **注**: この「新しいタブで開く」方式は**中間形態**であり、Patch 9 で BottomSheet 方式に置き換えられた。
> 最終的なポップアップ表示は Patch 9 の BottomSheet。本節は経緯の記録。

拡張機能ポップアップを `AnchoredPopupWindow` ではなく**新しいタブで開く**ように変更。
モバイルでのフルスクリーン表示に対応。

**C++ 変更:**
- `extension_action_popup_contents.h/cc`: `GetPopupUrl()` JNI メソッド追加
  - `host_->initial_url().spec()` でポップアップURLを取得

**Java 変更:**
- `ExtensionActionPopupContents.java`: `getPopupUrl()` メソッド + Natives インターフェース追加
- `ExtensionActionListMediator.java`: `TabCreator` を追加、`triggerPopup()` をタブベースに変更
- `ExtensionActionListCoordinator.java`: `TabCreator` パラメータを伝播
- `ExtensionToolbarCoordinatorImpl.java`: `tabCreator` を ExtensionActionListCoordinator に渡す
- `ExtensionActionPopup.java`: Patch 5 の `setMaxWidth` をリバート

**ポップアップ表示フロー (Patch 6 時点の中間形態 — Patch 9 で置き換え済み):**
```
ユーザーが拡張機能アイコンをタップ
  → executeUserAction(actionId, TOOLBAR_BUTTON)
  → triggerPopup(actionId, nativeHostPtr)
  → ExtensionActionPopupContents.create(nativeHostPtr)
  → contents.getPopupUrl()  // JNI → C++ host_->initial_url()
  → TabCreator.createNewTab(popupUrl, FROM_CHROME_UI)
  → 新しいタブでポップアップHTML表示
  → contents.destroy()
```

## 期待される動作

全パッチ適用 + リビルド後:

1. **ツールバー**: 拡張機能アイコン（パズルアイコン）が URL バーの右側に表示
2. **パズルアイコン → メニュー**: インストール済み拡張機能の一覧、「管理」「Discover」リンク
3. **拡張機能タップ → BottomSheet**: `popup.html` が画面下からスライドアップ表示（画面の50-70%）
4. **スワイプダウン / 戻るボタン**: BottomSheet を閉じる
5. **window.close()**: 拡張機能 JS から BottomSheet を閉じる
6. **三点メニュー**: 「拡張機能」項目 → `chrome://extensions` を開く

## ビルド手順

```bash
# WSL で実行
cd ~/chromium/src
autoninja -C out/MobileBex chrome_public_apk
```

### Patch 7: `07-sidepanel-permission-allow.patch`
**ファイル**: `chrome/common/extensions/api/_permission_features.json`

sidePanel パーミッションの `platforms` に `desktop_android` を追加。
これにより拡張機能が `"permissions": ["sidePanel"]` を宣言できるようになる。

### Patch 8: `08-sidepanel-api-stub.patch`
**ファイル**: 6ファイル（5 modify + 1 new）

`chrome.sidePanel` API を Desktop Android で利用可能にするスタブ実装。
sidePanel API は `SidePanelService`（デスクトップ UI 依存）のため Android でコンパイル不可。
ヘッダー (`side_panel_api.h`) はそのまま利用し、スタブ `.cc` で全7関数を no-op / デフォルト値で実装。

**変更内容:**
1. `api_sources.gni`: `side_panel.idl` を base `schema_sources_` へ移動（API 登録コード生成を有効化）
2. `chrome/common/extensions/BUILD.gn`: `side_panel_info.cc/h` を `enable_extensions_core` セクションへ移動
3. `chrome_manifest_handlers.cc`: include/register のガードを `ENABLE_EXTENSIONS_CORE` に変更
4. `side_panel/BUILD.gn`: `assert(enable_extensions_core)` + 条件付きコンパイル（desktop: full, android: stub）
5. `side_panel_api_stub.cc`: **新規** — 全7関数のスタブ（setOptions/getOptions/setPanelBehavior/getPanelBehavior/open/getLayout/close）
6. `api/BUILD.gn`: `side_panel` を base `public_deps` へ移動

**効果**: sidePanel を使う拡張機能（例: Domain Traffic Inspector）の Service Worker が正常に登録される（status code 3 エラー解消）。

### Patch 9: `09-popup-bottomsheet.patch`
**ファイル**: 6ファイル（2 new + 4 modify）

拡張機能ポップアップの表示方式を「新しいタブ」から「BottomSheet」に変更。
`BottomSheetController` を使い、画面下からスライドアップするパネル内に
拡張機能の WebContents を表示する。

**新規ファイル:**
- `ExtensionBottomSheetContent.java`: `BottomSheetContent` インターフェース実装
  - ThinWebView を FrameLayout にラップ
  - 画面の70%（full）/ 50%（half）表示
  - スワイプダウンで閉じる対応
  - 戻るボタンで dismiss
- `ExtensionBottomSheetCoordinator.java`: ライフサイクル管理
  - PaymentHandlerCoordinator パターンに準拠
  - `showPopup()`: WebContents → ContentView → ThinWebView → BottomSheet 表示
  - `hide()`: BottomSheet 非表示 → ThinWebView/Contents 破棄
  - `onClose` delegate で `window.close()` に対応

**変更ファイル:**
- `ExtensionActionListMediator.java`: `triggerPopup()` を BottomSheet 表示に変更
  - `TabCreator` 削除 → `ExtensionBottomSheetCoordinator` 使用
  - `closeCurrentSheet()` メソッド追加
- `ExtensionActionListCoordinator.java`: `TabCreator` パラメータ削除
- `ExtensionToolbarCoordinatorImpl.java`: `tabCreator` を渡さないように変更
- `BUILD.gn`: bottomsheet / thin_webview / content_view 依存追加

**ポップアップ表示フロー (最終形):**
```
ユーザーが拡張機能アイコンをタップ
  → executeUserAction(actionId, TOOLBAR_BUTTON)
  → triggerPopup(actionId, nativeHostPtr)
  → ExtensionActionPopupContents.create(nativeHostPtr)
  → ExtensionBottomSheetCoordinator.showPopup()
    → contents.getWebContents()
    → ContentView + ThinWebView 作成
    → ExtensionBottomSheetContent でラップ
    → BottomSheetController.requestShowContent()
    → contents.loadInitialPage()
  → 画面下からスライドアップで表示
```

### Patch 10: `10-tests.patch`
**テスト種別**: Robolectric (JVM) + GTest (C++) + Instrumentation (実機)

Phase 3 パッチのコード変更に対する自動テスト。カバレッジ目標 80%+。

**新規テストファイル:**

| ファイル | 種別 | テスト数 | 対象 |
|---------|------|---------|------|
| `ExtensionBottomSheetContentTest.java` | Robolectric | 13 | BottomSheetContent ラッパー全メソッド |
| `ExtensionBottomSheetCoordinatorTest.java` | Robolectric | 9 | showPopup 成功/失敗, hide, cleanup |
| `ExtensionActionListMediatorPopupTest.java` | Robolectric | 4 | triggerPopup, closeCurrentSheet, destroy |
| `side_panel_api_stub_unittest.cc` | GTest | 7 | sidePanel スタブ 7 API |
| `ExtensionPopupBottomSheetTest.java` | Instrumentation | 3 | BottomSheet E2E 表示 |

**BUILD.gn 変更:**
- `chrome/browser/ui/android/extensions/BUILD.gn`: `robolectric_binary("extensions_bottomsheet_junit_tests")` 追加
- `chrome/browser/ui/android/toolbar/java/BUILD.gn`: 既存 junit target に `ExtensionActionListMediatorPopupTest.java` 追加
- `chrome/browser/extensions/api/side_panel/BUILD.gn`: `test("side_panel_api_stub_unittest")` 追加

**ビルド・実行コマンド:**
```bash
# Robolectric テスト (JVM, ~30秒)
autoninja -C out/MobileBex extensions_bottomsheet_junit_tests
out/MobileBex/bin/run_extensions_bottomsheet_junit_tests

# C++ テスト (ホスト, ~10秒)
autoninja -C out/MobileBex side_panel_api_stub_unittest
out/MobileBex/side_panel_api_stub_unittest

# Instrumentation テスト (実機, ~5分)
autoninja -C out/MobileBex chrome_public_test_apk
out/MobileBex/bin/run_chrome_public_test_apk -f '*ExtensionPopupBottomSheet*'
```

**カバレッジ見積:**

| コンポーネント | 行数 | カバー率 |
|--------------|------|---------|
| ExtensionBottomSheetContent.java | 109 | ~95% |
| ExtensionBottomSheetCoordinator.java | 121 | ~85% |
| ExtensionActionListMediator (変更部分) | ~35 | ~80% |
| side_panel_api_stub.cc | 69 | ~100% |
| **合計** | ~334 | **~87%** |

### Patch 11: `11-sidepanel-overlay.patch`
**ファイル**: 8ファイル（5 new + 3 modify）

Patch 8 で no-op スタブだった `sidePanel.open()` / `close()` を、
**画面右からスライドインする Dialog オーバーレイ**として実装。

**新規ファイル:**
- `ExtensionSidePanelBridge.java`: C++ から呼ばれる JNI エントリポイント。
  Coordinator を static 保持して showSidePanel / closeSidePanel を仲介
- `ExtensionSidePanelCoordinator.java`: オーバーレイ本体
  - WebContents → ContentView → ThinWebView を Dialog に載せる（BottomSheet と同じ構成）
  - 幅は画面の70% (`WIDTH_RATIO = 0.7f`)、高さは `MATCH_PARENT`、`Gravity.END` で右寄せ
  - 背景を 0.4 の dim（scrim）、外側タップで閉じる
- `res/anim/extension_side_panel_enter.xml` / `_exit.xml`: 右からのスライドアニメーション
- `res/values/styles.xml`: 上記アニメを束ねる `ExtensionSidePanelAnimation` スタイル

**変更ファイル:**
- `side_panel_api_stub.cc`: `open()` / `close()` を JNI 経由のオーバーレイ表示/非表示に変更
- `extension_action_view_model.cc`: デスクトップ以外（`!ENABLE_EXTENSIONS`）でも
  `SidePanelInfo::HasSidePanel()` を見て sidePanel アクションを持つと判定するよう分岐追加。
  `SidePanelService` が使えない desktop-android でもアイコンが有効になる
- `BUILD.gn` 2ファイル: 新規 Java/リソースと依存の追加

**注意点:**
- パッチのヘッダコメントは "left-slide overlay" のままだが、実装は右スライド（Patch 12 でコメントも修正）
- `chrome/browser/ui/android/extensions/BUILD.gn` の `java_resources` に
  `java/res/values/strings.xml` を追加しているが、このファイル自体はパッチに含まれない（既存前提）

### Patch 12: `12-sidepanel-open-service-worker-fix.patch`
**ファイル**: `chrome/browser/extensions/api/side_panel/side_panel_api_stub.cc`

Service Worker から `chrome.sidePanel.open()` を呼んだときにパネルが出ない問題の修正。

**問題**: Patch 11 の実装は `GetSenderWebContents()` で対象タブを取得していたが、
Service Worker コンテキスト（例: `action.onClicked` ハンドラ）からの呼び出しでは
これが null を返すため、何も起きずに終了していた。

**修正**: `open()` の引数 `options.tabId` から `ExtensionTabUtil::GetTabById()` で
WebContents を解決することを優先し、取れなければ従来どおり `GetSenderWebContents()` に
フォールバックする。これで popup / Service Worker の両コンテキストから開けるようになる。

### Patch 13: `13-menu-extension-icons.patch`
**ファイル**: 3ファイル（C++ 1 + Java 2）

拡張機能メニューの各行に拡張機能の `default_icon` を表示する
（Chromium 側は `TODO(crbug.com/471016915)` でアイコン未実装だった）。

**C++ 変更:**
- `extensions_menu_delegate_android.cc`:
  - `ControlState` の生成時に `gfx::ImageSkia` → `SkBitmap` → `gfx::ConvertToJavaBitmap()` で
    Java の Bitmap に変換して渡す
  - アイコンサイズのプレースホルダ `gfx::Size()` を `gfx::Size(24, 24)` に変更

**Java 変更:**
- `ExtensionsMenuTypes.java`: `ControlState` に `@Nullable Bitmap icon` フィールドと
  コンストラクタ引数を追加（`@CalledByNative` のシグネチャ変更）
- `ExtensionsMenuMediator.java`: `PropertyModel` の組み立てを Builder 変数経由に変え、
  アイコンがある行だけ `ExtensionsMenuItemProperties.ICON` をセット

**注意点**: `ControlState` のコンストラクタは JNI 経由で呼ばれるため、
C++ 側 (`CreateJavaControlState`) と Java 側の引数を必ず同時に変更すること。

### Patch 14: `14-omnibox-input-entered.patch`
**ファイル**: 4ファイル（C++ 2 + Java 2）

アドレスバーで拡張機能のキーワード（例: `bex `）を確定したときに、
`chrome.omnibox.onInputEntered` を拡張機能へ発火させる。
Android の omnibox はデスクトップの `ChromeOmniboxClient::ProcessExtensionMatch` 相当の
処理を持っておらず、キーワード match が通常のナビゲーションとして扱われていた。

**C++ 変更:**
- `autocomplete_controller_android.h/cc`: `ProcessExtensionKeywordMatch()` を追加
  - match の `TemplateURL` が `OMNIBOX_API_EXTENSION` 型かを判定
  - `AutocompleteInput::SplitKeywordFromInput()` でキーワード部分を除去
  - `extensions::ExtensionOmniboxEventRouter::OnInputEntered()` を発火し、true を返す

**Java 変更:**
- `AutocompleteController.java`: `processExtensionKeywordMatch()` と JNI 宣言を追加
- `AutocompleteMediator.java`: `loadUrlForOmniboxMatch()` で上記を呼び、
  true（拡張機能が処理した）なら URL ロードをスキップして早期 return

**注意点:**
- 早期 return する分岐では、通常経路が末尾で呼ぶ `mHandler.post(this::finishInteraction)` を
  自前で呼ぶ必要がある。これを忘れるとサジェスト一覧が閉じず、遷移後のページを覆ってしまう
  （実機で確認された症状。修正は適用済み・リビルド検証待ち。詳細は `docs/phase3-ui-styles.md` の #10 参照）
- コミット済みのパッチファイルにはこの `finishInteraction` の1行がまだ入っていない

### Patch 15: `15-extensions-webui-mobile.patch`
**ファイル**: 4ファイル（HTML 1 + CSS 3）

`chrome://extensions` をスマホ幅で使えるようにする WebUI 側のスタイル調整。
デスクトップ前提のレイアウトのままだと、横スクロールが出る・ボタンが画面外に出る等で操作できなかった。

**変更内容:**
- `extensions.html`: `<meta name="viewport" content="width=device-width, initial-scale=1">` を追加
- `item_list.css`: 680px 以下で拡張機能カードを1カラム表示にし、余白を縮小
- `manager.css`: 680px 以下でトーストを折り返し表示（`--cr-toast-white-space: normal`）。
  デベロッパーモード Off 通知などの長文が1行で切れるのを防ぐ
- `toolbar.css`: 680px 以下でボタン群を `flex-wrap` で折り返し、
  モバイルでほぼ使わない「拡張機能をパッケージ化」ボタンを非表示に

**注意点**: ブレークポイントは 3 つの CSS で 680px に揃えてある。変更する場合は全て同時に。

## 影響範囲

**Patch 1〜10 時点の集計:**

- 変更ファイル: 28 + 8 テスト関連（累計、Patch 1-10）
- C++ 変更: 3ファイル（JNI getter + スタブ + manifest handler ガード変更）+ 1 テスト
- Java 変更: 17ファイル（+2 new, +2 modify）+ 4 テスト
- GN 変更: 5ファイル（ビルド定義の移動 + bottomsheet 依存追加）+ 3 テスト target
- 既存コードの動作変更: `triggerPopup()` の表示を新しいタブ → BottomSheet に変更
- リスク: 低〜中（スタブは no-op のみ、既存デスクトップ動作に影響なし）

**Patch 11〜15 での追加分:**

| パッチ | 変更ファイル数 | 内訳 |
|---|---|---|
| 11: sidepanel-overlay | 8 | Java 2 new + リソース 3 new + C++ 2 + GN 2（`side_panel_api_stub.cc` は C++ に計上） |
| 12: sidepanel-open-service-worker-fix | 1 | C++ 1 |
| 13: menu-extension-icons | 3 | C++ 1 + Java 2 |
| 14: omnibox-input-entered | 4 | C++ 2 + Java 2 |
| 15: extensions-webui-mobile | 4 | HTML 1 + CSS 3 |

- 既存コードの動作変更: `sidePanel.open()` が no-op から実際のオーバーレイ表示に、
  omnibox のキーワード確定が通常ナビゲーションから拡張機能イベント発火に変わる
- リスク: 低〜中（いずれも desktop-android 側の分岐 or Android 専用ファイルに閉じている。
  ただし Patch 13 は `@CalledByNative` のシグネチャを変えるため C++/Java の同期が必須）
