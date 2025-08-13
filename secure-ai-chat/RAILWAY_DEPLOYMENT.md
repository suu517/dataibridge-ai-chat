# 🚂 Railway デプロイメント手順

## 📋 概要

DataiBridge AI Chat を Railway でホスティング
- **フロントエンド**: Next.js (Vercel連携推奨)
- **バックエンド**: FastAPI + PostgreSQL (Railway)
- **費用**: 月額 $5-25 (¥750-3,750)

## 🚀 デプロイ手順

### 1. Railway アカウント作成
1. https://railway.app にアクセス
2. GitHub アカウントでサインアップ
3. 無料枠で開始（月5ドル分）

### 2. バックエンドデプロイ

#### **GitHub連携デプロイ**
```bash
# Railway CLI インストール
npm install -g @railway/cli

# Railway ログイン
railway login

# プロジェクト作成
railway new

# GitHub リポジトリ連携
railway link
```

#### **設定手順**:
1. **New Project** → **Deploy from GitHub repo**
2. **dataibridge-ai-chat** リポジトリ選択
3. **Root Directory**: `/backend` 設定
4. **Build Command**: 自動検出
5. **Start Command**: `gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT`

### 3. PostgreSQL データベース追加

```bash
# データベースサービス追加
railway add postgresql

# 接続情報確認
railway variables
```

**設定される環境変数**:
- `DATABASE_URL`: postgresql://user:pass@host:port/db
- `POSTGRES_HOST`: ホスト名
- `POSTGRES_USER`: ユーザー名  
- `POSTGRES_PASSWORD`: パスワード
- `POSTGRES_DB`: データベース名

### 4. 環境変数設定

**Railway Dashboard**で以下を設定:

#### **必須環境変数**
```env
# アプリケーション設定
SECRET_KEY=WF6Nd4q2@nN*Za$vGw5CVS41#@X838l*j^z&NRF416j^wfU$uDhm^LUDzZd9mSPd
JWT_SECRET_KEY=YHTpMaCiq4HmXo2e0waTmwV0IlMrKlJqSwyzRPluECY=
ENCRYPTION_KEY=qUcm4OnoaaOlt94bNIbxaFyd1FVqmUrX

# OpenAI API
OPENAI_API_KEY=sk-proj-your-key-here

# データベース (自動設定)
DATABASE_URL=${{Postgres.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}

# Railway 固有
PORT=${{RAILWAY_STATIC_URL}}
RAILWAY_ENVIRONMENT=production
```

#### **オプション環境変数**
```env
# SMTP設定 (SendGrid推奨)
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=your-sendgrid-api-key

# Slack通知
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### 5. Redis 追加 (オプション)

```bash
# Redis サービス追加
railway add redis
```

### 6. フロントエンドデプロイ

#### **Vercel 推奨構成**
```bash
# Vercel CLI インストール
npm i -g vercel

# フロントエンドディレクトリへ移動
cd frontend

# Vercel デプロイ
vercel

# 本番デプロイ
vercel --prod
```

**環境変数設定 (Vercel)**:
```env
NEXT_PUBLIC_API_URL=https://your-app.railway.app
NEXT_PUBLIC_WS_URL=wss://your-app.railway.app
```

### 7. カスタムドメイン設定

#### **Railway カスタムドメイン**
1. Railway Dashboard → **Settings** → **Domains**
2. **Custom Domain** 追加: `api.dataibridge.com`
3. **CNAME レコード**をロリポップDNSに追加:
   ```
   api.dataibridge.com CNAME your-app.railway.app
   ```

#### **Vercel カスタムドメイン**  
1. Vercel Dashboard → **Domains**
2. `chat.dataibridge.com` 追加
3. **CNAME レコード**をロリポップDNSに追加:
   ```
   chat.dataibridge.com CNAME cname.vercel-dns.com
   ```

## 📊 料金プラン

### Railway 料金
```
Hobby Plan: $5/月
- 5GB転送量
- 512MB RAM
- 1GB ストレージ

