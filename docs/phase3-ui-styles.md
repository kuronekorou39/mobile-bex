# Phase 3: 拡張機能 UI スタイル対応状況

> 2026-05-29 / 2026-05-30 Pixel 9a (Android 16) / Chromium 147.0.7692.0 (Developer Build) で実機テスト実施。
> ビルド構成: `is_desktop_android = true` + Patch 1〜12 + 未コミット作業 (Patch 13/14 + Phase 3b 修正試行 3 件) すべて適用済み。

## テスト結果サマリ

| # | 拡張 / スタイル | テスト拡張ディレクトリ | 結果 | 関連修正 |
|---|---|---|---|---|
| 1 | Content Script | `test-extension` | ✅ PASS | Phase 1 (パッチなし) |
| 2 | Popup + API | `test-extension-phase2` | ✅ PASS | Phase 2 + Patch 1〜4,9 |
| 3 | Side Panel | `test-extension-sidepanel` | ✅ PASS (初回FAIL→リトライPASS) | Patch 7,8,11,12 |
| 4 | Full Tab Page | `test-extension-fulltab` | ✅ PASS | Phase 2 |
| 5 | Options Page | `test-extension-options` | ✅ PASS | **Phase 3b: chrome_runtime_api_delegate.cc** |
| 6 | Notifications | `test-extension-notifications` | ✅ PASS | (OS権限懸念は杞憂) |
| 7 | Context Menus | `test-extension-contextmenu` | ⚠️ 部分PASS | page/link/image OK、selection NG |
| 8 | New Tab Override | `test-extension-newtab` | ✅ PASS | **Phase 3b: chrome_feature_list.cc** |
| 9 | DevTools Panel | `test-extension-devtools` | ❌ **FAIL (起動阻害)** | **Phase 3b: devtools_ui_bindings.cc 修正不完全** |
| 10 | Omnibox | `test-extension-omnibox` | ❌ **FAIL (Enter発火なし)** | **Patch 14 未動作** |

### 追加で動作確認できた項目

- ✅ **Patch 13 (メニューアイコン)**: 拡張機能メニューの各行に default_icon が正しく表示される

## Phase 3b 修正成果まとめ

未コミット時点で `~/chromium/src` に入っていた Phase 3b の試行修正:

| 修正対象ファイル | 内容 | 結果 |
|---|---|---|
| `chrome_runtime_api_delegate.cc` | `OpenOptionsPage()` を `NOTIMPLEMENTED` から TabModel 経由の新タブ open に実装 | ✅ 動作確認 |
| `chrome_feature_list.cc` | `kChromeNativeUrlOverriding` を `ENABLED_BY_DEFAULT` に変更 | ✅ 動作確認 (NTPオーバーライド OK) |
| `devtools_ui_bindings.cc` | `ENABLE_EXTENSIONS` → `ENABLE_EXTENSIONS_CORE` でAndroidに開放 | ❌ **不完全。起動阻害を誘発** |

## 詳細

### #1 Content Script — PASS
全URLでページ上部に青いバナー注入。Phase 1 と同じ動作を再確認。

### #2 Popup + API — PASS（+ Patch 13 同時確認）
- BottomSheet ポップアップ (Patch 9) 正常表示
- 拡張機能メニュー内に **アイコン表示 (Patch 13)** が正しく動作
- chrome.runtime / chrome.storage / chrome.tabs の各APIテスト 全PASS

### #3 Side Panel — PASS (初回FAILの注意点あり)
- 右からスライドイン (Patch 11)
- 7 API (setOptions/getOptions/setPanelBehavior/getPanelBehavior/open/getLayout/close) 全PASS
- **既知のクセ**: 初回の API テストは失敗、リトライで成功。Service Worker のlazy startup タイミング起因と推測（Phase 3 の修正起因ではない）

### #4 Full Tab Page — PASS
`chrome.tabs.create()` で新タブに拡張機能ページ表示。chrome-extension:// URL が正常動作、`chrome.runtime.id`/`getURL()`/`chrome.tabs` 全アクセス可能。

