# 🌐 ロリポップDNS設定 - Railway対応版

## 📋 概要

dataibridge.com ドメインのサブドメインを Railway + Vercel に向ける設定手順

## 🎯 設定目標

```
既存: dataibridge.com → ロリポップサーバー (継続)
新規: api.dataibridge.com → Railway (APIサーバー)
新規: chat.dataibridge.com → Vercel (フロントエンド)
```

## 🔧 手順1: Railway URLの確認

### **Railway デプロイ後にURL取得**
```bash
# Railway CLI で確認
railway domain

# または Railway Dashboard で確認
# https://railway.app/dashboard
```

**例: `your-app-abcd123.railway.app`**

## 🔧 手順2: Vercel URLの確認

### **Vercel デプロイ後にURL取得**
```bash
# Vercel CLI で確認
vercel ls

# または Vercel Dashboard で確認
# https://vercel.com/dashboard
```

**例: `your-frontend-xyz789.vercel.app`**

## 🌐 手順3: ロリポップDNS設定

### **ロリポップ管理画面アクセス**
1. https://user.lolipop.jp にログイン
2. **「サーバーの管理・設定」** → **「独自ドメイン設定」** をクリック
3. **「サブドメイン設定」** を選択

### **APIサーバー用CNAME設定**
```
サブドメイン: api
ドメイン: dataibridge.com
種別: CNAME
値: your-app-abcd123.railway.app
TTL: 3600 (1時間)
```

### **フロントエンド用CNAME設定**
```
サブドメイン: chat  
ドメイン: dataibridge.com
種別: CNAME
値: cname.vercel-dns.com
TTL: 3600 (1時間)
```

## ⚙️ 手順4: Railway カスタムドメイン設定

### **Railway Dashboard**
1. https://railway.app/dashboard → プロジェクト選択
2. **Settings** → **Domains** をクリック
3. **Custom Domain** に `api.dataibridge.com` を入力
4. **Add Domain** をクリック

### **SSL証明書**
- Railway が自動でLet's Encrypt証明書を発行
- 通常5-15分で有効化

## ⚙️ 手順5: Vercel カスタムドメイン設定

### **Vercel Dashboard**
1. https://vercel.com/dashboard → プロジェクト選択  
2. **Settings** → **Domains** をクリック
3. `chat.dataibridge.com` を入力
4. **Add** をクリック

### **DNS設定確認**
Vercel が自動でDNS設定を確認し、SSL証明書を発行

## 🔍 手順6: 設定確認

### **DNSプロパゲーション確認**
```bash
# DNS確認
nslookup api.dataibridge.com
nslookup chat.dataibridge.com

# または オンラインツール使用
# https://www.whatsmydns.net/
```

### **SSL証明書確認**
```bash
# SSL確認
curl -I https://api.dataibridge.com/health
curl -I https://chat.dataibridge.com
```

## 📊 設定完了後の構成

```
┌─────────────────────────────────────────────┐
│            dataibridge.com                  │
├─────────────────────────────────────────────┤
│                                             │
│  dataibridge.com                            │
│  ├── 既存HP (ロリポップサーバー)             │
│  │   ├── /                                  │
│  │   ├── /about                             │
│  │   └── /contact                           │
│                                             │
│  api.dataibridge.com                        │
│  ├── Railway APIサーバー                    │
│  │   ├── /health                            │
│  │   ├── /api/chat                          │
│  │   └── /api/templates                     │
│                                             │
│  chat.dataibridge.com                       │
│  ├── Vercel フロントエンド                  │
│  │   ├── /                                  │
│  │   ├── /chat                              │
│  │   └── /admin                             │
│                                             │
└─────────────────────────────────────────────┘
```

## 🕐 反映時間の目安

### **DNSプロパゲーション**
- **日本国内**: 1-6時間
- **海外**: 6-24時間  
- **完全反映**: 最大48時間

### **SSL証明書発行**
- **Railway**: 5-15分
- **Vercel**: 5-10分

## 🚨 トラブルシューティング

### **DNSが反映されない**
```bash
# キャッシュクリア
sudo dscacheutil -flushcache

# 別のDNSで確認
nslookup api.dataibridge.com 8.8.8.8
nslookup chat.dataibridge.com 8.8.8.8
```

### **SSL証明書エラー**
1. **DNSが正しく設定されているか確認**
2. **24時間待ってから再試行**
3. **Railway/Vercel のサポートに問い合わせ**

### **既存サイトにアクセスできない**
```bash
# メインドメインの確認
nslookup dataibridge.com

# ロリポップ設定確認
# user.lolipop.jp → 独自ドメイン設定
```

## 📱 動作確認

### **API接続テスト**
```javascript
// ブラウザ開発者ツールで実行
fetch('https://api.dataibridge.com/health')
  .then(response => response.json())
  .then(data => console.log(data));
```

### **フロントエンド確認**
1. https://chat.dataibridge.com にアクセス
2. AIチャット機能をテスト
3. API連携が正常に動作するか確認

## 🔄 切り戻し手順 (緊急時)

### **DNS設定を元に戻す**
```
# ロリポップ管理画面で削除
api.dataibridge.com CNAME 設定削除
chat.dataibridge.com CNAME 設定削除
```

### **サービス停止**
```bash
# Railway プロジェクト停止
railway down

# Vercel デプロイ停止
vercel remove
```

## 💡 ベストプラクティス

### **段階的移行**
1. **テスト環境**: `api-test.dataibridge.com` で先行テスト
2. **本番環境**: 動作確認後に本番DNS切り替え
3. **モニタリング**: 切り替え後24時間の監視

### **バックアップ計画**
- 現在のDNS設定をメモ・スクリーンショット保存
- 切り戻し手順書の準備
- 緊急連絡先の確保

### **監視設定**
```bash
# Uptime監視 (推奨ツール)
# - UptimeRobot (無料)
# - Pingdom  
# - StatusCake
```

## 📞 サポート情報

### **ロリポップサポート**
- **サポート**: https://lolipop.jp/support/
- **マニュアル**: DNS設定関連
- **電話**: 平日10:00-18:00

### **Railway サポート**
- **Discord**: https://discord.gg/railway
- **Documentation**: https://docs.railway.app
- **Status**: https://status.railway.app

### **Vercel サポート**
- **Discord**: https://discord.gg/vercel  
- **Documentation**: https://vercel.com/docs
- **Status**: https://vercel.com/status

---

## ✅ 設定完了チェックリスト

- [ ] Railway アプリケーションデプロイ完了
- [ ] Vercel フロントエンドデプロイ完了  
- [ ] ロリポップDNS CNAME設定完了
- [ ] Railway カスタムドメイン設定完了
- [ ] Vercel カスタムドメイン設定完了
- [ ] SSL証明書発行確認
- [ ] DNS反映確認
- [ ] API接続テスト完了
- [ ] フロントエンド表示確認
- [ ] 既存サイト影響なし確認
- [ ] 監視・アラート設定

**すべて完了後、https://chat.dataibridge.com で本格運用開始！**