Pro Plan: $20/月  
- 100GB転送量
- 8GB RAM
- 100GB ストレージ
```

### Vercel 料金
```
Hobby: 無料
- 100GB帯域幅
- Vercel ドメイン

Pro: $20/月
- 1TB帯域幅  
- カスタムドメイン
```

## 🔒 セキュリティ設定

### SSL/TLS証明書
- **自動発行**: Railway/Vercel が自動で Let's Encrypt 証明書発行
- **更新**: 自動更新
- **強制HTTPS**: 自動リダイレクト

### 環境変数暗号化
- Railway/Vercel で環境変数は暗号化保存
- GitHub Secrets は不要（直接設定）

### アクセス制御
```python
# CORS設定例
CORS_ORIGINS = [
    "https://chat.dataibridge.com",
    "https://www.dataibridge.com",
    "https://dataibridge.com"
]
```

## 🔄 CI/CDパイプライン

### 自動デプロイ
1. **GitHub プッシュ** → **Railway 自動デプロイ**
2. **ゼロダウンタイムデプロイ**
3. **ロールバック機能**

### デプロイメントフロー
```
git push origin main
↓
Railway 自動ビルド
↓  
Docker イメージ作成
↓
本番環境デプロイ
↓
ヘルスチェック
↓
完了通知
```

## 📈 監視・アラート

### Railway 監視機能
- **CPU/メモリ使用率**
- **レスポンス時間**  
- **エラー率**
- **データベース接続数**

### アラート設定
```env
# Slack通知設定
SLACK_WEBHOOK_URL=your-webhook-url
ALERT_CPU_THRESHOLD=80
ALERT_MEMORY_THRESHOLD=90
```

## 🛠️ メンテナンス

### バックアップ
- **PostgreSQL**: Railway が自動バックアップ（7日間保存）
- **手動バックアップ**: `railway pg:dump`

### スケーリング
```bash
# Railway でリソース増強
railway scale --memory 2048 --cpu 2000
```

### ログ確認
```bash
# リアルタイムログ
railway logs

# エラーログのみ
railway logs --filter error
```

## 🎯 運用のベストプラクティス

### 1. 環境分離
- **Production**: `main` ブランチ
- **Staging**: `develop` ブランチ

### 2. 監視設定
- **Uptime監視**: Railway内蔵
- **パフォーマンス**: New Relic (無料枠)
- **エラー追跡**: Sentry (無料枠)

### 3. バックアップ戦略
- **日次**: データベース自動バックアップ
- **週次**: アプリケーション全体バックアップ
- **月次**: 災害復旧テスト

## ⚡ パフォーマンス最適化

### 1. Database
```python
# 接続プール最適化
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)
```

### 2. Redis キャッシュ
```python
# セッション・キャッシュ
REDIS_URL = os.getenv("REDIS_URL") 
redis_client = redis.from_url(REDIS_URL)
```

### 3. CDN
- **静的ファイル**: Vercel CDN (自動)
- **API レスポンス**: Railway Edge Cache

## 🚨 トラブルシューティング

### よくある問題

#### **1. デプロイ失敗**
```bash
# ログ確認
railway logs --tail

# 再デプロイ
railway redeploy
```

#### **2. データベース接続エラー**
```bash
# 接続テスト
railway shell
python -c "import asyncpg; print('DB OK')"
```

#### **3. 環境変数未設定**
```bash
# 環境変数確認
railway variables

# 変数設定
railway variables set KEY=VALUE
```

## 📞 サポート

### Railway サポート
- **Discord**: https://discord.gg/railway
- **Documentation**: https://docs.railway.app
- **Status**: https://status.railway.app

### Vercel サポート  
- **Discord**: https://discord.gg/vercel
- **Documentation**: https://vercel.com/docs
- **Status**: https://vercel.com/status

---

## 🎉 次のステップ

1. **Railway アカウント作成**
2. **PostgreSQL データベース作成**  
3. **環境変数設定**
4. **GitHub 連携デプロイ**
5. **カスタムドメイン設定**
6. **SSL証明書確認**
7. **本番環境テスト**

**デプロイ完了後**: https://api.dataibridge.com でAPIアクセス可能！