import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/router';
import { 
  Send, 
  ArrowLeft, 
  User, 
  Bot, 
  FileText, 
  Settings,
  Trash2,
  Edit3,
  Shield
} from 'lucide-react';
import toast from 'react-hot-toast';
import ReactMarkdown from 'react-markdown';

interface ChatMessage {
  id: number;
  message_type: 'user' | 'assistant';
  content: string;
  timestamp: string;
  processing_time?: number;
}

interface ChatSession {
  id: number;
  session_id: string;
  title: string;
}

export default function Chat() {
  const router = useRouter();
  const { sessionId } = router.query;
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [session, setSession] = useState<ChatSession | null>(null);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (sessionId) {
      loadChatData();
    }
  }, [sessionId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadChatData = async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        router.push('/login');
        return;
      }

      // チャット履歴取得
      const response = await fetch(`/api/v1/chat/sessions/${sessionId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const chatHistory = await response.json();
        setMessages(chatHistory);
      } else {
        toast.error('チャット履歴の読み込みに失敗しました');
        router.push('/dashboard');
      }

      // セッション情報を推測（簡略化）
      if (chatHistory.length > 0) {
        setSession({
          id: 1,
          session_id: sessionId as string,
          title: chatHistory[0]?.content?.substring(0, 50) + '...' || '新しいチャット'
        });
      }
    } catch (error) {
      console.error('Load chat error:', error);
      toast.error('ネットワークエラーが発生しました');
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const messageText = inputMessage.trim();
    setInputMessage('');
    setIsLoading(true);

    // ユーザーメッセージを即座に表示
    const userMessage: ChatMessage = {
      id: Date.now(),
      message_type: 'user',
      content: messageText,
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMessage]);

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('/api/v1/chat/message', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: messageText,
          session_id: sessionId,
        }),
      });

      if (response.ok) {
        const result = await response.json();
        
        // AIレスポンスを追加
        const aiMessage: ChatMessage = {
          id: result.message_id,
          message_type: 'assistant',
          content: result.response,
          timestamp: result.timestamp,
          processing_time: result.processing_time
        };
        
        setMessages(prev => [...prev, aiMessage]);

        // セッションタイトルが未設定の場合は更新
        if (session?.title === '新しいチャット' && messages.length === 0) {
          setSession(prev => prev ? { ...prev, title: messageText.substring(0, 50) + '...' } : null);
        }
      } else {
        const error = await response.json();
        toast.error(error.detail || 'メッセージ送信に失敗しました');
        
        // エラー時はユーザーメッセージを削除
        setMessages(prev => prev.slice(0, -1));
      }
    } catch (error) {
      console.error('Send message error:', error);
      toast.error('ネットワークエラーが発生しました');
      
      // エラー時はユーザーメッセージを削除
      setMessages(prev => prev.slice(0, -1));
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const updateSessionTitle = async () => {
    if (!newTitle.trim() || !session) return;

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`/api/v1/chat/sessions/${sessionId}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: newTitle.trim(),
        }),
      });

      if (response.ok) {
        setSession(prev => prev ? { ...prev, title: newTitle.trim() } : null);
        setIsEditingTitle(false);
        toast.success('タイトルを更新しました');
      } else {
        toast.error('タイトル更新に失敗しました');
      }
    } catch (error) {
      console.error('Update title error:', error);
      toast.error('ネットワークエラーが発生しました');
    }
  };

  const deleteSession = async () => {
    if (!confirm('このチャットセッションを削除しますか？')) return;

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`/api/v1/chat/sessions/${sessionId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        toast.success('チャットセッションを削除しました');
        router.push('/dashboard');
      } else {
        toast.error('削除に失敗しました');
      }
    } catch (error) {
      console.error('Delete session error:', error);
      toast.error('ネットワークエラーが発生しました');
    }
  };

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString('ja-JP', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* ヘッダー */}
      <header className="bg-white border-b border-gray-200 px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <button
              onClick={() => router.push('/dashboard')}
              className="mr-4 p-2 text-gray-400 hover:text-gray-600 transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            
            {isEditingTitle ? (
              <div className="flex items-center">
                <input
                  type="text"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  onBlur={updateSessionTitle}
                  onKeyPress={(e) => e.key === 'Enter' && updateSessionTitle()}
                  className="text-lg font-semibold bg-transparent border-b-2 border-indigo-500 focus:outline-none"
                  autoFocus
                />
              </div>
            ) : (
              <div className="flex items-center">
                <Shield className="w-6 h-6 text-indigo-600 mr-2" />
                <h1 className="text-lg font-semibold text-gray-900">
                  {session?.title || '読み込み中...'}
                </h1>
                <button
                  onClick={() => {
                    setNewTitle(session?.title || '');
                    setIsEditingTitle(true);
                  }}
                  className="ml-2 p-1 text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <Edit3 className="w-4 h-4" />
                </button>
              </div>
            )}
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={deleteSession}
              className="p-2 text-gray-400 hover:text-red-500 transition-colors"
              title="セッション削除"
            >
              <Trash2 className="w-5 h-5" />
            </button>
          </div>
        </div>
      </header>

      {/* メッセージエリア */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-3xl mx-auto space-y-6">
          {messages.length === 0 ? (
            <div className="text-center py-12">
              <Bot className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-600 mb-2">
                AIアシスタントとチャットを開始
              </h3>
              <p className="text-gray-500">
                質問や相談を入力してください。安全で高性能なAIが回答します。
              </p>
            </div>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${
                  message.message_type === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                <div
                  className={`max-w-2xl rounded-lg px-4 py-3 ${
                    message.message_type === 'user'
                      ? 'bg-indigo-600 text-white'
                      : 'bg-white border border-gray-200'
                  }`}
                >
                  <div className="flex items-center mb-2">
                    {message.message_type === 'user' ? (
                      <User className="w-4 h-4 mr-2" />
                    ) : (
                      <Bot className="w-4 h-4 mr-2 text-indigo-600" />
                    )}
                    <span className="text-xs opacity-75">
                      {formatTime(message.timestamp)}
                    </span>
                    {message.processing_time && (
                      <span className="text-xs opacity-75 ml-2">
                        ({message.processing_time.toFixed(2)}s)
                      </span>
                    )}
                  </div>
                  
                  <div className="prose prose-sm max-w-none">
                    {message.message_type === 'assistant' ? (
                      <ReactMarkdown>{message.content}</ReactMarkdown>
                    ) : (
                      <p className="whitespace-pre-wrap">{message.content}</p>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
          
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-white border border-gray-200 rounded-lg px-4 py-3">
                <div className="flex items-center">
                  <Bot className="w-4 h-4 mr-2 text-indigo-600" />
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
        <div ref={messagesEndRef} />
      </div>

      {/* 入力エリア */}
      <div className="bg-white border-t border-gray-200 px-4 py-4">
        <div className="max-w-3xl mx-auto">
          <div className="flex items-end space-x-4">
            <div className="flex-1">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="メッセージを入力してください..."
                className="w-full px-4 py-3 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                rows={3}
                disabled={isLoading}
              />
            </div>
            <button
              onClick={sendMessage}
              disabled={!inputMessage.trim() || isLoading}
              className="bg-indigo-600 text-white p-3 rounded-lg hover:bg-indigo-700 focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
          
          <div className="flex items-center justify-between mt-2 text-xs text-gray-500">
            <div className="flex items-center">
              <Shield className="w-3 h-3 mr-1" />
              <span>すべての会話は暗号化されて保護されています</span>
            </div>
            <span>Shift + Enter で改行</span>
          </div>
        </div>
      </div>
    </div>
  );
}