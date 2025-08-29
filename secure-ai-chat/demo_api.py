#!/usr/bin/env python3
"""
デモ用簡易APIサーバー - お客様プレゼンテーション用
FastAPI不要のシンプル版 + 実際のOpenAI API連携
"""

import json
import time
import uuid
import os
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
from datetime import datetime
from dotenv import load_dotenv

# .envファイルを読み込み
load_dotenv()

# OpenAI API設定
try:
    from openai import OpenAI
    OPENAI_CLIENT = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    OPENAI_AVAILABLE = bool(os.getenv('OPENAI_API_KEY'))
    print(f"🔑 OpenAI API: {'利用可能' if OPENAI_AVAILABLE else '未設定（デモモードで動作）'}")
except ImportError:
    OPENAI_CLIENT = None
    OPENAI_AVAILABLE = False
    print("⚠️ OpenAI ライブラリが見つかりません。デモモードで動作します。")

# インメモリテンプレートストレージ（デモ用）
templates_storage = {}

def initialize_demo_templates():
    """デモ用テンプレートを初期化"""
    demo_templates = [
        {
            "id": "1",
            "name": "📊 プロジェクト管理アドバイス",
            "description": "プロジェクト進行管理のための専門的なアドバイスを提供",
            "category": "ビジネス",
            "system_prompt": "以下のプロジェクトについて、進行管理のアドバイスをください：\n\nプロジェクト名: {project_name}\n期間: {duration}\nチーム規模: {team_size}",
            "variables": [
                {"name": "project_name", "description": "プロジェクト名", "type": "text", "required": True},
                {"name": "duration", "description": "期間", "type": "text", "required": True},
                {"name": "team_size", "description": "チーム規模", "type": "text", "required": True}
            ],
            "example_input": "新しいECサイトの開発プロジェクトについて管理のアドバイスをお願いします",
            "example_output": "プロジェクト管理の観点から、以下のアドバイスをします...",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "is_active": True
        },
        {
            "id": "2", 
            "name": "🔒 セキュリティ検討",
            "description": "システムのセキュリティ対策を専門的に評価・提案",
            "category": "技術",
            "system_prompt": "{system_name}のセキュリティ対策について検討したいです。特に{concern_area}の観点から評価・提案をお願いします。",
            "variables": [
                {"name": "system_name", "description": "システム名", "type": "text", "required": True},
                {"name": "concern_area", "description": "重点的に確認したい領域", "type": "text", "required": True}
            ],
            "example_input": "クラウド環境のセキュリティについて検討してください",
            "example_output": "クラウドセキュリティについて、以下の観点から評価します...",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "is_active": True
        },
        {
            "id": "3",
            "name": "📧 ビジネスメール作成",
            "description": "丁寧で効果的なビジネスメールを自動生成",
            "category": "ビジネス", 
            "system_prompt": "件名: {subject}について\n\n{recipient}様\n\nいつもお世話になっております。\n{sender_name}です。\n\n{main_content}\n\n何かご不明な点がございましたら、\nお気軽にお声かけください。\n\nよろしくお願いいたします。",
            "variables": [
                {"name": "subject", "description": "件名", "type": "text", "required": True},
                {"name": "recipient", "description": "宛先", "type": "text", "required": True},
                {"name": "sender_name", "description": "送信者名", "type": "text", "required": True},
                {"name": "main_content", "description": "メイン内容", "type": "textarea", "required": True}
            ],
            "example_input": "明日の会議の資料について連絡したい",
            "example_output": "件名: 会議資料について\n\n田中様\n\nいつもお世話になっております...",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "is_active": True
        }
    ]
    
    for template in demo_templates:
        templates_storage[template["id"]] = template
    
    print(f"📝 デモテンプレート初期化完了: {len(demo_templates)}件")

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
            print("📝 テンプレート一覧取得リクエスト")
            # ストレージからアクティブなテンプレートを取得
            active_templates = [
                template for template in templates_storage.values() 
                if template.get('is_active', True)
            ]
            # 更新日時でソート
            active_templates.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
            print(f"📋 アクティブなテンプレート: {len(active_templates)}件")
            self.send_json_response(active_templates)
        elif parsed_path.path == '/api/models':
            # 利用可能なAIモデル
            models = [
                {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "available": True},
                {"id": "gpt-4", "name": "GPT-4", "available": True},
                {"id": "gpt-4o", "name": "GPT-4o", "available": True}
            ]
            self.send_json_response(models)
        elif parsed_path.path == '/api/dashboard/kpi':
            # ダッシュボードKPIデータ
            kpi_data = {
                "totalMessages": 12847,
                "activeUsers": 156,
                "monthlyCost": 45230,
                "avgResponse": 1.2,
                "trends": {
                    "messages": "+15.2%",
                    "users": "+8.7%",
                    "cost": "+2.1%",
                    "response": "-0.3秒"
                }
            }
            self.send_json_response(kpi_data)
        elif parsed_path.path == '/api/dashboard/usage':
            # 使用量データ
            usage_data = {
                "daily": [120, 135, 98, 145, 167, 134, 156, 178, 145, 189, 156, 167, 134, 145, 178, 156, 134, 189, 167, 145, 156, 178, 134, 167, 145, 189, 156, 178, 167, 145],
                "teams": {
                    "sales": {"messages": 4230, "efficiency_hours": 950, "cost": 18450},
                    "dev": {"messages": 6180, "efficiency_hours": 1380, "cost": 19680},
                    "marketing": {"messages": 2437, "efficiency_hours": 510, "cost": 7100}
                }
            }
            self.send_json_response(usage_data)
        elif parsed_path.path == '/api/dashboard/audit':
            # 監査ログ
            audit_logs = [
                {
                    "timestamp": "2024-01-15 14:35:22",
                    "action": "ユーザー権限変更",
                    "detail": "田中太郎の権限を管理者に変更",
                    "user": "システム管理者"
                },
                {
                    "timestamp": "2024-01-15 13:20:15", 
                    "action": "新規チーム作成",
                    "detail": "マーケティング部チームを作成",
                    "user": "佐藤花子"
                },
                {
                    "timestamp": "2024-01-15 11:45:08",
                    "action": "セキュリティ設定変更", 
                    "detail": "二要素認証を有効化",
                    "user": "システム管理者"
                }
            ]
            self.send_json_response(audit_logs)
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
                
                print(f"💬 チャットリクエスト: {message[:50]}...")
                
                # 実際のOpenAI APIを最初に試す
                ai_response = self.get_real_ai_response(message, model)
                
                if ai_response:
                    print("✅ 実際のAI APIで応答")
                    self.send_json_response(ai_response)
                else:
                    print("⚠️ デモモードで応答")
                    # フォールバック：デモ用AI応答生成
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
        elif parsed_path.path == '/api/templates':
            # テンプレート作成API
            self.handle_create_template_request()
        elif parsed_path.path.startswith('/api/templates/') and parsed_path.path.endswith('/use'):
            # テンプレート使用API
            self.handle_template_use_request(parsed_path)
        elif parsed_path.path.startswith('/api/templates/'):
            # 特定テンプレート操作
            self.send_json_response({"message": "Template operation completed"})
        else:
            self.send_error(404, "Not Found")

    def do_DELETE(self):
        """DELETEリクエスト処理"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path.startswith('/api/templates/'):
            # テンプレート削除API
            self.handle_delete_template_request(parsed_path)
        else:
            self.send_error(404, "Not Found")

    def do_PUT(self):
        """PUTリクエスト処理"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path.startswith('/api/templates/'):
            # テンプレート更新API
            self.handle_update_template_request(parsed_path)
        else:
            self.send_error(404, "Not Found")

    def get_real_ai_response(self, message, model):
        """実際のOpenAI APIを使用してAI応答を生成"""
        if not OPENAI_AVAILABLE or not OPENAI_CLIENT:
            return None
            
        try:
            start_time = time.time()
            
            response = OPENAI_CLIENT.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": """あなたは日本語で応答する親切で知識豊富なAIアシスタントです。企業向けのセキュアなAIチャットシステムとして、専門的で有用な回答を提供してください。

