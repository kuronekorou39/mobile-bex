# mobile-bex パッチ

Chromium Android に拡張機能サポートを追加するためのパッチ群。

## ディレクトリ構成

```
patches/
├── phase1/    # PoC: Content Script動作確認
├── phase2/    # API移植: chrome.tabs, CRXインストール等
└── phase3/    # UX最適化: WebStore, 管理画面
```

## Phase 1 パッチ一覧 (PoC)

| # | ファイル名 | 内容 |
|---|-----------|------|
| 01 | `01-gn-build-flags.patch` | buildflags.gni, BUILD.gn の Android制限解除 |
| 02 | `02-resources-grd.patch` | generated_resources.grd 等の条件修正 |
| 03 | `03-profile-extra-parts-init.patch` | ExtensionService初期化の有効化 |
| 04 | `04-extension-system-delayed-reload.patch` | 遅延リロード機構 |
| 05 | `05-api-stubs.patch` | 非対応API/UIのスタブ化 |
| 06 | `06-runtime-api-android.patch` | Android OS識別追加 |
| 07 | `07-crx-install-stub.patch` | CRXインストール最小スタブ |
| 08 | `08-component-loader-fix.patch` | 不要コンポーネント無効化 |

## 適用方法

```bash
# ドライラン（実際には適用しない）
./scripts/apply-patches.sh --phase 1 --dry-run

# Phase 1 パッチを適用
./scripts/apply-patches.sh --phase 1

# パッチを元に戻す
./scripts/apply-patches.sh --phase 1 --reverse
```

## パッチ作成規則

- ファイル名は `NN-short-description.patch` 形式（NNは適用順序）
- `git diff` 形式で作成
- 各パッチはできるだけ独立して適用可能にする
- パッチ先頭にコメントで目的と変更概要を記載
