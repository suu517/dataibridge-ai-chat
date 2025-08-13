"""
請求・決済サービス（Stripe統合）
"""
import stripe
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from decimal import Decimal

from app.core.config import settings
from app.models.subscription import Subscription, SubscriptionStatus, Invoice, BillingHistory
from app.models.tenant import Tenant
from app.services.email_service import send_trial_reminder_email

logger = logging.getLogger(__name__)

# Stripe設定
stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', 'sk_test_dummy_key')
STRIPE_WEBHOOK_SECRET = getattr(settings, 'STRIPE_WEBHOOK_SECRET', 'whsec_dummy_secret')

class BillingService:
    """請求・決済管理サービス"""
    
    def __init__(self):
        self.stripe_enabled = hasattr(settings, 'STRIPE_SECRET_KEY') and settings.STRIPE_SECRET_KEY
        
    async def create_stripe_customer(self, tenant: Tenant, admin_email: str) -> Optional[str]:
        """Stripe顧客作成"""
        if not self.stripe_enabled:
            logger.info("Stripeが設定されていないため、ダミー顧客IDを返します")
            return f"cus_dummy_{tenant.id}"
        
        try:
            customer = stripe.Customer.create(
                email=admin_email,
                name=tenant.name,
                description=f"Secure AI Chat - {tenant.name}",
                metadata={
                    'tenant_id': str(tenant.id),
                    'subdomain': tenant.subdomain,
                    'plan': tenant.plan
                }
            )
            
            logger.info(f"Stripe顧客作成成功: {customer.id} for tenant {tenant.id}")
            return customer.id
            
        except Exception as e:
            logger.error(f"Stripe顧客作成エラー: {e}")
            return None
    
    async def create_subscription(self, 
                                db: AsyncSession,
                                subscription: Subscription, 
                                payment_method_id: Optional[str] = None) -> bool:
        """Stripeサブスクリプション作成"""
        if not self.stripe_enabled:
            logger.info("Stripeが設定されていないため、ダミー処理を実行")
            subscription.stripe_subscription_id = f"sub_dummy_{subscription.id}"
            return True
        
        try:
            # プラン情報取得
            plan = subscription.plan
            if not plan:
                logger.error("プラン情報が見つかりません")
                return False
            
            # Stripe価格オブジェクトの確認・作成
            price_id = await self.ensure_stripe_price(plan.plan_type.value, int(subscription.monthly_price))
            
            # 顧客の支払い方法設定
            if payment_method_id:
                stripe.PaymentMethod.attach(
                    payment_method_id,
                    customer=subscription.tenant.subscription.stripe_customer_id or await self.create_stripe_customer(
                        subscription.tenant, 
                        subscription.tenant.users[0].email  # 管理者のメール
                    )
                )
                
                stripe.Customer.modify(
                    subscription.tenant.subscription.stripe_customer_id,
                    invoice_settings={'default_payment_method': payment_method_id}
                )
            
            # サブスクリプション作成
            stripe_subscription = stripe.Subscription.create(
                customer=subscription.tenant.subscription.stripe_customer_id,
                items=[{'price': price_id}],
                trial_end=int(subscription.trial_end_date.timestamp()) if subscription.trial_end_date else None,
                metadata={
                    'tenant_id': str(subscription.tenant_id),
                    'subscription_id': str(subscription.id)
                }
            )
            
            # データベース更新
            subscription.stripe_subscription_id = stripe_subscription.id
            subscription.status = SubscriptionStatus.TRIAL if stripe_subscription.status == 'trialing' else SubscriptionStatus.ACTIVE
            
            await db.commit()
            logger.info(f"Stripeサブスクリプション作成成功: {stripe_subscription.id}")
            return True
            
        except Exception as e:
            logger.error(f"Stripeサブスクリプション作成エラー: {e}")
            return False
    
    async def ensure_stripe_price(self, plan_type: str, amount: int) -> str:
        """Stripe価格オブジェクトの確認・作成"""
        if not self.stripe_enabled:
            return f"price_dummy_{plan_type}"
        
        try:
            # 既存の価格を検索
            prices = stripe.Price.list(
                lookup_keys=[f"secure_ai_chat_{plan_type}"],
                limit=1
            )
            
            if prices.data:
                return prices.data[0].id
            
            # 価格オブジェクトを新規作成
            product = await self.ensure_stripe_product()
            
            price = stripe.Price.create(
                unit_amount=amount,  # 円単位
                currency='jpy',
                recurring={'interval': 'month'},
                product=product.id,
                lookup_key=f"secure_ai_chat_{plan_type}",
                metadata={'plan_type': plan_type}
            )
            
            return price.id
            
        except Exception as e:
            logger.error(f"Stripe価格オブジェクト作成エラー: {e}")
            return f"price_dummy_{plan_type}"
    
    async def ensure_stripe_product(self):
        """Stripe商品オブジェクトの確認・作成"""
        try:
            # 既存商品を検索
            products = stripe.Product.list(
                ids=['secure_ai_chat'],
                limit=1
            )
            
            if products.data:
                return products.data[0]
            
            # 商品を新規作成
            product = stripe.Product.create(
                id='secure_ai_chat',
                name='Secure AI Chat',
                description='企業向けセキュアAIチャットサービス'
            )
            
            return product
            
        except Exception as e:
            logger.error(f"Stripe商品作成エラー: {e}")
            # ダミーオブジェクトを返す
            class DummyProduct:
                id = 'secure_ai_chat'
            return DummyProduct()
    
    async def cancel_subscription(self, 
                                 db: AsyncSession,
                                 subscription: Subscription,
                                 reason: Optional[str] = None) -> bool:
        """サブスクリプション解約"""
        if not self.stripe_enabled or not subscription.stripe_subscription_id:
            # ローカル処理のみ
            subscription.cancel_subscription(reason)
            await db.commit()
            logger.info(f"ローカルサブスクリプション解約: {subscription.id}")
            return True
        
        try:
            # Stripe側で解約
            stripe.Subscription.delete(subscription.stripe_subscription_id)
            
            # ローカル処理
            subscription.cancel_subscription(reason)
            await db.commit()
            
            logger.info(f"サブスクリプション解約成功: {subscription.stripe_subscription_id}")
            return True
            
        except Exception as e:
            logger.error(f"サブスクリプション解約エラー: {e}")
            return False
    
    async def update_subscription_plan(self, 
                                     db: AsyncSession,
                                     subscription: Subscription, 
                                     new_plan_type: str,
                                     plan_details: Dict[str, Any]) -> bool:
        """サブスクリプションプラン変更"""
        if not self.stripe_enabled or not subscription.stripe_subscription_id:
            # ローカル処理のみ
            from app.models.subscription import PlanType
            subscription.upgrade_plan(PlanType(new_plan_type), plan_details)
            await db.commit()
            return True
        
        try:
            # 新しい価格ID取得
            new_price_id = await self.ensure_stripe_price(new_plan_type, plan_details['price_monthly'])
            
            # Stripe側でプラン変更
            stripe_subscription = stripe.Subscription.retrieve(subscription.stripe_subscription_id)
            stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                items=[{
                    'id': stripe_subscription['items']['data'][0]['id'],
                    'price': new_price_id
                }],
                proration_behavior='create_prorations'
            )
            
            # ローカル処理
            from app.models.subscription import PlanType
            subscription.upgrade_plan(PlanType(new_plan_type), plan_details)
            await db.commit()
            
            logger.info(f"サブスクリプションプラン変更成功: {subscription.stripe_subscription_id}")
            return True
            
        except Exception as e:
            logger.error(f"サブスクリプションプラン変更エラー: {e}")
            return False
    
    async def handle_webhook(self, payload: str, signature: str) -> bool:
        """Stripe Webhook処理"""
        if not self.stripe_enabled:
            return True
        
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, STRIPE_WEBHOOK_SECRET
            )
            
            event_type = event['type']
            logger.info(f"Stripe Webhook受信: {event_type}")
            
            if event_type == 'invoice.payment_succeeded':
                await self.handle_payment_succeeded(event['data']['object'])
            elif event_type == 'invoice.payment_failed':
                await self.handle_payment_failed(event['data']['object'])
            elif event_type == 'customer.subscription.deleted':
                await self.handle_subscription_cancelled(event['data']['object'])
            elif event_type == 'customer.subscription.trial_will_end':
                await self.handle_trial_ending(event['data']['object'])
            
            return True
            
        except Exception as e:
            logger.error(f"Webhook処理エラー: {e}")
            return False
    
    async def handle_payment_succeeded(self, invoice_obj: Dict[str, Any]):
        """支払い成功処理"""
        try:
            subscription_id = invoice_obj.get('subscription')
            if not subscription_id:
                return
            
            # サブスクリプション情報を更新
            # 実装: データベースのステータス更新、請求履歴の作成など
            logger.info(f"支払い成功処理: {subscription_id}")
            
        except Exception as e:
            logger.error(f"支払い成功処理エラー: {e}")
    
    async def handle_payment_failed(self, invoice_obj: Dict[str, Any]):
        """支払い失敗処理"""
        try:
            subscription_id = invoice_obj.get('subscription')
            if not subscription_id:
                return
            
            # 支払い失敗の通知、サブスクリプション一時停止など
            logger.info(f"支払い失敗処理: {subscription_id}")
            
        except Exception as e:
            logger.error(f"支払い失敗処理エラー: {e}")
    
    async def handle_subscription_cancelled(self, subscription_obj: Dict[str, Any]):
        """サブスクリプション解約処理"""
        try:
            stripe_sub_id = subscription_obj.get('id')
            if not stripe_sub_id:
                return
            
            # ローカルサブスクリプションをキャンセル状態に更新
            logger.info(f"サブスクリプション解約処理: {stripe_sub_id}")
            
        except Exception as e:
            logger.error(f"サブスクリプション解約処理エラー: {e}")
    
    async def handle_trial_ending(self, subscription_obj: Dict[str, Any]):
        """トライアル終了通知処理"""
        try:
            stripe_sub_id = subscription_obj.get('id')
            customer_id = subscription_obj.get('customer')
            
            if not stripe_sub_id or not customer_id:
                return
            
            # 顧客情報取得
            customer = stripe.Customer.retrieve(customer_id)
            
            # トライアル終了通知メール送信
            await send_trial_reminder_email(
                customer.email,
                customer.name or 'お客様',
                3  # 3日前通知
            )
            
            logger.info(f"トライアル終了通知送信: {customer.email}")
            
        except Exception as e:
            logger.error(f"トライアル終了通知エラー: {e}")
    
    async def generate_billing_portal_url(self, customer_id: str, return_url: str) -> Optional[str]:
        """請求ポータルURL生成"""
        if not self.stripe_enabled:
            return f"/billing?customer={customer_id}"  # ダミーURL
        
        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url
            )
            return session.url
            
        except Exception as e:
            logger.error(f"請求ポータルURL生成エラー: {e}")
            return None
    
    async def get_usage_summary(self, db: AsyncSession, tenant_id: str, month: Optional[datetime] = None) -> Dict[str, Any]:
        """使用量サマリー取得"""
        if not month:
            month = datetime.now(timezone.utc)
        
        # 月初と月末を計算
        start_of_month = month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if month.month == 12:
            end_of_month = start_of_month.replace(year=month.year + 1, month=1) - timedelta(days=1)
        else:
            end_of_month = start_of_month.replace(month=month.month + 1) - timedelta(days=1)
        
        try:
            # サブスクリプション情報取得
            result = await db.execute(
                select(Subscription).join(Tenant).where(Tenant.id == tenant_id)
            )
            subscription = result.scalar_one_or_none()
            
            if not subscription:
                return {'error': 'サブスクリプションが見つかりません'}
            
            # 使用量データ取得（実際の実装では使用量テーブルから集計）
            usage_data = {
                'period': {
                    'start': start_of_month.isoformat(),
                    'end': end_of_month.isoformat()
                },
                'subscription': {
                    'plan': subscription.plan.name if subscription.plan else 'Unknown',
                    'status': subscription.status.value,
                    'monthly_price': float(subscription.monthly_price)
                },
                'usage': {
                    'tokens_used': subscription.tokens_used_this_month,
                    'tokens_limit': subscription.plan.max_tokens_per_month if subscription.plan else 0,
                    'users_active': subscription.current_users,
                    'users_limit': subscription.plan.max_users if subscription.plan else 0
                },
                'costs': {
                    'base_cost': float(subscription.monthly_price),
                    'overage_cost': 0,  # 実装: 超過料金計算
                    'total_cost': float(subscription.monthly_price)
                }
            }
            
            return usage_data
            
        except Exception as e:
            logger.error(f"使用量サマリー取得エラー: {e}")
            return {'error': str(e)}


# グローバルインスタンス
billing_service = BillingService()


# 請求関連のユーティリティ関数
def calculate_prorated_amount(old_price: Decimal, new_price: Decimal, days_remaining: int, days_in_period: int) -> Decimal:
    """日割り計算"""
    daily_old = old_price / days_in_period
    daily_new = new_price / days_in_period
    return (daily_new - daily_old) * days_remaining


def format_currency(amount: float, currency: str = 'JPY') -> str:
    """通貨フォーマット"""
    if currency == 'JPY':
        return f"¥{int(amount):,}"
    elif currency == 'USD':
        return f"${amount:.2f}"
    else:
        return f"{amount:.2f} {currency}"


def calculate_next_billing_date(current_date: datetime, billing_interval: str) -> datetime:
    """次回請求日計算"""
    if billing_interval == 'monthly':
        if current_date.month == 12:
            return current_date.replace(year=current_date.year + 1, month=1)
        else:
            return current_date.replace(month=current_date.month + 1)
    elif billing_interval == 'yearly':
        return current_date.replace(year=current_date.year + 1)
    else:
        return current_date + timedelta(days=30)  # デフォルト