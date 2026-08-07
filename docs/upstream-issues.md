# 特定した上流バグと修正

Chromium の desktop-android 構成（`is_desktop_android = true`。Google が開発中の
実験的なビルド）を使う過程で見つかった、上流側に起因する問題と対処の記録。
いずれも自作パッチのバグではなく、Chromium の実装が Android の新しい API 仕様や
外部ストレージのパス構造に追いついていないことによるもの。

## 1. Android 15+ でフォルダ選択が必ず失敗する

**症状**: 「パッケージ化されていない拡張機能を読み込む」でフォルダを選んでも、
エラーも出ずに何も起こらない。Pixel 9a (Android 16) で再現、SHV48 (Android 10)
では発生しない。

**原因**: `SelectFileDialog.doesCallerHavePermissionForUri()` が Android 15 で
追加された `checkContentUriPermission()` を呼ぶが、この API はドキュメント URI
しか評価できない。`ACTION_OPEN_DOCUMENT_TREE` が返すツリー URI に対しては
DocumentsProvider 側が `UnsupportedOperationException` を投げる。それが catch
されて「権限なし」と解釈され、選択が無言で却下されていた。

```
W cr_SelectFileDialog: java.lang.UnsupportedOperationException:
  Unsupported Uri content://com.android.externalstorage.documents/tree/...
```

Android 14 以下は SDK 判定で早期 return するため影響を受けない。

**対処**: ツリー URI はシステムのピッカー経由でのみ得られ、呼び出し元アプリが
渡してくるものではないため、権限チェックの対象外とした（Patch 22）。

## 2. `_locales` を持つ拡張機能でブラウザが落ちる

**症状**: uBlock Origin Lite など多言語対応の拡張機能を読み込むと、ブラウザが
プロセスごと終了する。

```
Abort message: '[FATAL:extensions/common/extension_l10n_util.cc:569] NOTREACHED hit.'
```

**原因**: 外部ストレージ (SAF) のパスでは `FileEnumerator` が `content://` 形式の
URI を返す。これは親ディレクトリのパスを前方一致で含まないため、
`locales_path.AppendRelativePath(locale_path, ...)` が失敗する。
`ShouldSkipValidation()` はこの成功を前提に `NOTREACHED()` を置いており、
`_locales` を持つ拡張機能では必ずここに到達していた。

これまでのテスト拡張機能が動いていたのは、どれも `_locales` を持たなかったため。
実用的な拡張機能はほぼ必ず多言語対応しているので、この壁は uBlock に限らない。

**対処**: 選択されたフォルダをプロファイル配下にコピーしてから、通常のローカル
パスとして読み込む方式に変更した（Patch 23）。`base::CopyDirectory` も
`MakeAbsoluteFilePath` 等に依存しており content URI では動かないため、
`FileEnumerator::GetInfo().GetName()` で表示名を取る専用のコピー処理を実装した。

副次的に、SAF の権限が再起動で失われて次回起動時に拡張機能を読み込めなくなる
問題（「マニフェストが読み取れません」）も解消した。

## 3. 日常操作でのクラッシュ

**症状**: テキストを選択した状態でスクロールしたり、アプリを切り替えたりすると
高確率でクラッシュする。

**原因**: 非 official ビルドではデフォルトで `dcheck_always_on` が有効になり
（`build/config/dcheck_always_on.gni`）、開発中の desktop-android コードが
持つ `DCHECK` を踏むたびにプロセスが終了していた。実際に記録されていたのは
以下の2種類で、いずれもリリース版 Chrome にはコンパイル時に除去されて存在しない。

- `[FATAL:gpu_watchdog_thread.cc] DCHECK failed: !is_backgrounded_`
- `AssertionError at FrozenNativePage.getView`

**対処**: ビルド構成で `dcheck_always_on = false` / `enable_java_asserts = false`
を指定した。あわせて、この設定が `args.gn` に反映されないままビルドされる事故を
防ぐため、既存の `args.gn` がビルドスクリプトの生成内容と一致しない場合は
エラーで停止する仕組みを入れた（実際にこの反映漏れで、原因究明に時間を要した）。

