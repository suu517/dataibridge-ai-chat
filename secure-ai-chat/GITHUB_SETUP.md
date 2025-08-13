# GitHub リポジトリセットアップ手順

## 🔧 **1. GitHubリポジトリ作成**

### GitHub.com でリポジトリ作成
1. https://github.com にログイン
2. 「New repository」をクリック
3. 以下の設定で作成：
   ```
   Repository name: dataibridge-ai-chat
   Description: DataiBridge AI Chat - Production-ready SaaS application
   Visibility: Private (推奨) または Public
   ✅ Add a README file: チェックしない（既にある）
   ✅ Add .gitignore: チェックしない（既にある）
   ✅ Choose a license: チェックしない
   ```

### ローカルリポジトリとの接続
```bash
# リモートリポジトリ追加
git remote add origin https://github.com/YOUR-USERNAME/dataibridge-ai-chat.git

# メインブランチにプッシュ
git branch -M main
git push -u origin main
```

## 🔐 **2. GitHub Secrets 設定**

リポジトリの「Settings」→「Secrets and variables」→「Actions」で以下を追加：

### AWS 関連
```
AWS_ACCESS_KEY_ID = your-aws-access-key-id
AWS_SECRET_ACCESS_KEY = your-aws-secret-access-key
```

### アプリケーション シークレット
```
SECRET_KEY = WF6Nd4q2@nN*Za$vGw5CVS41#@X838l*j^z&NRF416j^wfU$uDhm^LUDzZd9mSPd
JWT_SECRET_KEY = YHTpMaCiq4HmXo2e0waTmwV0IlMrKlJqSwyzRPluECY=
ENCRYPTION_KEY = qUcm4OnoaaOlt94bNIbxaFyd1FVqmUrX
```

### 外部サービス API
```
OPENAI_API_KEY = sk-proj-your-actual-openai-key-here
AZURE_OPENAI_API_KEY = your-azure-openai-key-here
AZURE_OPENAI_ENDPOINT = https://your-resource.openai.azure.com/
```

### データベース（デプロイ後に設定）
```
DATABASE_URL = postgresql+asyncpg://username:password@host:5432/dbname
REDIS_URL = redis://:password@host:6379/0
```

### 通知設定（オプション）
```
SLACK_WEBHOOK_URL = https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
```

## 🚀 **3. GitHub Actions 有効化**

1. リポジトリの「Actions」タブを開く
2. 「I understand my workflows, go ahead and enable them」をクリック
3. 以下のワークフローが自動実行される：
   - **CI Pipeline**: コード変更時のテスト・ビルド
   - **Deploy to AWS**: メインブランチへのプッシュ時にデプロイ

## 📋 **4. ブランチ保護ルール設定（推奨）**

リポジトリの「Settings」→「Branches」で `main` ブランチに以下を設定：

```
✅ Require a pull request before merging
✅ Require status checks to pass before merging
   - CI Pipeline / test
   - CI Pipeline / security
✅ Require branches to be up to date before merging
✅ Restrict pushes that create files larger than 100MB
```

## 🔄 **5. 開発ワークフロー**

### 機能開発
```bash
# 新機能ブランチ作成
git checkout -b feature/new-feature

# 開発・コミット
git add .
git commit -m "Add new feature"

# プッシュ
git push origin feature/new-feature

# GitHub でプルリクエスト作成
```

### デプロイ
```bash
# メインブランチへマージ → 自動デプロイ実行
# または手動デプロイ
# GitHub Actions で「Deploy to AWS」を手動実行
```

## 📁 **6. リポジトリ構造確認**

```
dataibridge-ai-chat/
├── .github/workflows/          # CI/CD パイプライン
├── backend/                    # Python FastAPI アプリ
├── frontend/                   # Next.js フロントエンド
├── k8s/                       # Kubernetes マニフェスト
├── terraform/                 # AWS インフラ設定
├── scripts/                   # 運用スクリプト
├── docker-compose.yml         # ローカル開発環境
├── .gitignore                 # Git除外設定
└── README.md                  # プロジェクト説明
```

## ⚠️ **セキュリティ注意事項**

1. **シークレット管理**
   - 実際のAPIキーは絶対にコードにコミットしない
   - GitHub Secrets にのみ保存
   - ローカル開発は `.env` ファイル使用（`.gitignore`済み）

2. **ブランチ保護**
   - `main` ブランチへの直接プッシュを禁止
   - プルリクエスト経由でのみマージ許可
   - CI テスト通過を必須に

3. **アクセス権限**
   - リポジトリアクセスを最小限に
   - AWS認証情報は信頼できる人のみ

---

## 🎯 **次のステップ**

1. GitHubリポジトリ作成
2. ローカルコードをプッシュ
3. GitHub Secrets設定
4. AWS契約後にデプロイ実行

**これでGitHub上でのプロジェクト管理とCI/CDが完全にセットアップされます！**