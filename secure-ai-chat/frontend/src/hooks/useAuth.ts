/**
 * セキュアAIチャット - 認証管理フック
 */

import { useState, useEffect, useCallback, createContext, useContext } from 'react';
import { toast } from 'react-hot-toast';
import Cookies from 'js-cookie';
import { User, LoginRequest, LoginResponse } from '@/types';
import { authApi } from '@/utils/api';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  
  // Actions
  login: (credentials: LoginRequest) => Promise<boolean>;
  logout: () => void;
  refreshUser: () => Promise<void>;
  changePassword: (currentPassword: string, newPassword: string) => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const useAuthProvider = (): AuthContextType => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const isAuthenticated = !!user && !!Cookies.get('access_token');

  const login = useCallback(async (credentials: LoginRequest): Promise<boolean> => {
    setLoading(true);

    try {
      const response: LoginResponse = await authApi.login(credentials);
      
      // トークンを保存
      Cookies.set('access_token', response.access_token, { expires: 7 });
      Cookies.set('refresh_token', response.refresh_token, { expires: 30 });
      
      // ユーザー情報を設定
      setUser(response.user);
      
      toast.success('ログインしました');
      return true;
    } catch (error: any) {
      const errorMessage = error.response?.data?.message || 'ログインに失敗しました';
      toast.error(errorMessage);
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    // トークンを削除
    Cookies.remove('access_token');
    Cookies.remove('refresh_token');
    Cookies.remove('user');
    
    // ユーザー状態をクリア
    setUser(null);
    
    // サーバーにログアウト通知（バックグラウンドで実行）
    authApi.logout().catch(() => {
      // エラーは無視（既にローカル状態はクリアされている）
    });
    
    toast.success('ログアウトしました');
  }, []);

  const refreshUser = useCallback(async () => {
    if (!Cookies.get('access_token')) {
      setUser(null);
      setLoading(false);
      return;
    }

    try {
      const userData = await authApi.me();
      setUser(userData);
    } catch (error) {
      // トークンが無効な場合はログアウト
      logout();
    } finally {
      setLoading(false);
    }
  }, [logout]);

  const changePassword = useCallback(async (
    currentPassword: string,
    newPassword: string
  ): Promise<boolean> => {
    setLoading(true);

    try {
      await authApi.changePassword({
        current_password: currentPassword,
        new_password: newPassword
      });
      
      toast.success('パスワードを変更しました');
      return true;
    } catch (error: any) {
      const errorMessage = error.response?.data?.message || 'パスワードの変更に失敗しました';
      toast.error(errorMessage);
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  // 初期化時にユーザー情報を取得
  useEffect(() => {
    refreshUser();
  }, []);

  return {
    user,
    loading,
    isAuthenticated,
    login,
    logout,
    refreshUser,
    changePassword
  };
};

export { AuthContext };