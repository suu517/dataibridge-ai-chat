// 料金シミュレーター JavaScript

// 料金計算の設定
const PRICING_CONFIG = {
    // 基本料金（月額）
    baseFee: 10000,
    
    // ユーザー単価（月額）
    userFeePerUser: 500,
    
    // AIモデル別単価（1000メッセージあたり）
    modelPricing: {
        'gpt-3.5': 100,
        'gpt-4o-mini': 200,
        'gpt-4o': 800,
        'gpt-4': 1200
    },
    
    // サポートレベル別料金（月額）
    supportPricing: {
        'basic': 0,
        'standard': 5000,
        'premium': 15000
    },
    
    // 時給（業務効率化計算用）
    hourlyRate: 4000
};

// 料金計算を更新
function updatePricing() {
    const userCount = parseInt(document.getElementById('userCount').value);
    const messagesPerUser = parseInt(document.getElementById('messagesPerUser').value);
    const modelType = document.getElementById('modelType').value;
    const supportLevel = document.getElementById('supportLevel').value;
    
    // UI更新
    document.getElementById('userCountValue').textContent = `${userCount}人`;
    document.getElementById('messagesValue').textContent = `${messagesPerUser}件`;
    
    // 料金計算
    const baseFee = PRICING_CONFIG.baseFee;
    const userFee = userCount * PRICING_CONFIG.userFeePerUser;
    const totalMessages = userCount * messagesPerUser;
    const aiFee = Math.ceil(totalMessages / 1000) * PRICING_CONFIG.modelPricing[modelType];
    const supportFee = PRICING_CONFIG.supportPricing[supportLevel];
    const totalPrice = baseFee + userFee + aiFee + supportFee;
    
    // ROI計算
    const timeSavingPerUser = messagesPerUser * 0.25; // 1メッセージあたり15分節約
    const totalTimeSaving = userCount * timeSavingPerUser;
    const costSaving = totalTimeSaving * PRICING_CONFIG.hourlyRate;
    const roiRatio = Math.round(((costSaving - totalPrice) / totalPrice) * 100);
    
    // UI更新
    document.getElementById('baseFee').textContent = `¥${baseFee.toLocaleString()}`;
    document.getElementById('userFee').textContent = `¥${userFee.toLocaleString()}`;
    document.getElementById('aiFee').textContent = `¥${aiFee.toLocaleString()}`;
    document.getElementById('supportFee').textContent = `¥${supportFee.toLocaleString()}`;
    document.getElementById('totalPrice').textContent = `¥${totalPrice.toLocaleString()}`;
    
    document.getElementById('timeSaving').textContent = `${Math.round(totalTimeSaving)}時間/月`;
    document.getElementById('costSaving').textContent = `¥${costSaving.toLocaleString()}`;
    document.getElementById('roiRatio').textContent = `${roiRatio}%`;
}

// プラン選択
function selectPlan(planType) {
    const planMessages = {
        'starter': 'スタータープランを選択しました。14日間の無料トライアルから始めることができます。',
        'business': 'ビジネスプランを選択しました。営業担当からご連絡いたします。',
        'enterprise': 'エンタープライズプランへのお問い合わせありがとうございます。専任担当がご連絡いたします。'
    };
    
    alert(planMessages[planType]);
    
    // 実際の実装では、ここでプラン選択APIを呼び出すか、お問い合わせフォームにリダイレクト
    if (planType === 'starter') {
        // トライアル登録処理
        console.log('トライアル登録処理を開始');
    } else {
        // お問い合わせ処理
        console.log(`${planType}プランのお問い合わせ処理を開始`);
    }
}

// ファイルドラッグ&ドロップ処理
function handleDragOver(event) {
    event.preventDefault();
    event.currentTarget.classList.add('drag-over');
}

function handleFileDrop(event) {
    event.preventDefault();
    event.currentTarget.classList.remove('drag-over');
    
    const files = event.dataTransfer.files;
    if (files.length > 0) {
        processFile(files[0]);
    }
}

function handleFileSelect(event) {
    const files = event.target.files;
    if (files.length > 0) {
        processFile(files[0]);
    }
}

