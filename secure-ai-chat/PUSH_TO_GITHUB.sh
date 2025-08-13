#!/bin/bash

# DataiBridge AI Chat - GitHub Push Script
# Usage: ./PUSH_TO_GITHUB.sh YOUR-GITHUB-USERNAME

echo "🚀 DataiBridge AI Chat - GitHub Setup"
echo "========================================"

# Check if username provided
if [ $# -eq 0 ]; then
    echo "❌ Error: GitHub username required"
    echo "Usage: ./PUSH_TO_GITHUB.sh YOUR-GITHUB-USERNAME"
    exit 1
fi

USERNAME=$1
REPO_URL="https://github.com/$USERNAME/dataibridge-ai-chat.git"

echo "📁 Repository: $REPO_URL"
echo ""

# Check if remote already exists
if git remote get-url origin 2>/dev/null; then
    echo "✅ Remote origin already configured"
    git remote -v
else
    echo "🔗 Adding remote origin..."
    git remote add origin $REPO_URL
fi

echo ""
echo "📤 Pushing to GitHub..."

# Push to GitHub
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Success! Code pushed to GitHub"
    echo "📋 Next steps:"
    echo "1. Visit: https://github.com/$USERNAME/dataibridge-ai-chat"
    echo "2. Enable GitHub Actions (Actions tab)"
    echo "3. Add GitHub Secrets (Settings → Secrets and variables → Actions)"
    echo ""
    echo "🔐 Required Secrets:"
    echo "- AWS_ACCESS_KEY_ID"
    echo "- AWS_SECRET_ACCESS_KEY" 
    echo "- SECRET_KEY"
    echo "- JWT_SECRET_KEY"
    echo "- ENCRYPTION_KEY"
    echo "- OPENAI_API_KEY"
    echo ""
    echo "📖 See GITHUB_SETUP.md for detailed instructions"
else
    echo ""
    echo "❌ Push failed. Please check:"
    echo "1. GitHub repository exists"
    echo "2. You have write access"
    echo "3. GitHub authentication is configured"
    echo ""
    echo "💡 Alternative: Use GitHub CLI or SSH keys"
fi