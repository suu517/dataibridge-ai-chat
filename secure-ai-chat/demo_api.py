#!/usr/bin/env python3
"""
デモ用簡易APIサーバー - お客様プレゼンテーション用
FastAPI不要のシンプル版
"""

import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
from datetime import datetime

class DemoAPIHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """CORS preflight対応"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_GET(self):
        """GETリクエスト処理"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/health':
            self.send_json_response({"status": "healthy", "timestamp": datetime.now().isoformat()})
        elif parsed_path.path == '/api/templates':
            # デモ用テンプレート
            templates = [
                {
                    "id": "1",
                    "name": "プロジェクト管理アドバイス",
                    "content": "以下のプロジェクトについて、進行管理のアドバイスをください：\\n\\nプロジェクト名: {{project_name}}\\n期間: {{duration}}\\nチーム規模: {{team_size}}",
                    "variables": ["project_name", "duration", "team_size"]
                },
                {
                    "id": "2", 
                    "name": "セキュリティ検討",
                    "content": "{{system_name}}のセキュリティ対策について検討したいです。特に{{concern_area}}の観点から評価・提案をお願いします。",
                    "variables": ["system_name", "concern_area"]
                }
            ]
            self.send_json_response(templates)
        elif parsed_path.path == '/api/models':
            # 利用可能なAIモデル
            models = [
                {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "available": True},
                {"id": "gpt-4", "name": "GPT-4", "available": True},
                {"id": "gpt-4o", "name": "GPT-4o", "available": True}
            ]
            self.send_json_response(models)
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        """POSTリクエスト処理"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/chat':
            # チャットAPI（デモ応答）
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                request_data = json.loads(post_data.decode('utf-8'))
                message = request_data.get('message', '')
                model = request_data.get('model', 'gpt-3.5-turbo')
                
                # デモ用AI応答生成
                demo_response = self.generate_demo_response(message, model)
                
                response = {
                    "response": demo_response,
                    "model": model,
                    "timestamp": datetime.now().isoformat(),
                    "demo_mode": True
                }
                
                self.send_json_response(response)
                
            except json.JSONDecodeError:
                self.send_error(400, "Invalid JSON")
        else:
            self.send_error(404, "Not Found")

    def generate_demo_response(self, message, model):
        """デモ用のAI応答を生成"""
        # キーワードベースの応答生成
        message_lower = message.lower()
        
        if 'プロジェクト' in message:
            return f"""📊 **プロジェクト管理について** ({model}で分析)

**効果的なプロジェクト管理のポイント：**

✅ **計画フェーズ**
- 明確な目標設定と成功指標の定義
- リスク分析と対策の事前準備
- 適切なチーム編成とロール分担

✅ **実行フェーズ**  
- 定期的な進捗確認とコミュニケーション
- 問題の早期発見と迅速な対応
- 品質管理と継続的改善

✅ **ツール活用**
- ガントチャートでスケジュール管理
- カンバンボードでタスク可視化
- 定期的なレトロスペクティブ

ご不明な点があれば、具体的な状況をお聞かせください！"""
        
        elif 'セキュリティ' in message:
            return f"""🔒 **セキュリティ対策について** ({model}で分析)

**企業セキュリティの重要ポイント：**

🛡️ **技術的対策**
- 多要素認証（MFA）の導入
- エンドポイント保護
- ネットワークセグメンテーション
- 定期的な脆弱性スキャン

👥 **人的セキュリティ**
- 従業員向けセキュリティ教育
- アクセス権限の適切な管理
- インシデント対応手順の整備

📋 **コンプライアンス**
- GDPR、個人情報保護法への対応
- セキュリティポリシーの策定
- 定期的な監査とレビュー

具体的なセキュリティ要件についてお聞かせください！"""
        
        elif '技術' in message or '導入' in message:
            return f"""💡 **新技術導入について** ({model}で分析)

**技術導入の成功要因：**

🎯 **戦略的アプローチ**
- ビジネス目標との整合性確認
- ROI（投資対効果）の明確化
- 段階的な導入計画

🔧 **技術選定**
- 既存システムとの互換性
- スケーラビリティと将来性
- サポート体制とコミュニティ

👨‍💼 **組織的準備**
- チームのスキルアップ計画
- 変更管理プロセス
- ステークホルダーとの合意形成

どのような技術分野での導入をご検討でしょうか？"""
        
        else:
            return f"""🤖 **AI アシスタント** ({model}で応答)

ご質問ありがとうございます！

**このAIチャットシステムの特徴：**
- 🔐 セキュアな企業向け通信
- 🚀 リアルタイム応答
- 📝 カスタムテンプレート対応
- 👥 マルチテナント管理

何か具体的なご質問やご相談があれば、お気軽にお聞かせください。

**例：**
- プロジェクト管理について
- セキュリティ対策について  
- 新技術導入について

より詳しくサポートいたします！"""

    def send_json_response(self, data):
        """JSON応答を送信"""
        response = json.dumps(data, ensure_ascii=False, indent=2)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))

    def log_message(self, format, *args):
        """ログメッセージを制御"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {format % args}")

def start_demo_server():
    """デモサーバーを開始"""
    server_address = ('localhost', 8000)
    httpd = HTTPServer(server_address, DemoAPIHandler)
    print("🚀 デモ用APIサーバー起動中...")
    print("📍 URL: http://localhost:8000")
    print("🔧 ヘルスチェック: http://localhost:8000/health")
    print("💬 チャットAPI: http://localhost:8000/api/chat")
    print("📝 テンプレート: http://localhost:8000/api/templates")
    print("⭐ モデル一覧: http://localhost:8000/api/models")
    print("=" * 50)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 サーバーを停止しています...")
        httpd.shutdown()

if __name__ == '__main__':
    start_demo_server()