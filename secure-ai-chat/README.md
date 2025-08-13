# 🔐 DataiBridge AI Chat - セキュアなエンタープライズAIチャット

Railway + Vercel で構築された、中小企業向けの安全で高性能なSaaS型AIチャットシステム

## 🌟 特徴

### ✨ エンタープライズ機能
- **🔒 セキュアな暗号化通信** - エンドツーエンド暗号化でデータ保護
- **👥 マルチテナント対応** - 企業ごとに独立したデータ管理
- **📝 プロンプトテンプレート** - 業務効率化のためのカスタムテンプレート
- **🤖 多種AI対応** - GPT-3.5, GPT-4, GPT-4o をサポート
- **📊 管理者ダッシュボード** - リアルタイム監視・ユーザー管理

### 💰 コスト最適化
- **Railway バックエンド**: 月額 $5-20
- **Vercel フロントエンド**: 無料-$20  
- **総額**: 月額 ¥750-6,000 (従来AWS比95%削減)

### 🚀 高速デプロイ
- **GitHub Actions**: プッシュで自動デプロイ
- **10分でプロダクション環境**: テスト→本番まで高速化
- **ゼロダウンタイム**: ローリングアップデート対応

## 🎯 デモ環境 (ローカル)

### 🚀 クイックスタート
```bash
# デモ環境起動
python3 demo_api.py &
cd frontend/public && python3 -m http.server 8080

# アクセス
open http://localhost:8080/chat.html
```

### 📱 利用可能機能
- **AIチャット**: リアルタイム会話
- **テンプレート**: 業務効率化機能
- **管理画面**: ユーザー・システム管理
- **API設定**: AIモデル選択・設定

## 🏗️ アーキテクチャ

### **Railway (バックエンド)**
```
┌─────────────────────────────────┐
│        Railway Platform         │
├─────────────────────────────────┤
│ 🐍 FastAPI アプリケーション      │
│ 🗄️  PostgreSQL データベース     │
│ 🚀 Redis キャッシュ (オプション) │
│ 🔒 自動SSL/TLS証明書            │
│ 📊 自動監視・アラート            │
│ ⚡ 自動スケーリング             │
└─────────────────────────────────┘
```

### **Vercel (フロントエンド)**
```
┌─────────────────────────────────┐
│        Vercel Platform          │
├─────────────────────────────────┤
│ ⚛️  Next.js アプリケーション     │
│ 🌐 グローバルCDN配信            │
│ 🔒 エッジでのSSL終端            │
│ 📱 レスポンシブUI               │
│ ⚡ 瞬間的なデプロイ             │
└─────────────────────────────────┘
```

## 📦 デプロイメント

### 🔑 必要なアカウント
1. **Railway**: https://railway.app
2. **Vercel**: https://vercel.com  
3. **GitHub**: リポジトリ管理
4. **OpenAI**: API利用

### ⚙️ セットアップ手順

#### **1. GitHub Secrets設定**
```bash
# 必須シークレット
RAILWAY_TOKEN=your-railway-token
VERCEL_TOKEN=your-vercel-token
VERCEL_ORG_ID=your-org-id
VERCEL_PROJECT_ID=your-project-id

# アプリケーション
SECRET_KEY=WF6Nd4q2@nN*Za$vGw5CVS41#@X838l*j^z&NRF416j^wfU$uDhm^LUDzZd9mSPd
JWT_SECRET_KEY=YHTpMaCiq4HmXo2e0waTmwV0IlMrKlJqSwyzRPluECY=
ENCRYPTION_KEY=qUcm4OnoaaOlt94bNIbxaFyd1FVqmUrX
OPENAI_API_KEY=your-openai-api-key
```

#### **2. 自動デプロイ**
```bash
# メインブランチにプッシュで自動デプロイ
git push origin main

# 手動デプロイも可能
# GitHub Actions → Deploy to Railway → Run workflow
```

#### **3. カスタムドメイン設定**
```bash
# ロリポップDNSで設定
api.dataibridge.com CNAME your-app.railway.app
chat.dataibridge.com CNAME cname.vercel-dns.com
```

## 🔒 セキュリティ機能

### **認証・認可**
- JWT ベースの認証システム
- 多要素認証 (MFA) サポート
- ロールベースアクセス制御 (RBAC)
- セッション管理・タイムアウト

### **暗号化**
- データベース暗号化 (AES-256)
- 通信暗号化 (TLS 1.3)
- API通信暗号化
- 秘密鍵ローテーション

### **監査・ログ**
- 全ユーザー行動ログ
- API アクセスログ
- セキュリティイベント監視
- GDPR 準拠データ管理

## 📊 監視・運用

### **自動監視**
- **Railway**: CPU, メモリ, ディスク使用率
- **Vercel**: レスポンス時間, エラー率
- **アプリケーション**: API応答時間, データベース性能

