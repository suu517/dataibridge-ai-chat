/**
 * セキュアAIチャット - テンプレート一覧コンポーネント
 */

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Search, 
  Filter, 
  Plus, 
  Grid, 
  List, 
  ArrowUpDown,
  Tag,
  Eye,
  Edit,
  Trash2,
  Copy,
  Star,
  Clock,
  Users,
  Lock
} from 'lucide-react';
import { format } from 'date-fns';
import { ja } from 'date-fns/locale';
import { useTemplates } from '@/hooks/useTemplates';
import { PromptTemplate, TemplateAccessLevel, TemplateStatus, User } from '@/types';

interface TemplateListProps {
  onTemplateSelect?: (template: PromptTemplate) => void;
  onCreateTemplate?: () => void;
  onEditTemplate?: (template: PromptTemplate) => void;
  currentUser?: User;
}

export const TemplateList: React.FC<TemplateListProps> = ({
  onTemplateSelect,
  onCreateTemplate,
  onEditTemplate,
  currentUser
}) => {
  const {
    templates,
    categories,
    loading,
    error,
    pagination,
    searchParams,
    setSearchParams,
    deleteTemplate,
    useTemplate
  } = useTemplates();

  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [showFilters, setShowFilters] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<number | null>(null);
  const [selectedStatus, setSelectedStatus] = useState<TemplateStatus | null>(null);
  const [selectedAccessLevel, setSelectedAccessLevel] = useState<TemplateAccessLevel | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  // フィルタ適用
  const applyFilters = () => {
    setSearchParams({
      categoryId: selectedCategory || undefined,
      status: selectedStatus || undefined,
      accessLevel: selectedAccessLevel || undefined,
      search: searchTerm || undefined,
      page: 1
    });
    setShowFilters(false);
  };

  // フィルタクリア
  const clearFilters = () => {
    setSelectedCategory(null);
    setSelectedStatus(null);
    setSelectedAccessLevel(null);
    setSearchTerm('');
    setSearchParams({
      categoryId: undefined,
      status: undefined,
      accessLevel: undefined,
      search: undefined,
      page: 1
    });
    setShowFilters(false);
  };

  // ページ変更
  const handlePageChange = (newPage: number) => {
    setSearchParams({ page: newPage });
  };

  // ソート変更
  const handleSortChange = (sortBy: string) => {
    const newOrder = searchParams.sortBy === sortBy && searchParams.sortOrder === 'desc' ? 'asc' : 'desc';
    setSearchParams({ sortBy, sortOrder: newOrder });
  };

  // テンプレート使用
  const handleUseTemplate = async (template: PromptTemplate) => {
    if (onTemplateSelect) {
      onTemplateSelect(template);
    }
  };

  // アクセスレベルアイコン
  const getAccessLevelIcon = (level: TemplateAccessLevel) => {
    switch (level) {
      case TemplateAccessLevel.PUBLIC:
        return <Users className="w-4 h-4 text-green-500" />;
      case TemplateAccessLevel.DEPARTMENT:
        return <Users className="w-4 h-4 text-blue-500" />;
      case TemplateAccessLevel.ROLE:
        return <Users className="w-4 h-4 text-orange-500" />;
      case TemplateAccessLevel.PRIVATE:
        return <Lock className="w-4 h-4 text-red-500" />;
      default:
        return <Users className="w-4 h-4 text-gray-500" />;
    }
  };

  // ステータスバッジ
  const getStatusBadge = (status: TemplateStatus) => {
    const statusConfig = {
      [TemplateStatus.ACTIVE]: { color: 'bg-green-100 text-green-800', label: 'アクティブ' },
      [TemplateStatus.INACTIVE]: { color: 'bg-gray-100 text-gray-800', label: '非アクティブ' },
      [TemplateStatus.DRAFT]: { color: 'bg-yellow-100 text-yellow-800', label: '下書き' },
      [TemplateStatus.ARCHIVED]: { color: 'bg-red-100 text-red-800', label: 'アーカイブ' }
    };

    const config = statusConfig[status] || statusConfig[TemplateStatus.DRAFT];

    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${config.color}`}>
        {config.label}
      </span>
    );
  };

  // テンプレートカード
  const TemplateCard: React.FC<{ template: PromptTemplate; index: number }> = ({ template, index }) => (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
      className="bg-white rounded-lg shadow-soft hover:shadow-medium transition-all duration-200 border border-gray-200"
    >
      <div className="p-6">
        {/* ヘッダー */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-start space-x-3">
            {template.category && (
              <div 
                className="w-3 h-3 rounded-full mt-1"
                style={{ backgroundColor: template.category.color || '#6b7280' }}
              />
            )}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-1">
                {template.name}
              </h3>
              {template.description && (
                <p className="text-gray-600 text-sm line-clamp-2">
                  {template.description}
                </p>
              )}
            </div>
          </div>
          <div className="flex items-center space-x-1">
            {getAccessLevelIcon(template.access_level)}
            {getStatusBadge(template.status)}
          </div>
        </div>

        {/* メタ情報 */}
        <div className="flex items-center justify-between text-sm text-gray-500 mb-4">
          <div className="flex items-center space-x-4">
            <span className="flex items-center space-x-1">
              <Eye className="w-4 h-4" />
              <span>{template.usage_count}</span>
            </span>
            <span className="flex items-center space-x-1">
              <Clock className="w-4 h-4" />
              <span>{format(new Date(template.updated_at), 'MM/dd', { locale: ja })}</span>
            </span>
          </div>
          {template.creator && (
            <span className="text-xs">
              by {template.creator.username}
            </span>
          )}
        </div>

        {/* タグ */}
        {template.tags && template.tags.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-4">
            {template.tags.slice(0, 3).map((tag, tagIndex) => (
              <span
                key={tagIndex}
                className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded-md"
              >
                {tag}
              </span>
            ))}
            {template.tags.length > 3 && (
              <span className="px-2 py-1 text-xs bg-gray-100 text-gray-500 rounded-md">
                +{template.tags.length - 3}
              </span>
            )}
          </div>
        )}

        {/* アクション */}
        <div className="flex items-center justify-between">
          <button
            onClick={() => handleUseTemplate(template)}
            className="px-4 py-2 text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 rounded-md transition-colors"
          >
            使用する
          </button>
          
          <div className="flex items-center space-x-1">
            {template.can_edit && (
              <button
                onClick={() => onEditTemplate?.(template)}
                className="p-2 text-gray-400 hover:text-gray-600 rounded-md hover:bg-gray-100"
                title="編集"
              >
                <Edit className="w-4 h-4" />
              </button>
            )}
            <button
              className="p-2 text-gray-400 hover:text-gray-600 rounded-md hover:bg-gray-100"
              title="複製"
            >
              <Copy className="w-4 h-4" />
            </button>
            {template.can_edit && (
              <button
                onClick={() => deleteTemplate(template.id)}
                className="p-2 text-gray-400 hover:text-red-600 rounded-md hover:bg-red-50"
                title="削除"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );

  return (
    <div className="space-y-6">
      {/* ヘッダー */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">プロンプトテンプレート</h1>
          <p className="text-gray-600">効率的なAI活用のための事前定義プロンプト</p>
        </div>

        <div className="flex items-center space-x-3">
          {/* 表示モード切替 */}
          <div className="flex items-center bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-2 rounded-md transition-colors ${
                viewMode === 'grid' ? 'bg-white shadow-sm' : 'text-gray-600'
              }`}
            >
              <Grid className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-2 rounded-md transition-colors ${
                viewMode === 'list' ? 'bg-white shadow-sm' : 'text-gray-600'
              }`}
            >
              <List className="w-4 h-4" />
            </button>
          </div>

          {/* 新規作成ボタン */}
          {currentUser?.can_access_templates && (
            <button
              onClick={onCreateTemplate}
              className="flex items-center space-x-2 px-4 py-2 text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 rounded-md transition-colors"
            >
              <Plus className="w-4 h-4" />
              <span>新規作成</span>
            </button>
          )}
        </div>
      </div>

      {/* 検索・フィルタ */}
      <div className="bg-white rounded-lg shadow-soft p-4 border border-gray-200">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          {/* 検索バー */}
          <div className="flex-1 max-w-md">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="テンプレートを検索..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && applyFilters()}
                className="pl-10 pr-4 py-2 w-full border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
          </div>

          {/* フィルタ・ソート */}
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`flex items-center space-x-2 px-3 py-2 text-sm font-medium border rounded-md transition-colors ${
                showFilters 
                  ? 'bg-primary-50 text-primary-700 border-primary-200'
                  : 'text-gray-700 border-gray-300 hover:bg-gray-50'
              }`}
            >
              <Filter className="w-4 h-4" />
              <span>フィルタ</span>
            </button>

            <button
              onClick={() => handleSortChange('updated_at')}
              className="flex items-center space-x-2 px-3 py-2 text-sm font-medium text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
            >
              <ArrowUpDown className="w-4 h-4" />
              <span>更新日時</span>
            </button>
          </div>
        </div>

        {/* フィルタパネル */}
        <AnimatePresence>
          {showFilters && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mt-4 pt-4 border-t border-gray-200"
            >
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* カテゴリ */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    カテゴリ
                  </label>
                  <select
                    value={selectedCategory || ''}
                    onChange={(e) => setSelectedCategory(e.target.value ? Number(e.target.value) : null)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  >
                    <option value="">すべて</option>
                    {categories.map((category) => (
                      <option key={category.id} value={category.id}>
                        {category.name}
                      </option>
                    ))}
                  </select>
                </div>

                {/* ステータス */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    ステータス
                  </label>
                  <select
                    value={selectedStatus || ''}
                    onChange={(e) => setSelectedStatus(e.target.value as TemplateStatus || null)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  >
                    <option value="">すべて</option>
                    <option value={TemplateStatus.ACTIVE}>アクティブ</option>
                    <option value={TemplateStatus.INACTIVE}>非アクティブ</option>
                    <option value={TemplateStatus.DRAFT}>下書き</option>
                    <option value={TemplateStatus.ARCHIVED}>アーカイブ</option>
                  </select>
                </div>

                {/* アクセスレベル */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    アクセスレベル
                  </label>
                  <select
                    value={selectedAccessLevel || ''}
                    onChange={(e) => setSelectedAccessLevel(e.target.value as TemplateAccessLevel || null)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  >
                    <option value="">すべて</option>
                    <option value={TemplateAccessLevel.PUBLIC}>パブリック</option>
                    <option value={TemplateAccessLevel.DEPARTMENT}>部署限定</option>
                    <option value={TemplateAccessLevel.ROLE}>役職限定</option>
                    <option value={TemplateAccessLevel.PRIVATE}>プライベート</option>
                  </select>
                </div>
              </div>

              <div className="flex items-center justify-end space-x-3 mt-4">
                <button
                  onClick={clearFilters}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
                >
                  クリア
                </button>
                <button
                  onClick={applyFilters}
                  className="px-4 py-2 text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 rounded-md transition-colors"
                >
                  適用
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* テンプレート一覧 */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          <span className="ml-3 text-gray-600">読み込み中...</span>
        </div>
      ) : error ? (
        <div className="text-center py-12">
          <div className="text-red-600 mb-2">エラーが発生しました</div>
          <div className="text-gray-500 text-sm">{error}</div>
        </div>
      ) : templates.length === 0 ? (
        <div className="text-center py-12">
          <div className="text-gray-500 mb-4">テンプレートが見つかりません</div>
          {currentUser?.can_access_templates && (
            <button
              onClick={onCreateTemplate}
              className="text-primary-600 hover:text-primary-700 font-medium"
            >
              新しいテンプレートを作成
            </button>
          )}
        </div>
      ) : (
        <>
          {/* グリッド表示 */}
          {viewMode === 'grid' && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {templates.map((template, index) => (
                <TemplateCard key={template.id} template={template} index={index} />
              ))}
            </div>
          )}

          {/* ページネーション */}
          {pagination.totalPages > 1 && (
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-700">
                {pagination.total}件中 {(pagination.page - 1) * searchParams.limit + 1}-{Math.min(pagination.page * searchParams.limit, pagination.total)}件を表示
              </div>
              
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => handlePageChange(pagination.page - 1)}
                  disabled={!pagination.hasPrev}
                  className="px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  前へ
                </button>
                
                <span className="text-sm text-gray-700">
                  {pagination.page} / {pagination.totalPages}
                </span>
                
                <button
                  onClick={() => handlePageChange(pagination.page + 1)}
                  disabled={!pagination.hasNext}
                  className="px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  次へ
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};