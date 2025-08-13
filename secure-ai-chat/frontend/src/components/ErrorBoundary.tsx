/**
 * セキュアAIチャット - エラーバウンダリーコンポーネント
 */

import React from 'react';
import { toast } from 'react-hot-toast';

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
}

interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ComponentType<ErrorFallbackProps>;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
  showNotification?: boolean;
}

interface ErrorFallbackProps {
  error: Error | null;
  resetError: () => void;
}

class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return {
      hasError: true,
      error
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    this.setState({
      error,
      errorInfo
    });

    // エラーレポート
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // 通知表示
    if (this.props.showNotification !== false) {
      toast.error('アプリケーションエラーが発生しました');
    }

    // エラーログ送信（本番環境で有効化）
    if (process.env.NODE_ENV === 'production') {
      this.reportError(error, errorInfo);
    }

    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  private reportError = async (error: Error, errorInfo: React.ErrorInfo) => {
    try {
      // エラーレポートサービスへの送信
      const errorReport = {
        message: error.message,
        stack: error.stack,
        componentStack: errorInfo.componentStack,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        url: window.location.href
      };

      // 実際の実装では、エラーレポートサービス（Sentry等）に送信
      console.log('Error report:', errorReport);
    } catch (reportingError) {
      console.error('Failed to report error:', reportingError);
    }
  };

  private resetError = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null
    });
  };

  render() {
    if (this.state.hasError) {
      const FallbackComponent = this.props.fallback || DefaultErrorFallback;
      
      return (
        <FallbackComponent 
          error={this.state.error} 
          resetError={this.resetError}
        />
      );
    }

    return this.props.children;
  }
}

// デフォルトエラーフォールバックコンポーネント
const DefaultErrorFallback: React.FC<ErrorFallbackProps> = ({ error, resetError }) => {
  const isProduction = process.env.NODE_ENV === 'production';
  
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <div className="mx-auto h-12 w-12 text-red-500">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth={2} 
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.502 0L4.268 18.5c-.77.833.192 2.5 1.732 2.5z" 
              />
            </svg>
          </div>
          
          <h2 className="mt-6 text-3xl font-extrabold text-gray-900">
            エラーが発生しました
          </h2>
          
          <p className="mt-2 text-sm text-gray-600">
            申し訳ございませんが、予期しないエラーが発生しました。
          </p>
          
          {!isProduction && error && (
            <div className="mt-4 p-4 bg-red-50 rounded-md">
              <div className="text-left">
                <h3 className="text-sm font-medium text-red-800">
                  エラー詳細 (開発環境)
                </h3>
                <div className="mt-2 text-sm text-red-700">
                  <p className="font-mono text-xs break-all">
                    {error.message}
                  </p>
                </div>
              </div>
            </div>
          )}
          
          <div className="mt-6 space-y-2">
            <button
              onClick={resetError}
              className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
            >
              再試行
            </button>
            
            <button
              onClick={() => window.location.reload()}
              className="w-full flex justify-center py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
            >
              ページを再読み込み
            </button>
            
            <button
              onClick={() => window.location.href = '/'}
              className="w-full flex justify-center py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
            >
              ホームに戻る
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// 小さいエラーフォールバック（コンポーネント部分用）
const MinimalErrorFallback: React.FC<ErrorFallbackProps> = ({ error, resetError }) => {
  return (
    <div className="p-4 border border-red-300 rounded-md bg-red-50">
      <div className="flex items-start">
        <div className="ml-3 flex-1">
          <h3 className="text-sm font-medium text-red-800">
            コンポーネントエラー
          </h3>
          <div className="mt-2 text-sm text-red-700">
            <p>この部分でエラーが発生しました。</p>
          </div>
          <div className="mt-4">
            <button
              onClick={resetError}
              className="bg-red-100 px-3 py-1 rounded-md text-sm font-medium text-red-800 hover:bg-red-200 transition-colors"
            >
              再試行
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// HOC版エラーバウンダリー
export const withErrorBoundary = <P extends object>(
  Component: React.ComponentType<P>,
  errorFallback?: React.ComponentType<ErrorFallbackProps>
) => {
  const WrappedComponent = (props: P) => (
    <ErrorBoundary fallback={errorFallback || MinimalErrorFallback}>
      <Component {...props} />
    </ErrorBoundary>
  );

  WrappedComponent.displayName = `withErrorBoundary(${Component.displayName || Component.name})`;
  
  return WrappedComponent;
};

// フック版エラーハンドリング
export const useErrorHandler = () => {
  const [error, setError] = React.useState<Error | null>(null);

  const handleError = React.useCallback((error: Error) => {
    setError(error);
    console.error('Error caught by useErrorHandler:', error);
  }, []);

  const resetError = React.useCallback(() => {
    setError(null);
  }, []);

  // エラーが設定されたら例外として投げる
  React.useEffect(() => {
    if (error) {
      throw error;
    }
  }, [error]);

  return { handleError, resetError };
};

export default ErrorBoundary;
export { DefaultErrorFallback, MinimalErrorFallback };