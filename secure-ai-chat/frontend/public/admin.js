// 管理画面用JavaScript
const API_BASE_URL = 'http://localhost:8000';

// グローバル変数
let templates = [];
let editingTemplateId = null;
let variableCounter = 0;

// 初期化
document.addEventListener('DOMContentLoaded', async () => {
    await checkApiConnection();
    await loadTemplates();
    updateStats();
    setupEventListeners();
});

// API接続確認
async function checkApiConnection() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        if (response.ok) {
            const statusDot = document.querySelector('.status-dot');
            const statusText = document.querySelector('.status-indicator span');
            if (statusDot && statusText) {
                statusDot.style.backgroundColor = '#10B981';
                statusText.textContent = 'API接続済み';
            }
            return true;
        }
    } catch (error) {
        console.error('API接続エラー:', error);
        const statusDot = document.querySelector('.status-dot');
        const statusText = document.querySelector('.status-indicator span');
        if (statusDot && statusText) {
            statusDot.style.backgroundColor = '#EF4444';
            statusText.textContent = 'API未接続';
        }
        return false;
    }
}

// テンプレート読み込み
async function loadTemplates() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/templates`);
        if (response.ok) {
            templates = await response.json();
            renderTemplatesList();
            console.log(`✅ ${templates.length}個のテンプレートを読み込み`);
        }
    } catch (error) {
        console.error('テンプレート読み込みエラー:', error);
        showError('テンプレートの読み込みに失敗しました');
    }
}

// テンプレート一覧の描画
function renderTemplatesList() {
    const grid = document.getElementById('templatesGrid');
    grid.innerHTML = templates.map(template => `
        <div class="template-card">
            <div class="template-card-header">
                <div>
                    <div class="template-title">${escapeHtml(template.name)}</div>
                    <div class="template-category">${escapeHtml(template.category)}</div>
                </div>
                <div class="template-status">
                    ${template.is_active ? '<span style="color: #10B981;">●</span>' : '<span style="color: #EF4444;">●</span>'}
                </div>
            </div>
            
            <div class="template-description">
                ${escapeHtml(template.description || '説明なし')}
            </div>
            
            <div class="template-stats">
                <span>変数: ${template.variables ? template.variables.length : 0}個</span>
                <span>更新: ${new Date(template.updated_at).toLocaleDateString('ja-JP')}</span>
            </div>
            
            <div class="template-actions">
                <button class="btn btn-outline btn-small" onclick="editTemplate('${template.id}')">
                    ✏️ 編集
                </button>
                <button class="btn btn-outline btn-small" onclick="duplicateTemplate('${template.id}')">
                    📋 複製
                </button>
                <button class="btn btn-outline btn-small" onclick="previewTemplate('${template.id}')">
                    👁️ プレビュー
                </button>
                <button class="btn btn-danger btn-small" onclick="deleteTemplate('${template.id}')">
                    🗑️ 削除
                </button>
            </div>
        </div>
    `).join('');
}

// 統計情報の更新
function updateStats() {
    const totalTemplates = templates.length;
    const activeTemplates = templates.filter(t => t.is_active).length;
    
    document.getElementById('totalTemplates').textContent = totalTemplates;
    document.getElementById('activeTemplates').textContent = activeTemplates;
    
    updateCategoriesStats();
}

// カテゴリ統計の更新
function updateCategoriesStats() {
    const categories = {};
    templates.forEach(template => {
        categories[template.category] = (categories[template.category] || 0) + 1;
    });
    
    const statsContainer = document.getElementById('categoriesStats');
    statsContainer.innerHTML = Object.entries(categories).map(([category, count]) => `
        <div class="category-stat-card">
            <h3>${escapeHtml(category)}</h3>
            <div class="count">${count}</div>
        </div>
    `).join('');
}

// セクション表示切り替え
function showSection(sectionName) {
    // 全てのセクションを非表示
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.remove('active');
    });
    
    // ナビゲーションのアクティブ状態をリセット
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // 指定されたセクションを表示
    document.getElementById(`${sectionName}-section`).classList.add('active');
    
    // ナビゲーションのアクティブ状態を更新
    document.querySelector(`[onclick="showSection('${sectionName}')"]`).classList.add('active');
    
    // 作成フォームの場合は新規作成モードに設定
    if (sectionName === 'create') {
        resetForm();
    }
}

// 変数追加
function addVariable() {
    const container = document.getElementById('variablesContainer');
    const variableId = `variable_${variableCounter++}`;
    
    const variableDiv = document.createElement('div');
    variableDiv.className = 'variable-item';
    variableDiv.innerHTML = `
        <div class="variable-header">
            <h4>変数 ${variableCounter}</h4>
            <button type="button" class="btn btn-danger btn-small" onclick="removeVariable(this)">削除</button>
        </div>
        <div class="variable-row">
            <div class="form-group">
                <label>変数名 *</label>
                <input type="text" class="variable-name" required placeholder="例: recipient">
            </div>
            <div class="form-group">
                <label>説明</label>
                <input type="text" class="variable-description" placeholder="例: メールの送信先">
            </div>
            <div class="form-group">
                <div class="checkbox-group">
                    <input type="checkbox" class="variable-required" id="${variableId}_required">
                    <label for="${variableId}_required">必須</label>
                </div>
            </div>
        </div>
        <div class="variable-row">
            <div class="form-group">
                <label>タイプ</label>
                <select class="variable-type">
                    <option value="string">テキスト</option>
                    <option value="select">選択肢</option>
                    <option value="textarea">長文テキスト</option>
                </select>
            </div>
            <div class="form-group">
                <label>デフォルト値</label>
                <input type="text" class="variable-default" placeholder="デフォルト値（任意）">
            </div>
            <div class="form-group">
                <label>選択肢（select時のみ）</label>
                <input type="text" class="variable-options" placeholder="選択肢1,選択肢2,選択肢3">
            </div>
        </div>
    `;
    
    container.appendChild(variableDiv);
}

// 変数削除
function removeVariable(button) {
    button.closest('.variable-item').remove();
}

// フォーム送信の設定
function setupEventListeners() {
    document.getElementById('templateForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        await saveTemplate();
    });
}

// テンプレート保存
async function saveTemplate() {
    const formData = collectFormData();
    
    if (!validateFormData(formData)) {
        return;
    }
    
    try {
        const isEditing = editingTemplateId !== null;
        const url = isEditing 
            ? `${API_BASE_URL}/api/v1/templates/${editingTemplateId}`
            : `${API_BASE_URL}/api/v1/templates`;
        const method = isEditing ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });
        
        if (response.ok) {
            showSuccess(isEditing ? 'テンプレートを更新しました' : 'テンプレートを作成しました');
            await loadTemplates();
            updateStats();
            showSection('templates');
            resetForm();
        } else {
            const error = await response.json();
            showError(`保存に失敗しました: ${error.detail || 'Unknown error'}`);
        }
    } catch (error) {
        console.error('保存エラー:', error);
        showError('保存中にエラーが発生しました');
    }
}

// フォームデータ収集
function collectFormData() {
    const variables = [];
    document.querySelectorAll('.variable-item').forEach(item => {
        const variable = {
            name: item.querySelector('.variable-name').value,
            description: item.querySelector('.variable-description').value,
            type: item.querySelector('.variable-type').value,
            required: item.querySelector('.variable-required').checked,
            default: item.querySelector('.variable-default').value || undefined
        };
        
        if (variable.type === 'select') {
            const options = item.querySelector('.variable-options').value;
            if (options) {
                variable.options = options.split(',').map(o => o.trim()).filter(o => o);
            }
        }
        
        variables.push(variable);
    });
    
    return {
        name: document.getElementById('templateName').value,
        description: document.getElementById('templateDescription').value,
        category: document.getElementById('templateCategory').value,
        system_prompt: document.getElementById('systemPrompt').value,
        variables: variables,
        example_input: document.getElementById('exampleInput').value || undefined,
        example_output: document.getElementById('exampleOutput').value || undefined
    };
}

// フォームバリデーション
function validateFormData(data) {
    if (!data.name.trim()) {
        showError('テンプレート名は必須です');
        return false;
    }
    
    if (!data.category) {
        showError('カテゴリを選択してください');
        return false;
    }
    
    if (!data.system_prompt.trim()) {
        showError('システムプロンプトは必須です');
        return false;
    }
    
    // 変数名の重複チェック
    const variableNames = data.variables.map(v => v.name);
    const duplicates = variableNames.filter((name, index) => variableNames.indexOf(name) !== index);
    if (duplicates.length > 0) {
        showError(`変数名が重複しています: ${duplicates.join(', ')}`);
        return false;
    }
    
    return true;
}

// テンプレート編集
async function editTemplate(templateId) {
    const template = templates.find(t => t.id === templateId);
    if (!template) return;
    
    editingTemplateId = templateId;
    
    // フォームに値を設定
    document.getElementById('templateId').value = template.id;
    document.getElementById('templateName').value = template.name;
    document.getElementById('templateDescription').value = template.description || '';
    document.getElementById('templateCategory').value = template.category;
    document.getElementById('systemPrompt').value = template.system_prompt;
    document.getElementById('exampleInput').value = template.example_input || '';
    document.getElementById('exampleOutput').value = template.example_output || '';
    
    // 変数を設定
    document.getElementById('variablesContainer').innerHTML = '';
    variableCounter = 0;
    
    if (template.variables && template.variables.length > 0) {
        template.variables.forEach(variable => {
            addVariable();
            const lastVariable = document.querySelector('.variable-item:last-child');
            lastVariable.querySelector('.variable-name').value = variable.name || '';
            lastVariable.querySelector('.variable-description').value = variable.description || '';
            lastVariable.querySelector('.variable-type').value = variable.type || 'string';
            lastVariable.querySelector('.variable-required').checked = variable.required || false;
            lastVariable.querySelector('.variable-default').value = variable.default || '';
            if (variable.options) {
                lastVariable.querySelector('.variable-options').value = variable.options.join(',');
            }
        });
    }
    
    // フォームタイトルを変更
    document.getElementById('formTitle').textContent = '✏️ テンプレート編集';
    document.getElementById('submitBtn').textContent = '💾 更新';
    
    // 編集画面に切り替え
    showSection('create');
}

// テンプレート複製
async function duplicateTemplate(templateId) {
    const template = templates.find(t => t.id === templateId);
    if (!template) return;
    
    // 編集モードをリセット
    editingTemplateId = null;
    
    // フォームに値を設定（名前に[複製]を追加）
    document.getElementById('templateId').value = '';
    document.getElementById('templateName').value = template.name + ' [複製]';
    document.getElementById('templateDescription').value = template.description || '';
    document.getElementById('templateCategory').value = template.category;
    document.getElementById('systemPrompt').value = template.system_prompt;
    document.getElementById('exampleInput').value = template.example_input || '';
    document.getElementById('exampleOutput').value = template.example_output || '';
    
    // 変数を設定
    document.getElementById('variablesContainer').innerHTML = '';
    variableCounter = 0;
    
    if (template.variables && template.variables.length > 0) {
        template.variables.forEach(variable => {
            addVariable();
            const lastVariable = document.querySelector('.variable-item:last-child');
            lastVariable.querySelector('.variable-name').value = variable.name || '';
            lastVariable.querySelector('.variable-description').value = variable.description || '';
            lastVariable.querySelector('.variable-type').value = variable.type || 'string';
            lastVariable.querySelector('.variable-required').checked = variable.required || false;
            lastVariable.querySelector('.variable-default').value = variable.default || '';
            if (variable.options) {
                lastVariable.querySelector('.variable-options').value = variable.options.join(',');
            }
        });
    }
    
    // フォームタイトルを変更
    document.getElementById('formTitle').textContent = '📋 テンプレート複製';
    document.getElementById('submitBtn').textContent = '💾 保存';
    
    // 作成画面に切り替え
    showSection('create');
}

// テンプレート削除
async function deleteTemplate(templateId) {
    const template = templates.find(t => t.id === templateId);
    if (!template) return;
    
    if (!confirm(`本当に「${template.name}」を削除しますか？`)) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/templates/${templateId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showSuccess('テンプレートを削除しました');
            await loadTemplates();
            updateStats();
        } else {
            showError('削除に失敗しました');
        }
    } catch (error) {
        console.error('削除エラー:', error);
        showError('削除中にエラーが発生しました');
    }
}

// プレビュー表示
function previewTemplate(templateId = null) {
    let template;
    
    if (templateId) {
        template = templates.find(t => t.id === templateId);
    } else {
        // フォームから現在の内容を取得
        template = collectFormData();
    }
    
    if (!template) return;
    
    const previewContent = document.getElementById('previewContent');
    previewContent.innerHTML = `
        <div style="margin-bottom: 2rem;">
            <h4 style="color: #1E293B; margin-bottom: 1rem;">📝 ${escapeHtml(template.name)}</h4>
            <div style="background: #F8FAFC; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
                <strong>カテゴリ:</strong> ${escapeHtml(template.category)}<br>
                <strong>説明:</strong> ${escapeHtml(template.description || '説明なし')}
            </div>
        </div>
        
        <div style="margin-bottom: 2rem;">
            <h5 style="color: #1E293B; margin-bottom: 1rem;">🤖 システムプロンプト</h5>
            <div style="background: #F1F5F9; padding: 1rem; border-radius: 8px; font-family: monospace; white-space: pre-wrap; max-height: 200px; overflow-y: auto;">
