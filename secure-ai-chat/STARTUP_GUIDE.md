# 🚀 Secure.AI スタートアップガイド

## 📋 システム概要
**Secure.AI** は企業向けセキュアAIチャットシステムのプロトタイプです。

### 🎯 主要機能
- 🔐 **エンドツーエンド暗号化** チャット
- 🤖 **AI統合** (OpenAI/Azure OpenAI対応)
- 🏢 **マルチテナント** 対応
- 👥 **ユーザー管理** & 権限制御
- 📊 **監査ログ** & セキュリティ監視
- 📝 **テンプレート機能** (定型業務の自動化)

---

## ⚡ クイックスタート（推奨方法）

### 1️⃣ 前提条件
- **Node.js** (v18以上)
- **Python** (v3.8以上) 
- **Git**

### 2️⃣ 1分で起動
```bash
# プロジェクトディレクトリに移動
cd /Users/sugayayoshiyuki/Desktop/secure-ai-chat

# バックエンド起動 (ターミナル1)
cd backend
source venv/bin/activate
python simple_api.py

# フロントエンド起動 (ターミナル2) 
cd frontend
npm run dev
```

### 3️⃣ アクセス
- **フロントエンド**: http://localhost:3000
- **バックエンドAPI**: http://localhost:8000
- **API ドキュメント**: http://localhost:8000/docs

---

## 🏗️ 完全セットアップ（本格運用）

### Option A: Docker使用（推奨）
```bash
cd /Users/sugayayoshiyuki/Desktop/secure-ai-chat

# Dockerコンテナ起動
docker-compose up -d

# 起動確認
docker-compose ps
```

### Option B: 手動セットアップ
#### 1. データベース準備
```bash
# PostgreSQL インストール (Mac)
brew install postgresql
brew services start postgresql

# データベース作成
createdb secure_ai_chat
```

#### 2. バックエンド設定
```bash
cd backend

# Python仮想環境作成
python -m venv venv
source venv/bin/activate

# 依存関係インストール
pip install -r requirements.txt

# 環境変数設定
cp .env.example .env
# .envファイルを編集（下記参照）

# データベース初期化
alembic upgrade head

# サーバー起動
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 3. フロントエンド設定
```bash
cd frontend

# 依存関係インストール
npm install

# 開発サーバー起動
npm run dev
```

---

## ⚙️ 環境変数設定 (.env)

### 最小限設定（デモ用）
```bash
# アプリケーション基本設定
SECRET_KEY="your-secret-key-here"
DATABASE_URL="postgresql://user:password@localhost:5432/secure_ai_chat"

# AI機能（オプション）
OPENAI_API_KEY="sk-..."  # OpenAI APIキー
```

### 完全設定（本番用）
```bash
# セキュリティ設定
SECRET_KEY="change-this-32-character-secret-key"
JWT_SECRET_KEY="jwt-secret-for-authentication"
DB_ENCRYPT_KEY="32-character-encryption-key!"

# データベース
DATABASE_URL="postgresql://chatuser:securepassword@localhost:5432/secure_ai_chat"

# Redis（セッション管理）
REDIS_URL="redis://localhost:6379/0"

# AI設定
OPENAI_API_KEY="sk-proj-your-openai-api-key"
OPENAI_MODEL="gpt-3.5-turbo"

# Azure OpenAI（企業向け推奨）
AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
AZURE_OPENAI_API_KEY="your-azure-api-key"
AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4"

