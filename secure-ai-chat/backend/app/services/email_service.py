"""
メール送信サービス
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Optional
from jinja2 import Template
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """メール送信サービス"""
    
    def __init__(self):
        self.smtp_server = getattr(settings, 'SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = getattr(settings, 'SMTP_PORT', 587)
        self.smtp_username = getattr(settings, 'SMTP_USERNAME', None)
        self.smtp_password = getattr(settings, 'SMTP_PASSWORD', None)
        self.from_email = getattr(settings, 'FROM_EMAIL', 'noreply@secure-ai-chat.com')
        self.from_name = getattr(settings, 'FROM_NAME', 'Secure AI Chat')
        self.executor = ThreadPoolExecutor(max_workers=3)
    
    def _send_email_sync(self, to_email: str, subject: str, html_content: str, text_content: Optional[str] = None):
        """同期メール送信（内部メソッド）"""
        try:
            # SMTP設定がない場合はログ出力のみ
            if not self.smtp_username or not self.smtp_password:
                logger.info(f"[メール送信ログ] To: {to_email}, Subject: {subject}")
                logger.info(f"[メール内容] {text_content or html_content}")
                return True
            
            # メッセージ作成
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            
            # テキスト版
            if text_content:
                text_part = MIMEText(text_content, 'plain', 'utf-8')
                msg.attach(text_part)
            
            # HTML版
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # SMTP送信
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"メール送信成功: {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"メール送信エラー [{to_email}]: {e}")
            return False
    
    async def send_email(self, to_email: str, subject: str, html_content: str, text_content: Optional[str] = None):
        """非同期メール送信"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._send_email_sync,
            to_email, subject, html_content, text_content
        )


# グローバルインスタンス
email_service = EmailService()


