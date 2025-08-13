/**
 * セキュアAIチャット - チャット統合インターフェース
 */

import React, { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  MessageSquare, 
  Template, 
  Settings,
  History,
  Plus,
  Search,
  Filter,
  Star,
  Clock,
  Users
} from 'lucide-react';
import { AIChat } from '@/components/ai/AIChat';
import { TemplateList } from '@/components/templates/TemplateList';
import { useTemplates } from '@/hooks/useTemplates';
import { PromptTemplate, User } from '@/types';

interface ChatInterfaceProps {
  currentUser?: User;
}

interface ChatSession {
  id: string;
  title: string;
  template?: PromptTemplate;
  messages: any[];
  createdAt: number;
  updatedAt: number;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({ currentUser }) => {
  const [activeTab, setActiveTab] = useState<'chat' | 'templates' | 'history'>('chat');
  const [currentSession, setCurrentSession] = useState<ChatSession | null>(null);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<PromptTemplate | null>(null);
  const [showTemplateModal, setShowTemplateModal] = useState(false);
  
  const { getPopularTemplates, getRecentTemplates } = useTemplates();

  // 新しいチャットセッション作成
  const createNewSession = useCallback((template?: PromptTemplate) => {
    const newSession: ChatSession = {
      id: `session-${Date.now()}`,
      title: template ? `${template.name} - チャット` : '新しいチャット',
      template,
      messages: [],
      createdAt: Date.now(),
      updatedAt: Date.now()
    };

    setSessions(prev => [newSession, ...prev]);
    setCurrentSession(newSession);
    setSelectedTemplate(template || null);
    setActiveTab('chat');
  }, []);

  // テンプレート選択処理
  const handleTemplateSelect = useCallback((template: PromptTemplate) => {
    if (activeTab === 'templates') {
      // テンプレート画面からの選択：新しいセッション作成
      createNewSession(template);
    } else {
      // 既存セッションにテンプレート適用
      setSelectedTemplate(template);
      setShowTemplateModal(false);
    }
  }, [activeTab, createNewSession]);

  // メッセージ送信時の処理
  const handleMessageSent = useCallback((message: any) => {
    if (currentSession) {
      const updatedSession = {
        ...currentSession,
        messages: [...currentSession.messages, message],
        updatedAt: Date.now()
      };
      setCurrentSession(updatedSession);
      setSessions(prev => 
        prev.map(session => 
          session.id === currentSession.id ? updatedSession : session
        )
      );
    }
  }, [currentSession]);

  // AI応答受信時の処理
  const handleResponseReceived = useCallback((message: any) => {
    if (currentSession) {
      const updatedSession = {
        ...currentSession,
        messages: [...currentSession.messages, message],
        updatedAt: Date.now()
      };
      setCurrentSession(updatedSession);
      setSessions(prev => 
        prev.map(session => 
          session.id === currentSession.id ? updatedSession : session
        )
      );
    }
  }, [currentSession]);

  // セッション選択
  const selectSession = useCallback((session: ChatSession) => {
    setCurrentSession(session);
    setSelectedTemplate(session.template || null);
    setActiveTab('chat');
  }, []);

  // システムプロンプトの生成
  const getSystemPrompt = useCallback(() => {
    if (!selectedTemplate) return undefined;
    
    let systemPrompt = selectedTemplate.system_message || '';
    
    // テンプレートの基本情報を追加
    if (selectedTemplate.description) {
      systemPrompt = `${selectedTemplate.description}\n\n${systemPrompt}`;
    }
    
    return systemPrompt.trim() || undefined;
  }, [selectedTemplate]);

  return (
    <div className="h-screen bg-gray-50 flex">
      {/* サイドバー */}
      <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
        {/* ヘッダー */}
        <div className="p-4 border-b border-gray-200">
          <h1 className="text-xl font-bold text-gray-900 mb-4">
            🔐 セキュア AI チャット
          </h1>
          
          {/* タブナビゲーション */}
          <div className="flex space-x-1">
            <button
              onClick={() => setActiveTab('chat')}
              className={`flex-1 flex items-center justify-center space-x-2 px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                activeTab === 'chat' 
                  ? 'bg-primary-100 text-primary-700' 
                  : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
              }`}
            >
              <MessageSquare className="w-4 h-4" />
              <span>チャット</span>
            </button>
            
            <button
              onClick={() => setActiveTab('templates')}
              className={`flex-1 flex items-center justify-center space-x-2 px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                activeTab === 'templates' 
                  ? 'bg-primary-100 text-primary-700' 
                  : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
              }`}
            >
              <Template className="w-4 h-4" />
              <span>テンプレート</span>
            </button>
            
            <button
              onClick={() => setActiveTab('history')}
              className={`flex-1 flex items-center justify-center space-x-2 px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                activeTab === 'history' 
                  ? 'bg-primary-100 text-primary-700' 
                  : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
              }`}
            >
              <History className="w-4 h-4" />
              <span>履歴</span>
            </button>
          </div>
        </div>

        {/* コンテンツエリア */}
        <div className="flex-1 overflow-y-auto">
          <AnimatePresence mode="wait">
            {/* チャットタブ */}
            {activeTab === 'chat' && (
              <motion.div
                key="chat"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                className="p-4 space-y-4"
              >
                {/* 新規チャットボタン */}
                <button
                  onClick={() => createNewSession()}
                  className="w-full flex items-center space-x-3 p-3 bg-primary-50 border-2 border-dashed border-primary-200 rounded-lg text-primary-700 hover:bg-primary-100 transition-colors"
                >
                  <Plus className="w-5 h-5" />
                  <span className="font-medium">新しいチャット</span>
                </button>

                {/* テンプレート選択ボタン */}
                <button
                  onClick={() => setShowTemplateModal(true)}
                  className="w-full flex items-center space-x-3 p-3 bg-gray-50 border border-gray-200 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors"
                >
                  <Template className="w-5 h-5" />
                  <span>テンプレートを選択</span>
                </button>

                {/* 現在のテンプレート */}
                {selectedTemplate && (
                  <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                    <div className="flex items-center space-x-2 mb-2">
                      <Template className="w-4 h-4 text-blue-600" />
                      <span className="text-sm font-medium text-blue-800">
                        使用中のテンプレート
                      </span>
                    </div>
                    <div className="text-sm text-blue-700">
                      {selectedTemplate.name}
                    </div>
                    {selectedTemplate.description && (
                      <div className="text-xs text-blue-600 mt-1">
                        {selectedTemplate.description}
                      </div>
                    )}
                  </div>
                )}

                {/* クイックアクセステンプレート */}
                <div className="space-y-3">
                  <h3 className="text-sm font-medium text-gray-700 flex items-center space-x-2">
                    <Star className="w-4 h-4" />
                    <span>人気のテンプレート</span>
                  </h3>
                  
                  {/* TODO: 人気テンプレートのリスト表示 */}
                  <div className="space-y-2">
                    <button className="w-full text-left p-2 text-sm text-gray-600 hover:bg-gray-50 rounded-md">
                      メール作成アシスタント
                    </button>
                    <button className="w-full text-left p-2 text-sm text-gray-600 hover:bg-gray-50 rounded-md">
                      コードレビュー
                    </button>
                  </div>
                </div>
              </motion.div>
            )}

            {/* テンプレートタブ */}
            {activeTab === 'templates' && (
              <motion.div
                key="templates"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                className="p-4"
              >
                <div className="space-y-3">
                  <h3 className="text-sm font-medium text-gray-700">
                    テンプレートを選択してチャットを開始
                  </h3>
                  
                  {/* 検索バー */}
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input
                      type="text"
                      placeholder="テンプレートを検索..."
                      className="w-full pl-10 pr-4 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    />
                  </div>

                  {/* カテゴリフィルタ */}
                  <div className="flex items-center space-x-2">
                    <Filter className="w-4 h-4 text-gray-400" />
                    <select className="flex-1 text-sm border border-gray-300 rounded-md px-2 py-1 focus:ring-2 focus:ring-primary-500 focus:border-primary-500">
                      <option>すべてのカテゴリ</option>
                      <option>ビジネス</option>
                      <option>技術</option>
                      <option>マーケティング</option>
                    </select>
                  </div>

                  {/* テンプレート一覧（簡易版） */}
                  <div className="space-y-2">
                    <div className="p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                      <div className="font-medium text-sm text-gray-900">メール作成アシスタント</div>
                      <div className="text-xs text-gray-500 mt-1">ビジネスメールの作成を支援</div>
                      <div className="flex items-center space-x-2 mt-2 text-xs text-gray-400">
                        <Users className="w-3 h-3" />
                        <span>パブリック</span>
                        <Clock className="w-3 h-3 ml-2" />
                        <span>12回使用</span>
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}

            {/* 履歴タブ */}
            {activeTab === 'history' && (
              <motion.div
                key="history"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                className="p-4"
              >
                <div className="space-y-3">
                  <h3 className="text-sm font-medium text-gray-700">チャット履歴</h3>
                  
                  {sessions.length === 0 ? (
                    <div className="text-center py-8 text-gray-500 text-sm">
                      まだチャット履歴がありません
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {sessions.map((session) => (
                        <button
                          key={session.id}
                          onClick={() => selectSession(session)}
                          className={`w-full text-left p-3 border rounded-lg hover:bg-gray-50 transition-colors ${
                            currentSession?.id === session.id 
                              ? 'border-primary-200 bg-primary-50' 
                              : 'border-gray-200'
                          }`}
                        >
                          <div className="font-medium text-sm text-gray-900 truncate">
                            {session.title}
                          </div>
                          <div className="text-xs text-gray-500 mt-1">
                            {session.messages.length} メッセージ
                          </div>
                          <div className="text-xs text-gray-400 mt-1">
                            {new Date(session.updatedAt).toLocaleString('ja-JP')}
                          </div>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* メインコンテンツエリア */}
      <div className="flex-1 flex flex-col">
        {currentSession ? (
          <AIChat
            key={currentSession.id}
            initialMessages={currentSession.messages}
            systemPrompt={getSystemPrompt()}
            onMessageSent={handleMessageSent}
            onResponseReceived={handleResponseReceived}
          />
        ) : (
          /* 初期状態 */
          <div className="flex-1 flex items-center justify-center bg-gray-50">
            <div className="text-center max-w-md mx-auto px-6">
              <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <MessageSquare className="w-8 h-8 text-primary-600" />
              </div>
              
              <h2 className="text-2xl font-bold text-gray-900 mb-4">
                セキュア AI チャットへようこそ
              </h2>
              
              <p className="text-gray-600 mb-8">
                企業専用の安全なAI対話環境です。<br />
                左のサイドバーから新しいチャットを開始するか、<br />
                テンプレートを選択してください。
              </p>
              
              <div className="space-y-3">
                <button
                  onClick={() => createNewSession()}
                  className="w-full bg-primary-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-primary-700 transition-colors"
                >
                  新しいチャットを開始
                </button>
                
                <button
                  onClick={() => setActiveTab('templates')}
                  className="w-full bg-gray-100 text-gray-700 py-3 px-6 rounded-lg font-medium hover:bg-gray-200 transition-colors"
                >
                  テンプレートを選択
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* テンプレート選択モーダル */}
      <AnimatePresence>
        {showTemplateModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden"
            >
              <div className="flex items-center justify-between p-6 border-b border-gray-200">
                <h2 className="text-xl font-bold text-gray-900">
                  テンプレートを選択
                </h2>
                <button
                  onClick={() => setShowTemplateModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>
              
              <div className="p-6 overflow-y-auto max-h-[calc(90vh-120px)]">
                <TemplateList
                  onTemplateSelect={handleTemplateSelect}
                  currentUser={currentUser}
                />
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};