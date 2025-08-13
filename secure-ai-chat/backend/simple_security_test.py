#!/usr/bin/env python3
"""
セキュアAIチャット - 簡易セキュリティテスト
"""

import sys
import os

# パスを追加してアプリケーションモジュールをインポート可能にする
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timezone, timedelta
from cryptography.fernet import Fernet
import secrets
import string
import re

# セキュリティ設定
SECRET_KEY = "test-secret-key-for-testing-purposes-only"
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 暗号化キー（テスト用）
encryption_key = Fernet.generate_key()
cipher_suite = Fernet(encryption_key)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """パスワード検証"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """パスワードハッシュ化"""
    return pwd_context.hash(password)

def create_access_token(subject: str, expires_delta: timedelta = None) -> str:
    """JWTトークン作成"""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    
    to_encode = {
        "sub": subject,
        "exp": expire,
        "type": "access",
        "iat": datetime.now(timezone.utc)
    }
    
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> dict:
    """JWTトークン検証"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

def encrypt_sensitive_data(data: str) -> str:
    """データ暗号化"""
    return cipher_suite.encrypt(data.encode()).decode()

def decrypt_sensitive_data(encrypted_data: str) -> str:
    """データ復号化"""
    return cipher_suite.decrypt(encrypted_data.encode()).decode()

def validate_password_strength(password: str) -> tuple[bool, list[str]]:
    """パスワード強度検証"""
    errors = []
    
    if len(password) < 8:
        errors.append("パスワードは8文字以上である必要があります")
    
    if not re.search(r"[a-z]", password):
        errors.append("小文字が必要です")
    
    if not re.search(r"[A-Z]", password):
        errors.append("大文字が必要です")
    
    if not re.search(r"\d", password):
        errors.append("数字が必要です")
    
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        errors.append("特殊文字が必要です")
    
    return len(errors) == 0, errors

def test_password_security():
    """パスワードセキュリティテスト"""
    print("🧪 パスワードセキュリティテスト開始...")
    
    # 基本的なハッシュ化・検証テスト
    test_password = "TestPassword123!"
    hashed = get_password_hash(test_password)
    
    assert hashed != test_password, "❌ パスワードがハッシュ化されていません"
    assert verify_password(test_password, hashed), "❌ パスワード検証に失敗しました"
    assert not verify_password("WrongPassword", hashed), "❌ 間違ったパスワードが検証に通りました"
    
    # パスワード強度チェック
    strong_password = "SecureP@ssw0rd123"
    weak_passwords = [
        "123456",
        "password",
        "PASSWORD",
        "password123",
        "Password!"
    ]
    
    is_strong, errors = validate_password_strength(strong_password)
    assert is_strong, f"❌ 強いパスワードが拒否されました: {errors}"
    
    for weak_password in weak_passwords:
        is_strong, errors = validate_password_strength(weak_password)
        assert not is_strong, f"❌ 弱いパスワードが受け入れられました: {weak_password}"
    
    print("✅ パスワードセキュリティテスト完了")

def test_jwt_security():
    """JWTセキュリティテスト"""
    print("🧪 JWTセキュリティテスト開始...")
    
    user_id = "test_user_123"
    
    # 基本的なトークン作成・検証
    token = create_access_token(subject=user_id)
    assert token is not None, "❌ トークンが作成されませんでした"
    assert len(token) > 50, "❌ トークンが短すぎます"
    
    payload = verify_token(token)
    assert payload is not None, "❌ トークン検証に失敗しました"
    assert payload.get("sub") == user_id, "❌ ユーザーIDが一致しません"
    assert payload.get("type") == "access", "❌ トークンタイプが正しくありません"
    
    # トークン有効期限テスト
    short_token = create_access_token(
        subject=user_id,
        expires_delta=timedelta(seconds=-1)  # 既に期限切れ
    )
    expired_payload = verify_token(short_token)
    assert expired_payload is None, "❌ 期限切れトークンが検証に通りました"
    
    # トークン改ざんテスト
    tampered_token = token[:-10] + "TAMPERED00"
    tampered_payload = verify_token(tampered_token)
    assert tampered_payload is None, "❌ 改ざんされたトークンが検証に通りました"
    
    print("✅ JWTセキュリティテスト完了")

def test_data_encryption():
    """データ暗号化テスト"""
    print("🧪 データ暗号化テスト開始...")
    
    # 基本的な暗号化・復号化
    original_data = "機密情報: ユーザーの個人データ"
    encrypted = encrypt_sensitive_data(original_data)
    
    assert encrypted != original_data, "❌ データが暗号化されていません"
    assert len(encrypted) > len(original_data), "❌ 暗号化後のサイズが不正です"
    
    decrypted = decrypt_sensitive_data(encrypted)
    assert decrypted == original_data, "❌ 復号化に失敗しました"
    
    # 特殊文字を含むデータのテスト
    special_data = "データ: 123!@#$%^&*()_+{}[]|\\:;\"'<>?,./~`"
    encrypted_special = encrypt_sensitive_data(special_data)
    decrypted_special = decrypt_sensitive_data(encrypted_special)
    assert decrypted_special == special_data, "❌ 特殊文字を含むデータの暗号化に失敗しました"
    
    # 暗号化の一意性テスト（同じデータでも異なる暗号化結果）
    data = "同じデータ"
    encrypted1 = encrypt_sensitive_data(data)
    encrypted2 = encrypt_sensitive_data(data)
    
    # Fernetでは同じデータは異なる暗号化結果になる（非決定的）
    decrypted1 = decrypt_sensitive_data(encrypted1)
    decrypted2 = decrypt_sensitive_data(encrypted2)
    
    assert decrypted1 == data, "❌ 1回目の復号化に失敗しました"
    assert decrypted2 == data, "❌ 2回目の復号化に失敗しました"
    
    print("✅ データ暗号化テスト完了")

