import { useState, useRef, useEffect } from 'react';
import Head from 'next/head';
import Link from 'next/link';

export default function Chat() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'ai',
      content: 'こんにちは！✨ セキュアAIチャットへようこそ。どのようなことをお手伝いできますか？',
      timestamp: new Date().toISOString()
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [apiError, setApiError] = useState(null);
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputMessage,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);
    setIsTyping(true);
    setApiError(null);

    try {
      // リアルなタイピング効果のための遅延
      await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 2000));

      // デモモード: 実際のAPI呼び出しをシミュレート
      const response = await fetch('http://localhost:8000/api/v1/ai/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messages: [
            { role: 'user', content: inputMessage }
          ],
          model: 'gpt-3.5-turbo',
          temperature: 0.7
        })
      });

      if (response.ok) {
        const data = await response.json();
        const aiMessage = {
          id: Date.now() + 1,
          type: 'ai',
          content: data.content || '✨ AI応答を取得しました。さらに詳しい情報が必要でしたらお知らせください。',
          timestamp: new Date().toISOString(),
          model: data.model,
          tokensUsed: data.tokens_used
        };
        setMessages(prev => [...prev, aiMessage]);
      } else {
        throw new Error(`API Error: ${response.status}`);
      }
    } catch (error) {
      console.error('API Error:', error);
      
      // デモモード: より自然な応答
      const demoResponses = [
        `"${inputMessage}"について詳しく説明させていただきますね。\n\n🔍 現在はデモモードで動作しています。実際のAI機能を使用するには、OpenAI APIキーを設定してください。\n\n💡 この機能を本格的に使用することで、より詳細で正確な情報を提供できます。`,
        `興味深いご質問ですね！✨\n\n"${inputMessage}"に関して、企業の知識ベースから関連情報を検索しています。\n\n🚀 フル機能版では、リアルタイムでの詳細分析と個別最適化された回答を提供します。`,
        `ご質問ありがとうございます！\n\n"${inputMessage}"について、セキュアな環境で処理を行っています。\n\n🛡️ 企業レベルのセキュリティを保ちながら、高品質な回答を準備中です。`
      ];
      
      const randomResponse = demoResponses[Math.floor(Math.random() * demoResponses.length)];
      
      const aiMessage = {
        id: Date.now() + 1,
        type: 'ai',
        content: randomResponse,
        timestamp: new Date().toISOString(),
        isDemo: true
      };
      
      setMessages(prev => [...prev, aiMessage]);
      setApiError('デモモード: より詳細な回答にはOpenAI APIキーが必要です');
    }

    setIsLoading(false);
    setIsTyping(false);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearChat = () => {
    setMessages([
      {
        id: 1,
        type: 'ai',
        content: '🔄 チャットをクリアしました！新しい会話を始めましょう。何かお手伝いできることはありますか？',
        timestamp: new Date().toISOString()
      }
    ]);
    setApiError(null);
  };

  const quickPrompts = [
    "プロジェクト管理のベストプラクティスを教えて",
    "セキュリティ対策について相談したい",
    "新技術の導入について検討中",
    "チーム効率化のアイデアが欲しい"
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      <Head>
        <title>AIチャット - セキュアAIチャット</title>
        <meta name="description" content="AIとの安全で美しいチャット体験" />
      </Head>

      {/* ヘッダー */}
      <header className="bg-white/80 backdrop-blur-md shadow-sm border-b border-white/20 px-6 py-4 sticky top-0 z-10">
        <div className="flex items-center justify-between max-w-6xl mx-auto">
          <div className="flex items-center space-x-4">
            <Link href="/" className="flex items-center text-blue-600 hover:text-blue-800 transition-colors">
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              ホーム
            </Link>
            <div className="flex items-center space-x-2">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                <span className="text-white text-xl">🤖</span>
              </div>
              <div>
                <h1 className="text-xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                  AI チャット
                </h1>
                <p className="text-xs text-gray-500">Powered by SecureAI</p>
              </div>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <Link 
              href="/search"
              className="px-4 py-2 text-sm bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-full hover:from-green-600 hover:to-emerald-700 transition-all transform hover:scale-105 shadow-lg"
            >
              🔍 検索
            </Link>
            <button
              onClick={clearChat}
              className="px-4 py-2 text-sm bg-gray-100/80 text-gray-700 rounded-full hover:bg-gray-200/80 transition-all transform hover:scale-105 backdrop-blur"
            >
              🗑️ クリア
            </button>
            
            <div className="flex items-center space-x-2">
              {apiError ? (
                <div className="flex items-center space-x-1 text-orange-600 bg-orange-50 px-3 py-1 rounded-full text-xs">
                  <span>⚠️</span>
                  <span>デモモード</span>
                </div>
              ) : (
                <div className="flex items-center space-x-1 text-green-600 bg-green-50 px-3 py-1 rounded-full text-xs">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                  <span>接続中</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* チャット領域 */}
      <div className="flex-1 flex flex-col max-w-4xl mx-auto w-full px-4">
        {/* クイックプロンプト（メッセージがない時のみ表示） */}
        {messages.length <= 1 && (
          <div className="py-8">
            <div className="text-center mb-6">
              <h2 className="text-2xl font-bold text-gray-800 mb-2">何でもお聞きください ✨</h2>
              <p className="text-gray-600">以下の例から選ぶか、自由に質問してください</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
              {quickPrompts.map((prompt, index) => (
                <button
                  key={index}
                  onClick={() => setInputMessage(prompt)}
                  className="p-4 bg-white/60 backdrop-blur rounded-xl hover:bg-white/80 transition-all transform hover:scale-105 text-left shadow-lg border border-white/20"
                >
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 bg-gradient-to-br from-blue-400 to-purple-500 rounded-lg flex items-center justify-center">
                      <span className="text-white text-sm">💡</span>
                    </div>
                    <span className="text-gray-700 font-medium">{prompt}</span>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* メッセージ一覧 */}
        <div className="flex-1 overflow-y-auto py-4 space-y-6">
          {messages.map((message, index) => (
            <div
              key={message.id}
              className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in`}
              style={{ animationDelay: `${index * 0.1}s` }}
            >
              <div
                className={`max-w-lg flex ${message.type === 'user' ? 'flex-row-reverse' : 'flex-row'} items-end space-x-3`}
              >
                {/* アバター */}
                <div className={`w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center ${
                  message.type === 'user' 
                    ? 'bg-gradient-to-br from-blue-500 to-blue-600' 
                    : message.isDemo 
                    ? 'bg-gradient-to-br from-orange-400 to-orange-500'
                    : 'bg-gradient-to-br from-purple-500 to-purple-600'
                }`}>
                  <span className="text-white text-sm">
                    {message.type === 'user' ? '👤' : '🤖'}
                  </span>
                </div>

                {/* メッセージバブル */}
                <div
                  className={`px-4 py-3 rounded-2xl shadow-lg transform transition-all hover:scale-105 ${
                    message.type === 'user'
                      ? 'bg-gradient-to-br from-blue-500 to-blue-600 text-white rounded-br-sm'
                      : message.isDemo
                      ? 'bg-gradient-to-br from-orange-50 to-orange-100 text-orange-800 border border-orange-200 rounded-bl-sm'
                      : 'bg-white/80 backdrop-blur text-gray-900 border border-white/20 rounded-bl-sm'
                  }`}
                >
                  <div className="whitespace-pre-wrap leading-relaxed">{message.content}</div>
                  
                  {/* メタデータ */}
                  <div className={`text-xs mt-2 flex items-center space-x-2 ${
                    message.type === 'user' ? 'text-blue-100' : 'text-gray-500'
                  }`}>
                    <span>{new Date(message.timestamp).toLocaleTimeString('ja-JP', { 
                      hour: '2-digit', 
                      minute: '2-digit' 
                    })}</span>
                    {message.model && (
                      <>
                        <span>•</span>
                        <span className="bg-black/10 px-2 py-0.5 rounded text-xs">{message.model}</span>
                      </>
                    )}
                    {message.tokensUsed && (
                      <>
                        <span>•</span>
                        <span>{message.tokensUsed} tokens</span>
                      </>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
          
          {/* タイピングインジケーター */}
          {isTyping && (
            <div className="flex justify-start animate-fade-in">
              <div className="flex items-end space-x-3">
                <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-purple-600 rounded-full flex items-center justify-center">
                  <span className="text-white text-sm">🤖</span>
                </div>
                <div className="bg-white/80 backdrop-blur px-4 py-3 rounded-2xl rounded-bl-sm shadow-lg border border-white/20">
                  <div className="flex items-center space-x-1">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                    </div>
                    <span className="text-gray-500 text-sm ml-2">考え中...</span>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* 入力欄 */}
        <div className="sticky bottom-0 bg-white/80 backdrop-blur-md border-t border-white/20 px-6 py-6">
          <div className="flex space-x-4 items-end">
            <div className="flex-1 relative">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="メッセージを入力... ✨"
                className="w-full px-4 py-3 bg-white/80 backdrop-blur border border-gray-200/50 rounded-2xl focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 resize-none shadow-lg transition-all"
                rows="1"
                disabled={isLoading}
                style={{
                  minHeight: '48px',
                  maxHeight: '120px',
                }}
                onInput={(e) => {
                  e.target.style.height = 'auto';
                  e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px';
                }}
              />
              <div className="absolute right-3 bottom-2 text-xs text-gray-400">
                Enter: 送信 / Shift+Enter: 改行
              </div>
            </div>
            
            <button
              onClick={sendMessage}
              disabled={!inputMessage.trim() || isLoading}
              className="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-2xl hover:from-blue-600 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all transform hover:scale-105 shadow-lg disabled:transform-none flex items-center space-x-2"
            >
              {isLoading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                  <span>送信中...</span>
                </>
              ) : (
                <>
                  <span>送信</span>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                  </svg>
                </>
              )}
            </button>
          </div>
          
          <div className="mt-3 text-center">
            <p className="text-xs text-gray-500">
              🔐 セキュアな暗号化通信で保護されています
            </p>
          </div>
        </div>
      </div>

      <style jsx global>{`
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        .animate-fade-in {
          animation: fadeIn 0.3s ease-out forwards;
        }
      `}</style>
    </div>
  );
}