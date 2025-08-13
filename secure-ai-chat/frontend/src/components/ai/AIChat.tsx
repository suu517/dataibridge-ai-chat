/**
 * セキュアAIチャット - AI チャットコンポーネント
 */

import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Send, 
  Bot, 
  User, 
  AlertCircle, 
  Loader,
  Copy,
  Check,
  Settings,
  Zap
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/cjs/styles/prism';
import { toast } from 'react-hot-toast';
import { aiApi } from '@/utils/api';

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: number;
  isStreaming?: boolean;
  tokens_used?: number;
  processing_time_ms?: number;
}

interface AIChatProps {
  initialMessages?: Message[];
  systemPrompt?: string;
  onMessageSent?: (message: Message) => void;
  onResponseReceived?: (message: Message) => void;
}

export const AIChat: React.FC<AIChatProps> = ({
  initialMessages = [],
  systemPrompt,
  onMessageSent,
  onResponseReceived
}) => {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showSettings, setShowSettings] = useState(false);
  const [settings, setSettings] = useState({
    model: 'gpt-3.5-turbo',
    temperature: 0.7,
    max_tokens: 2000,
    stream: true
  });
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // 自動スクロール
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // テキストエリアの高さ調整
  const adjustTextareaHeight = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  };

  useEffect(() => {
    adjustTextareaHeight();
  }, [inputText]);

  // メッセージ送信
  const sendMessage = async () => {
    if (!inputText.trim() || isLoading) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: inputText.trim(),
      timestamp: Date.now()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setIsLoading(true);
    setError(null);

    onMessageSent?.(userMessage);

    try {
      // メッセージ履歴を構築
      const messageHistory = [
        ...(systemPrompt ? [{ role: 'system' as const, content: systemPrompt }] : []),
        ...messages.map(msg => ({
          role: msg.role,
          content: msg.content
        })),
        {
          role: 'user' as const,
          content: inputText.trim()
        }
      ];

      if (settings.stream) {
        await handleStreamingResponse(messageHistory);
      } else {
        await handleSingleResponse(messageHistory);
      }

    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'メッセージの送信に失敗しました';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  // 単発レスポンス処理
  const handleSingleResponse = async (messageHistory: any[]) => {
    const response = await aiApi.createCompletion({
      messages: messageHistory,
      model: settings.model,
      temperature: settings.temperature,
      max_tokens: settings.max_tokens,
      stream: false
    });

    const assistantMessage: Message = {
      id: `assistant-${Date.now()}`,
      role: 'assistant',
      content: response.content,
      timestamp: Date.now(),
      tokens_used: response.tokens_used,
      processing_time_ms: response.processing_time_ms
    };

    setMessages(prev => [...prev, assistantMessage]);
    onResponseReceived?.(assistantMessage);
  };

  // ストリーミングレスポンス処理
  const handleStreamingResponse = async (messageHistory: any[]) => {
    const assistantMessageId = `assistant-${Date.now()}`;
    let assistantMessage: Message = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      timestamp: Date.now(),
      isStreaming: true
    };

    setMessages(prev => [...prev, assistantMessage]);

    try {
      const eventSource = await aiApi.createStreamingCompletion({
        messages: messageHistory,
        model: settings.model,
        temperature: settings.temperature,
        max_tokens: settings.max_tokens,
        stream: true
      });

      eventSource.onmessage = (event) => {
        if (event.data === '[DONE]') {
          eventSource.close();
          setMessages(prev => 
            prev.map(msg => 
              msg.id === assistantMessageId 
                ? { ...msg, isStreaming: false }
                : msg
            )
          );
          return;
        }

        try {
          const data = JSON.parse(event.data);
          
          if (data.type === 'content') {
            setMessages(prev => 
              prev.map(msg => 
                msg.id === assistantMessageId 
                  ? { ...msg, content: data.full_content }
                  : msg
              )
            );
          } else if (data.type === 'completed') {
            assistantMessage = {
              ...assistantMessage,
              content: data.content,
              tokens_used: data.tokens_used,
              processing_time_ms: data.processing_time_ms,
              isStreaming: false
            };
            
            setMessages(prev => 
              prev.map(msg => 
                msg.id === assistantMessageId 
                  ? assistantMessage
                  : msg
              )
            );
            
            onResponseReceived?.(assistantMessage);
          } else if (data.type === 'error') {
            throw new Error(data.error);
          }
        } catch (parseError) {
          console.error('ストリーミングデータの解析エラー:', parseError);
        }
      };

      eventSource.onerror = (error) => {
        console.error('ストリーミングエラー:', error);
        eventSource.close();
        setError('ストリーミング中にエラーが発生しました');
        setMessages(prev => 
          prev.map(msg => 
            msg.id === assistantMessageId 
              ? { ...msg, isStreaming: false }
              : msg
          )
        );
      };

    } catch (error: any) {
      throw error;
    }
  };

  // メッセージコピー
  const copyMessage = async (content: string) => {
    try {
      await navigator.clipboard.writeText(content);
      toast.success('メッセージをコピーしました');
    } catch (error) {
      toast.error('コピーに失敗しました');
    }
  };

  // キー入力処理
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // メッセージコンポーネント
  const MessageComponent: React.FC<{ message: Message; index: number }> = ({ message, index }) => {
    const [copied, setCopied] = useState(false);

    const handleCopy = async () => {
      await copyMessage(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    };

    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: index * 0.1 }}
        className={`flex items-start space-x-3 mb-6 ${
          message.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''
        }`}
      >
        {/* アバター */}
        <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
          message.role === 'user' 
            ? 'bg-primary-500 text-white' 
            : 'bg-gray-200 text-gray-600'
        }`}>
          {message.role === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
        </div>

        {/* メッセージ本体 */}
        <div className={`flex-1 max-w-3xl ${
          message.role === 'user' ? 'text-right' : 'text-left'
        }`}>
          <div className={`inline-block p-4 rounded-lg ${
            message.role === 'user'
              ? 'bg-primary-500 text-white'
              : 'bg-white border border-gray-200 text-gray-800'
          }`}>
            {message.role === 'assistant' ? (
              <ReactMarkdown
                components={{
                  code: ({ node, inline, className, children, ...props }) => {
                    const match = /language-(\w+)/.exec(className || '');
                    return !inline && match ? (
                      <SyntaxHighlighter
                        style={oneDark}
                        language={match[1]}
                        PreTag="div"
                        {...props}
                      >
                        {String(children).replace(/\n$/, '')}
                      </SyntaxHighlighter>
                    ) : (
                      <code className="bg-gray-100 px-1 py-0.5 rounded text-sm" {...props}>
                        {children}
                      </code>
                    );
                  }
                }}
              >
                {message.content}
              </ReactMarkdown>
            ) : (
              <div className="whitespace-pre-wrap">{message.content}</div>
            )}

            {message.isStreaming && (
              <div className="flex items-center space-x-2 mt-2 text-sm opacity-70">
                <Loader className="w-3 h-3 animate-spin" />
                <span>回答生成中...</span>
              </div>
            )}
          </div>

          {/* メタ情報 */}
          <div className={`flex items-center justify-between mt-2 text-xs text-gray-500 ${
            message.role === 'user' ? 'flex-row-reverse' : ''
          }`}>
            <span>
              {new Date(message.timestamp).toLocaleTimeString('ja-JP', {
                hour: '2-digit',
                minute: '2-digit'
              })}
            </span>

            <div className="flex items-center space-x-2">
              {message.tokens_used && (
                <span className="flex items-center space-x-1">
                  <Zap className="w-3 h-3" />
                  <span>{message.tokens_used} tokens</span>
                </span>
              )}
              
              <button
                onClick={handleCopy}
                className="p-1 hover:bg-gray-100 rounded transition-colors"
                title="コピー"
              >
                {copied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
              </button>
            </div>
          </div>
        </div>
      </motion.div>
    );
  };

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* ヘッダー */}
      <div className="flex items-center justify-between p-4 bg-white border-b border-gray-200">
        <div className="flex items-center space-x-3">
          <Bot className="w-6 h-6 text-primary-500" />
          <div>
            <h2 className="text-lg font-semibold text-gray-900">AI チャット</h2>
            <p className="text-sm text-gray-500">セキュアなAI対話環境</p>
          </div>
        </div>
        
        <button
          onClick={() => setShowSettings(!showSettings)}
          className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-md transition-colors"
        >
          <Settings className="w-5 h-5" />
        </button>
      </div>

      {/* 設定パネル */}
      <AnimatePresence>
        {showSettings && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="bg-white border-b border-gray-200 p-4"
          >
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  モデル
                </label>
                <select
                  value={settings.model}
                  onChange={(e) => setSettings(prev => ({ ...prev, model: e.target.value }))}
                  className="w-full text-sm border border-gray-300 rounded-md px-2 py-1 focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                >
                  <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                  <option value="gpt-4">GPT-4</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Temperature
                </label>
                <input
                  type="number"
                  min="0"
                  max="2"
                  step="0.1"
                  value={settings.temperature}
                  onChange={(e) => setSettings(prev => ({ ...prev, temperature: parseFloat(e.target.value) }))}
                  className="w-full text-sm border border-gray-300 rounded-md px-2 py-1 focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Max Tokens
                </label>
                <input
                  type="number"
                  min="1"
                  max="4000"
                  value={settings.max_tokens}
                  onChange={(e) => setSettings(prev => ({ ...prev, max_tokens: parseInt(e.target.value) }))}
                  className="w-full text-sm border border-gray-300 rounded-md px-2 py-1 focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                />
              </div>
              
              <div className="flex items-center">
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={settings.stream}
                    onChange={(e) => setSettings(prev => ({ ...prev, stream: e.target.checked }))}
                    className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                  <span className="text-sm font-medium text-gray-700">ストリーミング</span>
                </label>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* メッセージ一覧 */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center py-12">
            <Bot className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">AIチャットへようこそ</h3>
            <p className="text-gray-500">メッセージを入力して会話を開始してください</p>
          </div>
        ) : (
          messages.map((message, index) => (
            <MessageComponent key={message.id} message={message} index={index} />
          ))
        )}

        {/* エラー表示 */}
        {error && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start space-x-3"
          >
            <AlertCircle className="w-5 h-5 text-red-500 mt-0.5" />
            <div>
              <h4 className="text-sm font-medium text-red-800 mb-1">エラーが発生しました</h4>
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* 入力エリア */}
      <div className="bg-white border-t border-gray-200 p-4">
        <div className="flex items-end space-x-3">
          <div className="flex-1">
            <textarea
              ref={textareaRef}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="メッセージを入力してください..."
              disabled={isLoading}
              rows={1}
              className="w-full resize-none border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-primary-500 focus:border-primary-500 disabled:opacity-50"
            />
          </div>
          
          <button
            onClick={sendMessage}
            disabled={!inputText.trim() || isLoading}
            className="flex-shrink-0 w-10 h-10 bg-primary-500 text-white rounded-lg flex items-center justify-center hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? (
              <Loader className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </div>

        <div className="flex items-center justify-between mt-2 text-xs text-gray-500">
          <div>
            Enter で送信、Shift + Enter で改行
          </div>
          <div className="flex items-center space-x-4">
            <span>モデル: {settings.model}</span>
            {settings.stream && <span>ストリーミング有効</span>}
          </div>
        </div>
      </div>
    </div>
  );
};