重要な注意事項：
- ユーザーの質問に直接的に回答してください
- 現在の日時、天気、リアルタイム情報については「申し訳ございませんが、リアルタイム情報にはアクセスできません」と正直に伝えてください
- 分からないことは「分からない」と素直に答えてください
- 質問の内容をしっかり理解してから回答してください
- 曖昧な一般的な回答ではなく、具体的で役立つ情報を提供してください"""},
                    {"role": "user", "content": message}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            processing_time = int((time.time() - start_time) * 1000)
            
            return {
                "content": response.choices[0].message.content,
                "model": response.model,
                "tokens_used": response.usage.total_tokens,
                "processing_time_ms": processing_time,
                "finish_reason": response.choices[0].finish_reason,
                "metadata": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "real_ai": True,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            print(f"❌ OpenAI API Error: {e}")
            return None

    def handle_template_use_request(self, parsed_path):
        """テンプレート使用リクエストを処理"""
        try:
            # テンプレートIDを取得
            template_id = parsed_path.path.split('/')[-2]
            
            # リクエストボディを取得
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))
            
            user_message = request_data.get('user_message', '')
            variables = request_data.get('variables', {})
            model = request_data.get('model', 'gpt-3.5-turbo')
            
            print(f"📝 テンプレート使用: ID={template_id}, Message={user_message[:50]}...")
            
            # テンプレートを取得（デモ用の固定テンプレート）
            template = self.get_demo_template(template_id)
            if not template:
                self.send_error(404, "Template not found")
                return
            
            # テンプレートのシステムプロンプトに変数を適用
            system_prompt = template['content']
            for var_name, var_value in variables.items():
                placeholder = f"{{{{{var_name}}}}}"
                system_prompt = system_prompt.replace(placeholder, var_value)
            
            # 実際のAI APIを使用してテンプレート応答を生成
            ai_response = self.get_template_ai_response(system_prompt, user_message, model)
            
            if ai_response:
                print("✅ テンプレート + 実際のAI APIで応答")
                self.send_json_response(ai_response)
            else:
                print("⚠️ テンプレート + デモモードで応答")
                # フォールバック：デモ応答
                demo_response = f"""📝 **テンプレート適用結果** ({template['name']})

