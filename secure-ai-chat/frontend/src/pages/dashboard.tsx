import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { 
  MessageSquare, 
  FileText, 
  Settings, 
  LogOut, 
  Plus, 
  Search,
  Clock,
  User,
  Shield,
  Activity
} from 'lucide-react';
import toast from 'react-hot-toast';

interface ChatSession {
  id: number;
  session_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  last_message: string | null;
}

interface UserProfile {
  id: number;
  email: string;
  full_name: string;
  company_name: string | null;
  role: string;
}

export default function Dashboard() {
  const router = useRouter();
  const [chatSessions, setChatSessions] = useState<ChatSession[]>([]);
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        router.push('/login');
        return;
      }

      // ユーザープロフィール取得
      const profileResponse = await fetch('/api/v1/auth/me', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (profileResponse.ok) {
        const profile = await profileResponse.json();
        setUserProfile(profile);
      } else {
        throw new Error('Profile fetch failed');
      }

      // チャットセッション取得
      const sessionsResponse = await fetch('/api/v1/chat/sessions', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (sessionsResponse.ok) {
        const sessions = await sessionsResponse.json();
        setChatSessions(sessions);
      } else {
        throw new Error('Sessions fetch failed');
      }
    } catch (error) {
      console.error('Data loading error:', error);
      toast.error('データの読み込みに失敗しました');
      // トークンが無効な場合はログインページに戻る
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      router.push('/login');
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    toast.success('ログアウトしました');
    router.push('/login');
  };

  const createNewChat = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('/api/v1/chat/sessions', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: '新しいチャット'
        }),
      });

      if (response.ok) {
        const newSession = await response.json();
        router.push(`/chat/${newSession.session_id}`);
      } else {
        toast.error('新しいチャットの作成に失敗しました');
      }
    } catch (error) {
      console.error('Create chat error:', error);
      toast.error('ネットワークエラーが発生しました');
    }
  };

  const filteredSessions = chatSessions.filter(session =>
    session.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (session.last_message && session.last_message.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60));

    if (diffInMinutes < 60) {
      return `${diffInMinutes}分前`;
    } else if (diffInMinutes < 1440) {
      return `${Math.floor(diffInMinutes / 60)}時間前`;
    } else {
      return date.toLocaleDateString('ja-JP');
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">データを読み込み中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* ヘッダー */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <Shield className="w-8 h-8 text-indigo-600 mr-3" />
              <h1 className="text-xl font-semibold text-gray-900">セキュアAIチャット</h1>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="flex items-center text-sm text-gray-700">
                <User className="w-4 h-4 mr-2" />
                {userProfile?.full_name}
                {userProfile?.company_name && (
                  <span className="ml-1 text-gray-500">({userProfile.company_name})</span>
                )}
              </div>
              
              <button
                onClick={handleLogout}
                className="flex items-center text-sm text-gray-700 hover:text-gray-900 transition-colors"
              >
                <LogOut className="w-4 h-4 mr-1" />
                ログアウト
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* ウェルカムセクション */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            おかえりなさい、{userProfile?.full_name}さん
          </h2>
          <p className="text-gray-600">
            安全で高性能なAIチャットをお楽しみください
          </p>
        </div>

        {/* 統計カード */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <MessageSquare className="w-8 h-8 text-blue-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">総チャット数</p>
                <p className="text-2xl font-semibold text-gray-900">{chatSessions.length}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <Activity className="w-8 h-8 text-green-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">今週のメッセージ</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {chatSessions.reduce((acc, session) => acc + session.message_count, 0)}
                </p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <Shield className="w-8 h-8 text-purple-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">セキュリティレベル</p>
                <p className="text-2xl font-semibold text-gray-900">最高</p>
              </div>
            </div>
          </div>
        </div>

        {/* チャット管理セクション */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b border-gray-200">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-medium text-gray-900">チャット履歴</h3>
              <button
                onClick={createNewChat}
                className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition-colors flex items-center"
              >
                <Plus className="w-4 h-4 mr-2" />
                新しいチャット
              </button>
            </div>
            
            {/* 検索バー */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="チャットを検索..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 pr-4 py-2 w-full border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>
          </div>

          {/* チャットリスト */}
          <div className="divide-y divide-gray-200">
            {filteredSessions.length > 0 ? (
              filteredSessions.map((session) => (
                <div
                  key={session.id}
                  onClick={() => router.push(`/chat/${session.session_id}`)}
                  className="p-6 hover:bg-gray-50 cursor-pointer transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h4 className="text-sm font-medium text-gray-900 mb-1">
                        {session.title}
                      </h4>
                      {session.last_message && (
                        <p className="text-sm text-gray-600 mb-2 line-clamp-2">
                          {session.last_message}
                        </p>
                      )}
                      <div className="flex items-center text-xs text-gray-500">
                        <Clock className="w-3 h-3 mr-1" />
                        {formatDate(session.updated_at)}
                        <span className="ml-4">
                          {session.message_count}メッセージ
                        </span>
                      </div>
                    </div>
                    <MessageSquare className="w-5 h-5 text-gray-400 ml-4" />
                  </div>
                </div>
              ))
            ) : (
              <div className="p-8 text-center">
                <MessageSquare className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600 mb-4">
                  {searchTerm ? '検索結果が見つかりません' : 'まだチャットがありません'}
                </p>
                <button
                  onClick={createNewChat}
                  className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition-colors"
                >
                  最初のチャットを始める
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}