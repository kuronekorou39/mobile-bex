# Android版Chromium 拡張機能有効化 — パッチ調査レポート

> **本書は Phase 1 開始前の事前調査であり、結論は既に更新されている。**
> 当初は Kiwi Browser / wchen342 / Cromite の先行事例から「約75ファイルのパッチが必要」と
> 見積もっていたが、Phase 1 の実測でこの推定は覆り、**`is_desktop_android = true` の1行だけで
> 拡張機能の基盤が動作する**ことが判明した（`docs/phase1-results.md` 参照）。
> 以下の本文は当時の調査内容をそのまま残したもので、歴史的経緯として保存している。
> なお「`enable_extensions = true` を直接指定するとビルドが通らない」という指摘（第1節）は
> 現在も有効で、`scripts/build.sh` はこれを踏まえて `is_desktop_android` を使っている。

## 1. 現状の問題

Chromiumは `extensions/buildflags/buildflags.gni` で**Androidの拡張機能をデフォルト無効化**している：

```gn
enable_extensions = !is_android && !is_ios && !is_castos && !is_fuchsia
```

`enable_extensions = true` を設定するだけではビルドが通らない。約50以上のBUILD.gnに `assert(!is_android)` が存在し、大量のビルドエラーが発生する。

---

## 2. 参考プロジェクト比較

| プロジェクト | アプローチ | 状態 | パッチ規模 |
|------------|----------|------|----------|
| **Kiwi Browser** | 単一巨大パッチ（123+ファイル） | アーカイブ済（2025/1） | 大 |
| **wchen342/chromium-android-extension** | 分割パッチ（10+パッチファイル） | アーカイブ済（Chromium 88） | 中 |
| **Cromite** | `is_desktop_android` リネーム + featureフラグ | 実験的プレアルファ | 大（168ファイル） |
| **Google公式** | `enable_desktop_android_extensions` フラグ | 開発中 | - |

### Kiwi Browserのアプローチ

- 単一の巨大パッチ（`Add-support-for-extensions-on-Android.patch`）で123以上のファイルを修正
- 「コンパイルを通し、ランタイムクラッシュを防ぐ」最小アプローチ
- Tab APIはTabStripModelをAndroid TabModelに置換
- ウィンドウサイズはハードコード（800x600）
- 2025年1月にアーカイブ、メンテナンス終了

### Cromiteのアプローチ

- `is_desktop_android` を `is_desktop_android_cromite` にリネームし競合回避
- `build/config/chrome_build.gni` で `is_desktop_android_cromite = is_android` と設定
- featureフラグ `kEnableExtensionsAndroid` によるランタイム制御
- 最も新しいChromiumバージョンに対応

---

## 3. Chromiumビルドフラグ

### args.gn 最小構成

```gn
target_os = "android"
target_cpu = "arm64"
enable_extensions = true
is_debug = false
is_component_build = false
```

### 関連ビルドターゲット

- `//extensions:extensions`
- `//extensions/browser`
- `//extensions/renderer`
- `//extensions/common`
- `//chrome/browser/extensions`
- `//chrome/renderer/extensions`

### Google公式フラグ（最新Chromium）

```gn
enable_desktop_android_extensions  # Desktop Android向け拡張機能
enable_extensions_core             # enable_extensions or enable_desktop_android_extensions
```

---

## 4. 必要なソースコード変更（カテゴリ別）

### カテゴリ1: ビルドシステム変更（~50ファイル）

| ファイル | 変更内容 |
|---------|---------|
| `extensions/buildflags/buildflags.gni` | `!is_android` 条件を削除 |
| `apps/BUILD.gn` | `assert(!is_android && !is_ios)` 除去 |
| `chrome/browser/BUILD.gn` | ソースフィルタリング解除、依存関係追加 |
| `extensions/BUILD.gn` | Android制限の削除 |
| `extensions/browser/BUILD.gn` | 依存関係の追加 |
| `components/guest_view/browser/BUILD.gn` | Androidアサーション除去 |
| `components/guest_view/renderer/BUILD.gn` | 同上 |
| `components/keep_alive_registry/BUILD.gn` | 同上 |
| `components/web_modal/BUILD.gn` | 同上 |
| `components/zoom/BUILD.gn` | 同上 |
| `ui/views/BUILD.gn` | `toolkit_views` アサーション除去 |
| `chrome/browser/ui/views/BUILD.gn` | 同上 |
| `services/device/public/cpp/hid/BUILD.gn` | 依存関係の除去 |
| `extensions/browser/api/system_cpu/BUILD.gn` | Androidを Linux CPU info providerに追加 |
| `chrome/app/generated_resources.grd` | `not is_android` 条件修正（6箇所以上） |
| `chrome/app/theme/theme_resources.grd` | 同様の条件変更 |

