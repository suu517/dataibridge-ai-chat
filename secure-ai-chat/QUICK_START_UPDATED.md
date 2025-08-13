# セキュアAIチャット - 最新クイックスタートガイド

## 🎯 現在の開発状況

### ✅ 完了した機能
- **AI API統合**: OpenAI/Azure OpenAI対応
- **WebSocket実装**: リアルタイムチャット機能
- **認証・認可システム**: JWT認証、権限管理
- **テンプレート機能**: プロンプト管理システム
- **セキュリティ機能**: 暗号化、監査ログ、レート制限
- **フロントエンド**: React/Next.js UI実装

### 🔧 追加された新機能

#### 1. AI API接続テスト
```bash
cd backend
python ai_test.py
```

#### 2. WebSocket リアルタイム通信
- チャットルーム機能
- タイピングインジケーター
- AI応答ストリーミング

#### 3. 統合テストスイート
```bash
python integration_test.py
```

## 🚀 クイックスタート

### 1. 環境設定

#### AI APIキーの設定
```bash
# .envファイルを作成
cp .env.example .env

# OpenAI APIを使用する場合
export OPENAI_API_KEY="your-openai-api-key-here"

# または Azure OpenAIを使用する場合
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_API_KEY="your-azure-openai-api-key"
```

### 2. 開発サーバー起動

#### オプション A: 個別起動（推奨）
```bash
# バックエンド
cd backend
python3 -m venv venv
source venv/bin/activate  # Windowsの場合: venv\Scripts\activate
pip install fastapi uvicorn python-jose[cryptography] passlib[bcrypt]
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# フロントエンド（別ターミナル）
cd frontend
npm install
npm run dev
```

#### オプション B: Docker環境
```bash
# 全サービス起動
docker-compose up -d

# ログ確認
docker-compose logs -f
```

### 3. アクセス確認
- フロントエンド: http://localhost:3000
- バックエンドAPI: http://localhost:8000/docs
- ヘルスチェック: http://localhost:8000/health

### 4. 機能テスト

#### AI API接続テスト
```bash
cd backend
python ai_test.py
```

#### 統合テスト
```bash
python integration_test.py
```

## 📚 API エンドポイント

### 認証
- `POST /api/v1/auth/register` - ユーザー登録
- `POST /api/v1/auth/login` - ログイン
- `POST /api/v1/auth/refresh` - トークン更新

### AI機能
- `POST /api/v1/ai/chat` - AI応答生成
- `GET /api/v1/ai/models` - 利用可能モデル一覧

### テンプレート
- `GET /api/v1/templates` - テンプレート一覧
- `POST /api/v1/templates` - テンプレート作成
- `PUT /api/v1/templates/{id}` - テンプレート更新
- `DELETE /api/v1/templates/{id}` - テンプレート削除

### WebSocket
- `ws://localhost:8000/ws/chat/{chat_id}?token={jwt_token}` - チャット接続
- `ws://localhost:8000/ws/status?token={jwt_token}` - ステータス監視

## 🔧 開発者向け情報

### プロジェクト構成
```
secure-ai-chat/
├── backend/                 # FastAPI バックエンド
│   ├── app/
│   │   ├── api/endpoints/   # APIエンドポイント
│   │   ├── core/           # コア機能（設定、認証、セキュリティ）
│   │   ├── models/         # データベースモデル
│   │   ├── services/       # ビジネスロジック
│   │   └── websocket/      # WebSocket管理
│   ├── ai_test.py          # AI API接続テスト
│   └── alembic/            # データベースマイグレーション
├── frontend/                # Next.js フロントエンド
│   ├── src/
│   │   ├── components/     # React コンポーネント
│   │   ├── hooks/          # カスタムフック
│   │   ├── pages/          # ページコンポーネント
│   │   └── types/          # TypeScript型定義
├── integration_test.py      # 統合テストスイート
└── docker-compose.yml       # Docker環境設定
```

### セキュリティ機能
- JWT認証とリフレッシュトークン
- パスワードハッシュ化（bcrypt）
- データ暗号化（Fernet）
- レート制限
- 監査ログ機能
- CORS設定
- セキュリティヘッダー

### AI機能
- OpenAI/Azure OpenAI API統合
- ストリーミング応答対応
- トークン使用量監視
- エラーハンドリング
- レート制限

## 🛠️ トラブルシューティング

### 1. バックエンドが起動しない
```bash
# 依存関係の確認
pip list | grep fastapi

# ログ確認
uvicorn app.main:app --reload --log-level debug
```

### 2. AI APIエラー
```bash
# APIキー確認
echo $OPENAI_API_KEY

# テスト実行
python backend/ai_test.py
```

### 3. フロントエンド接続エラー
```bash
# 環境変数確認
cat frontend/.env.local

# Next.js設定確認
cat frontend/next.config.js
```

### 4. WebSocket接続エラー
- ブラウザのコンソールでエラー確認
- JWTトークンの有効性確認
- CORSエラーの場合は設定見直し

## 📈 次のステップ

### Phase 3: 高度な機能
1. **データベース初期化**
   ```bash
   cd backend
   alembic upgrade head
   ```

2. **管理者ダッシュボード**
   - ユーザー管理機能
   - システム監視
   - 使用状況分析

3. **企業機能**
   - チーム管理
   - 権限グループ
   - 使用量制限

4. **セキュリティ強化**
   - 二要素認証
   - IPホワイトリスト
   - 異常アクセス検知

## 📞 サポート

問題が発生した場合：
1. ログの確認
2. 環境変数の設定確認
3. 統合テストの実行
4. 各サービスの個別テスト

詳細なドキュメントは `DEVELOPMENT_ROADMAP.md` を参照してください。