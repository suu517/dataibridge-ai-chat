// ダッシュボード JavaScript

// グローバル変数
let usageChart, modelChart, detailedUsageChart;
let currentTab = 'overview';
let currentDateRange = 'month';

// 初期化
document.addEventListener('DOMContentLoaded', function() {
    initializeCharts();
    updateDashboard();
    startRealTimeUpdates();
});

// タブ切り替え
function switchTab(tabName) {
    // アクティブなタブとナビを更新
    document.querySelectorAll('.tab-panel').forEach(panel => {
        panel.classList.remove('active');
    });
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    
    document.getElementById(`${tabName}-tab`).classList.add('active');
    document.querySelector(`[onclick="switchTab('${tabName}')"]`).closest('.nav-item').classList.add('active');
    
    currentTab = tabName;
    
    // タブ別のタイトル更新
    const titles = {
        overview: { title: '📊 ダッシュボード概要', subtitle: 'リアルタイム使用状況とパフォーマンス分析' },
        usage: { title: '📈 使用量分析', subtitle: 'API使用量・コスト追跡・予算管理' },
        teams: { title: '👥 チーム管理', subtitle: 'チーム別パフォーマンス・ユーザー権限管理' },
        history: { title: '🔍 履歴・検索', subtitle: 'チャット履歴検索・ナレッジベース管理' },
        admin: { title: '⚙️ 管理者設定', subtitle: '監査ログ・システム設定・セキュリティ管理' }
    };
    
    const titleInfo = titles[tabName];
    document.getElementById('pageTitle').textContent = titleInfo.title;
    document.getElementById('pageSubtitle').textContent = titleInfo.subtitle;
    
    // タブ固有の処理
    if (tabName === 'usage') {
        updateUsageAnalytics();
    } else if (tabName === 'history') {
        loadChatHistory();
    }
}

// ダッシュボード更新
function updateDashboard() {
    const dateRange = document.getElementById('dateRange').value;
    currentDateRange = dateRange;
    
    // KPI更新
    updateKPIs();
    
    // チャート更新
    updateCharts();
    
    // 最終更新時刻を表示
    const now = new Date();
    console.log(`Dashboard updated at: ${now.toLocaleTimeString()}`);
}

// KPI更新
function updateKPIs() {
    const kpiData = generateKPIData(currentDateRange);
    
    document.getElementById('totalMessages').textContent = kpiData.totalMessages.toLocaleString();
    document.getElementById('activeUsers').textContent = kpiData.activeUsers.toString();
    document.getElementById('monthlyCost').textContent = `¥${kpiData.monthlyCost.toLocaleString()}`;
    document.getElementById('avgResponse').textContent = `${kpiData.avgResponse}秒`;
    
    // 変化率のアニメーション
    animateKPIChanges();
}

// KPIデータ生成（デモ用）
function generateKPIData(dateRange) {
    const baseData = {
        today: { totalMessages: 420, activeUsers: 28, monthlyCost: 1500, avgResponse: 0.8 },
        week: { totalMessages: 2840, activeUsers: 89, monthlyCost: 8500, avgResponse: 1.1 },
        month: { totalMessages: 12847, activeUsers: 156, monthlyCost: 45230, avgResponse: 1.2 },
        quarter: { totalMessages: 38520, activeUsers: 203, monthlyCost: 128700, avgResponse: 1.0 }
    };
    
    return baseData[dateRange] || baseData.month;
}