### カテゴリ2: ExtensionService初期化

**`chrome/browser/chrome_content_browser_client.cc`**

```cpp
// 削除対象:
#if defined(OS_ANDROID)
  if (startup_data_.HasBuiltProfilePrefService())
    add_profiles_extra_parts = false;
#endif
```

これによりChromeProfileBrowserMainExtraPartsProfilesが初期化され、ExtensionSystemFactory等のKeyedServiceが登録される。

**`chrome/browser/extensions/extension_service.cc`** (wchen342方式)

- `SetReadyAndNotifyListeners()` を遅延
- `ReloadExtensions()` メソッドを追加
- Java側に `ExtensionSystemManager.java` を新設しJNI経由で `ReInit()` を呼び出し
- `ChromeTabbedActivity.java` から最初のタブロード後に `initExtensionSystem()` を呼び出し

### カテゴリ3: ExtensionRegistry / ExtensionSystem

| ファイル | 変更内容 |
|---------|---------|
| `chrome/browser/extensions/extension_management.cc` | `kEnableExtensionsAndroid` フラグ確認追加 |
| `chrome/browser/extensions/extension_util.cc` | フラグ未有効時に拡張機能を無効化 |
| `chrome/browser/extensions/component_loader.cc` | PDF拡張機能の無効化、Web Store拡張機能のロード |
| `chrome/browser/extensions/default_apps.cc` | デフォルトアプリインストールの無効化 |
| `chrome/browser/browser_process_impl.cc` | 拡張機能・メディアレジストリの条件付き無効化 |
| `extensions/browser/extension_host.cc` | ホスト実装の修正 |
| `extensions/browser/extension_frame_host.cc` | フレームホストサポートの修正 |

### カテゴリ4: Content Script注入

| ファイル | 変更内容 |
|---------|---------|
| `chrome/browser/extensions/tab_helper.cc` | ナビゲーション追跡の無効化（Android非対応UI部分） |
| `chrome/renderer/extensions/` 関連ファイル | レンダラ側拡張機能コードのコンパイル有効化 |
| `chrome/browser/chrome_content_browser_client.cc` | Extension URL Loader Factoryの有効化 |

Content Script注入はExtensionSystemが正しく初期化されていれば、Chromium既存の `UserScriptLoader` / `ScriptInjectionTracker` / `ContentScriptTracker` メカニズムで動作する。

### カテゴリ5: Background Service Worker

| ファイル | 変更内容 |
|---------|---------|
| `chrome/browser/extensions/extension_service.cc` | Ready通知の遅延（タブロード後にreload） |
| `extensions/browser/extension_host.cc` | バックグラウンドホストの修正 |
| `chrome/browser/extensions/api/runtime/chrome_runtime_api_delegate.cc` | runtime API有効化 |

### カテゴリ6: chrome.* API

| API | 対応ファイル | 変更内容 |
|-----|------------|---------|
| `chrome.runtime` | `chrome_runtime_api_delegate.cc` | Android OS識別追加（`PLATFORM_OS_ANDROID`） |
| `chrome.storage` | ExtensionSystem初期化で自動有効 | ビルドフラグのみ |
| `chrome.tabs` | `tabs_event_router.cc/h` | TabStripModel → TabModel/TabModelList置換、ハードコード値（800x600） |
| `chrome.windows` | `windows_event_router.cc` | エラーディレクティブ除去 |
| `chrome.webNavigation` | `web_navigation_api.cc` | ナビゲーションイベントルーティング無効化 |
| `chrome.commands` | `command_service.cc` | キーバインディング割り当て無効化 |
| `chrome.debugger` | `debugger_api.cc` | DevTools統合無効化 |
| `chrome.fontSettings` | `font_settings_api.cc` | フォント変更監視無効化 |
| `chrome.browserAction` / `chrome.action` | `extension_action_api.cc` | ポップアップ処理無効化 |

### カテゴリ7: UI変更

| ファイル / コンポーネント | 変更内容 |
|-------------------------|---------|
| `AppMenuAdapter.java` | `EXT_FIVE_BUTTON` メニューアイテムタイプ追加 |
| `AppMenuPropertiesDelegateImpl.java` | 動的サブメニュー生成 |
| `ExtensionMenuViewBridge` | Java UI ↔ Native拡張機能ロジック間ブリッジ |
| `developer_preferences.xml` | `enable_extensions_android` トグル追加 |
| `manage_space_activity.xml` | 拡張機能ストレージデータクリアUI追加 |

### カテゴリ8: .crx / .zipインストール

