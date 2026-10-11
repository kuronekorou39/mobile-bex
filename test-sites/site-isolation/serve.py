#!/usr/bin/env python3
"""サイト分離の観察用ローカルサイトを配信する。

同じサーバーを http://localhost:PORT と http://127.0.0.1:PORT の2つの名前で開く。
Chromium から見るとこの2つは別サイト（eTLD+1 が違う）なので、ポート1つで
「攻撃側サイト」と「被害側サイト」の組を作れる。

実機から開くには: adb reverse tcp:8000 tcp:8000
"""
import argparse
import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # 編集がすぐ反映されるようにキャッシュさせない
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    handler = functools.partial(Handler, directory=str(Path(__file__).parent))
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    print(f"親ページ: http://localhost:{args.port}/")
    print(f"実機から開く場合: adb reverse tcp:{args.port} tcp:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