# メールテンプレート
WELCOME_EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Secure AI Chat へようこそ</title>
    <style>
        body { font-family: 'Hiragino Sans', 'Yu Gothic', sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
        .button { display: inline-block; background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 10px 0; }
        .info-box { background: white; border-left: 4px solid #667eea; padding: 15px; margin: 20px 0; }
        .footer { text-align: center; margin-top: 20px; color: #666; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎉 Secure AI Chat へようこそ！</h1>
            <p>{{ company }} のアカウントが正常に作成されました</p>
        </div>
        
        <div class="content">
            <p>{{ name }} 様</p>
            
            <p>この度は Secure AI Chat をお選びいただき、ありがとうございます！<br>
            {{ company }} のアカウントが正常に作成され、{{ trial_days }}日間の無料トライアルが開始されました。</p>
            
            <div class="info-box">
                <h3>📋 アカウント詳細</h3>
                <ul>
                    <li><strong>会社名:</strong> {{ company }}</li>
                    <li><strong>プラン:</strong> {{ plan }}</li>
                    <li><strong>ドメイン:</strong> {{ domain }}</li>
                    <li><strong>無料トライアル期間:</strong> {{ trial_days }}日間</li>
                </ul>
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="https://{{ domain }}" class="button">🚀 今すぐ始める</a>
            </div>
            
            <div class="info-box">
                <h3>🎯 次のステップ</h3>
                <ol>
                    <li>メールアドレスの確認（別途確認メールを送信済み）</li>
                    <li>チームメンバーの招待</li>
                    <li>API設定の選択</li>
                    <li>初回AIチャットのテスト</li>
                </ol>
            </div>
            
            <p>ご不明な点がございましたら、いつでもサポートチームまでお気軽にお問い合わせください。</p>
            
            <p>今後ともよろしくお願いいたします。</p>
            
            <p>Secure AI Chat チーム</p>
        </div>
        
        <div class="footer">
            <p>このメールに心当たりがない場合は、support@secure-ai-chat.com までご連絡ください。</p>
        </div>
    </div>
</body>
</html>
"""

CONFIRMATION_EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>メールアドレス確認</title>
    <style>
        body { font-family: 'Hiragino Sans', 'Yu Gothic', sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #4CAF50; color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
        .button { display: inline-block; background: #4CAF50; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 10px 0; }
        .warning { background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 6px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📧 メールアドレスの確認</h1>
            <p>アカウント有効化のため、メールアドレスを確認してください</p>
        </div>
        
        <div class="content">
            <p>こんにちは、</p>
            
            <p>Secure AI Chat アカウントの有効化には、メールアドレスの確認が必要です。<br>
            下記ボタンをクリックして、メールアドレスを確認してください。</p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{{ confirmation_url }}" class="button">✅ メールアドレスを確認する</a>
            </div>
            
            <div class="warning">
                <p><strong>⏰ 重要:</strong> このリンクは24時間で無効になります。</p>
                <p>上記ボタンが機能しない場合は、以下のURLを直接ブラウザに貼り付けてください：</p>
                <p style="word-break: break-all; font-size: 12px;">{{ confirmation_url }}</p>
            </div>
            
            <p>このメールに心当たりがない場合は、このメールを無視してください。</p>
            
            <p>よろしくお願いいたします。<br>
            Secure AI Chat チーム</p>
        </div>
    </div>
</body>
</html>
"""


async def send_welcome_email(email: str, context: Dict[str, str]) -> bool:
    """ウェルカムメール送信"""
    try:
        template = Template(WELCOME_EMAIL_TEMPLATE)
        html_content = template.render(**context)
        
        text_content = f"""
Secure AI Chat へようこそ！

{context['name']} 様

この度は Secure AI Chat をお選びいただき、ありがとうございます！
{context['company']} のアカウントが正常に作成され、{context['trial_days']}日間の無料トライアルが開始されました。

アカウント詳細:
- 会社名: {context['company']}
- プラン: {context['plan']}
- ドメイン: {context['domain']}
- 無料トライアル期間: {context['trial_days']}日間

今すぐアクセス: https://{context['domain']}

次のステップ:
1. メールアドレスの確認
2. チームメンバーの招待
3. API設定の選択
4. 初回AIチャットのテスト

ご質問がございましたら、support@secure-ai-chat.com までお問い合わせください。

Secure AI Chat チーム
"""
        
        return await email_service.send_email(
            email,
            f"🎉 {context['company']} - Secure AI Chat へようこそ！",
            html_content,
            text_content
        )
        
    except Exception as e:
        logger.error(f"ウェルカムメール送信エラー: {e}")
        return False


async def send_confirmation_email(email: str, user_id: str) -> bool:
    """確認メール送信"""
    try:
        # 確認URL生成（実際のドメインに置き換え）
        confirmation_url = f"https://secure-ai-chat.com/confirm-email?token={user_id}&email={email}"
        
        template = Template(CONFIRMATION_EMAIL_TEMPLATE)
        html_content = template.render(confirmation_url=confirmation_url)
        
        text_content = f"""
メールアドレスの確認

Secure AI Chat アカウントの有効化には、メールアドレスの確認が必要です。

以下のURLをクリックして、メールアドレスを確認してください：
{confirmation_url}

このリンクは24時間で無効になります。

このメールに心当たりがない場合は、このメールを無視してください。

Secure AI Chat チーム
"""
        
        return await email_service.send_email(
            email,
            "📧 Secure AI Chat - メールアドレスの確認",
            html_content,
            text_content
        )
        
    except Exception as e:
        logger.error(f"確認メール送信エラー: {e}")
        return False


async def send_trial_reminder_email(email: str, company_name: str, days_left: int) -> bool:
    """トライアル期限リマインダーメール"""
    try:
        html_content = f"""
        <h2>⏰ 無料トライアル終了のお知らせ</h2>
        <p>{company_name} の無料トライアル期間が残り{days_left}日となりました。</p>
        <p>継続してご利用いただくには、有料プランへのアップグレードが必要です。</p>
        <a href="https://secure-ai-chat.com/upgrade" style="background:#667eea;color:white;padding:12px 24px;text-decoration:none;border-radius:6px;">
            今すぐアップグレード
        </a>
        """
        
        return await email_service.send_email(
            email,
            f"⏰ {company_name} - 無料トライアル終了まで{days_left}日",
            html_content
        )
        
    except Exception as e:
        logger.error(f"トライアルリマインダーメール送信エラー: {e}")
        return False