# セキュリティ設定
ALLOWED_ORIGINS="http://localhost:3000,https://yourdomain.com"
MAX_LOGIN_ATTEMPTS=5
SESSION_TIMEOUT_MINUTES=60
```

---

## 🖥️ 各サービスの役割

### バックエンド (Port: 8000)
- **API サーバー**: FastAPI
- **データベース**: PostgreSQL
- **認証**: JWT + セッション管理
- **暗号化**: AES-256 (チャット内容)
- **AI統合**: OpenAI/Azure OpenAI

### フロントエンド (Port: 3000)  
- **UI フレームワーク**: Next.js + TypeScript
- **スタイリング**: Tailwind CSS
- **リアルタイム**: WebSocket
- **認証**: JWT トークン

---

## 📁 ディレクトリ構造
```
secure-ai-chat/
├── backend/               # Python FastAPI
│   ├── app/
│   │   ├── api/          # API エンドポイント
│   │   ├── core/         # 設定・セキュリティ
│   │   ├── models/       # データベースモデル
│   │   ├── services/     # ビジネスロジック
│   │   └── main.py       # アプリケーションエントリーポイント
│   ├── simple_api.py     # 簡易デモ用API
│   └── requirements.txt
├── frontend/             # Next.js React
│   ├── src/
│   │   ├── components/   # UIコンポーネント
│   │   ├── pages/        # ページコンポーネント
│   │   └── utils/        # ユーティリティ
│   ├── public/           # 静的ファイル + HTMLデモ
│   └── package.json
├── docker-compose.yml    # Docker設定
└── *.md                  # ドキュメント
```

---

## 🎮 デモ機能

### 基本機能テスト
1. **ユーザー登録/ログイン**
   - http://localhost:3000/register
   - http://localhost:3000/login

2. **チャット機能**  
   - http://localhost:3000/chat
   - リアルタイムメッセージング
   - AI応答（APIキー設定時）

3. **管理者機能**
   - http://localhost:3000/admin
   - ユーザー管理
   - 監査ログ

4. **テンプレート機能**
   - http://localhost:3000/templates
   - 定型業務の自動化

### API エンドポイント確認
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 🔧 トラブルシューティング

### よくある問題

#### 1. ポート使用エラー
```bash
# ポート使用状況確認
lsof -i :3000  # フロントエンド
lsof -i :8000  # バックエンド

# プロセス終了
kill -9 <PID>
```

#### 2. データベース接続エラー
```bash
# PostgreSQL状態確認
brew services list | grep postgresql

# PostgreSQL再起動
brew services restart postgresql
```

#### 3. 依存関係エラー
```bash
# Python依存関係再インストール
cd backend
source venv/bin/activate
pip install -r requirements.txt --force-reinstall

# Node.js依存関係再インストール
cd frontend
rm -rf node_modules package-lock.json
npm install
```

#### 4. API接続エラー
- **.env設定確認**: 環境変数が正しく設定されているか
- **CORS設定**: `ALLOWED_ORIGINS`にフロントエンドURLが含まれているか
- **ファイアウォール**: ポート3000,8000が開放されているか

---

## 🚀 本番環境デプロイ

### Railway (PaaS) - 推奨
```bash
# Railway CLI インストール
npm install -g @railway/cli

# プロジェクトデプロイ
railway login
railway link
railway up
```

### AWS/GCP/Azure
- **詳細**: `CLOUD_INFRASTRUCTURE_PLAN.md` 参照
- **Terraform設定**: `terraform/` ディレクトリ
- **Kubernetes設定**: `k8s/` ディレクトリ

---

## 🔐 セキュリティ考慮事項

### 開発環境
- ✅ **HTTPS**: Let's Encrypt等でSSL証明書設定
- ✅ **API キー**: 環境変数で管理（Gitコミット禁止）
- ✅ **データベース**: 強力なパスワード設定

### 本番環境  
- ✅ **WAF**: Web Application Firewall
- ✅ **VPN**: 社内ネットワーク制限
- ✅ **監査**: ログ監視・アラート設定
- ✅ **バックアップ**: 暗号化バックアップ

---

## 📞 サポート

### ドキュメント
- `README.md`: 全体概要
- `DEVELOPMENT_ROADMAP.md`: 開発計画
- `SAAS_CUSTOMER_FLOW.md`: ユーザーフロー

### 問題報告
1. **ログ確認**: `backend/logs/` ディレクトリ
2. **Issue作成**: GitHub Issues
3. **詳細情報**: 環境・エラーメッセージ・再現手順

---

## 🎯 次のステップ

### Phase 1: 基本機能確認 ✅
- [x] システム起動
- [x] UI動作確認  
- [x] API接続確認

### Phase 2: カスタマイズ
- [ ] 企業ロゴ・ブランディング
- [ ] カスタムテンプレート作成
- [ ] ユーザー権限設定

### Phase 3: 本番運用
- [ ] SSL証明書設定
- [ ] 本番データベース構築
- [ ] 監視・アラート設定
- [ ] バックアップ戦略

---

*最終更新: 2025年8月15日*
*バージョン: v1.0.0-prototype*