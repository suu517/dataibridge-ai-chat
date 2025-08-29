// セキュリティページ JavaScript

document.addEventListener('DOMContentLoaded', function() {
    initializeFAQ();
    initializeAnimations();
});

// FAQ機能の初期化
function initializeFAQ() {
    const faqItems = document.querySelectorAll('.faq-item');
    
    faqItems.forEach(item => {
        const question = item.querySelector('.faq-question');
        const answer = item.querySelector('.faq-answer');
        
        question.addEventListener('click', () => {
            const isActive = item.classList.contains('active');
            
            // 他のFAQを閉じる
            faqItems.forEach(otherItem => {
                if (otherItem !== item) {
                    otherItem.classList.remove('active');
                }
            });
            
            // 現在のFAQをトグル
            item.classList.toggle('active', !isActive);
        });
    });
}

// アニメーション効果の初期化
function initializeAnimations() {
    // Intersection Observer で要素が表示されたときにアニメーション
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.animationDelay = '0s';
                entry.target.classList.add('animate-in');
            }
        });
    }, observerOptions);
    
    // アニメーション対象要素を監視
    const animateElements = document.querySelectorAll('.stat-item, .feature-card, .compliance-card, .certificate-item');
    animateElements.forEach(el => {
        observer.observe(el);
    });
}

// セキュリティ証明書の詳細表示
function showCertificateDetails(certType) {
    const details = {
        ssl: {
            title: 'SSL/TLS証明書',
            content: `
                <h4>🔐 SSL/TLS証明書の詳細</h4>
                <ul>
                    <li><strong>発行者:</strong> Let's Encrypt Authority X3</li>
                    <li><strong>暗号化方式:</strong> TLS 1.3, AES-256</li>
                    <li><strong>有効期限:</strong> 自動更新（90日サイクル）</li>
                    <li><strong>対象ドメイン:</strong> *.dataibridge.com</li>
                    <li><strong>検証レベル:</strong> Domain Validated (DV)</li>
                </ul>
                <p>全ての通信が暗号化され、中間者攻撃やデータ盗聴から保護されています。</p>
            `
        },
        vulnerability: {
            title: '脆弱性スキャン',
            content: `
                <h4>🔍 脆弱性スキャンの詳細</h4>
                <ul>
                    <li><strong>スキャンツール:</strong> Trivy, OWASP ZAP</li>
                    <li><strong>実行頻度:</strong> 日次自動実行</li>
                    <li><strong>検査項目:</strong> CVE脆弱性、SQLインジェクション、XSS</li>
                    <li><strong>最新レポート:</strong> クリティカル 0件、高 0件</li>
                    <li><strong>修正時間:</strong> 検出から24時間以内</li>
                </ul>
                <p>最新の脅威情報を元に、継続的なセキュリティ監視を実施しています。</p>
            `
        },
        ddos: {
            title: 'DDoS攻撃対策',
            content: `
                <h4>🛡️ DDoS攻撃対策の詳細</h4>
                <ul>
                    <li><strong>保護レベル:</strong> L3/L4/L7 全階層対応</li>
                    <li><strong>対応容量:</strong> 100Gbps以上の攻撃に対応</li>
                    <li><strong>検知時間:</strong> 攻撃開始から数秒以内</li>
                    <li><strong>地理的分散:</strong> グローバルCDNによる負荷分散</li>
                    <li><strong>自動対応:</strong> リアルタイムでの攻撃トラフィック遮断</li>
                </ul>
                <p>Cloudflareの世界最大級のネットワークによる高度な保護を提供しています。</p>
            `
        },
        backup: {
            title: 'データバックアップ',
            content: `
                <h4>💾 データバックアップの詳細</h4>
                <ul>
                    <li><strong>バックアップ頻度:</strong> 日次自動実行</li>
                    <li><strong>保存期間:</strong> 30日間（ポイントインタイム復旧）</li>
                    <li><strong>地理的冗長:</strong> 複数リージョンでの分散保存</li>
                    <li><strong>暗号化:</strong> AES-256による暗号化保存</li>
                    <li><strong>復旧時間:</strong> 15分以内（RTO目標）</li>
                </ul>
                <p>災害やシステム障害に備えて、確実なデータ保護を実施しています。</p>
            `
        }
    };
    
    const detail = details[certType];
    if (detail) {
        showModal(detail.title, detail.content);
    }
}

