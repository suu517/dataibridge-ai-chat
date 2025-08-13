// API設定画面のJavaScript
class APISettingsManager {
    constructor() {
        this.apiBase = '/api/v1';
        this.currentTenant = null;
        this.currentUser = null;
        this.init();
    }

    async init() {
        await this.checkAuth();
        await this.loadCurrentSettings();
        await this.loadUsageStats();
        this.bindEvents();
        this.updateUI();
    }

    // 認証チェック
    async checkAuth() {
        try {
            const token = localStorage.getItem('token');
            if (!token) {
                window.location.href = 'login.html';
                return;
            }

            const response = await fetch(`${this.apiBase}/auth/me`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                throw new Error('認証に失敗しました');
            }

            const data = await response.json();
            this.currentUser = data.user;
            this.currentTenant = data.tenant;

            // ユーザー名表示
            document.getElementById('userName').textContent = this.currentUser.full_name || this.currentUser.email;

        } catch (error) {
            console.error('認証エラー:', error);
            localStorage.removeItem('token');
            window.location.href = 'login.html';
        }
    }

    // 現在の設定を読み込み
    async loadCurrentSettings() {
        try {
            const token = localStorage.getItem('token');
            const response = await fetch(`${this.apiBase}/tenants/ai-settings`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                throw new Error('設定の読み込みに失敗しました');
            }

            const settings = await response.json();
            this.populateForm(settings);

        } catch (error) {
            console.error('設定読み込みエラー:', error);
            this.showToast('設定の読み込みに失敗しました', 'error');
        }
    }

    // フォームに設定を反映
    populateForm(settings) {
        const provider = settings.ai_provider || 'system_default';
        
        // プロバイダー選択
        const providerRadio = document.querySelector(`input[name="provider"][value="${provider}"]`);
        if (providerRadio) {
            providerRadio.checked = true;
        }

        // 現在のプロバイダー表示
        document.getElementById('currentProvider').textContent = this.getProviderDisplayName(provider);

        // Azure OpenAI設定
        if (settings.azure_settings) {
            document.getElementById('azureEndpoint').value = settings.azure_settings.endpoint || '';
            document.getElementById('azureApiKey').value = '••••••••••••••••'; // マスク表示
            document.getElementById('azureApiVersion').value = settings.azure_settings.api_version || '2024-02-01';
            document.getElementById('azureDeployment').value = settings.azure_settings.deployment_name || 'gpt-4';
        }

        // OpenAI設定
        if (settings.openai_settings) {
            document.getElementById('openaiApiKey').value = '••••••••••••••••'; // マスク表示
            document.getElementById('openaiModel').value = settings.openai_settings.model || 'gpt-4';
        }

        this.updateProviderConfig(provider);
    }

    // 使用量統計を読み込み
    async loadUsageStats() {
        try {
            const token = localStorage.getItem('token');
            const response = await fetch(`${this.apiBase}/tenants/usage-stats`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                throw new Error('使用量の読み込みに失敗しました');
            }

            const stats = await response.json();
            this.updateUsageDisplay(stats);

        } catch (error) {
            console.error('使用量読み込みエラー:', error);
            // エラーでも画面は表示できるようにする
        }
    }

    // 使用量表示を更新
    updateUsageDisplay(stats) {
        document.getElementById('monthlyTokens').textContent = this.formatNumber(stats.monthly_tokens || 0);
        document.getElementById('dailyTokens').textContent = this.formatNumber(stats.daily_tokens || 0);
        document.getElementById('monthlyLimit').textContent = this.formatNumber(stats.monthly_limit || 0);
        document.getElementById('remainingTokens').textContent = this.formatNumber(stats.remaining_tokens || 0);

        // 進捗バー
        const usagePercent = stats.monthly_limit > 0 ? Math.round((stats.monthly_tokens / stats.monthly_limit) * 100) : 0;
        document.getElementById('usagePercent').textContent = `${usagePercent}%`;
        document.getElementById('usageProgress').style.width = `${Math.min(usagePercent, 100)}%`;

        // プログレスバーの色を使用率に応じて変更
        const progressFill = document.getElementById('usageProgress');
        if (usagePercent >= 90) {
            progressFill.style.backgroundColor = 'var(--error-color)';
        } else if (usagePercent >= 70) {
            progressFill.style.backgroundColor = 'var(--warning-color)';
        } else {
            progressFill.style.backgroundColor = 'var(--primary-color)';
        }
    }

