/**
 * セキュアAIチャット - 型定義
 */

// ユーザー関連の型
export interface User {
  id: number;
  username: string;
  email: string;
  fullName?: string;
  department?: string;
  position?: string;
  role: UserRole;
  status: UserStatus;
  isActive: boolean;
  isVerified: boolean;
  lastLogin?: string;
  createdAt: string;
  updatedAt: string;
}

export enum UserRole {
  ADMIN = 'admin',
  MANAGER = 'manager',
  USER = 'user',
  VIEWER = 'viewer'
}

export enum UserStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  LOCKED = 'locked',
  PENDING = 'pending'
}

// 認証関連の型
export interface LoginRequest {
  username: string;
  password: string;
  remember?: boolean;
}

export interface LoginResponse {
  accessToken: string;
  refreshToken: string;
  user: User;
  expiresIn: number;
}

export interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

// チャット関連の型
export interface Chat {
  id: number;
  title: string;
  description?: string;
  status: ChatStatus;
  userId: number;
  aiModel: string;
  systemPrompt?: string;
  temperature: string;
  maxTokens?: number;
  metadata?: Record<string, any>;
  messageCount: number;
  createdAt: string;
  updatedAt: string;
  lastMessageAt?: string;
  messages: ChatMessage[];
}

export enum ChatStatus {
  ACTIVE = 'active',
  ARCHIVED = 'archived',
  DELETED = 'deleted'
}

export interface ChatMessage {
  id: number;
  chatId: number;
  messageType: MessageType;
  content: string;
  promptTemplateId?: number;
  aiModel?: string;
  tokensUsed?: number;
  processingTimeMs?: number;
  metadata?: Record<string, any>;
  isDeleted: boolean;
  createdAt: string;
  updatedAt: string;
}

export enum MessageType {
  USER = 'user',
  ASSISTANT = 'assistant',
  SYSTEM = 'system',
  TEMPLATE = 'template'
}

// プロンプトテンプレート関連の型
export interface PromptTemplate {
  id: number;
  name: string;
  description?: string;
  templateContent: string;
  categoryId?: number;
  createdBy: number;
  accessLevel: TemplateAccessLevel;
  allowedDepartments?: string[];
  allowedRoles?: string[];
  parameters?: TemplateParameter[];
  defaultModel?: string;
  defaultTemperature?: string;
  defaultMaxTokens?: number;
  systemMessage?: string;
  usageCount: number;
  lastUsedAt?: string;
  status: TemplateStatus;
  version: string;
  sortOrder: number;
  tags?: string[];
  createdAt: string;
  updatedAt: string;
  category?: TemplateCategory;
  creator?: User;
}

export enum TemplateStatus {
  DRAFT = 'draft',
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  ARCHIVED = 'archived'
}

export enum TemplateAccessLevel {
  PUBLIC = 'public',
  DEPARTMENT = 'department',
  ROLE = 'role',
  PRIVATE = 'private'
}

export interface TemplateParameter {
  name: string;
  type: 'text' | 'textarea' | 'number' | 'select' | 'boolean';
  label: string;
  description?: string;
  required: boolean;
  defaultValue?: any;
  options?: string[];
  validation?: {
    min?: number;
    max?: number;
    pattern?: string;
  };
}

export interface TemplateCategory {
  id: number;
  name: string;
  description?: string;
  icon?: string;
  color?: string;
  sortOrder: number;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

// API関連の型
export interface ApiResponse<T = any> {
  data?: T;
  error?: boolean;
  message?: string;
  status_code?: number;
  timestamp?: number;
}

export interface PaginationParams {
  page?: number;
  limit?: number;
  sort?: string;
  order?: 'asc' | 'desc';
  search?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  totalPages: number;
  hasNext: boolean;
  hasPrev: boolean;
}

// UI関連の型
export interface LoadingState {
  [key: string]: boolean;
}

export interface NotificationMessage {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export interface ChatConfig {
  model: string;
  temperature: number;
  maxTokens?: number;
  systemPrompt?: string;
}

// WebSocket関連の型
export interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: number;
}

export interface ChatMessageEvent extends WebSocketMessage {
  type: 'chat_message';
  data: {
    chatId: number;
    message: ChatMessage;
  };
}

export interface TypingEvent extends WebSocketMessage {
  type: 'typing';
  data: {
    chatId: number;
    userId: number;
    isTyping: boolean;
  };
}

// フォーム関連の型
export interface CreateChatForm {
  title: string;
  description?: string;
  model: string;
  temperature: number;
  maxTokens?: number;
  systemPrompt?: string;
}

export interface SendMessageForm {
  message: string;
  templateId?: number;
  templateParams?: Record<string, any>;
}

export interface CreateTemplateForm {
  name: string;
  description?: string;
  templateContent: string;
  categoryId?: number;
  accessLevel: TemplateAccessLevel;
  allowedDepartments?: string[];
  allowedRoles?: string[];
  parameters?: TemplateParameter[];
  defaultModel?: string;
  defaultTemperature?: string;
  defaultMaxTokens?: number;
  systemMessage?: string;
  tags?: string[];
}

// エラー関連の型
export interface ValidationError {
  field: string;
  message: string;
}

export interface ApiError {
  message: string;
  code?: string;
  details?: ValidationError[];
}

// 設定関連の型
export interface AppConfig {
  apiUrl: string;
  wsUrl: string;
  appName: string;
  version: string;
  features: {
    registration: boolean;
    fileUpload: boolean;
    templateManagement: boolean;
    userManagement: boolean;
  };
}