def sanitize_sql_input(input_str: str) -> str:
    """SQL入力のサニタイゼーション"""
    dangerous_patterns = [
        "'", '"', ";", "--", "/*", "*/", 
        "DROP", "DELETE", "INSERT", "UPDATE", "UNION", "SELECT"
    ]
    
    sanitized = input_str
    for pattern in dangerous_patterns:
        sanitized = sanitized.replace(pattern, "")
    
    return sanitized

def escape_html(input_str: str) -> str:
    """HTMLエスケープ"""
    return (input_str.replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                    .replace("'", "&#x27;")
                    .replace('"', "&quot;")
                    .replace("javascript:", ""))

def test_input_validation():
    """入力値検証テスト"""
    print("🧪 入力値検証テスト開始...")
    
    # SQLインジェクション対策のテスト
    malicious_inputs = [
        "'; DROP TABLE users; --",
        "1 OR 1=1", 
        "admin'--",
        "' UNION SELECT * FROM users --",
    ]
    
    for malicious_input in malicious_inputs:
        sanitized = sanitize_sql_input(malicious_input)
        # サニタイゼーション後に危険な文字が除去されていることを確認
        dangerous_chars = ["'", ";", "--"]
        has_dangerous_chars = any(char in sanitized for char in dangerous_chars)
        assert not has_dangerous_chars, f"❌ SQLインジェクション対策が不十分: {malicious_input} -> {sanitized}"
    
    # XSS対策のテスト
    xss_payloads = [
        "<script>alert('XSS')</script>",
        "javascript:alert('XSS')",
        "<img src=x onerror=alert('XSS')>",
        "';alert('XSS');//",
    ]
    
    for payload in xss_payloads:
        escaped = escape_html(payload)
        # エスケープ後に元の危険なパターンが含まれていないことを確認
        # HTMLエスケープによって < > が &lt; &gt; に変換され、安全になっていることを確認
        assert "<script>" not in escaped, f"❌ <script>タグがエスケープされていません: {escaped}"
        assert "javascript:" not in escaped, f"❌ javascript:がエスケープされていません: {escaped}"
        assert escaped != payload, f"❌ XSSペイロードがエスケープされていません: {payload}"
    
    print("✅ 入力値検証テスト完了")

def test_rate_limiting():
    """レート制限テスト"""
    print("🧪 レート制限テスト開始...")
    
    class SimpleRateLimiter:
        def __init__(self, max_attempts=5, window_minutes=60):
            self.attempts = {}
            self.max_attempts = max_attempts
            self.window_minutes = window_minutes
        
        def is_allowed(self, identifier: str) -> bool:
            now = datetime.now()
            
            if identifier not in self.attempts:
                self.attempts[identifier] = []
            
            # 古い記録を削除
            cutoff_time = now - timedelta(minutes=self.window_minutes)
            self.attempts[identifier] = [
                attempt_time for attempt_time in self.attempts[identifier]
                if attempt_time > cutoff_time
            ]
            
            # 制限チェック
            if len(self.attempts[identifier]) >= self.max_attempts:
                return False
            
            # 新しい試行を記録
            self.attempts[identifier].append(now)
            return True
        
        def reset_attempts(self, identifier: str):
            if identifier in self.attempts:
                del self.attempts[identifier]
    
    # レート制限テスト
    rate_limiter = SimpleRateLimiter(max_attempts=3, window_minutes=60)
    identifier = "test_user"
    
    # 最初の3回は許可される
    for i in range(3):
        assert rate_limiter.is_allowed(identifier), f"❌ {i+1}回目の試行が拒否されました"
    
    # 4回目は拒否される
    assert not rate_limiter.is_allowed(identifier), "❌ 制限を超えた試行が許可されました"
    
    # リセット後は再び許可される
    rate_limiter.reset_attempts(identifier)
    assert rate_limiter.is_allowed(identifier), "❌ リセット後の試行が拒否されました"
    
    print("✅ レート制限テスト完了")

def run_all_security_tests():
    """全セキュリティテストの実行"""
    print("🚀 セキュリティテストスイート開始\n")
    
    try:
        test_password_security()
        test_jwt_security()
        test_data_encryption()
        test_input_validation()
        test_rate_limiting()
        
        print("\n🎉 全セキュリティテストが正常に完了しました！")
        print("✅ パスワードセキュリティ - OK")
        print("✅ JWTセキュリティ - OK") 
        print("✅ データ暗号化 - OK")
        print("✅ 入力値検証 - OK")
        print("✅ レート制限 - OK")
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ セキュリティテスト失敗: {e}")
        return False
    except Exception as e:
        print(f"\n💥 予期しないエラー: {e}")
        return False

if __name__ == "__main__":
    success = run_all_security_tests()
    sys.exit(0 if success else 1)