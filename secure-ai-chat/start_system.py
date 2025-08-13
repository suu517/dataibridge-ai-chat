#!/usr/bin/env python3
"""
セキュアAIチャット - 全システム起動スクリプト
"""

import subprocess
import time
import threading
import signal
import sys
from pathlib import Path

def run_backend():
    """バックエンドAPIサーバーを起動"""
    backend_dir = Path(__file__).parent / "backend"
    cmd = ["python3", "simple_api.py"]
    
    try:
        process = subprocess.run(
            cmd, 
            cwd=backend_dir, 
            capture_output=False
        )
    except KeyboardInterrupt:
        pass

def run_frontend():
    """フロントエンドサーバーを起動"""
    cmd = ["python3", "start_frontend.py"]
    
    try:
        process = subprocess.run(
            cmd, 
            cwd=Path(__file__).parent,
            capture_output=False
        )
    except KeyboardInterrupt:
        pass

def signal_handler(sig, frame):
    """Ctrl+C ハンドラー"""
    print('\n\n🛑 システムを停止しています...')
    sys.exit(0)

def main():
    print("🚀 セキュアAIチャット システム起動")
    print("=" * 40)
    
    # シグナルハンドラーを設定
    signal.signal(signal.SIGINT, signal_handler)
    
    # バックエンドとフロントエンドを並行実行
    backend_thread = threading.Thread(target=run_backend, daemon=True)
    frontend_thread = threading.Thread(target=run_frontend, daemon=True)
    
    print("🔧 バックエンドAPI起動中... (Port 8000)")
    backend_thread.start()
    time.sleep(2)
    
    print("🌐 フロントエンド起動中... (Port 3000)")
    frontend_thread.start()
    time.sleep(2)
    
    print("\n✅ システム起動完了！")
    print("=" * 40)
    print("🌐 アクセスURL:")
    print("   🏠 ホーム:       http://localhost:3000/")
    print("   💬 チャット:     http://localhost:3000/chat.html")
    print("   📝 テンプレート:  http://localhost:3000/templates.html")
    print("   🔧 API:         http://localhost:8000/")
    print("\n⚠️  停止するには Ctrl+C を押してください")
    
    try:
        # メインスレッドを維持
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 システムを停止しました")
        sys.exit(0)

if __name__ == "__main__":
    main()