// ファイル処理
function processFile(file) {
    const filePreview = document.getElementById('filePreview');
    const fileInfo = document.getElementById('fileInfo');
    const fileAnalysis = document.getElementById('fileAnalysis');
    
    // ファイル情報表示
    fileInfo.innerHTML = `
        <div style="display: flex; align-items: center; gap: 1rem;">
            <div style="font-size: 2rem;">${getFileIcon(file.type)}</div>
            <div>
                <div style="font-weight: 600; color: var(--text-primary);">${file.name}</div>
                <div style="color: var(--text-secondary); font-size: 0.875rem;">
                    ${(file.size / 1024 / 1024).toFixed(2)} MB • ${file.type || '不明なファイル'}
                </div>
            </div>
        </div>
    `;
    
    // デモ用の解析結果を表示
    fileAnalysis.innerHTML = `
        <div style="margin-bottom: 1rem;">
            <h5 style="font-weight: 600; color: var(--text-primary); margin-bottom: 0.5rem;">🤖 AI解析結果：</h5>
            <div style="color: var(--text-secondary);">
                ファイルを解析しています... 
                <span style="display: inline-block; animation: spin 1s linear infinite;">⚙️</span>
            </div>
        </div>
    `;
    
    filePreview.style.display = 'block';
    
    // 2秒後にデモ解析結果を表示
    setTimeout(() => {
        const analysisResult = generateDemoAnalysis(file);
        fileAnalysis.innerHTML = `
            <div style="margin-bottom: 1rem;">
                <h5 style="font-weight: 600; color: var(--text-primary); margin-bottom: 0.5rem;">🤖 AI解析結果：</h5>
                <div style="background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 8px; padding: 1rem;">
                    ${analysisResult}
                </div>
            </div>
            <div style="margin-top: 1rem;">
                <button style="background: var(--primary-color); color: white; border: none; padding: 0.5rem 1rem; border-radius: 6px; cursor: pointer;" 
                        onclick="askQuestion('${file.name}')">
                    💬 このファイルについて質問する
                </button>
            </div>
        `;
    }, 2000);
}

// ファイルタイプアイコン
function getFileIcon(fileType) {
    if (fileType.includes('excel') || fileType.includes('spreadsheet')) {
        return '📊';
    } else if (fileType.includes('image')) {
        return '🖼️';
    } else if (fileType.includes('pdf')) {
        return '📋';
    } else if (fileType.includes('csv')) {
        return '📈';
    } else {
        return '📁';
    }
}

// デモ解析結果生成
function generateDemoAnalysis(file) {
    const fileName = file.name.toLowerCase();
    
    if (fileName.includes('excel') || fileName.includes('.xlsx') || fileName.includes('.xls')) {
        return `
            <strong>📊 Excel ファイル解析:</strong><br>
            • ワークシート数: 3枚<br>
            • データ行数: 約1,250行<br>
            • 主な内容: 売上データ、顧客リスト、月次レポート<br>
            • 検出されたパターン: 2023年1月-12月の月次売上推移<br>
            • 推奨アクション: グラフ化、トレンド分析、異常値検出
        `;
    } else if (fileName.includes('image') || fileName.includes('.png') || fileName.includes('.jpg')) {
        return `
            <strong>🖼️ 画像解析:</strong><br>
            • 画像タイプ: ビジネス資料（グラフ・チャート）<br>
            • 検出されたテキスト: 売上推移、四半期業績<br>
            • データポイント: 12個のデータ点を検出<br>
            • 推奨アクション: データ抽出、テキスト化、分析レポート作成
        `;
    } else if (fileName.includes('pdf')) {
        return `
            <strong>📋 PDF文書解析:</strong><br>
            • ページ数: 15ページ<br>
            • 主な内容: ビジネスプラン、戦略資料<br>
            • 検出されたセクション: 目標設定、市場分析、財務計画<br>
            • 推奨アクション: 要約作成、キーポイント抽出、Q&A生成
        `;
    } else {
        return `
            <strong>📁 ファイル解析:</strong><br>
            • ファイル形式: ${file.type || '不明'}<br>
            • ファイルサイズ: ${(file.size / 1024 / 1024).toFixed(2)} MB<br>
            • 処理可能: テキスト抽出、構造解析<br>
            • 推奨アクション: 内容確認、データ変換、分析準備
        `;
    }
}

// ファイルについて質問
function askQuestion(fileName) {
    const question = prompt(`"${fileName}" について質問してください:`);
    if (question) {
        // デモ用の回答生成
        const demoAnswer = generateDemoAnswer(fileName, question);
        alert(`🤖 AI回答:\n\n${demoAnswer}`);
    }
}

// デモ回答生成
function generateDemoAnswer(fileName, question) {
    const questionLower = question.toLowerCase();
    
    if (questionLower.includes('売上') || questionLower.includes('データ')) {
        return `${fileName}の売上データを分析しました。\n\n主要な洞察:\n• 第3四半期に最高売上を記録\n• 前年同期比15%増\n• 主力商品カテゴリが全体の65%を占める\n\n詳細な分析レポートが必要でしたらお声かけください。`;
    } else if (questionLower.includes('グラフ') || questionLower.includes('チャート')) {
        return `${fileName}のグラフを解析しました。\n\n視覚化されたデータ:\n• 時系列トレンド: 右肩上がりの成長\n• 季節性: 12月に売上ピーク\n• 異常値: 8月に一時的な落ち込み\n\n改善提案も含めたレポートをご希望でしたらお申し付けください。`;
    } else {
        return `${fileName}について分析いたします。\n\n${question}に関して:\n• ファイル内容を精査し関連情報を抽出\n• データパターンを分析\n• 改善点や次のアクションを提案\n\nより具体的な質問があればお聞かせください。`;
    }
}

// DOMロード時の初期化
document.addEventListener('DOMContentLoaded', function() {
    // 初期計算実行
    updatePricing();
    
    // CSS アニメーション用のKeyframes追加
    if (!document.querySelector('#spinKeyframes')) {
        const style = document.createElement('style');
        style.id = 'spinKeyframes';
        style.textContent = `
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        `;
        document.head.appendChild(style);
    }
});