/**
 * セキュアAIチャット - API ユーティリティ
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import { toast } from 'react-hot-toast';
import Cookies from 'js-cookie';
import { 
  ApiResponse, 
  User, 
  LoginRequest, 
  LoginResponse,
  PromptTemplate,
  TemplateCategory,
  CreateTemplateForm,
  PaginatedResponse
} from '@/types';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // リクエストインターセプター
    this.client.interceptors.request.use(
      (config) => {
        const token = Cookies.get('access_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        
        // CSRF保護のためのリクエストID追加
        config.headers['X-Request-ID'] = this.generateRequestId();
        
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // レスポンスインターセプター
    this.client.interceptors.response.use(
      (response: AxiosResponse) => {
        return response;
      },
      async (error) => {
        const originalRequest = error.config;

        // 401エラーの場合はトークンリフレッシュを試行
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            const refreshToken = Cookies.get('refresh_token');
            if (refreshToken) {
              const response = await this.client.post('/api/v1/auth/refresh', {
                refresh_token: refreshToken
              });

              const { access_token } = response.data;
              Cookies.set('access_token', access_token);
              originalRequest.headers.Authorization = `Bearer ${access_token}`;

              return this.client(originalRequest);
            }
          } catch (refreshError) {
            // リフレッシュに失敗した場合はログアウト
            this.logout();
            window.location.href = '/login';
            return Promise.reject(refreshError);
          }
        }

        // 403エラーの場合は権限不足メッセージ
        if (error.response?.status === 403) {
          toast.error('この操作を実行する権限がありません');
        }

        // 429エラーの場合はレート制限メッセージ
        if (error.response?.status === 429) {
          toast.error('リクエストが多すぎます。しばらく時間をおいてから再試行してください');
        }

        // 500エラーの場合はサーバーエラーメッセージ
        if (error.response?.status >= 500) {
          toast.error('サーバーエラーが発生しました。管理者にお問い合わせください');
        }

        return Promise.reject(error);
      }
    );
  }

  private generateRequestId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  private logout(): void {
    Cookies.remove('access_token');
    Cookies.remove('refresh_token');
    Cookies.remove('user');
  }

  // 汎用API呼び出しメソッド
  async request<T = any>(config: AxiosRequestConfig): Promise<T> {
    try {
      const response = await this.client.request<T>(config);
      return response.data;
    } catch (error: any) {
      throw error;
    }
  }

  async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return this.request<T>({ ...config, method: 'GET', url });
  }

  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return this.request<T>({ ...config, method: 'POST', url, data });
  }

  async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return this.request<T>({ ...config, method: 'PUT', url, data });
  }

  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return this.request<T>({ ...config, method: 'DELETE', url });
  }
}

// APIクライアントインスタンス
export const apiClient = new ApiClient();

// 認証API
export const authApi = {
  login: (credentials: LoginRequest): Promise<LoginResponse> =>
    apiClient.post('/api/v1/auth/login', credentials),

  logout: (): Promise<void> =>
    apiClient.post('/api/v1/auth/logout'),

  refresh: (refreshToken: string): Promise<{ access_token: string }> =>
    apiClient.post('/api/v1/auth/refresh', { refresh_token: refreshToken }),

  me: (): Promise<User> =>
    apiClient.get('/api/v1/auth/me'),

  changePassword: (data: { current_password: string; new_password: string }): Promise<void> =>
    apiClient.put('/api/v1/auth/change-password', data),
};

// テンプレートAPI
export const templateApi = {
  getCategories: (activeOnly: boolean = true): Promise<TemplateCategory[]> =>
    apiClient.get('/api/v1/templates/categories', { params: { active_only: activeOnly } }),

  createCategory: (data: {
    name: string;
    description?: string;
    icon?: string;
    color?: string;
    sort_order?: number;
  }): Promise<TemplateCategory> =>
    apiClient.post('/api/v1/templates/categories', data),

  getTemplates: (params: {
    categoryId?: number;
    status?: string;
    accessLevel?: string;
    search?: string;
    tags?: string[];
    page?: number;
    limit?: number;
    sortBy?: string;
    sortOrder?: 'asc' | 'desc';
  }): Promise<PaginatedResponse<PromptTemplate> & { templates: PromptTemplate[] }> => {
    const queryParams: any = { ...params };
    
    // tagsを文字列に変換
    if (params.tags && params.tags.length > 0) {
      queryParams.tags = params.tags.join(',');
    }
    
    return apiClient.get('/api/v1/templates/', { params: queryParams });
  },

  getTemplate: (id: number): Promise<PromptTemplate> =>
    apiClient.get(`/api/v1/templates/${id}`),

  createTemplate: (data: CreateTemplateForm): Promise<{ id: number; name: string; message: string }> =>
    apiClient.post('/api/v1/templates/', data),

  updateTemplate: (
    id: number, 
    data: Partial<CreateTemplateForm>
  ): Promise<{ id: number; name: string; message: string }> =>
    apiClient.put(`/api/v1/templates/${id}`, data),

  deleteTemplate: (id: number): Promise<{ message: string }> =>
    apiClient.delete(`/api/v1/templates/${id}`),

  useTemplate: (
    id: number, 
    parameters: Record<string, any>
  ): Promise<{ rendered_prompt: string }> =>
    apiClient.post(`/api/v1/templates/${id}/use`, { parameters }),

  getPopularTemplates: (limit: number = 10): Promise<PromptTemplate[]> =>
    apiClient.get('/api/v1/templates/popular/list', { params: { limit } }),

  getRecentTemplates: (limit: number = 10): Promise<PromptTemplate[]> =>
    apiClient.get('/api/v1/templates/recent/list', { params: { limit } }),
};

// AI API
export const aiApi = {
  getModels: (): Promise<any[]> =>
    apiClient.get('/api/v1/ai/models'),

  getTokenUsage: (): Promise<{
    user_id: number;
    tokens_used_today: number;
    daily_limit: number;
    remaining_tokens: number;
    limit_reached: boolean;
  }> =>
    apiClient.get('/api/v1/ai/usage'),

  createCompletion: (data: {
    messages: Array<{ role: string; content: string }>;
    model?: string;
    temperature?: number;
    max_tokens?: number;
    stream?: boolean;
  }): Promise<{
    content: string;
    model: string;
    tokens_used: number;
    processing_time_ms: number;
    finish_reason: string;
    metadata: any;
  }> =>
    apiClient.post('/api/v1/ai/chat', data),

  createStreamingCompletion: (data: {
    messages: Array<{ role: string; content: string }>;
    model?: string;
    temperature?: number;
    max_tokens?: number;
    stream?: boolean;
  }): Promise<Response> => {
    return apiClient.request({
      method: 'POST',
      url: '/api/v1/ai/chat/stream',
      data: { ...data, stream: true },
      headers: {
        'Accept': 'text/event-stream',
        'Cache-Control': 'no-cache',
      },
      responseType: 'stream'
    });
  },

  validateContent: (data: { text: string }): Promise<{
    is_safe: boolean;
    violations: string[];
    message: string;
  }> =>
    apiClient.post('/api/v1/ai/validate-content', data),

  healthCheck: (): Promise<{
    status: string;
    ai_service: string;
    model_tested?: string;
    response_time_ms?: number;
    error?: string;
  }> =>
    apiClient.get('/api/v1/ai/health'),
};

// チャットAPI
export const chatApi = {
  getChats: (params?: {
    skip?: number;
    limit?: number;
    search?: string;
  }): Promise<{
    chats: Array<{
      id: number;
      title: string;
      created_at: string;
      updated_at: string;
      message_count: number;
      last_message?: string;
    }>;
    total: number;
  }> =>
    apiClient.get('/api/v1/chats/', { params }),

  getChat: (id: number): Promise<{
    id: number;
    title: string;
    created_at: string;
    updated_at: string;
    messages: Array<{
      id: number;
      role: string;
      content: string;
      created_at: string;
      metadata: any;
    }>;
  }> =>
    apiClient.get(`/api/v1/chats/${id}`),

  createChat: (data: {
    title: string;
    system_prompt?: string;
    template_id?: number;
  }): Promise<{
    id: number;
    title: string;
    created_at: string;
  }> =>
    apiClient.post('/api/v1/chats/', data),

  updateChat: (id: number, data: {
    title?: string;
    system_prompt?: string;
  }): Promise<{
    id: number;
    title: string;
    updated_at: string;
  }> =>
    apiClient.put(`/api/v1/chats/${id}`, data),

  deleteChat: (id: number): Promise<{ message: string }> =>
    apiClient.delete(`/api/v1/chats/${id}`),

  sendMessage: (chatId: number, data: {
    content: string;
    role?: string;
    metadata?: any;
  }): Promise<{
    message: {
      id: number;
      role: string;
      content: string;
      created_at: string;
      metadata: any;
    };
    ai_response?: {
      id: number;
      content: string;
      created_at: string;
      metadata: any;
    };
  }> =>
    apiClient.post(`/api/v1/chats/${chatId}/messages`, data),

  getMessages: (chatId: number, params?: {
    skip?: number;
    limit?: number;
  }): Promise<Array<{
    id: number;
    role: string;
    content: string;
    created_at: string;
    metadata: any;
  }>> =>
    apiClient.get(`/api/v1/chats/${chatId}/messages`, { params }),

  updateMessage: (chatId: number, messageId: number, data: {
    content: string;
    metadata?: any;
  }): Promise<{
    id: number;
    content: string;
    updated_at: string;
  }> =>
    apiClient.put(`/api/v1/chats/${chatId}/messages/${messageId}`, data),

  deleteMessage: (chatId: number, messageId: number): Promise<{ message: string }> =>
    apiClient.delete(`/api/v1/chats/${chatId}/messages/${messageId}`),
};

// ユーザー管理API
export const userApi = {
  getProfile: (): Promise<{
    id: number;
    username: string;
    email: string;
    full_name?: string;
    department?: string;
    position?: string;
    role: string;
    status: string;
    is_active: boolean;
    created_at: string;
    last_login?: string;
  }> =>
    apiClient.get('/api/v1/users/profile'),

  updateProfile: (data: {
    full_name?: string;
    department?: string;
    position?: string;
  }): Promise<{
    id: number;
    username: string;
    email: string;
    full_name?: string;
    department?: string;
    position?: string;
    role: string;
    status: string;
    is_active: boolean;
    created_at: string;
    last_login?: string;
  }> =>
    apiClient.put('/api/v1/users/profile', data),

  getUsersList: (params?: {
    skip?: number;
    limit?: number;
    search?: string;
    role?: string;
    is_active?: boolean;
  }): Promise<Array<{
    id: number;
    username: string;
    email: string;
    full_name?: string;
    department?: string;
    position?: string;
    role: string;
    status: string;
    is_active: boolean;
    created_at: string;
    last_login?: string;
  }>> =>
    apiClient.get('/api/v1/users/list', { params }),

  getUserStats: (): Promise<{
    total_users: number;
    active_users: number;
    new_users_today: number;
    new_users_week: number;
  }> =>
    apiClient.get('/api/v1/users/stats'),

  getUserActivity: (params?: {
    days?: number;
  }): Promise<Array<{
    date: string;
    login_count: number;
    chat_count: number;
  }>> =>
    apiClient.get('/api/v1/users/activity', { params }),

  updateUserRole: (userId: number, role: string): Promise<{ message: string }> =>
    apiClient.put(`/api/v1/users/${userId}/role`, { role }),

  toggleUserStatus: (userId: number, is_active: boolean): Promise<{ message: string }> =>
    apiClient.put(`/api/v1/users/${userId}/status`, { is_active }),
};

// システム関連API
export const systemApi = {
  healthCheck: (): Promise<{ status: string; timestamp: number }> =>
    apiClient.get('/health'),

  getAuditLogs: (params?: any): Promise<any[]> =>
    apiClient.get('/api/v1/admin/audit-logs', { params }),
};

export default apiClient;