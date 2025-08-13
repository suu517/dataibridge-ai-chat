# 🔐 GitHub Secrets 設定手順

## **1. GitHub Secrets設定画面へ移動**

1. あなたの GitHub リポジトリページを開く
2. **「Settings」** タブをクリック
3. 左サイドバーで **「Secrets and variables」** → **「Actions」** をクリック
4. **「New repository secret」** をクリック

## **2. 必須シークレット設定**

以下の順番で1つずつ追加してください：

### **🔧 AWS認証情報（AWS契約後に設定）**
```
Name: AWS_ACCESS_KEY_ID
Secret: [AWS Access Key IDを入力]

Name: AWS_SECRET_ACCESS_KEY  
Secret: [AWS Secret Access Keyを入力]
```

### **🔐 アプリケーションシークレット（生成済み）**
```
Name: SECRET_KEY
Secret: WF6Nd4q2@nN*Za$vGw5CVS41#@X838l*j^z&NRF416j^wfU$uDhm^LUDzZd9mSPd

Name: JWT_SECRET_KEY
Secret: YHTpMaCiq4HmXo2e0waTmwV0IlMrKlJqSwyzRPluECY=

Name: ENCRYPTION_KEY
Secret: qUcm4OnoaaOlt94bNIbxaFyd1FVqmUrX
```

### **🤖 OpenAI API設定**
```
Name: OPENAI_API_KEY
Secret: [あなたのOpenAI APIキー]

Name: AZURE_OPENAI_API_KEY
Secret: [Azure OpenAI APIキー（使用する場合）]

Name: AZURE_OPENAI_ENDPOINT
Secret: https://your-resource.openai.azure.com/
```

### **📧 SMTP設定（後で追加可能）**
```
Name: SMTP_HOST
Secret: smtp.sendgrid.net

Name: SMTP_PORT
Secret: 587

Name: SMTP_USERNAME
Secret: [SMTPユーザー名]

Name: SMTP_PASSWORD
Secret: [SMTPパスワード]
```

### **💾 データベース設定（AWS デプロイ後に自動設定）**
```
Name: DATABASE_URL
Secret: [Terraformで自動生成されるDB URL]

Name: REDIS_URL
Secret: [Terraformで自動生成されるRedis URL]
```

### **📢 通知設定（オプション）**
```
Name: SLACK_WEBHOOK_URL
Secret: https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
```

## **3. GitHub Actions有効化**

1. リポジトリの **「Actions」** タブをクリック
2. **「I understand my workflows, go ahead and enable them」** をクリック
3. 以下の2つのワークフローが表示されることを確認：
   - ✅ **CI Pipeline** - テスト・ビルド
   - ✅ **Deploy to AWS** - デプロイメント

## **4. 現在設定可能なシークレット**

**今すぐ設定できるもの：**
- ✅ SECRET_KEY
- ✅ JWT_SECRET_KEY  
- ✅ ENCRYPTION_KEY
- ⏳ OPENAI_API_KEY（要取得）

**AWS契約後に設定：**
- ⏳ AWS_ACCESS_KEY_ID
- ⏳ AWS_SECRET_ACCESS_KEY
- ⏳ DATABASE_URL（自動生成）
- ⏳ REDIS_URL（自動生成）

## **5. OpenAI APIキー取得手順**

### **OpenAI Platform**
1. https://platform.openai.com にアクセス
2. アカウント作成・ログイン
3. **「API keys」** → **「Create new secret key」**
4. キーをコピーして GitHub Secrets に追加

### **利用制限設定（推奨）**
1. **「Usage」** → **「Limits」**
2. **Monthly budget**: $50-100 設定
3. **Email alerts**: 有効化

## **6. 設定確認方法**

### **シークレット一覧確認**
- GitHub リポジトリ → Settings → Secrets and variables → Actions
- 設定済みシークレットが一覧表示される

### **GitHub Actions動作確認**
- コードをプッシュすると自動で CI Pipeline が実行される
- Actions タブで実行状況を確認可能

## **7. セキュリティベストプラクティス**

### **✅ DO（推奨）**
- 定期的なシークレットローテーション
- 最小権限の原則
- 本番・開発環境の分離
- ログ監視

### **❌ DON'T（禁止）**
- シークレットをコードにコミット
- 公開チャンネルでシークレット共有
- 不要なアクセス権限付与
- 古いシークレットの放置

---

## **🚀 次のステップ**

1. **✅ 基本シークレット設定** → 今すぐ実行
2. **⏳ OpenAI APIキー取得** → 5分で完了
3. **⏳ AWS契約後** → AWS認証情報追加
4. **🎯 自動デプロイ開始** → 30分でプロダクション環境

**GitHub Secrets設定完了で、AWS契約後すぐに自動デプロイが可能になります！**