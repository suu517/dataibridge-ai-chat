// プロンプトテンプレート管理 - JavaScript

const API_BASE_URL = 'http://localhost:8000';
let templates = [];
let currentTemplate = null;
let editingTemplateId = null;
let availableModels = [];

// API接続テスト関数（デバッグ用）
window.testApiConnection = function() {
    console.log('🔧 API接続テストを開始...');
    
    // ステップ1: ヘルスチェック
    fetch(`${API_BASE_URL}/health`)
        .then(response => {
            console.log('💚 ヘルスチェック:', response.status);
            return response.json();
        })
        .then(data => {
            console.log('💚 ヘルスチェック結果:', data);
            
            // ステップ2: テンプレートAPI
            return fetch(`${API_BASE_URL}/api/templates`);
        })
        .then(response => {
            console.log('📝 テンプレートAPI:', response.status);
            return response.json();
        })
        .then(templates => {
            console.log('📝 テンプレート取得結果:', templates);
            alert(`✅ API接続成功！\n- ヘルスチェック: OK\n- テンプレート: ${templates.length}件`);
        })
        .catch(error => {
            console.error('❌ API接続エラー:', error);
            alert(`❌ API接続失敗:\n${error.message}`);
        });
};

// 初期化
document.addEventListener('DOMContentLoaded', function() {
    console.log('📄 templates.js初期化開始');
    loadTemplates();
    loadModels();
    setupEventListeners();
});

// イベントリスナーの設定
function setupEventListeners() {
    // カテゴリフィルター
    document.querySelectorAll('.filter-tab').forEach(tab => {
        tab.addEventListener('click', function() {
            document.querySelectorAll('.filter-tab').forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            filterTemplates();
        });
    });

    // フォーム送信
    document.getElementById('templateForm').addEventListener('submit', handleFormSubmit);
    document.getElementById('useForm').addEventListener('submit', handleUseTemplate);
    
    // モデル選択変更時のイベント
    const modelSelect = document.getElementById('modelSelect');
    if (modelSelect) {
        modelSelect.addEventListener('change', updateModelInfo);
    }

    // キーボードショートカット
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeModal();
            closeUseModal();
            closeResultModal();
        }
        if (e.ctrlKey && e.key === 'n') {
            e.preventDefault();
            openCreateModal();
        }
    });
}

// テンプレート一覧を読み込み
window.loadTemplates = async function loadTemplates() {
    try {
        console.log('🚀 テンプレート読み込み開始:', `${API_BASE_URL}/api/templates`);
        
        // ローディング表示を確実に表示
        const templateGrid = document.getElementById('templateGrid');
        if (templateGrid) {
            templateGrid.innerHTML = `
                <div class="loading-message">
                    <div class="loading-spinner"></div>
                    <p>テンプレートを読み込み中...</p>
                </div>
            `;
        }
        
        const response = await fetch(`${API_BASE_URL}/api/templates`);
        console.log('📡 レスポンス受信:', response.status, response.statusText);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        templates = await response.json();
        console.log('✅ テンプレート取得成功:', templates.length, '件');
        console.log('📋 テンプレート詳細:', templates);
        
        displayTemplates(templates);
        
        // カテゴリタブを更新
        updateCategoryTabs();

    } catch (error) {
        console.error('❌ テンプレート読み込みエラー:', error);
        showErrorMessage('テンプレートの読み込みに失敗しました。APIサーバーが起動しているか確認してください。');
        
        // ローディングメッセージを隠してエラー表示
        const templateGrid = document.getElementById('templateGrid');
        if (templateGrid) {
            templateGrid.innerHTML = `
                <div style="text-align: center; padding: 40px; color: #dc2626;">
                    <h3>⚠️ エラーが発生しました</h3>
                    <p>${error.message}</p>
                    <button onclick="window.loadTemplates()" style="margin-top: 20px; padding: 10px 20px; background: #3b82f6; color: white; border: none; border-radius: 4px; cursor: pointer;">再試行</button>
                </div>
            `;
        }
    }
}