### **アラート設定**
```bash
# 高負荷時の自動通知
CPU使用率 > 80%
メモリ使用率 > 90%
エラー率 > 5%
応答時間 > 2秒
```

### **ログ管理**
```bash
# Railway ログ確認
railway logs --tail

# Vercel ログ確認  
vercel logs

# アプリケーションログ
curl https://api.dataibridge.com/logs
```

## 💡 プロンプトテンプレート機能

### **テンプレート例**

#### **📧 ビジネスメール作成**
```
件名: {{subject}}について

{{recipient}}様

いつもお世話になっております。
{{company}}の{{name}}です。

{{content}}

何かご不明な点がございましたら、
お気軽にお声かけください。

よろしくお願いいたします。
```

#### **🔍 コードレビュー**
```
以下の{{language}}コードをレビューしてください:

```{{language}}
{{code}}
```

重点的に確認したい項目:
- {{focus_area}}
- セキュリティ
- パフォーマンス
- 可読性
```

### **変数システム**
- `{{variable}}` 形式で変数定義
- リアルタイム変数置換
- 条件分岐サポート
- ネストした変数対応

## 🚀 スケーラビリティ

### **成長段階別構成**

#### **スタートアップ (1-10社)**
```
Railway Hobby: $5/月
Vercel Hobby: 無料
PostgreSQL: $5/月
────────────────────
総額: $10/月 (¥1,500)
```

#### **成長期 (10-50社)**
```
Railway Pro: $20/月
Vercel Pro: $20/月  
PostgreSQL Pro: $15/月
Redis: $10/月
────────────────────
総額: $65/月 (¥10,000)
```

#### **本格展開 (50社以上)**
```
Railway Scale: $100/月
Vercel Enterprise: $150/月
PostgreSQL Scale: $50/月
────────────────────
総額: $300/月 (¥45,000)
```

## 📁 プロジェクト構造

```
secure-ai-chat/
├── 🔙 backend/              # FastAPI バックエンド
│   ├── app/
│   │   ├── api/             # API エンドポイント
│   │   ├── core/            # 設定・セキュリティ
│   │   ├── models/          # データベースモデル
│   │   ├── services/        # ビジネスロジック
│   │   └── main.py          # アプリケーションエントリ
│   ├── Dockerfile           # Railway用コンテナ
│   └── requirements.txt     # Python依存関係
│
├── 🎨 frontend/             # Next.js フロントエンド
│   ├── public/              # 静的ファイル  
│   ├── src/                 # Reactコンポーネント
│   ├── vercel.json          # Vercel設定
│   └── package.json         # Node.js依存関係
│
├── 🔄 .github/workflows/    # GitHub Actions
│   ├── ci.yml               # テスト・ビルド
│   └── deploy-railway.yml   # Railway デプロイ
│
├── 📋 docs/                 # ドキュメント
│   ├── RAILWAY_DEPLOYMENT.md
│   ├── RAILWAY_SECRETS_SETUP.md  
│   ├── LOLIPOP_DNS_RAILWAY.md
│   └── INFRASTRUCTURE_COMPARISON.md
│
├── ⚙️  railway.toml         # Railway 設定
├── 🐳 docker-compose.yml    # ローカル開発環境
└── 📖 README.md             # このファイル
```

## 🤝 コントリビューション

### **開発環境セットアップ**
```bash
# リポジトリクローン
git clone https://github.com/your-username/secure-ai-chat.git
cd secure-ai-chat

# バックエンド起動
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload

# フロントエンド起動  
cd ../frontend
npm install
npm run dev
```

### **プルリクエスト**
1. Feature ブランチ作成
2. 変更実装・テスト
3. Pull Request作成
4. CI/CD チェック通過
5. コードレビュー
6. マージ・自動デプロイ

## 📞 サポート

### **技術サポート**
- **GitHub Issues**: バグ報告・機能要望
- **Discord**: リアルタイムサポート
- **Email**: enterprise@dataibridge.com

### **ドキュメント**
- [Railway デプロイメント](./RAILWAY_DEPLOYMENT.md)
- [DNS設定手順](./LOLIPOP_DNS_RAILWAY.md)  
- [セキュリティガイド](./docs/security.md)
- [API リファレンス](./docs/api.md)

---

## 🎯 今すぐ始める

### **1. デモ体験**
```bash
python3 demo_api.py &
cd frontend/public && python3 -m http.server 8080
open http://localhost:8080/chat.html
```

### **2. 本格運用**
1. [Railway Secrets設定](./RAILWAY_SECRETS_SETUP.md)
2. [GitHub Actions デプロイ](./RAILWAY_DEPLOYMENT.md)
3. [DNS設定](./LOLIPOP_DNS_RAILWAY.md)
4. **https://chat.dataibridge.com で運用開始！**

---

**🚂 Railway + ⚡ Vercel で実現する、コスト効率的なエンタープライズAIチャット**

**月額¥1,500から始められる本格的なSaaSプラットフォーム！**