## 4. ThinWebView のリサイズで描画が止まる（未解決・回避）

**症状**: 拡張機能ポップアップの表示領域を内容の高さに合わせて変更すると、
ポップアップが一切描画されなくなる（シートは開くが中身が空白）。

**原因（推定）**: `CompositorViewImpl.recreateSurface()` が空実装のまま
（TODO コメントのみ）で、ビューのリサイズにサーフェスが追従できていないと
思われる。

**回避**: 表示領域のサイズは変更せず、ポップアップ側にシート全体を埋める
サイズでレイアウトさせることで、背景が露出しないようにした（Patch 25）。

## 5. 知らない拡張機能 ID を渡すとブラウザが落ちる

**症状**: ホーム画面のショートカットから、既にアンインストールした拡張機能を
起動しようとするとプロセスごと落ちる。

```
Fatal signal 11 (SIGSEGV), code 1 (SEGV_MAPERR), fault addr 0x0
  ExtensionsToolbarViewModel::ExecuteUserAction
  Muxed_..._ExtensionsToolbarBridge_executeUserAction
```

**原因**: `ExtensionsToolbarViewModel::GetActionModelForId()` は知らない ID に
対して `nullptr` を返す作りなのに、呼び出し側が素通しで参照していた。

```cpp
GetActionModelForId(action_id)->ExecuteUserAction(source);
```

同じ経路の `ExtensionsToolbarAndroid::GetAction()` も、Java 側が `@Nullable` と
宣言しているのに `action->GetActionName()` を無条件で呼んでいた。つまり
「この ID は知らない」を安全に問い合わせる手段が無い状態だった。

上流では、ツールバーに並んでいるボタンを押す経路しか無く、ID は必ずモデルに
存在する前提になっている。ID を外から持ち込む経路（ショートカット）を足した
ことで表面化した。

**対処**: 両方に null チェックを入れ、`GetAction()` は宣言どおり null を返す
ようにした。併せて Java 側でも、ツールバーがまだ把握していない ID は
`onActionsInitialized` まで実行を保留するようにした（Patch 35）。

## 6. シークレットのウィンドウに拡張機能用の controller が付かない

**症状**: 「シークレット モードでの実行を許可する」を付けた拡張機能が、
シークレットモードで壊れる。`chrome.tabs.query()` を呼ぶとブラウザごと落ち、
「現在のウィンドウ」を要求する API は `No current window` を返す。

```
[FATAL:chrome/browser/extensions/api/tabs/tabs_api.cc:1716]
Check failed: window_controller.
```

コンテンツスクリプトとタブ操作だけで完結する拡張機能は影響を受けないため、
「動くものと動かないものがある」という形で現れる。

**原因**: `ChromeActivity` は起動時のプロファイル1つ分しか
`ExtensionWindowControllerBridge` を登録しない。

```java
// TODO(crbug.com/475200706): Handle multiple profiles for mobile.
Profile profile = tabModelSelector.getCurrentModel().getProfile();
```

一方 `ChromeAndroidTaskImpl` は、シークレットのタブモデルが出来ると、そのために
別の `BrowserWindow` を作る。結果、片方だけ controller を持たないウィンドウが
できる。上流のコードはこの状態を想定していない。

- `tabs_api.cc` は `CHECK(window_controller)` でプロセスを落とす
- `chrome_extension_function_details.cc` の「現在のウィンドウ」探索は、
  プロファイルが一致した時点で、controller が null でも探索を打ち切る。
  通常ウィンドウという答えがあるのに辿り着かない

**対処**: シークレットのプロファイルにも controller を登録する。加えて上流側の
2箇所も、controller を持たないウィンドウがあっても壊れないようにした（Patch 36）。

後者を残すのは、シークレットのタブを全部閉じるとプロファイルと controller は
消えるのに、ウィンドウはアクティビティ終了まで残るため。`ChromeAndroidTaskImpl` に
その旨のコメント（crbug.com/479566813）があり、上流も未解決と認識している。