    // イベントバインディング
    bindEvents() {
        // プロバイダー選択
        document.querySelectorAll('input[name="provider"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.updateProviderConfig(e.target.value);
                this.validateForm();
            });
        });

        // フォーム入力
        document.querySelectorAll('.provider-config input, .provider-config select').forEach(input => {
            input.addEventListener('input', () => {
                this.validateForm();
            });
        });

        // 接続テスト
        document.getElementById('testConnection').addEventListener('click', () => {
            this.testConnection();
        });

        // 設定保存
        document.getElementById('saveSettings').addEventListener('click', () => {
            this.saveSettings();
        });

        // キャンセル
        document.getElementById('cancelSettings').addEventListener('click', () => {
            this.loadCurrentSettings();
        });

        // ログアウト
        document.getElementById('logoutBtn').addEventListener('click', () => {
            localStorage.removeItem('token');
            window.location.href = 'login.html';
        });
    }

    // プロバイダー設定表示を更新
    updateProviderConfig(provider) {
        // 全ての設定セクションを非表示
        document.querySelectorAll('.provider-config').forEach(config => {
            config.classList.add('hidden');
        });

        // 選択されたプロバイダーの設定を表示
        if (provider === 'azure_openai') {
            document.getElementById('azureSettings').classList.remove('hidden');
        } else if (provider === 'openai') {
            document.getElementById('openaiSettings').classList.remove('hidden');
        }
    }

    // フォーム検証
    validateForm() {
        const provider = document.querySelector('input[name="provider"]:checked').value;
        let isValid = true;

        if (provider === 'azure_openai') {
            const endpoint = document.getElementById('azureEndpoint').value.trim();
            const apiKey = document.getElementById('azureApiKey').value.trim();
            const deployment = document.getElementById('azureDeployment').value.trim();

            isValid = endpoint && apiKey && deployment && apiKey !== '••••••••••••••••';
        } else if (provider === 'openai') {
            const apiKey = document.getElementById('openaiApiKey').value.trim();
            isValid = apiKey && apiKey !== '••••••••••••••••';
        }

        // ボタンの有効/無効を制御
        document.getElementById('testConnection').disabled = !isValid || provider === 'system_default';
        document.getElementById('saveSettings').disabled = false; // 設定変更があれば保存可能
    }

    // 接続テスト
    async testConnection() {
        const provider = document.querySelector('input[name="provider"]:checked').value;
        
        if (provider === 'system_default') {
            return;
        }

        this.showLoading(true);
        this.hideTestResult();

        try {
            const testData = this.collectFormData();
            const token = localStorage.getItem('token');

            const response = await fetch(`${this.apiBase}/tenants/test-ai-connection`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(testData)
            });

            const result = await response.json();

            if (response.ok && result.success) {
                this.showTestResult('接続テストが成功しました！AIとの通信が正常に確立されました。', 'success');
            } else {
                this.showTestResult(`接続テストに失敗しました: ${result.message || '不明なエラー'}`, 'error');
            }

        } catch (error) {
            console.error('接続テストエラー:', error);
            this.showTestResult('接続テストでエラーが発生しました。設定を確認してください。', 'error');
        } finally {
            this.showLoading(false);
        }
    }

    // 設定保存
    async saveSettings() {
        this.showLoading(true);

        try {
            const formData = this.collectFormData();
            const token = localStorage.getItem('token');

            const response = await fetch(`${this.apiBase}/tenants/ai-settings`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(formData)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || '設定の保存に失敗しました');
            }

            this.showToast('設定が正常に保存されました', 'success');
            
            // 設定を再読み込み
            await this.loadCurrentSettings();
            await this.loadUsageStats();

        } catch (error) {
            console.error('設定保存エラー:', error);
            this.showToast(`設定の保存に失敗しました: ${error.message}`, 'error');
        } finally {
            this.showLoading(false);
        }
    }

    // フォームデータ収集
    collectFormData() {
        const provider = document.querySelector('input[name="provider"]:checked').value;
        const data = { provider };

        if (provider === 'azure_openai') {
            const apiKey = document.getElementById('azureApiKey').value.trim();
            data.azure_settings = {
                endpoint: document.getElementById('azureEndpoint').value.trim(),
                api_key: apiKey !== '••••••••••••••••' ? apiKey : null, // マスクされていない場合のみ送信
                api_version: document.getElementById('azureApiVersion').value,
                deployment_name: document.getElementById('azureDeployment').value.trim()
            };
        } else if (provider === 'openai') {
            const apiKey = document.getElementById('openaiApiKey').value.trim();
            data.openai_settings = {
                api_key: apiKey !== '••••••••••••••••' ? apiKey : null, // マスクされていない場合のみ送信
                model: document.getElementById('openaiModel').value
            };
        }

        return data;
    }

    // UI更新
    updateUI() {
        this.validateForm();
    }

    // ユーティリティメソッド
    getProviderDisplayName(provider) {
        const names = {
            'system_default': 'システムデフォルト',
            'azure_openai': 'Azure OpenAI',
            'openai': 'OpenAI'
        };
        return names[provider] || provider;
    }

    formatNumber(num) {
        return new Intl.NumberFormat('ja-JP').format(num);
    }

    showLoading(show) {
        const overlay = document.getElementById('loadingOverlay');
        if (show) {
            overlay.classList.remove('hidden');
        } else {
            overlay.classList.add('hidden');
        }
    }

    showTestResult(message, type) {
        const result = document.getElementById('testResult');
        result.textContent = message;
        result.className = `test-result ${type}`;
        result.style.display = 'block';
    }

    hideTestResult() {
        const result = document.getElementById('testResult');
        result.style.display = 'none';
    }

    showToast(message, type) {
        const toast = document.getElementById('toast');
        toast.textContent = message;
        toast.className = `toast ${type}`;
        toast.classList.remove('hidden');
        toast.classList.add('show');

        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => {
                toast.classList.add('hidden');
            }, 300);
        }, 3000);
    }
}

// パスワード表示/非表示切り替え
function togglePassword(inputId) {
    const input = document.getElementById(inputId);
    const button = input.parentElement.querySelector('.toggle-password');
    const icon = button.querySelector('i');

    if (input.type === 'password') {
        input.type = 'text';
        icon.classList.remove('fa-eye');
        icon.classList.add('fa-eye-slash');
    } else {
        input.type = 'password';
        icon.classList.remove('fa-eye-slash');
        icon.classList.add('fa-eye');
    }
}

// ページ読み込み時に初期化
document.addEventListener('DOMContentLoaded', () => {
    new APISettingsManager();
});