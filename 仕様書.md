Project: mobile-bex
1. 概要 (Overview)
Beyond Extension (BEX) は、モバイル環境におけるブラウザの制限を「解除（Unlock）」し、PC版のChrome拡張機能をスマートフォン上で完全動作させることを目指すオープンソースのモバイルブラウザプロジェクト。

2. ビジョン (Vision)
Desktop Power in Pocket: PCで愛用している拡張機能を、そのままスマホのブラウザ体験に持ち込む。

Developer Friendly: 開発者が自分の作ったChrome拡張（例：Domain Traffic Inspectorなど）を、スマホで即座にテスト・運用できる環境を提供する。

3. 主要機能 (Key Features)
Chrome Extension Support: * manifest.json (v2/v3) への対応。

Background Service Workers の動作サポート。

Content Scripts の注入と実行。

Chromium-Based Core: Android版Chromiumをベースに、デスクトップ版の拡張機能APIを移植。

Extension Management UI: * インストール済み拡張機能の一覧表示・有効無効の切り替え。

.crx ファイルや .zip からの直接インストール機能。

デベロッパーモードによるローカル読み込み。

4. 技術スタック (Technical Stack - 暫定)
Engine: Chromium (Android) / WebKit (iOS - 実験的)

Language: Kotlin / Java (Android Native), C++ (Chromium Patching)

Environment: Claude Code による開発、GitHub Actions によるビルド管理。

5. 開発フェーズ (Roadmap)
Phase 1: 基盤構築 (PoC)
Android版Chromiumのビルド環境構築。

シンプルなContent Scriptが動作することの確認。

Phase 2: API 移植
chrome.storage, chrome.tabs, chrome.runtime などの主要APIの実装。

拡張機能用の設定ポップアップ表示機能の実装。

Phase 3: UX 最適化
モバイル特有のツールバー、メニューへの拡張機能アイコンの統合。

いずれ、iOSにも対応したい。共通部分は共有できるような設計で行きたい