### #5 Options Page — PASS（CSP修正後）
- **当初FAIL**: popup.html 内に `<script>...</script>` インラインスクリプトがあり Manifest V3 の CSP `script-src 'self'` に違反していた（拡張機能テストコード側のバグ、Phase 3b 修正とは無関係）
- popup.js への分離後、`chrome.runtime.openOptionsPage()` 経由で**新タブに options.html が開く** → Phase 3b の `chrome_runtime_api_delegate.cc` 修正動作確認

### #6 Notifications — PASS
通知バーへの表示、各種オプション、クリアまで全て動作。事前に懸念していた OS 通知権限の問題は発生せず。

### #7 Context Menus — 部分 PASS
- ✅ page (ページ長押し) — "Show Page Info" 動作
- ✅ link (リンク長押し) — "Copy Link Domain" 動作
- ✅ image (画像長押し) — "Show Image Size" 動作
- ❌ **selection (テキスト選択時)** — **Android のテキスト選択UI (カット/コピー/共有バー) に統合されず、長押しメニュー自体が出ない**
- 結論: contextMenus 自体は動くが、Android 特有のテキスト選択ハンドリングと拡張機能 contextMenus の統合は Chromium Android 側で未実装。要別途調査

### #8 New Tab Override — PASS
- タブバーの「+」ボタンで新規タブを開く → カスタム `newtab.html` 表示
- Phase 3b の `chrome_feature_list.cc` で `kChromeNativeUrlOverriding = ENABLED_BY_DEFAULT` に切り替えた効果が出ている
- メニューからの「新しいタブ」や URLバー長押しの「新しいタブ」では別経路でカスタムNTP に飛ばない可能性あり (未深堀)

### #9 DevTools Panel — FAIL（起動阻害）
- **症状**: `devtools_page` を含む拡張機能を Chromium に読み込み登録すると、**次回以降の起動時にスプラッシュ画面でハング**する
- 再現性: 100% (Preferences から該当エントリを削除しない限り Chromium が起動不能)
- logcat 観測: `Child process died (type=6)` (Zygote プロセス) のループ発生
- ANR や FATAL は出ない（プロセスは生きているが UI thread が初期化を完了しない）
- **復旧手順** (記録用):
  1. `adb shell run-as org.chromium.chrome cat /data/data/org.chromium.chrome/app_chrome/Default/Preferences > prefs.json` で Preferences を取得
  2. JSON の `extensions.settings` から `devtools_page` 持ちエントリ or path に `devtools` を含むエントリを削除
  3. `adb push fixed.json /data/local/tmp/`
  4. `adb shell run-as org.chromium.chrome cp /data/local/tmp/fixed.json /data/data/.../Preferences`
  5. Chromium 起動 → 復活
  - スクリプト化済み: `scripts/strip-devtools-extension.py`, `scripts/strip-all-extensions.py`
- **原因仮説**: `devtools_ui_bindings.cc` の `ENABLE_EXTENSIONS_CORE` ガード変更だけでは不十分。起動シーケンス中の他の DevTools 初期化コードパスで未対応のコードがあり、デッドロックまたは無限再試行ループを誘発している
- **次のアクション**: 起動シーケンス中の DevTools 関連コードの完全な棚卸し + 追加パッチが必要。当面は devtools_page を持つ拡張機能を使わない運用にする

### #10 Omnibox — FAIL (Patch 14 未動作)
- **症状**:
  - アドレスバーに `bex ` 入力 → サジェスト一覧表示 ✅ (`onInputStarted` / `onInputChanged` 動作)
  - 続けて文字入力 → サジェストがフィルタされる ✅
  - **Enter キー押下 → 何も起きない / または Chrome のフォールバックで「このサイトにアクセスできません」**
  - **サジェスト項目をタップ → これも何も起きない**
  - 結果: `chrome.tabs.update({url})` が呼ばれず、ナビゲーションも遷移も発生しない