**適用されたプロンプト:**
{system_prompt}

**ユーザーメッセージ:**
{user_message}

⚠️ **デモモード**: OpenAI APIキーが設定されていないため、デモ応答を表示しています。
実際の運用では、ここに高品質なAI応答が表示されます。

🔧 **設定方法**: .envファイルにOPENAI_API_KEYを設定してください。"""
                
                response = {
                    "content": demo_response,
                    "model": model,
                    "tokens_used": len(demo_response.split()),
                    "processing_time_ms": 300,
                    "finish_reason": "stop",
                    "metadata": {
                        "template_id": template_id,
                        "template_name": template['name'],
                        "prompt_tokens": len(system_prompt.split()),
                        "completion_tokens": len(demo_response.split()),
                        "demo_mode": True,
                        "timestamp": datetime.now().isoformat()
                    }
                }
                self.send_json_response(response)
                
        except Exception as e:
            print(f"❌ Template use error: {e}")
            self.send_error(500, f"Template processing error: {str(e)}")

    def handle_create_template_request(self):
        """テンプレート作成リクエストを処理"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))
            
            # 新しいテンプレートIDを生成
            template_id = str(uuid.uuid4())
            
            # テンプレートデータを作成
            template = {
                "id": template_id,
                "name": request_data.get('name', ''),
                "description": request_data.get('description', ''),
                "category": request_data.get('category', ''),
                "system_prompt": request_data.get('system_prompt', ''),
                "variables": request_data.get('variables', []),
                "example_input": request_data.get('example_input', ''),
                "example_output": request_data.get('example_output', ''),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "is_active": True
            }
            
            # ストレージに保存
            templates_storage[template_id] = template
            
            print(f"✅ テンプレート作成: {template['name']} (ID: {template_id})")
            self.send_json_response({
                "message": "Template created successfully",
                "id": template_id,
                "template": template
            })
            
        except Exception as e:
            print(f"❌ テンプレート作成エラー: {e}")
            self.send_error(500, f"Template creation error: {str(e)}")

    def handle_update_template_request(self, parsed_path):
        """テンプレート更新リクエストを処理"""
        try:
            template_id = parsed_path.path.split('/')[-1]
            
            if template_id not in templates_storage:
                self.send_error(404, "Template not found")
                return
            
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))
            
            # 既存テンプレートを更新
            template = templates_storage[template_id]
            template.update({
                "name": request_data.get('name', template['name']),
                "description": request_data.get('description', template['description']),
                "category": request_data.get('category', template['category']),
                "system_prompt": request_data.get('system_prompt', template['system_prompt']),
                "variables": request_data.get('variables', template['variables']),
                "example_input": request_data.get('example_input', template['example_input']),
                "example_output": request_data.get('example_output', template['example_output']),
                "updated_at": datetime.now().isoformat()
            })
            
            print(f"✅ テンプレート更新: {template['name']} (ID: {template_id})")
            self.send_json_response({
                "message": "Template updated successfully",
                "template": template
            })
            
        except Exception as e:
            print(f"❌ テンプレート更新エラー: {e}")
            self.send_error(500, f"Template update error: {str(e)}")

    def handle_delete_template_request(self, parsed_path):
        """テンプレート削除リクエストを処理"""
        try:
            template_id = parsed_path.path.split('/')[-1]
            
            if template_id not in templates_storage:
                self.send_error(404, "Template not found")
                return
            
            # 論理削除（is_activeをFalseに設定）
            template = templates_storage[template_id]
            template['is_active'] = False
            template['updated_at'] = datetime.now().isoformat()
            
            print(f"✅ テンプレート削除: {template['name']} (ID: {template_id})")
            self.send_json_response({
                "message": "Template deleted successfully"
            })
            
        except Exception as e:
            print(f"❌ テンプレート削除エラー: {e}")
            self.send_error(500, f"Template deletion error: {str(e)}")

    def get_demo_template(self, template_id):
        """ストレージからテンプレートを取得"""
        template = templates_storage.get(template_id)
        if template and template.get('is_active', True):
            return {
                "name": template['name'],
                "content": template['system_prompt']
            }
        return None

    def get_template_ai_response(self, system_prompt, user_message, model):
        """テンプレートを使用したAI応答を生成"""
        if not OPENAI_AVAILABLE or not OPENAI_CLIENT:
            return None
            
        try:
            start_time = time.time()
            
            response = OPENAI_CLIENT.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            processing_time = int((time.time() - start_time) * 1000)
            
            return {
                "content": response.choices[0].message.content,
                "model": response.model,
                "tokens_used": response.usage.total_tokens,
                "processing_time_ms": processing_time,
                "finish_reason": response.choices[0].finish_reason,
                "metadata": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "template_used": True,
                    "real_ai": True,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            print(f"❌ Template OpenAI API Error: {e}")
            return None

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
    # デモテンプレートを初期化
    initialize_demo_templates()
    
    server_address = ('localhost', 8000)
    httpd = HTTPServer(server_address, DemoAPIHandler)
    print("🚀 デモ用APIサーバー起動中...")
    print("📍 URL: http://localhost:8000")
    print("🔧 ヘルスチェック: http://localhost:8000/health")
    print("💬 チャットAPI: http://localhost:8000/api/chat")
    print("📝 テンプレート: http://localhost:8000/api/templates")
    print("⭐ モデル一覧: http://localhost:8000/api/models")
    print("📝 テンプレート管理: CREATE/UPDATE/DELETE対応")
    print("=" * 50)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 サーバーを停止しています...")
        httpd.shutdown()

if __name__ == '__main__':
    start_demo_server()