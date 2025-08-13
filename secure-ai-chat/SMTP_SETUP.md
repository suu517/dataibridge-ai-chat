# メール通知用SMTP設定

## 📧 **推奨SMTPサービス**

### 1. **SendGrid（推奨）**
- 無料枠: 100通/日
- セットアップ: https://sendgrid.com
- 設定例:
```
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=your-sendgrid-api-key
```

### 2. **Mailtrap（開発用）**
- 無料枠: 500通/月
- セットアップ: https://mailtrap.io
- 設定例:
```
SMTP_HOST=smtp.mailtrap.io
SMTP_PORT=2525
SMTP_USERNAME=your-mailtrap-username
SMTP_PASSWORD=your-mailtrap-password
```

### 3. **AWS SES（本番推奨）**
- AWS統合
- 低コスト
- 設定例:
```
SMTP_HOST=email-smtp.ap-northeast-1.amazonaws.com
SMTP_PORT=587
SMTP_USERNAME=your-ses-access-key
SMTP_PASSWORD=your-ses-secret-key
```

## ⚙️ **設定手順**

1. **SMTPサービス契約**
2. **認証情報取得**
3. **terraform.tfvars更新**
4. **GitHub Secrets追加**

準備完了後にAWS環境変数として設定されます。