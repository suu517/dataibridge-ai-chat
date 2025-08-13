"""
セキュアAIチャット - カスタム例外定義
"""

from typing import Any, Dict, Optional, Union
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)

class BaseCustomException(HTTPException):
    """基底カスタム例外クラス"""
    
    def __init__(
        self,
        detail: Union[str, Dict[str, Any]],
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        headers: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
        log_message: Optional[str] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code
        
        # ログ出力
        if log_message:
            logger.error(f"[{error_code}] {log_message}: {detail}")

# 認証・認可関連例外
class AuthenticationError(BaseCustomException):
    """認証エラー"""
    def __init__(self, detail: str = "認証に失敗しました"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTH_001",
            log_message="Authentication error"
        )

class AuthorizationError(BaseCustomException):
    """認可エラー"""
    def __init__(self, detail: str = "この操作を実行する権限がありません"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="AUTH_002",
            log_message="Authorization error"
        )

class TokenExpiredError(BaseCustomException):
    """トークン期限切れエラー"""
    def __init__(self, detail: str = "認証トークンの有効期限が切れています"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTH_003",
            log_message="Token expired"
        )

class InvalidTokenError(BaseCustomException):
    """無効トークンエラー"""
    def __init__(self, detail: str = "無効な認証トークンです"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTH_004",
            log_message="Invalid token"
        )

class AccountLockoutError(BaseCustomException):
    """アカウントロックアウトエラー"""
    def __init__(self, detail: str = "アカウントがロックされています。しばらくお待ちください"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="AUTH_005",
            log_message="Account locked out"
        )

# データベース関連例外
class DatabaseError(BaseCustomException):
    """データベースエラー"""
    def __init__(self, detail: str = "データベースエラーが発生しました"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="DB_001",
            log_message="Database error"
        )

class RecordNotFoundError(BaseCustomException):
    """レコード未発見エラー"""
    def __init__(self, detail: str = "指定されたリソースが見つかりません"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="DB_002",
            log_message="Record not found"
        )

class DataIntegrityError(BaseCustomException):
    """データ整合性エラー"""
    def __init__(self, detail: str = "データの整合性に問題があります"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="DB_003",
            log_message="Data integrity error"
        )

# AI サービス関連例外
class AIServiceError(BaseCustomException):
    """AIサービスエラー"""
    def __init__(self, detail: str = "AIサービスでエラーが発生しました"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="AI_001",
            log_message="AI service error"
        )

class AIServiceUnavailableError(BaseCustomException):
    """AIサービス利用不可エラー"""
    def __init__(self, detail: str = "AIサービスが一時的に利用できません"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="AI_002",
            log_message="AI service unavailable"
        )

class AIRateLimitError(BaseCustomException):
    """AIレート制限エラー"""
    def __init__(self, detail: str = "AIサービスのレート制限に達しました"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="AI_003",
            log_message="AI rate limit exceeded"
        )

class TokenLimitExceededError(BaseCustomException):
    """トークン制限超過エラー"""
    def __init__(self, detail: str = "トークンの利用上限に達しました"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="AI_004",
            log_message="Token limit exceeded"
        )

class ContentFilterError(BaseCustomException):
    """コンテンツフィルターエラー"""
    def __init__(self, detail: str = "入力内容が安全性フィルターに引っかかりました"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="AI_005",
            log_message="Content filter violation"
        )

# バリデーション関連例外
class ValidationError(BaseCustomException):
    """バリデーションエラー"""
    def __init__(self, detail: Union[str, Dict[str, Any]] = "入力データの検証に失敗しました"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VAL_001",
            log_message="Validation error"
        )

class BusinessLogicError(BaseCustomException):
    """ビジネスロジックエラー"""
    def __init__(self, detail: str = "ビジネスルールに反する操作です"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="BIZ_001",
            log_message="Business logic error"
        )

# ファイル操作関連例外
class FileUploadError(BaseCustomException):
    """ファイルアップロードエラー"""
    def __init__(self, detail: str = "ファイルのアップロードに失敗しました"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="FILE_001",
            log_message="File upload error"
        )

class FileSizeExceededError(BaseCustomException):
    """ファイルサイズ超過エラー"""
    def __init__(self, detail: str = "ファイルサイズが上限を超えています"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            error_code="FILE_002",
            log_message="File size exceeded"
        )

class UnsupportedFileTypeError(BaseCustomException):
    """サポート外ファイルタイプエラー"""
    def __init__(self, detail: str = "サポートされていないファイル形式です"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="FILE_003",
            log_message="Unsupported file type"
        )

# システム関連例外
class ExternalServiceError(BaseCustomException):
    """外部サービスエラー"""
    def __init__(self, detail: str = "外部サービスでエラーが発生しました"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_502_BAD_GATEWAY,
            error_code="SYS_001",
            log_message="External service error"
        )

class ConfigurationError(BaseCustomException):
    """設定エラー"""
    def __init__(self, detail: str = "システム設定にエラーがあります"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="SYS_002",
            log_message="Configuration error"
        )

class SecurityViolationError(BaseCustomException):
    """セキュリティ違反エラー"""
    def __init__(self, detail: str = "セキュリティポリシー違反が検出されました"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="SEC_001",
            log_message="Security violation"
        )

# エラーレスポンス形成ヘルパー関数
def create_error_response(
    error_code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
) -> Dict[str, Any]:
    """標準エラーレスポンスを作成"""
    response = {
        "error": True,
        "error_code": error_code,
        "message": message,
        "status_code": status_code,
        "timestamp": int(__import__("time").time())
    }
    
    if details:
        response["details"] = details
    
    return response

# エラーハンドリングデコレータ
def handle_errors(func):
    """エラーハンドリングデコレータ"""
    import functools
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except BaseCustomException:
            # カスタム例外はそのまま再発生
            raise
        except Exception as e:
            # 予期しない例外はログ出力してシステムエラーとして処理
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}", exc_info=True)
            raise BaseCustomException(
                detail="システムエラーが発生しました",
                error_code="SYS_999",
                log_message=f"Unexpected error in {func.__name__}"
            )
    
    return wrapper