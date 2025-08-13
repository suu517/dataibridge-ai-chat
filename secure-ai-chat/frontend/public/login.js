/**
 * セキュアAIチャット - ログイン画面
 */

class AuthManager {
    constructor() {
        this.apiBaseUrl = 'http://localhost:8000';
        this.init();
    }

    init() {
        this.bindEvents();
        this.checkToken();
    }

    bindEvents() {
        // フォーム切り替え
        document.getElementById('showSignupForm').addEventListener('click', (e) => {
            e.preventDefault();
            this.showForm('signup');
        });

        document.getElementById('showLoginForm').addEventListener('click', (e) => {
            e.preventDefault();
            this.showForm('login');
        });

        document.getElementById('showTenantSignupForm').addEventListener('click', (e) => {
            e.preventDefault();
            this.showForm('tenantSignup');
        });

        document.getElementById('showLoginFormFromTenant').addEventListener('click', (e) => {
            e.preventDefault();
            this.showForm('login');
        });

        // フォーム送信
        document.getElementById('loginFormElement').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleLogin();
        });

        document.getElementById('signupFormElement').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleSignup();
        });

        document.getElementById('tenantSignupFormElement').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleTenantSignup();
        });

        // パスワード確認
        document.getElementById('signupPasswordConfirm').addEventListener('input', (e) => {
            this.validatePasswordMatch();
        });
    }

    showForm(formType) {
        // 全フォームを隠す
        document.getElementById('loginForm').style.display = 'none';
        document.getElementById('signupForm').style.display = 'none';
        document.getElementById('tenantSignupForm').style.display = 'none';

        // 指定されたフォームを表示
        switch(formType) {
            case 'signup':
                document.getElementById('signupForm').style.display = 'block';
                break;
            case 'tenantSignup':
                document.getElementById('tenantSignupForm').style.display = 'block';
                break;
            default:
                document.getElementById('loginForm').style.display = 'block';
        }

        this.clearMessages();
    }

    validatePasswordMatch() {
        const password = document.getElementById('signupPassword').value;
        const confirmPassword = document.getElementById('signupPasswordConfirm').value;
        const confirmInput = document.getElementById('signupPasswordConfirm');

        if (confirmPassword && password !== confirmPassword) {
            confirmInput.setCustomValidity('パスワードが一致しません');
        } else {
            confirmInput.setCustomValidity('');
        }
    }

    async handleLogin() {
        const form = document.getElementById('loginFormElement');
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());

        // 空のテナントドメインを削除
        if (!data.tenant_domain.trim()) {
            delete data.tenant_domain;
        }

        try {
            this.setLoading('login', true);
            
            const response = await fetch(`${this.apiBaseUrl}/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (response.ok) {
                localStorage.setItem('access_token', result.access_token);
                localStorage.setItem('token_type', result.token_type);
                
                this.showSuccessMessage('ログインしました。チャット画面に移動します...');
                
                setTimeout(() => {
                    window.location.href = '/chat.html';
                }, 1500);
            } else {
                this.showErrorMessage(result.detail || 'ログインに失敗しました');
            }
        } catch (error) {
            console.error('ログインエラー:', error);
            this.showErrorMessage('サーバーとの通信に失敗しました');
        } finally {
            this.setLoading('login', false);
        }
    }

    async handleSignup() {
        const form = document.getElementById('signupFormElement');
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());

        // パスワード確認
        if (data.password !== data.password_confirm) {
            this.showErrorMessage('パスワードが一致しません');
            return;
        }

        delete data.password_confirm;

        try {
            this.setLoading('signup', true);
            
            const response = await fetch(`${this.apiBaseUrl}/auth/accept-invitation`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (response.ok) {
                localStorage.setItem('access_token', result.access_token);
                localStorage.setItem('token_type', result.token_type);
                
                this.showSuccessMessage('登録が完了しました。チャット画面に移動します...');
                
                setTimeout(() => {
                    window.location.href = '/chat.html';
                }, 1500);
            } else {
                this.showErrorMessage(result.detail || '登録に失敗しました');
            }
        } catch (error) {
            console.error('登録エラー:', error);
            this.showErrorMessage('サーバーとの通信に失敗しました');
        } finally {
            this.setLoading('signup', false);
        }
    }

    async handleTenantSignup() {
        const form = document.getElementById('tenantSignupFormElement');
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());

        try {
            this.setLoading('tenantSignup', true);
            
            const response = await fetch(`${this.apiBaseUrl}/auth/register/tenant`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (response.ok) {
                this.showSuccessMessage(
                    '組織登録が完了しました。管理者アカウントでログインしてください。'
                );
                
                // ログインフォームに切り替え、メールアドレスを設定
                setTimeout(() => {
                    this.showForm('login');
                    document.getElementById('loginEmail').value = data.admin_email;
                    document.getElementById('loginTenantDomain').value = data.domain;
                }, 2000);
            } else {
                this.showErrorMessage(result.detail || '組織登録に失敗しました');
            }
        } catch (error) {
            console.error('組織登録エラー:', error);
            this.showErrorMessage('サーバーとの通信に失敗しました');
        } finally {
            this.setLoading('tenantSignup', false);
        }
    }

    setLoading(formType, isLoading) {
        const btnId = formType + 'Btn';
        const button = document.getElementById(btnId);
        const textSpan = button.querySelector('.btn-text');
        const loadingSpan = button.querySelector('.btn-loading');

        button.disabled = isLoading;
        textSpan.style.display = isLoading ? 'none' : 'inline';
        loadingSpan.style.display = isLoading ? 'flex' : 'none';
    }

    showErrorMessage(message) {
        this.clearMessages();
        const errorDiv = document.getElementById('errorMessage');
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
        
        setTimeout(() => {
            errorDiv.style.display = 'none';
        }, 5000);
    }

    showSuccessMessage(message) {
        this.clearMessages();
        const successDiv = document.getElementById('successMessage');
        successDiv.textContent = message;
        successDiv.style.display = 'block';
    }

    clearMessages() {
        document.getElementById('errorMessage').style.display = 'none';
        document.getElementById('successMessage').style.display = 'none';
    }

    checkToken() {
        const token = localStorage.getItem('access_token');
        if (token) {
            // トークンが有効か確認
            this.validateToken(token).then(isValid => {
                if (isValid) {
                    window.location.href = '/chat.html';
                } else {
                    localStorage.removeItem('access_token');
                    localStorage.removeItem('token_type');
                }
            });
        }
    }

    async validateToken(token) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/auth/me`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            return response.ok;
        } catch (error) {
            return false;
        }
    }
}

// ページ読み込み時に初期化
document.addEventListener('DOMContentLoaded', () => {
    new AuthManager();
});