- **Patch 14 の実装内容** (パッチ作成済み・適用済み):
  - C++: `AutocompleteControllerAndroid::ProcessExtensionKeywordMatch` 追加（extension keyword の match を検出して `ExtensionOmniboxEventRouter::OnInputEntered` を発火）
  - Java: `AutocompleteController.processExtensionKeywordMatch` 追加 (JNI bridge)
  - Java: `AutocompleteMediator.loadUrlFromOmniboxMatch` で extension keyword 判定 + 早期 return
- **仮説の絞り込み** (2026-06-01 追加):
  - **タップとEnter の両方が発火しない**ことから、Patch 14 が修正を入れた `AutocompleteMediator.loadUrlFromOmniboxMatch` は **Android omnibox の選択確定経路ではない**可能性が高い。
  - 実際の経路は `SuggestionListMediator.onItemSelected` または `OmniboxSuggestionsAdapter.onSuggestionClicked` のような別レイヤーである可能性。
  - 別仮説として、`loadUrlFromOmniboxMatch` は呼ばれているが、`processExtensionKeywordMatch` の中で `template_url->type() != OMNIBOX_API_EXTENSION` で false を返している ケースも残るが、その場合は早期 return せず通常ナビゲーションが走る (「アクセスできません」が出る)
  - 両症状が混在しているのは、入力タイミング/タブ状態によってフローが変わる可能性
- **次のアクション**:
  1. Service Worker / Native の logcat 確認（Service Worker の `console.log("[mobile-bex] Omnibox entered: ...")` が出ているかが一次切り分け）
  2. **Java 側のフック地点の見直し** — `AutocompleteMediator.loadUrlFromOmniboxMatch` 以外で Enter / タップ確定が処理される経路を探す
  3. C++ 側に `LOG(ERROR)` を仕込んで `ProcessExtensionKeywordMatch` が呼ばれているか確認

## 既知の派生課題

### test-extension-options のCSP問題（修正済み）
- 当初 popup.html にインラインスクリプトがあり Manifest V3 の CSP違反
- popup.js への分離で解決済み（修正コミット候補）

### Service Worker の初回起動遅延 (Side Panel)
- 拡張機能が登録された直後の最初の操作は失敗することがある
- 2回目以降は正常動作
- 拡張機能の常識的挙動の範疇 (Phase 3 修正の問題ではない)

## 次のステップ

1. **未コミット作業を正式にコミット** — Patch 13 (メニューアイコン)、Phase 3b 修正 3 件 (Options/NewTab/DevTools部分)、`fix_viewmodel.py` の SidePanel 拡張対応
2. **Patch 14 (Omnibox) のデバッグ** — Service Worker のログ確認 → Java/C++ 側調整
3. **DevTools Panel のハング根治** — 起動シーケンス中の DevTools 初期化コードパス全洗い出し + 追加パッチ
4. **test-extension-options の popup.js 分離** をテスト拡張機能側にコミット (CSP 修正)
5. **Context Menu の selection コンテキスト統合** — Android テキスト選択 UI と拡張機能 contextMenus の橋渡し（要 Chromium Android 側調査）

## テスト拡張機能一覧 (参考)

| ディレクトリ | スタイル | 確認方法 |
|---|---|---|
| `test-extension` | Content Script | ページ読み込みで青いバナー注入確認 |
| `test-extension-phase2` | Popup + API | アイコンタップ → ポップアップ → APIテストボタン |
| `test-extension-sidepanel` | Side Panel | Popup → Open Side Panel |
| `test-extension-fulltab` | Full Tab Page | アイコンタップ → 新タブで page.html |
| `test-extension-options` | Options Page | Popup → Open Options Page → 新タブで options.html |
| `test-extension-newtab` | New Tab Override | タブバーの「+」で新規タブ → カスタムページ |
| `test-extension-devtools` | DevTools Panel | **読み込み禁止 (Chromium起動阻害)** |
| `test-extension-omnibox` | Omnibox | アドレスバーに `bex ` 入力 |
| `test-extension-contextmenu` | Context Menu | ページ/リンク/画像長押し (selection 不可) |
| `test-extension-notifications` | Notifications | Popup → 通知ボタン |