// チャート初期化
function initializeCharts() {
    // 使用量トレンドチャート
    const usageCtx = document.getElementById('usageChart').getContext('2d');
    usageChart = new Chart(usageCtx, {
        type: 'line',
        data: {
            labels: generateDateLabels(),
            datasets: [{
                label: 'メッセージ数',
                data: generateUsageData(),
                borderColor: '#2563EB',
                backgroundColor: 'rgba(37, 99, 235, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
    
    // モデル使用率チャート
    const modelCtx = document.getElementById('modelChart').getContext('2d');
    modelChart = new Chart(modelCtx, {
        type: 'doughnut',
        data: {
            labels: ['GPT-4o', 'GPT-4', 'GPT-3.5 Turbo', 'GPT-4o Mini'],
            datasets: [{
                data: [45, 25, 20, 10],
                backgroundColor: ['#2563EB', '#7C3AED', '#059669', '#F59E0B'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { padding: 20 }
                }
            }
        }
    });
    
    // 詳細使用量チャート
    const detailedCtx = document.getElementById('detailedUsageChart').getContext('2d');
    detailedUsageChart = new Chart(detailedCtx, {
        type: 'bar',
        data: {
            labels: generateDateLabels(),
            datasets: [
                {
                    label: '営業部',
                    data: generateTeamUsageData('sales'),
                    backgroundColor: '#2563EB'
                },
                {
                    label: '開発部',
                    data: generateTeamUsageData('dev'),
                    backgroundColor: '#7C3AED'
                },
                {
                    label: 'マーケティング部',
                    data: generateTeamUsageData('marketing'),
                    backgroundColor: '#059669'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { stacked: true },
                y: { stacked: true, beginAtZero: true }
            }
        }
    });
}

// チャート更新
function updateCharts() {
    if (usageChart) {
        usageChart.data.labels = generateDateLabels();
        usageChart.data.datasets[0].data = generateUsageData();
        usageChart.update();
    }
    
    if (detailedUsageChart) {
        detailedUsageChart.data.labels = generateDateLabels();
        detailedUsageChart.data.datasets[0].data = generateTeamUsageData('sales');
        detailedUsageChart.data.datasets[1].data = generateTeamUsageData('dev');
        detailedUsageChart.data.datasets[2].data = generateTeamUsageData('marketing');
        detailedUsageChart.update();
    }
}

// チャート切り替え
function changeChart(chartType) {
    // ボタンのアクティブ状態を更新
    document.querySelectorAll('.chart-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // チャートデータを更新
    let newData;
    switch (chartType) {
        case 'messages':
            newData = generateUsageData();
            usageChart.data.datasets[0].label = 'メッセージ数';
            break;
        case 'users':
            newData = generateUserData();
            usageChart.data.datasets[0].label = 'アクティブユーザー数';
            break;
        case 'cost':
            newData = generateCostData();
            usageChart.data.datasets[0].label = '日次コスト (円)';
            break;
    }
    
    usageChart.data.datasets[0].data = newData;
    usageChart.update('active');
}

// データ生成関数（デモ用）
function generateDateLabels() {
    const labels = [];
    for (let i = 29; i >= 0; i--) {
        const date = new Date();
        date.setDate(date.getDate() - i);
        labels.push(date.toLocaleDateString('ja-JP', { month: 'short', day: 'numeric' }));
    }
    return labels;
}

function generateUsageData() {
    return Array.from({length: 30}, () => Math.floor(Math.random() * 200) + 100);
}

function generateUserData() {
    return Array.from({length: 30}, () => Math.floor(Math.random() * 50) + 20);
}

function generateCostData() {
    return Array.from({length: 30}, () => Math.floor(Math.random() * 3000) + 1000);
}

function generateTeamUsageData(team) {
    const multiplier = team === 'sales' ? 1.2 : team === 'dev' ? 1.5 : 0.8;
    return Array.from({length: 30}, () => Math.floor(Math.random() * 100 * multiplier) + 50);
}

// 使用量分析更新
function updateUsageAnalytics() {
    // コストアラートの更新
    const costAlert = document.getElementById('costAlert');
    const budgetUsage = Math.random() * 30 + 70; // 70-100%
    
    if (budgetUsage > 90) {
        costAlert.innerHTML = `<span class="alert-icon">🚨</span> 予算の${budgetUsage.toFixed(0)}%に到達 - 緊急対応が必要`;
        costAlert.style.background = 'rgba(239, 68, 68, 0.1)';
        costAlert.style.color = '#EF4444';
    } else if (budgetUsage > 80) {
        costAlert.innerHTML = `<span class="alert-icon">⚠️</span> 予算の${budgetUsage.toFixed(0)}%に到達しています`;
        costAlert.style.background = 'rgba(245, 158, 11, 0.1)';
        costAlert.style.color = '#F59E0B';
    } else {
        costAlert.innerHTML = `<span class="alert-icon">✅</span> 予算内で正常に運用中 (${budgetUsage.toFixed(0)}%)`;
        costAlert.style.background = 'rgba(16, 185, 129, 0.1)';
        costAlert.style.color = '#10B981';
    }
    
    // プログレスバーの更新
    document.querySelector('.progress-fill').style.width = `${budgetUsage}%`;
}

// チーム管理関数
function openTeamModal() {
    alert('チーム追加モーダルを開きます（デモ機能）');
}

function viewTeamDetails(teamId) {
    alert(`${teamId}チームの詳細を表示します（デモ機能）`);
}

function editTeam(teamId) {
    alert(`${teamId}チームを編集します（デモ機能）`);
}

function editUser(userId) {
    alert(`${userId}ユーザーを編集します（デモ機能）`);
}

// チャット履歴関数
function loadChatHistory() {
    console.log('チャット履歴を読み込みました');
}

function searchChatHistory() {
    const searchTerm = document.getElementById('historySearch').value;
    console.log(`検索: ${searchTerm}`);
    // 実際の実装では、ここで検索APIを呼び出し
}

function filterChatHistory() {
    const filter = document.getElementById('searchFilter').value;
    console.log(`フィルター: ${filter}`);
    // 実際の実装では、ここでフィルター処理を実行
}

function selectCategory(category) {
    // カテゴリアイテムのアクティブ状態を更新
    document.querySelectorAll('.category-item').forEach(item => {
        item.classList.remove('active');
    });
    event.target.closest('.category-item').classList.add('active');
    
    console.log(`カテゴリ選択: ${category}`);
    // 実際の実装では、ここでカテゴリ別の履歴を読み込み
}

function viewFullChat(chatId) {
    alert(`${chatId}の詳細チャットを表示します（デモ機能）`);
}

function exportChat(chatId) {
    alert(`${chatId}をエクスポートします（デモ機能）`);
}

function addToKnowledge(chatId) {
    alert(`${chatId}をナレッジベースに追加しました（デモ機能）`);
}

// 管理者機能
function exportAuditLog() {
    alert('監査ログをエクスポートします（デモ機能）');
}

function saveSettings() {
    alert('設定を保存しました（デモ機能）');
}

function exportROIReport() {
    alert('ROIレポートをエクスポートします（デモ機能）');
}

// リアルタイム更新
function startRealTimeUpdates() {
    // 30秒ごとにKPIを更新
    setInterval(() => {
        updateKPIs();
    }, 30000);
    
    // 5分ごとにチャートを更新
    setInterval(() => {
        updateCharts();
    }, 300000);
}

// KPI変化のアニメーション
function animateKPIChanges() {
    const kpiValues = document.querySelectorAll('.kpi-value');
    kpiValues.forEach(value => {
        value.style.transform = 'scale(1.05)';
        setTimeout(() => {
            value.style.transform = 'scale(1)';
        }, 200);
    });
}

// 数値カウンターアニメーション
function animateCounter(element, start, end, duration) {
    const startTime = performance.now();
    
    function updateCounter(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        const current = start + (end - start) * easeOutCubic(progress);
        element.textContent = Math.round(current).toLocaleString();
        
        if (progress < 1) {
            requestAnimationFrame(updateCounter);
        }
    }
    
    requestAnimationFrame(updateCounter);
}

function easeOutCubic(t) {
    return 1 - Math.pow(1 - t, 3);
}

// 検索とフィルタリング
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// デバウンス検索
const debouncedSearch = debounce(searchChatHistory, 300);

// イベントリスナーの追加
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('historySearch');
    if (searchInput) {
        searchInput.addEventListener('input', debouncedSearch);
    }
});

// ユーティリティ関数
function formatCurrency(amount) {
    return new Intl.NumberFormat('ja-JP', {
        style: 'currency',
        currency: 'JPY'
    }).format(amount);
}

function formatPercentage(value) {
    return new Intl.NumberFormat('ja-JP', {
        style: 'percent',
        minimumFractionDigits: 1,
        maximumFractionDigits: 1
    }).format(value / 100);
}

function formatDate(date) {
    return new Intl.DateTimeFormat('ja-JP', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    }).format(date);
}

// エラーハンドリング
window.addEventListener('error', function(e) {
    console.error('Dashboard error:', e.error);
    // 実際の実装では、エラーレポートサービスに送信
});

// パフォーマンス監視
function measurePerformance(name, fn) {
    const start = performance.now();
    const result = fn();
    const end = performance.now();
    console.log(`${name} took ${end - start} milliseconds`);
    return result;
}