| ファイル | 変更内容 |
|---------|---------|
| `ExtensionInstallDialogViewBridge.java` (新規) | C++ ↔ Android UIブリッジ |
| `ExtensionInstallCustomScrollView.java` (新規) | パーミッション表示スクロールView |
| `extension_install_dialog.xml` (新規) | ダイアログUIレイアウト |
| `extension_install_dialog_view_android.cc/h` (新規) | ネイティブダイアログロジック |
| `download/download_crx_util.cc` | CRXダウンロード検出 |
| `crx_verifier.cc` | Android Content URIからのCRXファイル読み込み |
| `file_util.cc` | Content URIサポート追加 |

### カテゴリ9: 権限・パーミッション

| ファイル | 変更内容 |
|---------|---------|
| `chrome/browser/extensions/webstore_inline_installer.cc` | パーミッションチェックのスタブ化 |
| `chrome/browser/extensions/extension_install_prompt.cc` | プロンプト表示の無効化 |
| `chrome/browser/extensions/extension_disabled_ui.cc` | アンインストールダイアログ無効化 |
| `chrome/browser/extensions/external_install_error.cc` | ダイアログ・メニューアラート無効化 |
| `chrome/browser/extensions/extension_reenabler.cc` | 再有効化プロンプト無効化 |

---

## 5. Phase 1 (PoC) 最小構成パッチリスト

### 目標

シンプルなContent Script（ページにbanner要素を挿入する拡張機能）が動作すること。

### 必要なパッチセット

| # | パッチ名 | 対象ファイル数 | 内容 |
|---|---------|-------------|------|
| **1** | `gn-build-flags.patch` | ~50 | `buildflags.gni` の `!is_android` 除去、BUILD.gnの `assert(!is_android)` 除去、依存関係修正 |
| **2** | `resources-grd.patch` | 2-3 | `generated_resources.grd` / `theme_resources.grd` の `not is_android` 条件修正 |
| **3** | `profile-extra-parts-init.patch` | 1-2 | `chrome_content_browser_client.cc` でExtensionService初期化の有効化 |
| **4** | `extension-system-delayed-reload.patch` | 2-3 | ExtensionService初期化を最初のタブロード後に遅延実行 |
| **5** | `api-stubs.patch` | ~15 | tabs, webNavigation, debugger, commands等のAPI/UIスタブ化 |
| **6** | `runtime-api-android.patch` | 1 | `chrome_runtime_api_delegate.cc` にAndroid OS識別追加 |
| **7** | `crx-install-stub.patch` | 1 | `download_crx_util.cc` のAndroid向け最小スタブ |
| **8** | `component-loader-fix.patch` | 2 | PDF拡張機能無効化、デフォルトアプリ無効化 |

**推定変更規模: 約75ファイル**

---

## 6. 推奨アプローチ（mobile-bex向け）

### 設計方針

1. **Cromite方式のfeatureフラグ** (`kEnableExtensionsAndroid`) — ランタイムで有効/無効制御
2. **wchen342方式の分割パッチ管理** — Chromiumバージョンアップ時のメンテナンス性確保
3. **Google公式 `enable_desktop_android_extensions`** フラグ活用 — 将来的な公式実装との互換性
4. **iOS対応を見据えた設計** — 共通部分（拡張機能解析、manifest処理等）は共有可能な設計

### 全体適用順序

```
Phase 1 (PoC):
  1. gn-build-flags.patch              — ビルドフラグ・BUILD.gn修正
  2. resources-grd.patch               — リソース条件修正
  3. profile-extra-parts-init.patch    — ExtensionService初期化
  4. extension-system-delayed-reload.patch — 遅延リロード
  5. api-stubs.patch                   — コンパイルエラー解消
  6. runtime-api-android.patch         — OS識別
  7. crx-install-stub.patch            — 最小インストール対応
  8. component-loader-fix.patch        — 不要コンポーネント無効化

Phase 2 (API移植):
  9. tab-api-fix.patch                 — Tab API (TabModel対応)
  10. crx-download-install.patch       — CRXインストールUI
  11. extension-menu-items.patch       — ツールバーUI

Phase 3 (UX最適化):
  12. chromium-webstore.patch          — Web Store対応
  13. extension-management-ui.patch    — 管理画面
```

---

## 7. 参考リンク

- [Kiwi Browser patches](https://github.com/kiwibrowser/patches/blob/master/Add-support-for-extensions-on-Android.patch)
- [wchen342/chromium-android-extension](https://github.com/wchen342/chromium-android-extension)
- [Cromite repository](https://github.com/uazo/cromite)
- [Cromite extensions discussion](https://github.com/uazo/cromite/issues/256)
- [Helium Browser (imputnet)](https://github.com/imputnet/helium)
- [ivan2kh/Chromium-Android-Extensions](https://github.com/ivan2kh/Chromium-Android-Extensions)
- [Chromium extensions design docs](https://www.chromium.org/developers/design-documents/extensions/)
