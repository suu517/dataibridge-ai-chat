# ロリポップDNS設定手順書

## 🔍 **現在の状況**

dataibridge.comのDNSは**ロリポップ**で管理されています：
```
dataibridge.com.  600  IN  NS  uns01.lolipop.jp.
dataibridge.com.  600  IN  NS  uns02.lolipop.jp.
```

## 📋 **必要な作業**

### 1. **AWS インフラデプロイ**
```bash
cd Desktop/secure-ai-chat/terraform
make init
make plan
make apply
```

### 2. **AWS出力値の確認**
デプロイ完了後、以下の値を確認：
```bash
terraform output cloudfront_domain_name  # 例: d123456789.cloudfront.net
terraform output alb_dns_name            # 例: secure-ai-chat-alb-123456789.ap-northeast-1.elb.amazonaws.com
```

### 3. **ロリポップDNS設定**

#### 3.1 ロリポップ管理画面にログイン
- ユーザー専用ページ → DNS設定

#### 3.2 サブドメイン追加
以下のCNAMEレコードを追加：

| サブドメイン | タイプ | 値 |
|-------------|--------|-----|
| `chat` | CNAME | `[cloudfront_domain_name]` |
| `api` | CNAME | `[alb_dns_name]` |
| `admin` | CNAME | `[cloudfront_domain_name]` |
| `static` | CNAME | `[cloudfront_domain_name]` |

#### 3.3 設定例
```
ホスト名: chat
タイプ: CNAME
値: d123456789.cloudfront.net

ホスト名: api  
タイプ: CNAME
値: secure-ai-chat-alb-123456789.ap-northeast-1.elb.amazonaws.com

ホスト名: admin
タイプ: CNAME  
値: d123456789.cloudfront.net

ホスト名: static
タイプ: CNAME
値: d123456789.cloudfront.net
```

### 4. **SSL証明書検証**

#### 4.1 AWS Certificate Manager確認
```bash
# ACM証明書のステータス確認
aws acm describe-certificate --certificate-arn $(terraform output certificate_arn)
```

#### 4.2 DNS検証レコード追加
ACMコンソールで表示される検証用CNAMEレコードをロリポップDNSに追加：

例：
```
ホスト名: _acme-challenge.chat
タイプ: CNAME
値: _12345678-1234-1234-1234-123456789abc.acme-validations.aws.
```

### 5. **検証とテスト**

#### 5.1 DNS伝播確認
```bash
# 30分〜2時間後に確認
dig chat.dataibridge.com
dig api.dataibridge.com
```

#### 5.2 SSL証明書確認
```bash
# 証明書が有効になったことを確認
openssl s_client -connect chat.dataibridge.com:443 -servername chat.dataibridge.com
```

#### 5.3 アプリケーション動作確認
```bash
curl -k https://chat.dataibridge.com/health
curl -k https://api.dataibridge.com/health
```

## ⚠️ **重要な注意事項**

### DNS設定の注意点
1. **既存サイト保護**: `dataibridge.com`（ルートドメイン）は変更しない
2. **TTL設定**: 短めの値（300秒）を設定して変更を迅速に反映
3. **バックアップ**: 既存DNS設定の完全なバックアップを取得

### 証明書検証の注意点
1. **全サブドメイン**: 4つのサブドメイン全てに検証レコードが必要
2. **有効化時間**: SSL証明書の有効化に30分〜数時間かかる場合有り
3. **ワイルドカード**: `*.dataibridge.com`は使用せず個別ドメインで設定

## 🔧 **トラブルシューティング**

### DNS が反映されない場合
```bash
# ロリポップのネームサーバーに直接問い合わせ
dig @uns01.lolipop.jp chat.dataibridge.com
dig @uns02.lolipop.jp chat.dataibridge.com
```

### SSL証明書が有効にならない場合
1. ACMコンソールで検証レコードを再確認
2. ロリポップDNSに正確にコピーされているか確認
3. DNS伝播を待つ（最大72時間）

### アプリケーションが応答しない場合
```bash
# ALBターゲットグループの状態確認
aws elbv2 describe-target-health --target-group-arn $(terraform output target_group_arn)

# EKSクラスター状態確認
kubectl get nodes
kubectl get pods -A
```

## 📞 **サポート情報**

### ロリポップサポート
- 管理画面: https://user.lolipop.jp/
- サポート: https://lolipop.jp/support/

### 参考資料
- [ロリポップDNS設定ガイド](https://lolipop.jp/manual/user/dns/)
- [AWS Certificate Manager ガイド](https://docs.aws.amazon.com/acm/)

---
**⚡ 設定完了後、既存のdataibridge.comサイトは影響を受けずに、新しいAIチャットサービスがサブドメインで利用できるようになります！**