#!/usr/bin/env python3
"""
フロントエンド用シンプルHTTPサーバー
"""

import http.server
import socketserver
import os
import sys
from pathlib import Path

# フロントエンドディレクトリに移動
frontend_dir = Path(__file__).parent / "frontend" / "public"
os.chdir(frontend_dir)

PORT = 3000

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # CORSヘッダーを追加
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

try:
    with socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
        print(f"🌐 フロントエンドサーバー起動中...")
        print(f"📁 提供ディレクトリ: {frontend_dir}")
        print(f"🔗 アクセスURL:")
        print(f"   ホーム:      http://localhost:{PORT}/")
        print(f"   チャット:    http://localhost:{PORT}/chat.html")
        print(f"   テンプレート: http://localhost:{PORT}/templates.html")
        print(f"\n⚠️ 停止するには Ctrl+C を押してください")
        
        httpd.serve_forever()
        
except KeyboardInterrupt:
    print("\n🛑 サーバーを停止しました")
except Exception as e:
    print(f"❌ サーバー起動エラー: {e}")
    sys.exit(1)