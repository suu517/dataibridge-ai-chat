import { useState } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { User, Mail, Lock, Building, Eye, EyeOff, Shield } from 'lucide-react';
import toast from 'react-hot-toast';

const registerSchema = z.object({
  full_name: z.string().min(2, '氏名は2文字以上で入力してください'),
  email: z.string().email('有効なメールアドレスを入力してください'),
  company_name: z.string().optional(),
  password: z.string()
    .min(8, 'パスワードは8文字以上で入力してください')
    .regex(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/, '大文字、小文字、数字を含む必要があります'),
  confirm_password: z.string(),
}).refine((data) => data.password === data.confirm_password, {
  message: "パスワードが一致しません",
  path: ["confirm_password"],
});

type RegisterForm = z.infer<typeof registerSchema>;

export default function Register() {
  const router = useRouter();
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
  });

  const onSubmit = async (data: RegisterForm) => {
    setIsLoading(true);
    
    try {
      const response = await fetch('/api/v1/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          full_name: data.full_name,
          email: data.email,
          company_name: data.company_name || null,
          password: data.password,
        }),
      });

      if (response.ok) {
        const result = await response.json();
        toast.success('アカウントが作成されました！ログインページに移動します...');
        
        // 自動的にログインページに遷移
        setTimeout(() => {
          router.push('/login');
        }, 2000);
      } else {
        const error = await response.json();
        toast.error(error.detail || '登録に失敗しました');
      }
    } catch (error) {
      console.error('Registration error:', error);
      toast.error('ネットワークエラーが発生しました');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-8">
        {/* ヘッダー */}
        <div className="text-center mb-8">
          <div className="mx-auto w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mb-4">
            <Shield className="w-8 h-8 text-emerald-600" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">新規アカウント作成</h1>
          <p className="text-gray-600 mt-2">セキュアAIチャットを始める</p>
        </div>

        {/* 登録フォーム */}
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
          {/* 氏名 */}
          <div>
            <label htmlFor="full_name" className="block text-sm font-medium text-gray-700 mb-2">
              氏名 <span className="text-red-500">*</span>
            </label>
            <div className="relative">
              <User className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                {...register('full_name')}
                type="text"
                id="full_name"
                className={`pl-10 pr-4 py-3 w-full border rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors ${
                  errors.full_name ? 'border-red-300' : 'border-gray-300'
                }`}
                placeholder="山田 太郎"
                disabled={isLoading}
              />
            </div>
            {errors.full_name && (
              <p className="mt-1 text-sm text-red-600">{errors.full_name.message}</p>
            )}
          </div>

          {/* メールアドレス */}
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
              メールアドレス <span className="text-red-500">*</span>
            </label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                {...register('email')}
                type="email"
                id="email"
                className={`pl-10 pr-4 py-3 w-full border rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors ${
                  errors.email ? 'border-red-300' : 'border-gray-300'
                }`}
                placeholder="your.email@company.com"
                disabled={isLoading}
              />
            </div>
            {errors.email && (
              <p className="mt-1 text-sm text-red-600">{errors.email.message}</p>
            )}
          </div>

          {/* 会社名 */}
          <div>
            <label htmlFor="company_name" className="block text-sm font-medium text-gray-700 mb-2">
              会社名（任意）
            </label>
            <div className="relative">
              <Building className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                {...register('company_name')}
                type="text"
                id="company_name"
                className="pl-10 pr-4 py-3 w-full border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors"
                placeholder="株式会社サンプル"
                disabled={isLoading}
              />
            </div>
          </div>

          {/* パスワード */}
          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
              パスワード <span className="text-red-500">*</span>
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                {...register('password')}
                type={showPassword ? 'text' : 'password'}
                id="password"
                className={`pl-10 pr-12 py-3 w-full border rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors ${
                  errors.password ? 'border-red-300' : 'border-gray-300'
                }`}
                placeholder="8文字以上（大小英数字含む）"
                disabled={isLoading}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400 hover:text-gray-600 transition-colors"
                disabled={isLoading}
              >
                {showPassword ? <EyeOff /> : <Eye />}
              </button>
            </div>
            {errors.password && (
              <p className="mt-1 text-sm text-red-600">{errors.password.message}</p>
            )}
          </div>

          {/* パスワード確認 */}
          <div>
            <label htmlFor="confirm_password" className="block text-sm font-medium text-gray-700 mb-2">
              パスワード確認 <span className="text-red-500">*</span>
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                {...register('confirm_password')}
                type={showConfirmPassword ? 'text' : 'password'}
                id="confirm_password"
                className={`pl-10 pr-12 py-3 w-full border rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors ${
                  errors.confirm_password ? 'border-red-300' : 'border-gray-300'
                }`}
                placeholder="パスワードを再入力"
                disabled={isLoading}
              />
              <button
                type="button"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400 hover:text-gray-600 transition-colors"
                disabled={isLoading}
              >
                {showConfirmPassword ? <EyeOff /> : <Eye />}
              </button>
            </div>
            {errors.confirm_password && (
              <p className="mt-1 text-sm text-red-600">{errors.confirm_password.message}</p>
            )}
          </div>

          {/* 登録ボタン */}
          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-emerald-600 text-white py-3 rounded-lg font-medium hover:bg-emerald-700 focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <div className="flex items-center justify-center">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                アカウント作成中...
              </div>
            ) : (
              'アカウント作成'
            )}
          </button>
        </form>

        {/* フッター */}
        <div className="mt-6 text-center">
          <p className="text-sm text-gray-600">
            既にアカウントをお持ちですか？{' '}
            <Link href="/login" className="text-emerald-600 hover:text-emerald-800 font-medium">
              ログイン
            </Link>
          </p>
        </div>

        {/* セキュリティ情報 */}
        <div className="mt-6 bg-gray-50 rounded-lg p-4">
          <div className="flex items-start text-sm text-gray-600">
            <Shield className="w-4 h-4 mr-2 mt-0.5 flex-shrink-0" />
            <div>
              <p className="font-medium mb-1">セキュリティ保護</p>
              <ul className="text-xs space-y-1">
                <li>• パスワードはbcryptで暗号化</li>
                <li>• 全通信はSSL/TLS保護</li>
                <li>• 個人情報は厳重に管理</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}