${escapeHtml(template.system_prompt)}</div>
        </div>
        
        ${template.variables && template.variables.length > 0 ? `
        <div style="margin-bottom: 2rem;">
            <h5 style="color: #1E293B; margin-bottom: 1rem;">📊 変数設定</h5>
            <div style="display: grid; gap: 1rem;">
                ${template.variables.map(variable => `
                    <div style="background: #F8FAFC; padding: 1rem; border-radius: 8px; border: 1px solid #E5E7EB;">
                        <div style="font-weight: 600; margin-bottom: 0.5rem;">
                            ${escapeHtml(variable.name)} ${variable.required ? '<span style="color: #EF4444;">*</span>' : ''}
                        </div>
                        <div style="font-size: 0.9rem; color: #6B7280; margin-bottom: 0.5rem;">
                            ${escapeHtml(variable.description || '説明なし')}
                        </div>
                        <div style="font-size: 0.8rem; color: #9CA3AF;">
                            タイプ: ${variable.type || 'string'} 
                            ${variable.default ? `| デフォルト: ${escapeHtml(variable.default)}` : ''}
                            ${variable.options ? `| 選択肢: ${variable.options.join(', ')}` : ''}
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
        ` : ''}
        
        ${template.example_input || template.example_output ? `
        <div>
            <h5 style="color: #1E293B; margin-bottom: 1rem;">📋 使用例</h5>
            ${template.example_input ? `
                <div style="margin-bottom: 1rem;">
                    <strong>入力例:</strong>
                    <div style="background: #F8FAFC; padding: 1rem; border-radius: 8px; margin-top: 0.5rem;">
                        ${escapeHtml(template.example_input)}
                    </div>
                </div>
            ` : ''}
            ${template.example_output ? `
                <div>
                    <strong>出力例:</strong>
                    <div style="background: #F8FAFC; padding: 1rem; border-radius: 8px; margin-top: 0.5rem;">
                        ${escapeHtml(template.example_output)}
                    </div>
                </div>
            ` : ''}
        </div>
        ` : ''}
    `;
    
    document.getElementById('previewModal').style.display = 'flex';
}

// プレビューを閉じる
function closePreview() {
    document.getElementById('previewModal').style.display = 'none';
}

// フォームリセット
function resetForm() {
    editingTemplateId = null;
    document.getElementById('templateForm').reset();
    document.getElementById('variablesContainer').innerHTML = '';
    variableCounter = 0;
    
    // フォームタイトルを変更
    document.getElementById('formTitle').textContent = '➕ 新規テンプレート作成';
    document.getElementById('submitBtn').textContent = '💾 保存';
}

// ユーティリティ関数
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showSuccess(message) {
    alert(`✅ ${message}`);
}

function showError(message) {
    alert(`❌ ${message}`);
}