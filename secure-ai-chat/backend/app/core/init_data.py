"""
データベース初期データ作成スクリプト
"""

from sqlalchemy.orm import Session
from app.models.subscription import Plan, PlanType
from app.core.database import get_db

def create_default_plans(db: Session):
    """デフォルトプランを作成"""
    
    # 既存のプランチェック
    existing_plans = db.query(Plan).count()
    if existing_plans > 0:
        print("プランは既に存在しています")
        return
    
    plans = [
        {
            "plan_type": PlanType.STARTER,
            "name": "スタータープラン",
            "max_users": 10,
            "max_tokens_per_month": 100000,
            "max_templates": 10,
            "max_storage_gb": 5,
            "monthly_price": 29800,
            "description": "小規模チーム向けの基本プラン",
            "features": '["基本AI機能", "メールサポート", "標準テンプレート"]',
            "has_api_access": False,
            "has_custom_branding": False,
            "has_priority_support": False,
            "has_advanced_analytics": False,
            "display_order": 1
        },
        {
            "plan_type": PlanType.STANDARD,
            "name": "スタンダードプラン",
            "max_users": 50,
            "max_tokens_per_month": 500000,
            "max_templates": 50,
            "max_storage_gb": 20,
            "monthly_price": 49800,
            "description": "中規模チーム向けの標準プラン",
            "features": '["全AI機能", "電話サポート", "カスタムテンプレート", "レポート機能"]',
            "has_api_access": True,
            "has_custom_branding": False,
            "has_priority_support": True,
            "has_advanced_analytics": True,
            "display_order": 2
        },
        {
            "plan_type": PlanType.PROFESSIONAL,
            "name": "プロフェッショナルプラン",
            "max_users": 200,
            "max_tokens_per_month": 2000000,
            "max_templates": -1,  # 無制限
            "max_storage_gb": 100,
            "monthly_price": 98000,
            "description": "大規模チーム向けのプレミアムプラン",
            "features": '["全機能", "専用サポート", "カスタムブランディング", "API access", "高度な分析"]',
            "has_api_access": True,
            "has_custom_branding": True,
            "has_priority_support": True,
            "has_advanced_analytics": True,
            "display_order": 3
        },
        {
            "plan_type": PlanType.ENTERPRISE,
            "name": "エンタープライズプラン",
            "max_users": -1,  # 無制限
            "max_tokens_per_month": -1,  # 無制限
            "max_templates": -1,  # 無制限
            "max_storage_gb": -1,  # 無制限
            "monthly_price": 198000,
            "description": "企業向けの包括的なソリューション",
            "features": '["全機能", "24/7専用サポート", "オンサイトサポート", "カスタム統合", "専用クラウド"]',
            "has_api_access": True,
            "has_custom_branding": True,
            "has_priority_support": True,
            "has_advanced_analytics": True,
            "display_order": 4
        }
    ]
    
    for plan_data in plans:
        plan = Plan(**plan_data)
        db.add(plan)
    
    try:
        db.commit()
        print("✅ デフォルトプランを作成しました")
    except Exception as e:
        db.rollback()
        print(f"❌ プラン作成エラー: {e}")

def init_database():
    """データベース初期化"""
    db = next(get_db())
    try:
        create_default_plans(db)
        print("✅ データベース初期化完了")
    finally:
        db.close()

if __name__ == "__main__":
    init_database()