// モーダル表示
function showModal(title, content) {
    // モーダルが既に存在する場合は削除
    const existingModal = document.getElementById('securityModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // モーダルを作成
    const modal = document.createElement('div');
    modal.id = 'securityModal';
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal-content" onclick="event.stopPropagation()">
            <div class="modal-header">
                <h2>${title}</h2>
                <button class="modal-close" onclick="closeSecurityModal()">×</button>
            </div>
            <div class="modal-body">
                ${content}
            </div>
            <div class="modal-footer">
                <button class="btn-primary" onclick="closeSecurityModal()">閉じる</button>
            </div>
        </div>
    `;
    
    // モーダルスタイルを追加
    if (!document.querySelector('#modalStyles')) {
        const style = document.createElement('style');
        style.id = 'modalStyles';
        style.textContent = `
            .modal-overlay {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background-color: rgba(0, 0, 0, 0.5);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 1000;
                animation: fadeIn 0.3s ease;
            }
            
            .modal-content {
                background: white;
                border-radius: 12px;
                max-width: 600px;
                width: 90%;
                max-height: 80vh;
                overflow-y: auto;
                box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
                animation: slideIn 0.3s ease;
            }
            
            .modal-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 1.5rem;
                border-bottom: 1px solid var(--border-color);
            }
            
            .modal-header h2 {
                margin: 0;
                font-size: 1.25rem;
                font-weight: 600;
            }
            
            .modal-close {
                background: none;
                border: none;
                font-size: 1.5rem;
                cursor: pointer;
                color: var(--text-secondary);
                width: 32px;
                height: 32px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 4px;
                transition: var(--transition);
            }
            
            .modal-close:hover {
                background-color: var(--background-color);
            }
            
            .modal-body {
                padding: 1.5rem;
            }
            
            .modal-body h4 {
                margin-bottom: 1rem;
                color: var(--text-primary);
            }
            
            .modal-body ul {
                margin-bottom: 1rem;
                padding-left: 1rem;
            }
            
            .modal-body li {
                margin-bottom: 0.5rem;
                line-height: 1.5;
            }
            
            .modal-footer {
                padding: 1rem 1.5rem;
                border-top: 1px solid var(--border-color);
                text-align: right;
            }
            
            .btn-primary {
                background: var(--primary-color);
                color: white;
                border: none;
                padding: 0.75rem 1.5rem;
                border-radius: 8px;
                cursor: pointer;
                font-weight: 500;
                transition: var(--transition);
            }
            
            .btn-primary:hover {
                background: var(--primary-dark);
            }
            
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            
            @keyframes slideIn {
                from {
                    opacity: 0;
                    transform: translateY(-20px) scale(0.95);
                }
                to {
                    opacity: 1;
                    transform: translateY(0) scale(1);
                }
            }
        `;
        document.head.appendChild(style);
    }
    
    // モーダルを表示
    document.body.appendChild(modal);
    
    // モーダル外クリックで閉じる
    modal.addEventListener('click', closeSecurityModal);
}

// モーダルを閉じる
function closeSecurityModal() {
    const modal = document.getElementById('securityModal');
    if (modal) {
        modal.style.animation = 'fadeOut 0.3s ease forwards';
        setTimeout(() => {
            modal.remove();
        }, 300);
    }
}

// セキュリティ診断を開始
function startSecurityAssessment() {
    const questions = [
        {
            question: "現在のセキュリティ対策について",
            options: ["基本的な対策のみ", "標準的な対策を実施", "高度な対策を実施", "わからない"]
        },
        {
            question: "取り扱うデータの機密度",
            options: ["一般的な業務データ", "個人情報を含む", "機密性の高いデータ", "規制対象データ"]
        },
        {
            question: "コンプライアンス要件",
            options: ["特になし", "業界標準への準拠", "GDPR等への対応", "複数の規制への対応"]
        }
    ];
    
    // 簡易診断用のモーダルを表示
    const assessmentContent = `
        <div style="text-align: center; padding: 2rem;">
            <h3>🔒 セキュリティ診断</h3>
            <p>お客様の要件に最適なセキュリティレベルを診断いたします</p>
            <div style="margin: 2rem 0;">
                <button class="btn-primary" onclick="closeSecurityModal(); alert('セキュリティ診断フォームへリダイレクトします');">
                    診断を開始
                </button>
            </div>
            <p style="font-size: 0.875rem; color: var(--text-secondary);">
                所要時間: 約5分
            </p>
        </div>
    `;
    
    showModal('セキュリティ診断', assessmentContent);
}

// スムーズスクロール
function scrollToSection(sectionId) {
    const section = document.getElementById(sectionId);
    if (section) {
        section.scrollIntoView({ 
            behavior: 'smooth',
            block: 'start'
        });
    }
}

// 統計カウンターアニメーション
function animateCounters() {
    const statNumbers = document.querySelectorAll('.stat-number');
    
    statNumbers.forEach(stat => {
        const target = stat.textContent;
        const isPercentage = target.includes('%');
        const numericTarget = parseFloat(target.replace(/[^\d.]/g, ''));
        
        if (!isNaN(numericTarget)) {
            animateCounter(stat, 0, numericTarget, 2000, isPercentage);
        }
    });
}

function animateCounter(element, start, end, duration, isPercentage) {
    const startTime = performance.now();
    
    function updateCounter(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        const current = start + (end - start) * easeOutCubic(progress);
        
        if (isPercentage) {
            element.textContent = `${current.toFixed(1)}%`;
        } else {
            element.textContent = Math.round(current).toString();
        }
        
        if (progress < 1) {
            requestAnimationFrame(updateCounter);
        }
    }
    
    requestAnimationFrame(updateCounter);
}

function easeOutCubic(t) {
    return 1 - Math.pow(1 - t, 3);
}

// 証明書クリックハンドラーを追加
document.addEventListener('DOMContentLoaded', function() {
    // 証明書アイテムにクリックイベントを追加
    const certificateItems = document.querySelectorAll('.certificate-item');
    certificateItems.forEach((item, index) => {
        const certTypes = ['ssl', 'vulnerability', 'ddos', 'backup'];
        item.style.cursor = 'pointer';
        item.addEventListener('click', () => {
            showCertificateDetails(certTypes[index]);
        });
    });
    
    // カウンターアニメーションを開始（ページロード時）
    setTimeout(animateCounters, 500);
});