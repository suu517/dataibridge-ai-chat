/**
 * セキュアAIチャット - チャット管理フック
 */

import { useState, useEffect, useCallback } from 'react';
import { toast } from 'react-hot-toast';
import { chatApi, aiApi } from '@/utils/api';

interface ChatMessage {
  id: number;
  role: string;
  content: string;
  created_at: string;
  metadata: any;
}

interface Chat {
  id: number;
  title: string;
  created_at: string;
  updated_at: string;
  messages: ChatMessage[];
}

interface ChatListItem {
  id: number;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  last_message?: string;
}

interface UseChatResult {
  // State
  chats: ChatListItem[];
  currentChat: Chat | null;
  messages: ChatMessage[];
  loading: boolean;
  sending: boolean;
  error: string | null;
  
  // Actions
  fetchChats: (params?: { skip?: number; limit?: number; search?: string }) => Promise<void>;
  createChat: (data: { title: string; system_prompt?: string; template_id?: number }) => Promise<number | null>;
  loadChat: (id: number) => Promise<void>;
  sendMessage: (content: string) => Promise<void>;
  updateChat: (id: number, data: { title?: string; system_prompt?: string }) => Promise<boolean>;
  deleteChat: (id: number) => Promise<boolean>;
  deleteMessage: (chatId: number, messageId: number) => Promise<boolean>;
  
  // Current chat info
  currentChatId: number | null;
  setCurrentChatId: (id: number | null) => void;
}

export const useChat = (): UseChatResult => {
  const [chats, setChats] = useState<ChatListItem[]>([]);
  const [currentChat, setCurrentChat] = useState<Chat | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentChatId, setCurrentChatId] = useState<number | null>(null);

  const fetchChats = useCallback(async (params?: { skip?: number; limit?: number; search?: string }) => {
    setLoading(true);
    setError(null);

    try {
      const response = await chatApi.getChats(params);
      setChats(response.chats);
    } catch (err: any) {
      const errorMessage = err.response?.data?.message || 'チャット一覧の取得に失敗しました';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  const createChat = useCallback(async (data: {
    title: string;
    system_prompt?: string;
    template_id?: number;
  }): Promise<number | null> => {
    setLoading(true);
    setError(null);

    try {
      const response = await chatApi.createChat(data);
      toast.success('新しいチャットを作成しました');
      
      // チャット一覧を更新
      await fetchChats();
      
      return response.id;
    } catch (err: any) {
      const errorMessage = err.response?.data?.message || 'チャットの作成に失敗しました';
      setError(errorMessage);
      toast.error(errorMessage);
      return null;
    } finally {
      setLoading(false);
    }
  }, [fetchChats]);

  const loadChat = useCallback(async (id: number) => {
    setLoading(true);
    setError(null);

    try {
      const response = await chatApi.getChat(id);
      setCurrentChat(response);
      setMessages(response.messages);
      setCurrentChatId(id);
    } catch (err: any) {
      const errorMessage = err.response?.data?.message || 'チャットの読み込みに失敗しました';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  const sendMessage = useCallback(async (content: string) => {
    if (!currentChatId || !content.trim()) {
      return;
    }

    setSending(true);
    setError(null);

    try {
      const response = await chatApi.sendMessage(currentChatId, {
        content: content.trim(),
        role: 'user'
      });

      // メッセージリストを更新
      const updatedMessages = [...messages, response.message];
      if (response.ai_response) {
        updatedMessages.push({
          id: response.ai_response.id,
          role: 'assistant',
          content: response.ai_response.content,
          created_at: response.ai_response.created_at,
          metadata: response.ai_response.metadata
        });
      }
      
      setMessages(updatedMessages);
      
      // チャット一覧も更新（最終メッセージが変更される）
      await fetchChats();
      
    } catch (err: any) {
      const errorMessage = err.response?.data?.message || 'メッセージの送信に失敗しました';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setSending(false);
    }
  }, [currentChatId, messages, fetchChats]);

  const updateChat = useCallback(async (id: number, data: {
    title?: string;
    system_prompt?: string;
  }): Promise<boolean> => {
    setLoading(true);
    setError(null);

    try {
      await chatApi.updateChat(id, data);
      toast.success('チャットを更新しました');
      
      // 現在のチャットが更新対象の場合は再読み込み
      if (currentChatId === id) {
        await loadChat(id);
      }
      
      // チャット一覧を更新
      await fetchChats();
      
      return true;
    } catch (err: any) {
      const errorMessage = err.response?.data?.message || 'チャットの更新に失敗しました';
      setError(errorMessage);
      toast.error(errorMessage);
      return false;
    } finally {
      setLoading(false);
    }
  }, [currentChatId, loadChat, fetchChats]);

  const deleteChat = useCallback(async (id: number): Promise<boolean> => {
    if (!confirm('このチャットを削除してもよろしいですか？')) {
      return false;
    }

    setLoading(true);
    setError(null);

    try {
      await chatApi.deleteChat(id);
      toast.success('チャットを削除しました');
      
      // 現在のチャットが削除対象の場合はクリア
      if (currentChatId === id) {
        setCurrentChat(null);
        setMessages([]);
        setCurrentChatId(null);
      }
      
      // チャット一覧を更新
      await fetchChats();
      
      return true;
    } catch (err: any) {
      const errorMessage = err.response?.data?.message || 'チャットの削除に失敗しました';
      setError(errorMessage);
      toast.error(errorMessage);
      return false;
    } finally {
      setLoading(false);
    }
  }, [currentChatId, fetchChats]);

  const deleteMessage = useCallback(async (chatId: number, messageId: number): Promise<boolean> => {
    if (!confirm('このメッセージを削除してもよろしいですか？')) {
      return false;
    }

    setLoading(true);
    setError(null);

    try {
      await chatApi.deleteMessage(chatId, messageId);
      toast.success('メッセージを削除しました');
      
      // 現在のチャットのメッセージの場合はリストから削除
      if (currentChatId === chatId) {
        setMessages(prev => prev.filter(msg => msg.id !== messageId));
      }
      
      return true;
    } catch (err: any) {
      const errorMessage = err.response?.data?.message || 'メッセージの削除に失敗しました';
      setError(errorMessage);
      toast.error(errorMessage);
      return false;
    } finally {
      setLoading(false);
    }
  }, [currentChatId]);

  // 初期データ取得
  useEffect(() => {
    fetchChats();
  }, [fetchChats]);

  return {
    chats,
    currentChat,
    messages,
    loading,
    sending,
    error,
    fetchChats,
    createChat,
    loadChat,
    sendMessage,
    updateChat,
    deleteChat,
    deleteMessage,
    currentChatId,
    setCurrentChatId
  };
};