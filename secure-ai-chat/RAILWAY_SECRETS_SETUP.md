# 🔐 Railway + Vercel GitHub Secrets 設定手順

## **1. GitHub Secrets設定画面へ移動**

1. あなたの GitHub リポジトリページを開く
2. **「Settings」** タブをクリック
3. 左サイドバーで **「Secrets and variables」** → **「Actions」** をクリック
4. **「New repository secret」** をクリック

## **2. Railway 認証設定**

### **🚂 Railway Token 取得**
1. https://railway.app にアクセス・ログイン
2. **Account Settings** → **Tokens** をクリック
3. **「Generate New Token」** をクリック
4. トークンをコピー

```
Name: RAILWAY_TOKEN
Secret: [あなたのRailway Token]
```

## **3. Vercel 認証設定**

### **⚡ Vercel Token 取得**
1. https://vercel.com にアクセス・ログイン
2. **Settings** → **Tokens** をクリック
3. **「Create」** をクリック
4. トークンをコピー

### **📊 Vercel プロジェクト情報取得**
```bash
# Vercel CLI でプロジェクト情報確認
npx vercel link
cat .vercel/project.json
```

```
Name: VERCEL_TOKEN
Secret: [あなたのVercel Token]

Name: VERCEL_ORG_ID
Secret: [.vercel/project.json の orgId]

Name: VERCEL_PROJECT_ID
Secret: [.vercel/project.json の projectId]
```

## **4. アプリケーションシークレット（生成済み）**

```
Name: SECRET_KEY
Secret: WF6Nd4q2@nN*Za$vGw5CVS41#@X838l*j^z&NRF416j^wfU$uDhm^LUDzZd9mSPd

Name: JWT_SECRET_KEY
Secret: YHTpMaCiq4HmXo2e0waTmwV0IlMrKlJqSwyzRPluECY=

Name: ENCRYPTION_KEY
Secret: qUcm4OnoaaOlt94bNIbxaFyd1FVqmUrX
```

## **5. OpenAI API設定**

### **🤖 OpenAI APIキー取得手順**
1. https://platform.openai.com にアクセス
2. アカウント作成・ログイン
3. **「API keys」** → **「Create new secret key」**
4. キーをコピーして GitHub Secrets に追加

```
Name: OPENAI_API_KEY
Secret: [あなたのOpenAI APIキー]
```

### **利用制限設定（推奨）**
1. **「Usage」** → **「Limits」**
2. **Monthly budget**: $20-50 設定
3. **Email alerts**: 有効化

## **6. SMTP設定（オプション・後で追加可能）**

### **📧 SendGrid 推奨設定**
```
Name: SMTP_HOST
Secret: smtp.sendgrid.net

Name: SMTP_PORT
Secret: 587

Name: SMTP_USERNAME
Secret: apikey

Name: SMTP_PASSWORD
Secret: [SendGrid APIキー]
```

## **7. Slack通知設定（オプション）**

```
Name: SLACK_WEBHOOK_URL
Secret: https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
```

## **8. 設定完了確認リスト**

### **✅ 必須シークレット（今すぐ設定）**
- [x] RAILWAY_TOKEN
- [x] VERCEL_TOKEN  
- [x] VERCEL_ORG_ID
- [x] VERCEL_PROJECT_ID
- [x] SECRET_KEY
- [x] JWT_SECRET_KEY
- [x] ENCRYPTION_KEY
- [x] OPENAI_API_KEY

### **⏳ オプションシークレット（後で設定可能）**
- [ ] SMTP_HOST
- [ ] SMTP_PORT  
- [ ] SMTP_USERNAME
- [ ] SMTP_PASSWORD
- [ ] SLACK_WEBHOOK_URL

## **9. GitHub Actions 有効化**

1. リポジトリの **「Actions」** タブをクリック
2. 以下のワークフローが表示されることを確認：
   - ✅ **CI Pipeline** - テスト・ビルド
   - ✅ **Deploy to Railway** - デプロイメント

## **10. 手動デプロイテスト**

1. **Actions** タブで **「Deploy to Railway」** を選択
2. **「Run workflow」** をクリック
3. **Environment**: `production` を選択
4. **「Run workflow」** をクリック

## **11. DNS設定（デプロイ後）**

### **ロリポップ DNS設定**
デプロイ完了後、以下のCNAMEレコードを追加：

```
# Railway API
api.dataibridge.com CNAME your-app.railway.app

# Vercel フロントエンド  
chat.dataibridge.com CNAME cname.vercel-dns.com
```

## **12. 料金・コスト管理**

### **Railway 料金監視**
1. Railway Dashboard → **Usage** 
2. 使用量・料金をチェック
3. アラート設定推奨

### **Vercel 料金監視**
1. Vercel Dashboard → **Usage**
2. 帯域幅使用量をチェック
3. 無料枠の上限監視

### **OpenAI 料金監視**  
1. OpenAI Platform → **Usage**
2. 月次使用量をチェック
3. 予算アラート設定

## **13. セキュリティベストプラクティス**

### **✅ DO（推奨）**
- 定期的なAPIキーローテーション
- 最小権限の原則
- 本番・開発環境の分離
- 異常アクセスの監視

### **❌ DON'T（禁止）**
- APIキーをコードにコミット
- 公開チャンネルでシークレット共有
- 不要なアクセス権限付与
- 古いAPIキーの放置

## **14. トラブルシューティング**

### **Railway デプロイ失敗**
```bash
# ログ確認
railway logs --tail

# 変数確認  
railway variables

# 再デプロイ
railway redeploy
```

### **Vercel デプロイ失敗**
```bash
# ログ確認
vercel logs

# プロジェクト情報確認
vercel project ls

# 再デプロイ
vercel --prod
```

### **環境変数未反映**
1. GitHub Secrets 再確認
2. ワークフロー再実行
3. Railway/Vercel ダッシュボードで確認

---

## **🚀 次のステップ**

1. **✅ 必須シークレット設定** → 今すぐ実行
2. **⏳ OpenAI APIキー取得** → 5分で完了
3. **🚂 Railway デプロイテスト** → 10分で完了
4. **⚡ Vercel フロントエンド** → 自動連携
5. **🌐 DNS設定** → ロリポップで簡単設定
6. **🎯 本番環境テスト** → https://chat.dataibridge.com

**Railway + Vercel設定完了で、月額¥4,000-6,000の低コストSaaS環境が完成します！**