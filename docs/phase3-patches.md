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

**ポップアップ表示フロー (変更後):**
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

**ポップアップ表示フロー (変更後):**
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

## 影響範囲

- 変更ファイル: 28 + 8 テスト関連（累計、Patch 1-10）
- C++ 変更: 3ファイル（JNI getter + スタブ + manifest handler ガード変更）+ 1 テスト
- Java 変更: 17ファイル（+2 new, +2 modify）+ 4 テスト
- GN 変更: 5ファイル（ビルド定義の移動 + bottomsheet 依存追加）+ 3 テスト target
- 既存コードの動作変更: `triggerPopup()` の表示を新しいタブ → BottomSheet に変更
- リスク: 低〜中（スタブは no-op のみ、既存デスクトップ動作に影響なし）