// 利用可能モデル一覧を読み込み
async function loadModels() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/models`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        availableModels = await response.json();
        updateModelSelects();

    } catch (error) {
        console.error('モデル読み込みエラー:', error);
        // エラーの場合はデフォルトモデルのみ表示
        availableModels = [
            { id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo', description: 'OpenAI GPT-3.5 Turbo' }
        ];
        updateModelSelects();
    }
}

// モデル選択ドロップダウンを更新
function updateModelSelects() {
    const modelSelect = document.getElementById('modelSelect');
    if (modelSelect) {
        modelSelect.innerHTML = availableModels.map(model => 
            `<option value="${model.id}">${model.name}</option>`
        ).join('');
        
        // デフォルト選択
        modelSelect.value = 'gpt-3.5-turbo';
        updateModelInfo();
    }
}

// モデル情報を更新
function updateModelInfo() {
    const modelSelect = document.getElementById('modelSelect');
    const modelInfo = document.getElementById('modelInfo');
    
    if (!modelSelect || !modelInfo) return;
    
    const selectedModelId = modelSelect.value;
    const selectedModel = availableModels.find(m => m.id === selectedModelId);
    
    if (selectedModel) {
        modelInfo.innerHTML = `
            <div class="model-description">${escapeHtml(selectedModel.description || selectedModel.name)}</div>
            <div class="model-details">
                <div class="model-detail-item">
                    <div class="detail-label">最大トークン</div>
                    <div class="detail-value">${selectedModel.max_tokens || '4096'}</div>
                </div>
                <div class="model-detail-item">
                    <div class="detail-label">コスト/1K</div>
                    <div class="detail-value">$${selectedModel.cost_per_1k_tokens || '0.002'}</div>
                </div>
            </div>
        `;
    }
}

// テンプレートを表示
function displayTemplates(templatesToShow) {
    const grid = document.getElementById('templateGrid');
    
    if (templatesToShow.length === 0) {
        grid.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📝</div>
                <h3>テンプレートがありません</h3>
                <p>新しいプロンプトテンプレートを作成して始めましょう</p>
                <button class="btn-primary" onclick="openCreateModal()">➕ 最初のテンプレートを作成</button>
            </div>
        `;
        return;
    }

    grid.innerHTML = templatesToShow.map(template => createTemplateCard(template)).join('');
}

// テンプレートカードを作成
function createTemplateCard(template) {
    const variables = template.variables || [];
    const variablesHtml = variables.length > 0 
        ? `<div class="template-variables">
               <div class="variables-list">
                   ${variables.map(v => `<span class="variable-tag">{${v.name}}</span>`).join('')}
               </div>
           </div>`
        : '';

    const createdDate = new Date(template.created_at).toLocaleDateString('ja-JP');

    return `
        <div class="template-card" data-category="${template.category}">
            <div class="template-card-header">
                <div class="template-info">
                    <h3>${escapeHtml(template.name)}</h3>
                    <span class="template-category">${escapeHtml(template.category)}</span>
                </div>
            </div>
            
            ${template.description ? `<div class="template-description">${escapeHtml(template.description)}</div>` : ''}
            
            ${variablesHtml}
            
            <div class="template-actions">
                <div class="template-meta">
                    作成日: ${createdDate}
                </div>
                <div class="template-buttons">
                    <button class="btn-use" onclick="openUseModal('${template.id}')" title="テンプレートを使用">
                        ▶️ 使用
                    </button>
                    <button class="btn-edit" onclick="editTemplate('${template.id}')" title="編集">
                        ✏️
                    </button>
                    <button class="btn-delete" onclick="deleteTemplate('${template.id}')" title="削除">
                        🗑️
                    </button>
                </div>
            </div>
        </div>
    `;
}

// カテゴリタブを更新
function updateCategoryTabs() {
    const categories = [...new Set(templates.map(t => t.category))];
    const tabsContainer = document.getElementById('categoryTabs');
    
    // 現在のアクティブタブを保持
    const currentActive = tabsContainer.querySelector('.filter-tab.active')?.dataset.category || 'all';
    
    tabsContainer.innerHTML = `
        <button class="filter-tab ${currentActive === 'all' ? 'active' : ''}" data-category="all">すべて</button>
        ${categories.map(cat => 
            `<button class="filter-tab ${currentActive === cat ? 'active' : ''}" data-category="${cat}">${cat}</button>`
        ).join('')}
    `;
    
    // イベントリスナーを再設定
    tabsContainer.querySelectorAll('.filter-tab').forEach(tab => {
        tab.addEventListener('click', function() {
            document.querySelectorAll('.filter-tab').forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            filterTemplates();
        });
    });
}

