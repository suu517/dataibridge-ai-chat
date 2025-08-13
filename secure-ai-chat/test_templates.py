#!/usr/bin/env python3
"""
プロンプトテンプレート機能テストスクリプト
"""

import requests
import json
from datetime import datetime

API_BASE = "http://localhost:8000"

def test_template_api():
    """テンプレートAPI機能をテストする"""
    
    print("🧪 プロンプトテンプレートAPI機能テスト")
    print("=" * 50)
    
    try:
        # 1. テンプレート一覧取得テスト
        print("\n1️⃣ テンプレート一覧取得テスト")
        response = requests.get(f"{API_BASE}/api/v1/templates")
        if response.status_code == 200:
            templates = response.json()
            print(f"✅ {len(templates)}個のテンプレートを取得")
            for template in templates:
                print(f"   - {template['name']} ({template['category']})")
        else:
            print(f"❌ 失敗: {response.status_code}")
            
        # 2. カテゴリ一覧取得テスト
        print("\n2️⃣ カテゴリ一覧取得テスト")
        response = requests.get(f"{API_BASE}/api/v1/templates/categories")
        if response.status_code == 200:
            categories = response.json()
            print(f"✅ {len(categories)}個のカテゴリ: {', '.join(categories)}")
        else:
            print(f"❌ 失敗: {response.status_code}")
            
        # 3. 新しいテンプレート作成テスト
        print("\n3️⃣ 新しいテンプレート作成テスト")
        new_template = {
            "name": "テスト用テンプレート",
            "description": "API機能テスト用に作成されたテンプレート",
            "category": "テスト",
            "system_prompt": "あなたはテスト専用のアシスタントです。{topic}について簡潔に説明してください。",
            "variables": [
                {
                    "name": "topic",
                    "type": "string",
                    "description": "説明するトピック",
                    "required": True
                }
            ],
            "example_input": "AIについて教えて",
            "example_output": "AI（人工知能）は、コンピューターが人間の知的活動を模倣する技術です..."
        }
        
        response = requests.post(
            f"{API_BASE}/api/v1/templates",
            headers={"Content-Type": "application/json"},
            json=new_template
        )
        
        if response.status_code == 200:
            created_template = response.json()
            print(f"✅ テンプレート作成成功: {created_template['name']}")
            template_id = created_template['id']
            
            # 4. 作成したテンプレートを使用テスト
            print("\n4️⃣ テンプレート使用テスト")
            use_request = {
                "template_id": template_id,
                "variables": {
                    "topic": "機械学習"
                },
                "user_message": "機械学習について詳しく教えてください"
            }
            
            response = requests.post(
                f"{API_BASE}/api/v1/templates/{template_id}/use",
                headers={"Content-Type": "application/json"},
                json=use_request
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ AI応答取得成功")
                print(f"   モデル: {result['model']}")
                print(f"   トークン使用量: {result['tokens_used']}")
                print(f"   処理時間: {result['processing_time_ms']}ms")
                print(f"   応答内容: {result['content'][:100]}...")
            else:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                print(f"❌ テンプレート使用失敗: {response.status_code}")
                print(f"   エラー: {error_data.get('detail', 'Unknown error')}")
                
            # 5. テンプレート削除テスト
            print("\n5️⃣ テンプレート削除テスト")
            response = requests.delete(f"{API_BASE}/api/v1/templates/{template_id}")
            if response.status_code == 200:
                print("✅ テンプレート削除成功")
            else:
                print(f"❌ 削除失敗: {response.status_code}")
                
        else:
            print(f"❌ テンプレート作成失敗: {response.status_code}")
            print(response.json())
            
    except requests.exceptions.ConnectionError:
        print("❌ API サーバーに接続できません")
        print("   python simple_api.py でサーバーを起動してください")
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 テスト完了")

def test_chat_api():
    """チャットAPI機能をテストする"""
    
    print("\n💬 チャットAPI機能テスト")
    print("=" * 30)
    
    try:
        # 基本チャット機能テスト
        chat_request = {
            "messages": [
                {"role": "user", "content": "こんにちは！"}
            ],
            "model": "gpt-3.5-turbo",
            "temperature": 0.7,
            "max_tokens": 100
        }
        
        response = requests.post(
            f"{API_BASE}/api/v1/ai/chat",
            headers={"Content-Type": "application/json"},
            json=chat_request
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ チャット機能正常")
            print(f"   応答: {result['content'][:50]}...")
        else:
            print(f"❌ チャット機能エラー: {response.status_code}")
            
    except Exception as e:
        print(f"❌ チャット機能エラー: {e}")

if __name__ == "__main__":
    # API サーバー接続テスト
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code == 200:
            print("🚀 APIサーバー接続確認済み")
            test_template_api()
            test_chat_api()
        else:
            print("❌ APIサーバー応答エラー")
    except:
        print("❌ APIサーバーに接続できません")
        print("   'python simple_api.py' でサーバーを起動してください")