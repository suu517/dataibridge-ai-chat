// セキュアAIチャット - チャット機能JavaScript (モデル選択対応版)

let messageId = 2;
let isLoading = false;
const API_BASE_URL = 'http://localhost:8000';
let availableTemplates = [];
let selectedTemplate = null;
let availableModels = [];

// メッセージを送信する関数
async function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    
    if (!message || isLoading) return;
    
    // ユーザーメッセージを追加
    addMessage(message, 'user');
    input.value = '';
    autoResize(input);
    
    // クイックプロンプトを非表示
    hideQuickPrompts();
    
    // ローディング状態を設定
    setLoading(true);
    showTypingIndicator();
    
    try {
        // 実際のAPI呼び出し
        await callRealAI(message);
    } catch (error) {
        console.error('API Error:', error);
        // API接続エラーの場合のみエラーメッセージを表示
        addMessage(
            `⚠️ API接続エラーが発生しました。\n\nエラー詳細: ${error.message}\n\n🔧 解決方法：\n• APIサーバー（http://localhost:8000）が起動しているか確認\n• OpenAI APIの課金設定を確認\n• ネットワーク接続を確認`,
            'ai',
            true
        );
    } finally {
        setLoading(false);
        hideTypingIndicator();
    }
}

// 実際のAI API呼び出し
async function callRealAI(userMessage) {
    try {
        // 選択されたモデルを取得
        const chatModelSelect = document.getElementById('chatModelSelect');
        const selectedModel = chatModelSelect ? chatModelSelect.value : 'gpt-3.5-turbo';
        
        console.log(`🚀 API呼び出し開始: ${API_BASE_URL}/api/chat`);
        console.log(`📝 メッセージ: "${userMessage}"`);
        console.log(`🤖 モデル: ${selectedModel}`);
        
        const response = await fetch(`${API_BASE_URL}/api/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: userMessage,  // demo_api.pyの形式に合わせて修正
                model: selectedModel
            })
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            
            if (response.status === 429) {
                addMessage('⚠️ APIレート制限に達しています。OpenAI APIの課金設定を確認してください。', 'ai', true);
                return;
            }
            
            throw new Error(`API Error: ${response.status} - ${errorData.message || 'Unknown error'}`);
        }

        const data = await response.json();
        
        if (data.content) {
            // 実際のAI応答を表示
            addMessage(data.content, 'ai', false, {
                model: data.model || 'gpt-3.5-turbo',
                tokens: data.tokens_used || 0,
                processingTime: data.processing_time_ms || 0
            });
            
            // コンソールにAPI使用状況を表示
            console.log(`✅ OpenAI API Success:`, {
                model: data.model,
                tokens: data.tokens_used,
                processingTime: `${data.processing_time_ms}ms`,
                finishReason: data.finish_reason
            });
        } else {
            throw new Error('Invalid response format');
        }
        
    } catch (error) {
        console.error('Real AI API Error:', error);
        throw error; // エラーを上位に伝播してフォールバック処理へ
    }
}

// AIレスポンスをシミュレート
async function simulateAIResponse(userMessage) {
    // リアルなタイピング遅延
    const delay = 1500 + Math.random() * 2000;
    await new Promise(resolve => setTimeout(resolve, delay));
    
    // デモレスポンスを生成（API接続失敗時のフォールバック）
    const demoResponses = [
        `"${userMessage}"について回答させていただきます。✨\n\n⚠️ **OpenAI API接続エラー**\n現在、OpenAI APIのクォータ制限により実際のAI機能が利用できません。\n\n🔧 **解決方法：**\n• OpenAI APIアカウントの課金設定を有効にする\n• または、Azure OpenAI サービスを利用する\n\n💡 API接続が回復すると、GPT-3.5-turbo または GPT-4 による高品質な回答を提供できます。`,
        
        `興味深いご質問ですね！\n\n⚠️ **API制限モード**\n"${userMessage}"に関して、通常であればリアルタイムでAIが回答を生成しますが、現在はクォータ制限のためデモモードで動作中です。\n\n🚀 **正常時の機能：**\n• GPTによるリアルタイム回答生成\n• コンテキストを考慮した対話\n• 専門的な知識に基づく詳細解説\n\n💳 課金設定を行うことで、すぐに本格的なAI機能をご利用いただけます。`,
        
        `ご質問ありがとうございます！\n\n🔄 **API接続状態：制限中**\n"${userMessage}"について、通常はOpenAI GPTが詳細な回答を生成しますが、現在はクォータ制限のためフォールバックモードで動作しています。\n\n✅ **システム状態：**\n• バックエンドAPI: 正常動作\n• OpenAI認証: 成功\n• 利用可能モデル: 39個のGPTモデル\n• 制限原因: 無料クォータ消費済み\n\n💡 実際のAI機能を利用するには、OpenAIアカウントで課金設定を行ってください。`
    ];
    
    const response = demoResponses[Math.floor(Math.random() * demoResponses.length)];
    addMessage(response, 'ai', true);
}

// メッセージを追加
function addMessage(content, type, isDemo = false, apiInfo = null) {
    const container = document.getElementById('messagesContainer');
    const messageDiv = document.createElement('div');
    
    const currentTime = new Date().toLocaleTimeString('ja-JP', { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
    
    messageDiv.className = `message ${type}-message`;
    
    // モデル情報の表示を決定
    let modelTag = '';
    if (isDemo) {
        modelTag = '<span class="model-tag demo-tag">Demo</span>';
    } else if (apiInfo && type === 'ai') {
        if (apiInfo.templateName) {
            modelTag = `<span class="model-tag template-tag">📝 ${apiInfo.templateName}</span>`;
            modelTag += `<span class="model-tag ai-tag">${apiInfo.model}</span>`;
        } else {
            modelTag = `<span class="model-tag ai-tag">${apiInfo.model}</span>`;
        }
        if (apiInfo.tokens > 0) {
            modelTag += `<span class="token-info">${apiInfo.tokens} tokens</span>`;
        }
    }
    
    messageDiv.innerHTML = `
        <div class="message-content">
            <div class="avatar ${type}-avatar">
                <span>${type === 'user' ? '👤' : '🤖'}</span>
            </div>
            <div class="message-bubble ${type}-bubble ${isDemo ? 'demo-bubble' : (apiInfo ? 'ai-real-bubble' : '')}">
                <div class="message-text">${content}</div>
                <div class="message-meta">
                    <span class="time">${currentTime}</span>
                    ${modelTag}
                </div>
            </div>
        </div>
    `;
    
    container.appendChild(messageDiv);
    scrollToBottom();
    messageId++;
}

// タイピングインジケーターを表示
function showTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    indicator.style.display = 'block';
    scrollToBottom();
}

// タイピングインジケーターを非表示
function hideTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    indicator.style.display = 'none';
}

// クイックプロンプトを非表示
function hideQuickPrompts() {
    const prompts = document.getElementById('quickPrompts');
    if (prompts) {
        prompts.style.display = 'none';
    }
}

// ローディング状態を設定
function setLoading(loading) {
    isLoading = loading;
    const sendButton = document.getElementById('sendButton');
    const input = document.getElementById('messageInput');
    
    if (loading) {
        sendButton.innerHTML = `
            <div style="width: 16px; height: 16px; border: 2px solid rgba(255,255,255,0.3); border-top: 2px solid white; border-radius: 50%; animation: spin 1s linear infinite;"></div>
            <span>送信中...</span>
        `;
        sendButton.disabled = true;
        input.disabled = true;
    } else {
        sendButton.innerHTML = `
            <span class="send-text">送信</span>
            <svg class="send-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
        `;
        sendButton.disabled = false;
        input.disabled = false;
    }
}

// 最下部にスクロール
function scrollToBottom() {
    const main = document.querySelector('.chat-main');
    setTimeout(() => {
        main.scrollTop = main.scrollHeight;
    }, 100);
}

// テキストエリアの自動リサイズ
function autoResize(textarea) {
    textarea.style.height = 'auto';
    const newHeight = Math.min(textarea.scrollHeight, 120);
    textarea.style.height = newHeight + 'px';
}

// キーボードイベントハンドラ
function handleKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

// メッセージを設定（クイックプロンプト用）
function setMessage(message) {
    const input = document.getElementById('messageInput');
    input.value = message;
    autoResize(input);
    input.focus();
}

// チャットをクリア
function clearChat() {
    const container = document.getElementById('messagesContainer');
    container.innerHTML = `
        <div class="message ai-message">
            <div class="message-content">
                <div class="avatar ai-avatar">
                    <span>🤖</span>
                </div>
                <div class="message-bubble ai-bubble">
                    <div class="message-text">🔄 チャットをクリアしました！新しい会話を始めましょう。何かお手伝いできることはありますか？</div>
                    <div class="message-meta">
                        <span class="time">今すぐ</span>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // クイックプロンプトを再表示
    const prompts = document.getElementById('quickPrompts');
    if (prompts) {
        prompts.style.display = 'block';
    }
    
    messageId = 2;
    scrollToBottom();
}

// スピン アニメーション用CSS と AI応答スタイル
const style = document.createElement('style');
style.textContent = `
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .ai-real-bubble {
        border-left: 3px solid #10B981 !important;
        background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%) !important;
    }
    
    .demo-bubble {
        border-left: 3px solid #F59E0B !important;
        background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%) !important;
    }
    
    .ai-tag {
        background: #10B981 !important;
        color: white !important;
        padding: 2px 6px !important;
        border-radius: 4px !important;
        font-size: 10px !important;
        font-weight: bold !important;
        margin-left: 8px !important;
    }
    
    .demo-tag {
        background: #F59E0B !important;
        color: white !important;
        padding: 2px 6px !important;
        border-radius: 4px !important;
        font-size: 10px !important;
        font-weight: bold !important;
        margin-left: 8px !important;
    }
    
    .token-info {
        background: #6B7280 !important;
        color: white !important;
        padding: 1px 4px !important;
        border-radius: 3px !important;
        font-size: 9px !important;
        margin-left: 4px !important;
    }
`;
document.head.appendChild(style);

// APIサーバーの接続状態をチェック
async function checkApiConnection() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        if (response.ok) {
            const data = await response.json();
            console.log('✅ API Server Connected:', data);
            
            // ステータス表示を更新
            const statusDot = document.querySelector('.status-dot');
            const statusText = document.querySelector('.status-indicator span');
            if (statusDot && statusText) {
                statusDot.style.backgroundColor = '#10B981';
                statusText.textContent = 'AI接続済み';
            }
            
            // 利用可能なモデルをチェック
            try {
                const modelsResponse = await fetch(`${API_BASE_URL}/api/models`);
                if (modelsResponse.ok) {
                    const models = await modelsResponse.json();
                    console.log(`🤖 Available AI Models: ${models.length} models`);
                    
                    // 初期メッセージを更新
                    const initialMessage = document.querySelector('.message-text');
                    if (initialMessage) {
                        initialMessage.innerHTML = `🎉 <strong>セキュアAIチャット</strong>が正常に起動しました！<br><br>✅ <strong>OpenAI APIサーバー</strong>: 接続済み<br>✅ <strong>利用可能モデル</strong>: ${models.length}個のGPTモデル<br>✅ <strong>リアルタイムAI応答</strong>: 有効<br><br>何でもお気軽にお聞きください！🚀`;
                    }
                }
            } catch (modelError) {
                console.warn('⚠️ Model check failed:', modelError);
            }
            
            return true;
        }
    } catch (error) {
        console.error('❌ API Server Connection Failed:', error);
        
        // エラー状態を表示
        const statusDot = document.querySelector('.status-dot');
        const statusText = document.querySelector('.status-indicator span');
        if (statusDot && statusText) {
            statusDot.style.backgroundColor = '#EF4444';
            statusText.textContent = 'API未接続';
        }
        
        // 警告メッセージを表示
        const initialMessage = document.querySelector('.message-text');
        if (initialMessage) {
            initialMessage.innerHTML = `⚠️ <strong>API サーバー未接続</strong><br><br>❌ バックエンドAPI（http://localhost:8000）に接続できません<br><br>🔧 <strong>解決方法：</strong><br>1. ターミナルでAPIサーバーを起動<br>2. <code>python simple_api.py</code> を実行<br>3. ページを再読み込み<br><br>サーバー起動後、リアルタイムAIチャット機能をご利用いただけます。`;
        }
        
        return false;
    }
}