// テンプレートをフィルタリング
function filterTemplates() {
    const activeCategory = document.querySelector('.filter-tab.active').dataset.category;
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    
    let filtered = templates;
    
    // カテゴリフィルター
    if (activeCategory !== 'all') {
        filtered = filtered.filter(t => t.category === activeCategory);
    }
    
    // 検索フィルター
    if (searchTerm) {
        filtered = filtered.filter(t => 
            t.name.toLowerCase().includes(searchTerm) ||
            (t.description && t.description.toLowerCase().includes(searchTerm)) ||
            t.category.toLowerCase().includes(searchTerm)
        );
    }
    
    displayTemplates(filtered);
}

// 作成モーダルを開く
function openCreateModal() {
    editingTemplateId = null;
    document.getElementById('modalTitle').textContent = '新しいテンプレートを作成';
    document.getElementById('submitBtn').textContent = '作成';
    
    // フォームをリセット
    document.getElementById('templateForm').reset();
    document.getElementById('variablesContainer').innerHTML = `
        <button type="button" class="add-variable-btn" onclick="addVariableField()">
            ➕ 変数を追加
        </button>
    `;
    
    document.getElementById('templateModal').classList.add('active');
    document.getElementById('templateName').focus();
}

// 編集モーダルを開く
function editTemplate(templateId) {
    const template = templates.find(t => t.id === templateId);
    if (!template) return;
    
    editingTemplateId = templateId;
    document.getElementById('modalTitle').textContent = 'テンプレートを編集';
    document.getElementById('submitBtn').textContent = '更新';
    
    // フォームに既存データを設定
    document.getElementById('templateName').value = template.name;
    document.getElementById('templateDescription').value = template.description || '';
    document.getElementById('templateCategory').value = template.category;
    document.getElementById('systemPrompt').value = template.system_prompt;
    document.getElementById('exampleInput').value = template.example_input || '';
    document.getElementById('exampleOutput').value = template.example_output || '';
    
    // 変数フィールドを設定
    const variablesContainer = document.getElementById('variablesContainer');
    variablesContainer.innerHTML = '';
    
    if (template.variables && template.variables.length > 0) {
        template.variables.forEach(variable => {
            addVariableField(variable);
        });
    }
    
    variablesContainer.innerHTML += `
        <button type="button" class="add-variable-btn" onclick="addVariableField()">
            ➕ 変数を追加
        </button>
    `;
    
    document.getElementById('templateModal').classList.add('active');
}

// 使用モーダルを開く
function openUseModal(templateId) {
    const template = templates.find(t => t.id === templateId);
    if (!template) return;
    
    currentTemplate = template;
    
    // テンプレート情報を表示
    document.getElementById('useModalTitle').textContent = `${template.name} を使用`;
    document.getElementById('templatePreview').innerHTML = `
        <h3>${escapeHtml(template.name)}</h3>
        <p>${escapeHtml(template.description || '')}</p>
        <div class="system-prompt">${escapeHtml(template.system_prompt)}</div>
    `;
    
    // 変数入力フィールドを生成
    const variableInputs = document.getElementById('variableInputs');
    if (template.variables && template.variables.length > 0) {
        variableInputs.innerHTML = template.variables.map(variable => `
            <div class="form-group">
                <label for="var_${variable.name}">
                    ${escapeHtml(variable.description || variable.name)} 
                    ${variable.required ? '*' : ''}
                </label>
                ${variable.type === 'select' && variable.options ? 
                    `<select id="var_${variable.name}" ${variable.required ? 'required' : ''}>
                        <option value="">選択してください</option>
                        ${variable.options.map(option => 
                            `<option value="${escapeHtml(option)}" ${option === variable.default ? 'selected' : ''}>
                                ${escapeHtml(option)}
                            </option>`
                        ).join('')}
                    </select>` :
                    `<input type="text" 
                           id="var_${variable.name}" 
                           placeholder="${escapeHtml(variable.description || variable.name)}"
                           ${variable.required ? 'required' : ''}
                           ${variable.default ? `value="${escapeHtml(variable.default)}"` : ''}>`
                }
            </div>
        `).join('');
    } else {
        variableInputs.innerHTML = '';
    }
    
    // 例文を設定
    if (template.example_input) {
        document.getElementById('userMessage').value = template.example_input;
    } else {
        document.getElementById('userMessage').value = '';
    }
    
    // モデル選択を初期化
    updateModelSelects();
    
    document.getElementById('useModal').classList.add('active');
    document.getElementById('userMessage').focus();
}

