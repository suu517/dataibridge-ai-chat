#!/usr/bin/env python3
"""
Minimal API server for demo - no external dependencies
Provides basic endpoints that the frontend expects
"""

import json
import time
import uuid
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from datetime import datetime

# インメモリーテンプレートストレージ
templates_storage = {}

class MinimalAPIHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_GET(self):
        """GET requests"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/health':
            self.send_json_response({"status": "healthy", "timestamp": datetime.now().isoformat()})
        elif parsed_path.path in ['/api/templates', '/api/v1/templates']:
            # Return stored templates or demo templates if storage is empty
            if not templates_storage:
                # Initialize with demo templates
                self.initialize_demo_templates()
            
            # Return all active templates
            templates = [t for t in templates_storage.values() if t.get('is_active', True)]
            templates.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
            self.send_json_response(templates)
        elif parsed_path.path in ['/api/models', '/api/v1/models']:
            # Return available models
            models = [
                {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "description": "Fast and efficient", "max_tokens": 4096, "cost_per_1k_tokens": 0.002},
                {"id": "gpt-4", "name": "GPT-4", "description": "Most capable", "max_tokens": 8192, "cost_per_1k_tokens": 0.03},
                {"id": "gpt-4o", "name": "GPT-4o", "description": "Optimized for speed", "max_tokens": 4096, "cost_per_1k_tokens": 0.005}
            ]
            self.send_json_response(models)
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        """POST requests"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path in ['/api/chat', '/api/v1/ai/chat']:
            # Chat endpoint - return demo response
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                request_data = json.loads(post_data.decode('utf-8'))
                message = request_data.get('message', '')
                if 'messages' in request_data:
                    # Handle messages array format
                    messages = request_data['messages']
                    if messages:
                        message = messages[-1].get('content', '')
                
                model = request_data.get('model', 'gpt-3.5-turbo')
                
                # Generate demo response
                demo_response = self.generate_demo_response(message, model)
                
                response = {
                    "content": demo_response,
                    "model": model,
                    "tokens_used": len(demo_response.split()) + len(message.split()),
                    "processing_time_ms": 500,
                    "finish_reason": "stop",
                    "metadata": {
                        "prompt_tokens": len(message.split()),
                        "completion_tokens": len(demo_response.split()),
                        "demo_mode": True,
                        "timestamp": datetime.now().isoformat()
                    }
                }
                
                self.send_json_response(response)
                
            except json.JSONDecodeError:
                self.send_error(400, "Invalid JSON")
        elif parsed_path.path in ['/api/templates', '/api/v1/templates']:
            # Template creation endpoint
            self.handle_create_template()
        else:
            self.send_error(404, "Not Found")

    def generate_demo_response(self, message, model):
        """Generate a demo AI response"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['プロジェクト', 'project']):
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

        elif any(word in message_lower for word in ['セキュリティ', 'security']):
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

        else:
            return f"""🤖 **AI アシスタント** ({model}で応答)

ご質問ありがとうございます！

**このSecure AIチャットシステムの特徴：**
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

    def initialize_demo_templates(self):
        """Initialize demo templates"""
        demo_templates = [
            {
                "id": "1",
                "name": "📧 ビジネスメール作成",
                "description": "丁寧で効果的なビジネスメールを自動生成",
                "category": "ビジネス",
                "system_prompt": "丁寧なビジネスメールを作成してください。件名: {subject}, 宛先: {recipient}, 内容: {content}",
                "variables": [
                    {"name": "subject", "description": "件名", "type": "text", "required": True},
                    {"name": "recipient", "description": "宛先", "type": "text", "required": True},
                    {"name": "content", "description": "メイン内容", "type": "textarea", "required": True}
                ],
                "example_input": "明日の会議について連絡したい",
                "example_output": "件名: 会議について\\n\\n田中様\\n\\nいつもお世話になっております...",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "is_active": True
            },
            {
                "id": "2",
                "name": "🔍 コードレビュー",
                "description": "コードを分析して改善点を提案",
                "category": "開発",
                "system_prompt": "{language}言語のコードをレビューし、{focus}の観点から改善点を提案してください。",
                "variables": [
                    {"name": "language", "description": "プログラミング言語", "type": "text", "required": True},
                    {"name": "focus", "description": "レビュー観点", "type": "select", "options": ["セキュリティ", "パフォーマンス", "可読性", "全般"], "required": True}
                ],
                "example_input": "このPython関数をレビューしてください",
                "example_output": "コードレビュー結果:\\n\\n良い点:\\n- 関数名が明確...",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "is_active": True
            }
        ]
        
        for template in demo_templates:
            templates_storage[template["id"]] = template
        
        print(f"📝 デモテンプレート初期化: {len(demo_templates)}件")

    def handle_create_template(self):
        """Handle template creation"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))
            
            # Generate new template ID
            template_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            
            # Create new template
            template = {
                "id": template_id,
                "name": request_data.get('name', ''),
                "description": request_data.get('description', ''),
                "category": request_data.get('category', ''),
                "system_prompt": request_data.get('system_prompt', ''),
                "variables": request_data.get('variables', []),
                "example_input": request_data.get('example_input', ''),
                "example_output": request_data.get('example_output', ''),
                "created_at": now,
                "updated_at": now,
                "is_active": True
            }
            
            # Store template
            templates_storage[template_id] = template
            
            print(f"✅ テンプレート作成: {template['name']} (ID: {template_id})")
            
            # Return created template
            self.send_json_response({
                "message": "Template created successfully",
                "id": template_id,
                "template": template
            })
            
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON")
        except Exception as e:
            print(f"❌ テンプレート作成エラー: {e}")
            self.send_error(500, f"Template creation error: {str(e)}")

    def send_json_response(self, data):
        """Send JSON response"""
        response = json.dumps(data, ensure_ascii=False, indent=2)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))

    def log_message(self, format, *args):
        """Control log messages"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {format % args}")

def start_minimal_server():
    """Start the minimal API server"""
    server_address = ('localhost', 8000)
    httpd = HTTPServer(server_address, MinimalAPIHandler)
    print("🚀 Minimal API Server starting...")
    print("📍 URL: http://localhost:8000")
    print("🔧 Health Check: http://localhost:8000/health")
    print("💬 Chat API: http://localhost:8000/api/chat")
    print("📝 Templates: http://localhost:8000/api/templates")
    print("⭐ Models: http://localhost:8000/api/models")
    print("=" * 50)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Stopping server...")
        httpd.shutdown()

if __name__ == '__main__':
    start_minimal_server()