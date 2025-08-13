# 🚀 クイックスタートガイド

## 📋 現在の状況
- ✅ 全コード実装完了
- ✅ セキュリティテスト完了
- ❌ データベース未設定（ローカル動作にはPostgreSQL必要）

## 💰 料金について
- **現在**: 0円（Claude Codeは無料、ローカルファイルのみ）
- **将来**: AI API使用時のみ課金（OpenAI: $0.002/1K tokens程度）

## 🖥️ ローカル環境で動作させる手順

### Option 1: Docker使用（推奨）
```bash
cd /Users/sugayayoshiyuki/Desktop/secure-ai-chat
docker-compose up -d
```

### Option 2: 手動インストール
1. PostgreSQL インストール
```bash
brew install postgresql
brew services start postgresql
createdb secure_ai_chat
```

2. Python依存関係インストール
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. 環境変数設定
```bash
cp .env.example .env
# .env ファイルを編集してデータベースURL等を設定
```

4. データベース初期化
```bash
alembic upgrade head
```

5. サーバー起動
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

6. フロントエンド起動（別ターミナル）
```bash
cd ../frontend
npm install
npm run dev
```

### アクセス
- フロントエンド: http://localhost:3000
- バックエンドAPI: http://localhost:8000
- API ドキュメント: http://localhost:8000/docs

## 🔧 必要な環境変数（.env）
```
DATABASE_URL=postgresql://user:password@localhost:5432/secure_ai_chat
SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=your-openai-key-here  # AI機能使用時のみ必要
ENCRYPTION_KEY=your-encryption-key-here
```

## 📝 注意点
- OpenAI APIキーを設定しない場合、AI機能は動作しません（料金は発生しません）
- データベース設定が完了すれば、UI は確認可能
- 本番運用には追加のセキュリティ設定が必要

## 🆘 簡単確認方法
最も簡単にUIを確認したい場合：
1. フロントエンドのみ起動
2. バックエンドAPIはモック化