// アプリ初期化関数
async function initializeApp() {
    console.log('🚀 アプリ初期化開始');
    
    // API接続確認
    const apiConnected = await checkApiConnection();
    
    if (apiConnected) {
        // テンプレートとモデル読み込み
        await loadTemplates();
        // await loadChatModels(); // HTMLの固定3つモデルを使用
        console.log('✅ アプリ初期化完了');
    } else {
        console.warn('⚠️ API未接続のため一部機能が利用できません');
    }
}

// モデル管理機能

async function loadChatModels() {
    try {
        console.log(`📡 モデル読み込み中: ${API_BASE_URL}/api/models`);
        const response = await fetch(`${API_BASE_URL}/api/models`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        availableModels = await response.json();
        updateChatModelSelect();
        console.log(`✅ ${availableModels.length}個のモデルを読み込みました`);

    } catch (error) {
        console.error('❌ モデル読み込みエラー:', error);
        // エラーの場合はデフォルトモデル
        availableModels = [
            { id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo', description: 'OpenAI GPT-3.5 Turbo' }
        ];
        updateChatModelSelect();
    }
}

function updateChatModelSelect() {
    const chatModelSelect = document.getElementById('chatModelSelect');
    const chatModelInfo = document.getElementById('chatModelInfo');
    
    if (chatModelSelect) {
        chatModelSelect.innerHTML = availableModels.map(model => 
            `<option value="${model.id}">${model.name}</option>`
        ).join('');
        
        // デフォルト選択
        chatModelSelect.value = 'gpt-3.5-turbo';
        
        // イベントリスナー追加
        chatModelSelect.addEventListener('change', function() {
            updateChatModelInfo();
            // モデル変更を視覚的に確認できるメッセージを表示
            const selectedModel = this.options[this.selectedIndex].text;
            addMessage(`🔄 モデルを ${selectedModel} に切り替えました`, 'ai', false, {
                model: selectedModel,
                tokens: 0,
                processingTime: 0
            });
        });
        
        updateChatModelInfo();
    }
}

function updateChatModelInfo() {
    const chatModelSelect = document.getElementById('chatModelSelect');
    
    if (!chatModelSelect) return;
    
    const selectedModelId = chatModelSelect.value;
    const selectedModel = availableModels.find(m => m.id === selectedModelId);
    
    // コンソールに選択されたモデルを表示
    if (selectedModel) {
        console.log(`🔄 モデル切り替え: ${selectedModel.name} (${selectedModel.id})`);
    }
}

// テンプレート管理機能

async function loadTemplates() {
    try {
        console.log(`📡 テンプレート読み込み中: ${API_BASE_URL}/api/templates`);
        const response = await fetch(`${API_BASE_URL}/api/templates`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        });
        
        console.log(`📡 レスポンス状態: ${response.status} ${response.statusText}`);
        
        if (response.ok) {
            const responseText = await response.text();
            console.log(`📡 生レスポンス:`, responseText);
            
            const templates = JSON.parse(responseText);
            availableTemplates = templates;
            console.log(`✅ ${availableTemplates.length}個のテンプレートを読み込み完了`, availableTemplates);
            return true;
        } else {
            console.error(`❌ API エラー: ${response.status} ${response.statusText}`);
            const errorText = await response.text();
            console.error(`❌ エラー詳細:`, errorText);
            availableTemplates = [];
            return false;
        }
    } catch (error) {
        console.error('❌ テンプレート読み込みエラー:', error);
        console.error('❌ エラー詳細:', error.message);
        console.error('❌ スタックトレース:', error.stack);
        availableTemplates = [];
        return false;
    }
}

function toggleTemplateSelector() {
    const selector = document.getElementById('templateSelector');
    const toggleBtn = document.querySelector('.template-toggle-btn');
    
    if (selector.style.display === 'none' || !selector.style.display) {
        showTemplateSelector();
        toggleBtn.classList.add('active');
    } else {
        closeTemplateSelector();
        toggleBtn.classList.remove('active');
    }
}

function showTemplateSelector() {
    const selector = document.getElementById('templateSelector');
    const templateList = document.getElementById('templateList');
    
    // テンプレートが読み込まれているか確認
    if (!availableTemplates || availableTemplates.length === 0) {
        console.warn('⚠️ テンプレートが読み込まれていません。再読み込みします...');
        loadTemplates().then(() => {
            if (availableTemplates && availableTemplates.length > 0) {
                showTemplateSelector(); // 再帰的に呼び出し
            } else {
                templateList.innerHTML = `
                    <div style="padding: 20px; text-align: center; color: #6B7280;">
                        <p>📭 テンプレートが見つかりません</p>
                        <p style="font-size: 12px; margin-top: 8px;">APIサーバーが起動していることを確認してください</p>
                        <button onclick="loadTemplates().then(() => showTemplateSelector())" 
                                style="margin-top: 12px; padding: 6px 12px; background: #3B82F6; color: white; border: none; border-radius: 4px; cursor: pointer;">
                            🔄 再読み込み
                        </button>
                    </div>
                `;
                selector.style.display = 'block';
            }
        });
        return;
    }
    
    console.log(`📝 ${availableTemplates.length}個のテンプレートを表示`);
    
    // カテゴリ別にテンプレートを整理
    const categories = {};
    availableTemplates.forEach(template => {
        if (!categories[template.category]) {
            categories[template.category] = [];
        }
        categories[template.category].push(template);
    });
    
    // カテゴリごとにテンプレートリストを生成
    templateList.innerHTML = Object.keys(categories).map(category => `
        <div class="template-category-section">
            <h3 class="category-title">${escapeHtml(category)}</h3>
            <div class="category-templates">
                ${categories[category].map(template => `
                    <div class="template-item">
                        <div class="template-item-info">
                            <h4>${escapeHtml(template.name)}</h4>
                            <p>${escapeHtml(template.description || '')}</p>
                        </div>
                        <div class="template-item-action">
                            <button class="use-template-btn" onclick="selectTemplate('${template.id}')">使用</button>
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
    `).join('');
    
    selector.style.display = 'block';
}

function closeTemplateSelector() {
    document.getElementById('templateSelector').style.display = 'none';
    document.querySelector('.template-toggle-btn').classList.remove('active');
}

// テンプレート処理の状態管理
let templateChatMode = false;
let currentVariableIndex = 0;
let collectedVariables = {};

function selectTemplate(templateId) {
    const template = availableTemplates.find(t => t.id === templateId);
    if (!template) return;
    
    selectedTemplate = template;
    closeTemplateSelector();
    hideQuickPrompts();
    
    console.log(`📝 テンプレート選択: ${template.name}`);
    
    // チャット形式での変数収集を開始
    if (template.variables && template.variables.length > 0) {
        startTemplateChat(template);
    } else {
        // 変数がない場合は直接テンプレートモードに
        enableTemplateMode(template);
    }
}

function startTemplateChat(template) {
    templateChatMode = true;
    currentVariableIndex = 0;
    collectedVariables = {};
    
    // 入力欄を強制クリア
    forceClearInput('テンプレートチャット開始');
    
    // テンプレート開始メッセージを表示
    addMessage(
        `🎯 **${template.name}** を開始します！\n\n${template.description}\n\nいくつか質問させていただきますね。`,
        'ai'
    );
    
    console.log(`🚀 テンプレートチャット開始: ${template.name}`);
    
    // 最初の質問を開始
    setTimeout(() => askNextVariable(template), 1000);
}

function askNextVariable(template) {
    if (currentVariableIndex >= template.variables.length) {
        // すべての変数を収集完了
        finishTemplateChat(template);
        return;
    }
    
    const variable = template.variables[currentVariableIndex];
    let questionText = `**${variable.description || variable.name}** について教えてください。`;
    
    if (variable.required) {
        questionText += ` *(必須)*`;
    }
    
    if (variable.default) {
        questionText += `\n\n💡 参考例: ${variable.default}`;
    }
    
    // 選択肢がある場合は選択肢も表示（でもユーザーは自由入力可能）
    if (variable.type === 'select' && variable.options) {
        questionText += `\n\n💭 参考選択肢:\n${variable.options.map((option, index) => `• ${option}`).join('\n')}\n\n※ 上記以外でも自由にご入力いただけます`;
    }
    
    addMessage(questionText, 'ai');
    
    // 入力待ち状態に（少し遅延してフォーカス）
    setTimeout(() => {
        const messageInput = document.getElementById('messageInput');
        messageInput.placeholder = `${variable.description || variable.name}を入力してください...`;
        
        // 強制クリアを実行（複数回実行で確実に）
        forceClearInput(`質問${currentVariableIndex + 1}表示`);
        
        // 更に遅延してもう一度クリア
        setTimeout(() => {
            forceClearInput(`質問${currentVariableIndex + 1}再クリア`);
        }, 100);
        
        messageInput.focus();
        console.log(`📝 テンプレート質問: ${variable.description || variable.name} - 強制クリア完了`);
    }, 500);
}

function finishTemplateChat(template) {
    templateChatMode = false;
    
    // 収集した情報をまとめて表示
    let summary = `✅ **情報収集完了！**\n\n`;
    template.variables.forEach(variable => {
        const value = collectedVariables[variable.name] || '未入力';
        summary += `**${variable.description || variable.name}**: ${value}\n`;
    });
    
    summary += `\n🚀 これらの情報を使って**${template.name}**を実行します。\nメッセージを送信してください！`;
    
    addMessage(summary, 'ai');
    
    // テンプレートモードを有効化
    enableTemplateMode(template);
}

function enableTemplateMode(template) {
    const messageInput = document.getElementById('messageInput');
    messageInput.placeholder = `${template.name} モード有効中...メッセージを入力してください`;
    
    // テンプレート選択表示を更新
    const selectedDiv = document.getElementById('selectedTemplate');
    const templateName = document.getElementById('selectedTemplateName');
    const templateVariables = document.getElementById('templateVariables');
    
    templateName.textContent = template.name;
    
    // 収集した変数を表示（読み取り専用）
    if (Object.keys(collectedVariables).length > 0) {
        templateVariables.innerHTML = Object.entries(collectedVariables).map(([key, value]) => {
            const variable = template.variables.find(v => v.name === key);
            return `
                <div class="template-variable collected">
                    <label>${variable ? variable.description || variable.name : key}</label>
                    <div class="collected-value">${escapeHtml(value)}</div>
                </div>
            `;
        }).join('');
    } else {
        templateVariables.innerHTML = '<p class="no-variables">変数なしのテンプレートです</p>';
    }
    
    selectedDiv.style.display = 'block';
}

function handleTemplateChatResponse(message) {
    if (!templateChatMode || !selectedTemplate) return false;
    
    const variable = selectedTemplate.variables[currentVariableIndex];
    
    // ユーザーの回答を保存
    collectedVariables[variable.name] = message.trim();
    
    console.log(`📝 テンプレート回答記録: ${variable.name} = "${message.trim()}"`);
    
    // 確認メッセージを表示
    addMessage(
        `👍 **${variable.description || variable.name}**: "${message.trim()}" として記録しました！`,
        'ai'
    );
    
    // 入力欄を強制クリア（念のため）
    forceClearInput('テンプレート回答処理後');
    
    // 次の質問へ
    currentVariableIndex++;
    setTimeout(() => askNextVariable(selectedTemplate), 1000);
    
    return true; // この応答を処理したことを示す
}

function clearSelectedTemplate() {
    selectedTemplate = null;
    templateChatMode = false;
    currentVariableIndex = 0;
    collectedVariables = {};
    
    document.getElementById('selectedTemplate').style.display = 'none';
    document.getElementById('messageInput').placeholder = 'メッセージを入力... ✨';
    
    // 成功メッセージを表示
    addMessage('✅ テンプレートをクリアしました。通常のチャットモードに戻ります。', 'ai');
}

// メッセージ送信をテンプレート対応に修正
async function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    
    if (!message || isLoading) return;
    
    console.log(`📤 メッセージ送信開始:`, {
        message: message,
        templateChatMode: templateChatMode,
        selectedTemplate: selectedTemplate ? selectedTemplate.name : null
    });
    
    // 入力欄を強制クリア（すべてのモードで共通）
    forceClearInput('メッセージ送信開始');
    
    // ユーザーメッセージを表示
    addMessage(message, 'user');
    
    // テンプレートチャットモード中の場合
    if (templateChatMode) {
        handleTemplateChatResponse(message);
        return;
    }
    
    // テンプレートが選択されている場合
    if (selectedTemplate) {
        await sendTemplateMessage(message);
    } else {
        // 通常のメッセージ送信
        await sendNormalMessage(message);
    }
}

// 通常のメッセージ送信
async function sendNormalMessage(message) {
    // クイックプロンプトを非表示
    hideQuickPrompts();
    
    // ローディング状態を設定
    setLoading(true);
    showTypingIndicator();
    
    try {
        await callRealAI(message);
    } catch (error) {
        console.error('API Error:', error);
        addMessage(
            `⚠️ API接続エラーが発生しました。\\n\\nエラー詳細: ${error.message}\\n\\n🔧 解決方法：\\n• APIサーバー（http://localhost:8000）が起動しているか確認\\n• OpenAI APIの課金設定を確認\\n• ネットワーク接続を確認`,
            'ai',
            true
        );
    } finally {
        setLoading(false);
        hideTypingIndicator();
    }
}