// 変数フィールドを追加
function addVariableField(existingVariable = null) {
    const container = document.getElementById('variablesContainer');
    const addButton = container.querySelector('.add-variable-btn');
    
    const fieldId = `var_${Date.now()}`;
    const fieldHtml = `
        <div class="variable-field">
            <div>
                <label>変数名</label>
                <input type="text" 
                       placeholder="variable_name" 
                       value="${existingVariable ? escapeHtml(existingVariable.name) : ''}"
                       onchange="updateVariableField(this)">
            </div>
            <div>
                <label>説明</label>
                <input type="text" 
                       placeholder="変数の説明" 
                       value="${existingVariable ? escapeHtml(existingVariable.description || '') : ''}"
                       onchange="updateVariableField(this)">
            </div>
            <button type="button" class="remove-variable-btn" onclick="removeVariableField(this)">
                🗑️
            </button>
        </div>
    `;
    
    addButton.insertAdjacentHTML('beforebegin', fieldHtml);
}

// 変数フィールドを削除
function removeVariableField(button) {
    button.closest('.variable-field').remove();
}

// フォーム送信処理
async function handleFormSubmit(e) {
    e.preventDefault();
    
    const formData = {
        name: document.getElementById('templateName').value,
        description: document.getElementById('templateDescription').value || null,
        category: document.getElementById('templateCategory').value,
        system_prompt: document.getElementById('systemPrompt').value,
        example_input: document.getElementById('exampleInput').value || null,
        example_output: document.getElementById('exampleOutput').value || null,
        variables: collectVariables()
    };
    
    try {
        let response;
        if (editingTemplateId) {
            response = await fetch(`${API_BASE_URL}/api/templates/${editingTemplateId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });
        } else {
            response = await fetch(`${API_BASE_URL}/api/templates`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });
        }
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const result = await response.json();
        console.log('テンプレート保存成功:', result);
        
        closeModal();
        await loadTemplates();
        
        showSuccessMessage(editingTemplateId ? 'テンプレートを更新しました' : 'テンプレートを作成しました');
        
    } catch (error) {
        console.error('テンプレート保存エラー:', error);
        showErrorMessage('テンプレートの保存に失敗しました');
    }
}

// 変数データを収集
function collectVariables() {
    const fields = document.querySelectorAll('.variable-field');
    const variables = [];
    
    fields.forEach(field => {
        const inputs = field.querySelectorAll('input');
        if (inputs.length >= 2 && inputs[0].value.trim()) {
            variables.push({
                name: inputs[0].value.trim(),
                description: inputs[1].value.trim() || null,
                type: 'string',
                required: true
            });
        }
    });
    
    return variables;
}

// テンプレート使用処理
async function handleUseTemplate(e) {
    e.preventDefault();
    
    if (!currentTemplate) return;
    
    const variables = {};
    if (currentTemplate.variables) {
        currentTemplate.variables.forEach(variable => {
            const input = document.getElementById(`var_${variable.name}`);
            if (input) {
                variables[variable.name] = input.value;
            }
        });
    }
    
    const selectedModel = document.getElementById('modelSelect').value || 'gpt-3.5-turbo';
    
    const requestData = {
        template_id: currentTemplate.id,
        variables: variables,
        user_message: document.getElementById('userMessage').value,
        model: selectedModel
    };
    
    try {
        // ローディング状態を表示
        const submitBtn = document.querySelector('#useForm button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.innerHTML = '⏳ 実行中...';
        submitBtn.disabled = true;
        
        const response = await fetch(`${API_BASE_URL}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData)
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP ${response.status}`);
        }
        
        const result = await response.json();
        
        closeUseModal();
        showResult(result);
        
    } catch (error) {
        console.error('テンプレート使用エラー:', error);
        showErrorMessage(`AI処理エラー: ${error.message}`);
    } finally {
        const submitBtn = document.querySelector('#useForm button[type="submit"]');
        if (submitBtn) {
            submitBtn.textContent = originalText;
            submitBtn.disabled = false;
        }
    }
}

// 結果を表示
function showResult(result) {
    document.getElementById('resultContent').innerHTML = `
        <div class="result-meta">
            <div class="result-meta-item">
                <div class="label">モデル</div>
                <div class="value">${result.model}</div>
            </div>
            <div class="result-meta-item">
                <div class="label">トークン使用量</div>
                <div class="value">${result.tokens_used}</div>
            </div>
            <div class="result-meta-item">
                <div class="label">処理時間</div>
                <div class="value">${result.processing_time_ms}ms</div>
            </div>
            <div class="result-meta-item">
                <div class="label">テンプレート</div>
                <div class="value">${result.metadata.template_name}</div>
            </div>
        </div>
        
        <div class="result-text" id="resultText">${escapeHtml(result.content)}</div>
    `;
    
    document.getElementById('resultModal').classList.add('active');
}

// テンプレート削除
async function deleteTemplate(templateId) {
    const template = templates.find(t => t.id === templateId);
    if (!template) return;
    
    if (!confirm(`「${template.name}」を削除しますか？この操作は元に戻せません。`)) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/templates/${templateId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        await loadTemplates();
        showSuccessMessage('テンプレートを削除しました');
        
    } catch (error) {
        console.error('テンプレート削除エラー:', error);
        showErrorMessage('テンプレートの削除に失敗しました');
    }
}

// モーダルを閉じる
function closeModal(event) {
    if (event && event.target !== event.currentTarget) return;
    document.getElementById('templateModal').classList.remove('active');
}

function closeUseModal(event) {
    if (event && event.target !== event.currentTarget) return;
    document.getElementById('useModal').classList.remove('active');
}

function closeResultModal(event) {
    if (event && event.target !== event.currentTarget) return;
    document.getElementById('resultModal').classList.remove('active');
}

// クリップボードにコピー
function copyToClipboard() {
    const resultText = document.getElementById('resultText');
    if (resultText) {
        navigator.clipboard.writeText(resultText.textContent).then(() => {
            showSuccessMessage('結果をクリップボードにコピーしました');
        }).catch(() => {
            showErrorMessage('コピーに失敗しました');
        });
    }
}

// ユーティリティ関数
function escapeHtml(text) {
    if (typeof text !== 'string') return text;
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showSuccessMessage(message) {
    showMessage(message, 'success');
}

function showErrorMessage(message) {
    showMessage(message, 'error');
}

function showMessage(message, type) {
    // 簡易的なメッセージ表示（必要に応じてトーストライブラリに置き換え）
    const alertClass = type === 'success' ? 'success' : 'error';
    const alertColor = type === 'success' ? '#10B981' : '#EF4444';
    
    const alertDiv = document.createElement('div');
    alertDiv.innerHTML = `
        <div style="
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${alertColor};
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 10000;
            animation: slideInRight 0.3s ease;
        ">
            ${escapeHtml(message)}
        </div>
    `;
    
    document.body.appendChild(alertDiv);
    
    setTimeout(() => {
        alertDiv.remove();
    }, 3000);
    
    // アニメーションCSS（動的追加）
    if (!document.querySelector('#alert-animation-styles')) {
        const style = document.createElement('style');
        style.id = 'alert-animation-styles';
        style.textContent = `
            @keyframes slideInRight {
                from {
                    opacity: 0;
                    transform: translateX(100%);
                }
                to {
                    opacity: 1;
                    transform: translateX(0);
                }
            }
        `;
        document.head.appendChild(style);
    }
}