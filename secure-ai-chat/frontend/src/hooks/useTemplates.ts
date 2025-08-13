/**
 * セキュアAIチャット - テンプレート管理フック
 */

import { useState, useEffect, useCallback } from 'react';
import { toast } from 'react-hot-toast';
import { 
  PromptTemplate, 
  TemplateCategory, 
  CreateTemplateForm, 
  TemplateStatus,
  TemplateAccessLevel,
  PaginatedResponse 
} from '@/types';
import { templateApi } from '@/utils/api';

interface UseTemplatesResult {
  templates: PromptTemplate[];
  categories: TemplateCategory[];
  loading: boolean;
  error: string | null;
  pagination: {
    page: number;
    totalPages: number;
    total: number;
    hasNext: boolean;
    hasPrev: boolean;
  };
  
  // Actions
  fetchTemplates: (params?: TemplateSearchParams) => Promise<void>;
  fetchCategories: () => Promise<void>;
  createTemplate: (data: CreateTemplateForm) => Promise<PromptTemplate | null>;
  updateTemplate: (id: number, data: Partial<CreateTemplateForm>) => Promise<PromptTemplate | null>;
  deleteTemplate: (id: number) => Promise<boolean>;
  useTemplate: (id: number, parameters: Record<string, any>) => Promise<string | null>;
  
  // Filters
  searchParams: TemplateSearchParams;
  setSearchParams: (params: Partial<TemplateSearchParams>) => void;
}

interface TemplateSearchParams {
  categoryId?: number;
  status?: TemplateStatus;
  accessLevel?: TemplateAccessLevel;
  search?: string;
  tags?: string[];
  page: number;
  limit: number;
  sortBy: string;
  sortOrder: 'asc' | 'desc';
}

const defaultSearchParams: TemplateSearchParams = {
  page: 1,
  limit: 20,
  sortBy: 'updated_at',
  sortOrder: 'desc'
};

export const useTemplates = (): UseTemplatesResult => {
  const [templates, setTemplates] = useState<PromptTemplate[]>([]);
  const [categories, setCategories] = useState<TemplateCategory[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pagination, setPagination] = useState({
    page: 1,
    totalPages: 1,
    total: 0,
    hasNext: false,
    hasPrev: false
  });
  const [searchParams, setSearchParamsState] = useState<TemplateSearchParams>(defaultSearchParams);

  const setSearchParams = useCallback((params: Partial<TemplateSearchParams>) => {
    setSearchParamsState(prev => ({
      ...prev,
      ...params,
      page: params.page ?? 1 // 検索条件が変わったら1ページ目に戻る（pageが明示的に指定されない限り）
    }));
  }, []);

  const fetchTemplates = useCallback(async (params?: TemplateSearchParams) => {
    setLoading(true);
    setError(null);

    try {
      const queryParams = params || searchParams;
      const response = await templateApi.getTemplates(queryParams);

      setTemplates(response.templates);
      setPagination({
        page: response.page,
        totalPages: response.totalPages,
        total: response.total,
        hasNext: response.hasNext,
        hasPrev: response.hasPrev
      });
    } catch (err: any) {
      const errorMessage = err.response?.data?.message || 'テンプレートの取得に失敗しました';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [searchParams]);

  const fetchCategories = useCallback(async () => {
    try {
      const response = await templateApi.getCategories();
      setCategories(response);
    } catch (err: any) {
      const errorMessage = err.response?.data?.message || 'カテゴリの取得に失敗しました';
      toast.error(errorMessage);
    }
  }, []);

  const createTemplate = useCallback(async (data: CreateTemplateForm): Promise<PromptTemplate | null> => {
    setLoading(true);
    setError(null);

    try {
      const response = await templateApi.createTemplate(data);
      toast.success('テンプレートを作成しました');
      
      // リストを再取得
      await fetchTemplates();
      
      return response;
    } catch (err: any) {
      const errorMessage = err.response?.data?.message || 'テンプレートの作成に失敗しました';
      setError(errorMessage);
      toast.error(errorMessage);
      return null;
    } finally {
      setLoading(false);
    }
  }, [fetchTemplates]);

  const updateTemplate = useCallback(async (
    id: number, 
    data: Partial<CreateTemplateForm>
  ): Promise<PromptTemplate | null> => {
    setLoading(true);
    setError(null);

    try {
      const response = await templateApi.updateTemplate(id, data);
      toast.success('テンプレートを更新しました');
      
      // リストを再取得
      await fetchTemplates();
      
      return response;
    } catch (err: any) {
      const errorMessage = err.response?.data?.message || 'テンプレートの更新に失敗しました';
      setError(errorMessage);
      toast.error(errorMessage);
      return null;
    } finally {
      setLoading(false);
    }
  }, [fetchTemplates]);

  const deleteTemplate = useCallback(async (id: number): Promise<boolean> => {
    if (!confirm('このテンプレートを削除してもよろしいですか？')) {
      return false;
    }

    setLoading(true);
    setError(null);

    try {
      await templateApi.deleteTemplate(id);
      toast.success('テンプレートを削除しました');
      
      // リストを再取得
      await fetchTemplates();
      
      return true;
    } catch (err: any) {
      const errorMessage = err.response?.data?.message || 'テンプレートの削除に失敗しました';
      setError(errorMessage);
      toast.error(errorMessage);
      return false;
    } finally {
      setLoading(false);
    }
  }, [fetchTemplates]);

  const useTemplate = useCallback(async (
    id: number, 
    parameters: Record<string, any>
  ): Promise<string | null> => {
    setLoading(true);
    setError(null);

    try {
      const response = await templateApi.useTemplate(id, parameters);
      toast.success('プロンプトを生成しました');
      return response.rendered_prompt;
    } catch (err: any) {
      const errorMessage = err.response?.data?.message || 'プロンプトの生成に失敗しました';
      setError(errorMessage);
      toast.error(errorMessage);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  // 初期データ取得
  useEffect(() => {
    fetchTemplates();
    fetchCategories();
  }, []);

  // 検索パラメータが変更されたらテンプレートを再取得
  useEffect(() => {
    fetchTemplates();
  }, [searchParams]);

  return {
    templates,
    categories,
    loading,
    error,
    pagination,
    fetchTemplates,
    fetchCategories,
    createTemplate,
    updateTemplate,
    deleteTemplate,
    useTemplate,
    searchParams,
    setSearchParams
  };
};