// テンプレートメッセージ送信
async function sendTemplateMessage(message) {
    // チャット形式で収集した変数を使用
    const variables = collectedVariables;
    
    // この部分は上位のsendMessage関数で処理済みなので削除
    
    // クイックプロンプトを非表示
    hideQuickPrompts();
    
    // ローディング状態を設定
    setLoading(true);
    showTypingIndicator();
    
    try {
        const url = `${API_BASE_URL}/api/chat`;
        const payload = {
            variables: variables,
            user_message: message
        };
        
        console.log(`📡 テンプレートAPI呼び出し:`, { url, payload });
        
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        console.log(`📨 レスポンス受信:`, { 
            status: response.status, 
            statusText: response.statusText, 
            ok: response.ok 
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            console.error(`❌ APIエラー:`, { response: response, errorData });
            throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        
        // AI応答を表示
        addMessage(result.content, 'ai', false, {
            model: result.model,
            tokens: result.tokens_used,
            processingTime: result.processing_time_ms,
            templateName: selectedTemplate.name
        });
        
        console.log(`✅ Template AI Success:`, {
            template: selectedTemplate.name,
            model: result.model,
            tokens: result.tokens_used,
            processingTime: `${result.processing_time_ms}ms`
        });
        
    } catch (error) {
        console.error('Template AI Error:', error);
        addMessage(
            `⚠️ テンプレート処理エラーが発生しました。\\n\\nエラー詳細: ${error.message}\\n\\n🔧 解決方法：\\n• APIサーバーが正常に動作しているか確認\\n• OpenAI APIの設定を確認\\n• 必要な変数がすべて入力されているか確認`,
            'ai',
            true
        );
    } finally {
        setLoading(false);
        hideTypingIndicator();
        
        // テンプレート選択をクリア
        clearSelectedTemplate();
    }
}

// HTMLエスケープユーティリティ
function escapeHtml(text) {
    if (typeof text !== 'string') return text;
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 入力欄監視のデバッグ機能
function debugInputField(context = '') {
    const input = document.getElementById('messageInput');
    if (input) {
        console.log(`🔍 [${context}] 入力欄状態: "${input.value}" (長さ: ${input.value.length})`);
    }
}

// 強制的に入力欄をクリア
function forceClearInput(context = '') {
    const input = document.getElementById('messageInput');
    if (input) {
        const beforeValue = input.value;
        input.value = '';
        input.textContent = '';
        input.innerHTML = '';
        autoResize(input);
        
        console.log(`🧹 [${context}] 強制クリア実行: "${beforeValue}" → "${input.value}"`);
        
        // クリア後も値が残っている場合の追加処理
        setTimeout(() => {
            if (input.value !== '') {
                console.log(`⚠️ [${context}] クリア失敗検出、再試行中...`);
                input.value = '';
                autoResize(input);
            }
        }, 100);
    }
}

// 初期化
document.addEventListener('DOMContentLoaded', function() {
    const input = document.getElementById('messageInput');
    input.focus();
    
    // Enterキーでフォーカスが外れるのを防ぐ
    input.addEventListener('keydown', function(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            sendMessage();
            setTimeout(() => {
                forceClearInput('Enter送信後');
                input.focus();
            }, 100);
        }
    });
    
    // API接続状態をチェックしてからテンプレートを読み込み
    initializeApp();
});