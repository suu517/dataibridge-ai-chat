import { useEffect } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import Head from 'next/head';
import { Shield, MessageSquare, Lock, Zap, Users, Globe } from 'lucide-react';

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    // トークンがある場合はダッシュボードにリダイレクト
    const token = localStorage.getItem('access_token');
    if (token) {
      router.push('/dashboard');
    }
  }, [router]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <Head>
        <title>セキュアAIチャット</title>
        <meta name="description" content="企業専用のセキュアなAIチャットサービス" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      {/* ヘッダー */}
      <header className="bg-white/80 backdrop-blur-md border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <Shield className="w-8 h-8 text-indigo-600 mr-3" />
              <h1 className="text-xl font-bold text-gray-900">セキュアAIチャット</h1>
            </div>
            
            <div className="flex items-center space-x-4">
              <Link 
                href="/login" 
                className="text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium transition-colors"
              >
                ログイン
              </Link>
              <Link 
                href="/register" 
                className="bg-indigo-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-indigo-700 transition-colors"
              >
                無料で始める
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* メインコンテンツ */}
      <main>
        {/* ヒーローセクション */}
        <section className="py-20 px-4 sm:px-6 lg:px-8">
          <div className="max-w-7xl mx-auto text-center">
            <div className="mx-auto w-24 h-24 bg-indigo-100 rounded-full flex items-center justify-center mb-8">
              <Shield className="w-12 h-12 text-indigo-600" />
            </div>
            
            <h2 className="text-4xl sm:text-5xl font-bold text-gray-900 mb-6">
              企業専用の
              <span className="text-indigo-600"> セキュアAI</span>
              チャットサービス
            </h2>
            
            <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
              最高レベルのセキュリティで保護された、企業向けAI対話プラットフォーム。
              機密情報を扱う企業でも安心してご利用いただけます。
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link 
                href="/register" 
                className="bg-indigo-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-indigo-700 transition-colors flex items-center justify-center"
              >
                <MessageSquare className="w-5 h-5 mr-2" />
                今すぐ始める
              </Link>
              <Link 
                href="#features" 
                className="border border-gray-300 text-gray-700 px-8 py-3 rounded-lg font-semibold hover:bg-gray-50 transition-colors"
              >
                詳細を見る
              </Link>
            </div>
          </div>
        </section>

        {/* 機能セクション */}
        <section id="features" className="py-20 bg-white">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-16">
              <h3 className="text-3xl font-bold text-gray-900 mb-4">
                なぜセキュアAIチャットを選ぶのか？
              </h3>
              <p className="text-lg text-gray-600">
                企業が求める高いセキュリティと使いやすさを両立
              </p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {/* セキュリティ */}
              <div className="text-center p-6">
                <div className="mx-auto w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-6">
                  <Lock className="w-8 h-8 text-red-600" />
                </div>
                <h4 className="text-xl font-semibold text-gray-900 mb-4">最高レベルのセキュリティ</h4>
                <ul className="text-gray-600 space-y-2 text-left">
                  <li>• AES-256暗号化</li>
                  <li>• JWT認証</li>
                  <li>• エンドツーエンド保護</li>
                  <li>• 監査ログ記録</li>
                </ul>
              </div>
              
              {/* パフォーマンス */}
              <div className="text-center p-6">
                <div className="mx-auto w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center mb-6">
                  <Zap className="w-8 h-8 text-yellow-600" />
                </div>
                <h4 className="text-xl font-semibold text-gray-900 mb-4">高速で正確な応答</h4>
                <ul className="text-gray-600 space-y-2 text-left">
                  <li>• 最新のAI技術</li>
                  <li>• 即座のレスポンス</li>
                  <li>• カスタムテンプレート</li>
                  <li>• 文脈理解</li>
                </ul>
              </div>
              
              {/* 管理 */}
              <div className="text-center p-6">
                <div className="mx-auto w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-6">
                  <Users className="w-8 h-8 text-green-600" />
                </div>
                <h4 className="text-xl font-semibold text-gray-900 mb-4">企業向け管理機能</h4>
                <ul className="text-gray-600 space-y-2 text-left">
                  <li>• ユーザー管理</li>
                  <li>• 権限制御</li>
                  <li>• 使用状況分析</li>
                  <li>• チーム機能</li>
                </ul>
              </div>
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="py-20 bg-indigo-600">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
            <h3 className="text-3xl font-bold text-white mb-4">
              今すぐセキュアAIチャットを体験
            </h3>
            <p className="text-xl text-indigo-100 mb-8">
              無料アカウント作成で、すぐに安全なAIチャットを開始できます
            </p>
            <Link 
              href="/register" 
              className="bg-white text-indigo-600 px-8 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors inline-flex items-center"
            >
              <MessageSquare className="w-5 h-5 mr-2" />
              無料で始める
            </Link>
          </div>
        </section>
      </main>

      {/* フッター */}
      <footer className="bg-white border-t border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="text-center">
            <div className="flex items-center justify-center mb-4">
              <Shield className="w-6 h-6 text-indigo-600 mr-2" />
              <span className="font-semibold text-gray-900">セキュアAIチャット</span>
            </div>
            <p className="text-gray-600">
              企業専用のセキュアなAIチャットサービス
            </p>
            <p className="text-sm text-gray-500 mt-4">
              © 2024 Secure AI Chat. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}