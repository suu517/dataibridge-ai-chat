# 🔐 セキュアAIチャット - プロンプトテンプレート機能搭載

OpenAI GPT-4を使った安全で高性能なAIチャットシステムに、GPTライクなカスタムプロンプトテンプレート機能を追加しました。

## 🚀 新機能: プロンプトテンプレート

### ✨ 特徴
- **GPTライクなテンプレート管理**: ChatGPTのカスタムGPTsのように独自のプロンプトテンプレートを作成・管理
- **変数サポート**: `{変数名}` 形式でテンプレート内に変数を定義可能
- **カテゴリ管理**: ビジネス、開発、クリエイティブなどカテゴリ別に整理
- **リアルタイムAI連携**: 作成したテンプレートで即座にOpenAI GPT-4とやり取り
- **直感的なUI**: 美しいWeb界面でテンプレートを作成・編集・使用

## 🎯 デモテンプレート

システムには以下のサンプルテンプレートが含まれています：

### 📧 ビジネスメール作成
- **カテゴリ**: ビジネス
- **変数**: recipient (送信先), purpose (目的), tone (トーン)
- **用途**: 丁寧で効果的なビジネスメールの自動生成

### 🔍 コードレビュー
- **カテゴリ**: 開発
- **変数**: language (プログラミング言語), focus (重点領域)
- **用途**: コードの品質と改善点の詳細分析

### ✍️ 創作支援
- **カテゴリ**: クリエイティブ
- **変数**: genre (ジャンル), length (長さ), theme (テーマ)
- **用途**: 小説や物語の創作サポート

## 🌐 アクセス方法

### 🚀 簡単起動（推奨）
```bash
python3 start_system.py
```
全システムが自動的に起動し、以下のURLでアクセス可能：
- **ホーム**: `http://localhost:3000/`
- **チャット**: `http://localhost:3000/chat.html`
- **テンプレート管理**: `http://localhost:3000/templates.html`

### 📝 フロントエンドのみ起動
```bash
python3 start_frontend.py
```

### 🔧 手動起動（上級者向け）
```bash
# バックエンドAPI（ターミナル1）
cd backend
source venv/bin/activate
python simple_api.py

# フロントエンド（ターミナル2）
python3 start_frontend.py
```

## 🛠️ API エンドポイント

### テンプレート管理API
- `GET /api/v1/templates` - テンプレート一覧取得
- `GET /api/v1/templates/{id}` - 特定テンプレート取得
- `POST /api/v1/templates` - 新規テンプレート作成
- `PUT /api/v1/templates/{id}` - テンプレート更新
- `DELETE /api/v1/templates/{id}` - テンプレート削除
- `GET /api/v1/templates/categories` - カテゴリ一覧取得
- `POST /api/v1/templates/{id}/use` - テンプレート使用

### チャットAPI
- `POST /api/v1/ai/chat` - AI チャット
- `GET /api/v1/ai/models` - 利用可能モデル一覧

## 💡 使用例

### テンプレート作成
```json
POST /api/v1/templates
{
  "name": "技術記事作成",
  "description": "技術記事の執筆をサポート",
  "category": "執筆",
  "system_prompt": "あなたは{expertise}の専門家です。{topic}について{tone}で記事を書いてください。",
  "variables": [
    {"name": "expertise", "type": "string", "description": "専門分野", "required": true},
    {"name": "topic", "type": "string", "description": "記事トピック", "required": true},
    {"name": "tone", "type": "select", "options": ["技術的", "初心者向け", "専門的"], "default": "技術的"}
  ]
}
```

### テンプレート使用
```json
POST /api/v1/templates/{template_id}/use
{
  "variables": {
    "expertise": "Web開発",
    "topic": "React Hooks",
    "tone": "初心者向け"
  },
  "user_message": "React Hooksの使い方を説明する記事を書いて"
}
```

## 🔧 技術スタック

### バックエンド
- **FastAPI**: 高速なWeb API フレームワーク
- **OpenAI API**: GPT-3.5-turbo / GPT-4 連携
- **Pydantic**: データバリデーション
- **Uvicorn**: ASGI サーバー

### フロントエンド
- **HTML5/CSS3/JavaScript**: モダンなWeb技術
- **Responsive Design**: スマートフォン対応
- **Real-time API**: リアルタイムAI応答

## 🎉 完成機能

✅ **プロンプトテンプレート管理システムAPI設計・実装**
✅ **プロンプトテンプレート作成・編集画面HTML/CSS作成**
✅ **プロンプトテンプレート一覧・管理画面作成**
✅ **チャット画面とテンプレート機能の統合**
✅ **OpenAI API連携とリアルタイム応答**
✅ **レスポンシブデザインと直感的なUI**

## 🚀 次のステップ

システムは完全に動作可能な状態です：

1. **APIサーバーを起動** (`python simple_api.py`)
2. **ブラウザでWeb界面にアクセス**
3. **既存のテンプレートを試用**
4. **独自のテンプレートを作成**
5. **チャット画面でAIとやり取り**

GPTライクなカスタムプロンプトテンプレート機能により、様々な用途に特化したAI体験が可能になりました！🎊