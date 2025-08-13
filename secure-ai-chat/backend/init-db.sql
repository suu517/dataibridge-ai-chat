-- セキュアAIチャット - データベース初期化スクリプト

-- データベース設定の最適化
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET log_statement = 'all';
ALTER SYSTEM SET log_min_duration_statement = 1000;

-- 管理者ユーザーの作成（初期セットアップ用）
-- 注意: 本番環境では必ずパスワードを変更してください

-- デフォルトテンプレートカテゴリの作成
INSERT INTO template_categories (name, description, icon, color, sort_order, is_active) VALUES
('ビジネス', 'ビジネス関連のテンプレート', 'briefcase', '#3b82f6', 1, true),
('技術', '技術・開発関連のテンプレート', 'code', '#10b981', 2, true),
('マーケティング', 'マーケティング・営業関連のテンプレート', 'megaphone', '#f59e0b', 3, true),
('人事・HR', '人事・人材関連のテンプレート', 'users', '#8b5cf6', 4, true),
('その他', 'その他のテンプレート', 'folder', '#6b7280', 5, true)
ON CONFLICT (name) DO NOTHING;

-- 初期プロンプトテンプレートの作成
INSERT INTO prompt_templates (
    name, 
    description, 
    template_content, 
    category_id, 
    created_by, 
    access_level, 
    parameters, 
    default_model, 
    status, 
    version
) VALUES
(
    'メール作成アシスタント',
    'ビジネスメールの作成を支援するテンプレート',
    'encrypt_content_here', -- 実際の運用では暗号化された内容
    (SELECT id FROM template_categories WHERE name = 'ビジネス' LIMIT 1),
    1, -- 管理者ユーザーID
    'public',
    '[
        {
            "name": "recipient",
            "type": "text",
            "label": "宛先",
            "description": "メールの宛先を入力してください",
            "required": true
        },
        {
            "name": "subject",
            "type": "text", 
            "label": "件名",
            "description": "メールの件名を入力してください",
            "required": true
        },
        {
            "name": "content",
            "type": "textarea",
            "label": "本文の要点",
            "description": "メールで伝えたい要点を入力してください",
            "required": true
        },
        {
            "name": "tone",
            "type": "select",
            "label": "口調",
            "description": "メールの口調を選択してください",
            "required": false,
            "options": ["丁寧", "カジュアル", "フォーマル"],
            "defaultValue": "丁寧"
        }
    ]',
    'gpt-4',
    'active',
    '1.0'
),
(
    'コードレビュー',
    'プログラムコードのレビューを行うテンプレート',
    'encrypt_content_here', -- 実際の運用では暗号化された内容
    (SELECT id FROM template_categories WHERE name = '技術' LIMIT 1),
    1, -- 管理者ユーザーID
    'public',
    '[
        {
            "name": "code",
            "type": "textarea",
            "label": "コード",
            "description": "レビューするコードを貼り付けてください",
            "required": true
        },
        {
            "name": "language",
            "type": "select",
            "label": "プログラミング言語",
            "description": "コードの言語を選択してください",
            "required": true,
            "options": ["Python", "JavaScript", "Java", "C++", "Go", "Rust", "その他"]
        },
        {
            "name": "focus",
            "type": "select",
            "label": "レビューの焦点",
            "description": "重点的にレビューしたい観点を選択してください",
            "required": false,
            "options": ["セキュリティ", "パフォーマンス", "可読性", "保守性", "総合"],
            "defaultValue": "総合"
        }
    ]',
    'gpt-4',
    'active',
    '1.0'
)
ON CONFLICT (name) DO NOTHING;

-- インデックスの作成（パフォーマンス向上）
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_status ON users(status);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_created_at ON users(created_at);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_chats_user_id ON chats(user_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_chats_status ON chats(status);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_chats_created_at ON chats(created_at);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_chats_updated_at ON chats(updated_at);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_chat_messages_chat_id ON chat_messages(chat_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_chat_messages_type ON chat_messages(message_type);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_chat_messages_created_at ON chat_messages(created_at);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_prompt_templates_category_id ON prompt_templates(category_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_prompt_templates_created_by ON prompt_templates(created_by);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_prompt_templates_status ON prompt_templates(status);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_prompt_templates_access_level ON prompt_templates(access_level);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_level ON audit_logs(level);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_resource_type ON audit_logs(resource_type);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_sessions_session_id ON user_sessions(session_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_sessions_expires_at ON user_sessions(expires_at);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_sessions_created_at ON user_sessions(created_at);

-- 統計情報の更新
ANALYZE;