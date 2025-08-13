import { useState } from 'react';
import Head from 'next/head';
import Link from 'next/link';

export default function Search() {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [searchHistory, setSearchHistory] = useState([
    { id: 1, query: 'JavaScriptの非同期処理について', timestamp: '2025-08-07T12:00:00Z', results: 5 },
    { id: 2, query: 'Reactのベストプラクティス', timestamp: '2025-08-07T11:30:00Z', results: 8 },
    { id: 3, query: 'データベース設計のポイント', timestamp: '2025-08-07T11:00:00Z', results: 12 },
  ]);

  const performSearch = async () => {
    if (!searchQuery.trim() || isSearching) return;

    setIsSearching(true);

    try {
      // デモ検索結果を生成
      const demoResults = [
        {
          id: 1,
          title: `"${searchQuery}" に関する詳細解説`,
          content: `${searchQuery}について詳しく説明します。この情報は企業の知識ベースから検索された結果です。`,
          source: '内部ドキュメント',
          confidence: 95,
          timestamp: new Date().toISOString()
        },
        {
          id: 2,
          title: `${searchQuery}のベストプラクティス`,
          content: `実際のプロジェクトで${searchQuery}を使用する際の推奨事項とガイドラインです。`,
          source: 'プロジェクト資料',
          confidence: 88,
          timestamp: new Date().toISOString()
        },
        {
          id: 3,
          title: `${searchQuery}の応用例`,
          content: `${searchQuery}を活用した具体的な事例と実装例を紹介します。`,
          source: 'ケーススタディ',
          confidence: 92,
          timestamp: new Date().toISOString()
        }
      ];

      // 検索履歴に追加
      const newHistoryItem = {
        id: Date.now(),
        query: searchQuery,
        timestamp: new Date().toISOString(),
        results: demoResults.length
      };
      setSearchHistory(prev => [newHistoryItem, ...prev.slice(0, 9)]); // 最新10件を保持

      setSearchResults(demoResults);
    } catch (error) {
      console.error('Search error:', error);
      setSearchResults([{
        id: 'error',
        title: '検索エラー',
        content: '検索中にエラーが発生しました。しばらく後に再試行してください。',
        source: 'システム',
        confidence: 0,
        timestamp: new Date().toISOString()
      }]);
    }

    setIsSearching(false);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      performSearch();
    }
  };

  const clearResults = () => {
    setSearchResults([]);
    setSearchQuery('');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Head>
        <title>知識検索 - セキュアAIチャット</title>
        <meta name="description" content="企業の知識ベースを安全に検索" />
      </Head>

      {/* ヘッダー */}
      <header className="bg-white shadow-sm border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between max-w-6xl mx-auto">
          <div className="flex items-center space-x-4">
            <Link href="/" className="text-blue-600 hover:text-blue-800">
              ← ホームに戻る
            </Link>
            <h1 className="text-2xl font-semibold text-gray-900">
              🔍 知識検索
            </h1>
          </div>
          
          <Link 
            href="/chat"
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            AIチャットに切り替え
          </Link>
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-6 py-8">
        {/* 検索フォーム */}
        <div className="mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex space-x-4">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="知識ベースを検索..."
                className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={isSearching}
              />
              <button
                onClick={performSearch}
                disabled={!searchQuery.trim() || isSearching}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isSearching ? '検索中...' : '検索'}
              </button>
              {searchResults.length > 0 && (
                <button
                  onClick={clearResults}
                  className="px-6 py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                >
                  クリア
                </button>
              )}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* 検索結果 */}
          <div className="lg:col-span-2">
            {searchResults.length > 0 && (
              <div className="mb-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">
                  検索結果 ({searchResults.length}件)
                </h2>
                <div className="space-y-4">
                  {searchResults.map((result) => (
                    <div key={result.id} className="bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow">
                      <div className="flex items-start justify-between mb-2">
                        <h3 className="text-lg font-semibold text-gray-900 flex-1">
                          {result.title}
                        </h3>
                        <div className="flex items-center space-x-2 text-sm text-gray-500 ml-4">
                          <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">
                            {result.source}
                          </span>
                          {result.confidence > 0 && (
                            <span className={`px-2 py-1 rounded text-xs ${
                              result.confidence >= 90 ? 'bg-green-100 text-green-800' :
                              result.confidence >= 70 ? 'bg-yellow-100 text-yellow-800' :
                              'bg-red-100 text-red-800'
                            }`}>
                              信頼度: {result.confidence}%
                            </span>
                          )}
                        </div>
                      </div>
                      
                      <p className="text-gray-700 mb-3">
                        {result.content}
                      </p>
                      
                      <div className="text-sm text-gray-500">
                        {new Date(result.timestamp).toLocaleString('ja-JP')}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 検索前の説明 */}
            {searchResults.length === 0 && !isSearching && (
              <div className="bg-white rounded-lg shadow p-8 text-center">
                <div className="text-6xl mb-4">🔍</div>
                <h2 className="text-2xl font-semibold text-gray-900 mb-4">企業知識ベース検索</h2>
                <p className="text-gray-600 mb-6">
                  内部ドキュメント、プロジェクト資料、ベストプラクティスなどを安全に検索できます。
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-left">
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <h3 className="font-semibold text-blue-900 mb-2">🔒 セキュア検索</h3>
                    <p className="text-blue-800 text-sm">暗号化された検索で機密情報を保護</p>
                  </div>
                  <div className="bg-green-50 p-4 rounded-lg">
                    <h3 className="font-semibold text-green-900 mb-2">🎯 高精度</h3>
                    <p className="text-green-800 text-sm">AIによる関連度の高い検索結果</p>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* 検索履歴サイドバー */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">📚 検索履歴</h3>
              <div className="space-y-3">
                {searchHistory.map((item) => (
                  <div key={item.id} className="border-b border-gray-100 pb-3 last:border-b-0 last:pb-0">
                    <button
                      onClick={() => setSearchQuery(item.query)}
                      className="text-left w-full hover:text-blue-600 transition-colors"
                    >
                      <div className="font-medium text-sm text-gray-900 mb-1">
                        {item.query}
                      </div>
                      <div className="text-xs text-gray-500">
                        {new Date(item.timestamp).toLocaleDateString('ja-JP')} • {item.results}件
                      </div>
                    </button>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-blue-50 rounded-lg p-6 mt-6">
              <h4 className="font-semibold text-blue-900 mb-2">💡 検索のコツ</h4>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>• 具体的なキーワードを使用</li>
                <li>• 複数の単語で絞り込み</li>
                <li>• 関連用語も試してみる</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}