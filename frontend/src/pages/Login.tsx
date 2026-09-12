import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { Mail, Lock, ArrowRight, BrainCircuit } from 'lucide-react';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    try {
      const formData = new URLSearchParams();
      formData.append('username', email.trim());
      formData.append('password', password);

      const response = await axios.post('http://localhost:8000/api/v1/auth/login', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });
      
      const loggedUser = await login(response.data.access_token);
      if (loggedUser?.role === 'PLATFORM_ADMIN') {
        navigate('/platform-admin/overview');
      } else {
        navigate('/dashboard/overview');
      }
    } catch (err: any) {
      const msg = err?.response?.data?.detail || 'Invalid email or password. Please try again.';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-gray-50 dark:bg-gray-950 selection:bg-indigo-500/30">
      {/* Left Panel - Branding & Visuals */}
      <div className="relative hidden w-1/2 lg:block overflow-hidden bg-indigo-600">
        <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1550751827-4bd374c3f58b?q=80&w=2070&auto=format&fit=crop')] bg-cover bg-center opacity-20 mix-blend-overlay"></div>
        <div className="absolute inset-0 bg-gradient-to-t from-indigo-900/90 via-indigo-800/80 to-transparent"></div>
        
        <div className="relative z-10 flex h-full flex-col justify-between p-12 text-white">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-white/20 backdrop-blur-md shadow-inner">
              <BrainCircuit className="h-7 w-7 text-white" />
            </div>
            <span className="text-2xl font-bold tracking-tight">NeuroHR <span className="text-indigo-300">X</span></span>
          </div>

          <div className="max-w-xl">
            <h1 className="mb-6 text-5xl font-extrabold leading-tight tracking-tight text-white drop-shadow-md">
              Enterprise HR <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-200 to-white">Intelligence Platform</span>
            </h1>
            <p className="text-lg text-indigo-100/90 leading-relaxed max-w-lg font-medium">
              Empower your workforce with AI-driven insights, predictive attrition modeling, and seamless talent management all in one modern platform.
            </p>
          </div>
          
          <div className="text-sm font-medium text-indigo-200/60">
            &copy; {new Date().getFullYear()} NeuroHR X. All rights reserved.
          </div>
        </div>
      </div>

      {/* Right Panel - Login Form */}
      <div className="flex w-full items-center justify-center p-8 lg:w-1/2">
        <div className="w-full max-w-md space-y-10">
          
          {/* Mobile Header (Hidden on large screens) */}
          <div className="flex flex-col items-center justify-center lg:hidden mb-12">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-600 shadow-xl mb-4">
              <BrainCircuit className="h-8 w-8 text-white" />
            </div>
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white">NeuroHR X</h2>
            <p className="text-gray-500 dark:text-gray-400 mt-2 font-medium text-center">Enterprise HR Intelligence</p>
          </div>

          <div className="space-y-3">
            <h2 className="text-3xl font-bold tracking-tight text-gray-900 dark:text-white lg:text-4xl">
              Welcome back
            </h2>
            <p className="text-gray-500 dark:text-gray-400">
              Please enter your details to access your dashboard.
            </p>
          </div>

          <form className="space-y-6" onSubmit={handleSubmit}>
            {error && (
              <div className="rounded-xl bg-red-50 dark:bg-red-900/20 p-4 border border-red-200 dark:border-red-800/50 flex items-center gap-3 animate-in fade-in slide-in-from-top-2">
                <div className="text-sm text-red-600 dark:text-red-400 font-medium">{error}</div>
              </div>
            )}
            
            <div className="space-y-5">
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300" htmlFor="email">
                  Email Address
                </label>
                <div className="relative">
                  <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                    <Mail className="h-5 w-5 text-gray-400 transition-colors group-focus-within:text-indigo-500" />
                  </div>
                  <input
                    id="email"
                    type="email"
                    required
                    className="block w-full rounded-xl border border-gray-200 bg-white/50 px-10 py-3 text-gray-900 placeholder-gray-400 transition-all focus:border-indigo-500 focus:bg-white focus:outline-none focus:ring-4 focus:ring-indigo-500/10 dark:border-gray-800 dark:bg-gray-900/50 dark:text-white dark:focus:bg-gray-900"
                    placeholder="name@company.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium text-gray-700 dark:text-gray-300" htmlFor="password">
                    Password
                  </label>
                  <a href="#" className="text-sm font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-400 dark:hover:text-indigo-300 transition-colors">
                    Forgot password?
                  </a>
                </div>
                <div className="relative">
                  <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                    <Lock className="h-5 w-5 text-gray-400 transition-colors group-focus-within:text-indigo-500" />
                  </div>
                  <input
                    id="password"
                    type="password"
                    required
                    className="block w-full rounded-xl border border-gray-200 bg-white/50 px-10 py-3 text-gray-900 placeholder-gray-400 transition-all focus:border-indigo-500 focus:bg-white focus:outline-none focus:ring-4 focus:ring-indigo-500/10 dark:border-gray-800 dark:bg-gray-900/50 dark:text-white dark:focus:bg-gray-900"
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                  />
                </div>
              </div>
            </div>

            <div className="flex items-center">
              <input
                id="remember-me"
                name="remember-me"
                type="checkbox"
                className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500 dark:border-gray-700 dark:bg-gray-900 dark:checked:bg-indigo-500"
              />
              <label htmlFor="remember-me" className="ml-2 block text-sm text-gray-700 dark:text-gray-300">
                Remember me for 30 days
              </label>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="group relative flex w-full items-center justify-center gap-2 rounded-xl bg-indigo-600 px-4 py-3.5 text-sm font-semibold text-white transition-all hover:bg-indigo-700 hover:shadow-lg hover:shadow-indigo-500/25 focus:outline-none focus:ring-4 focus:ring-indigo-500/50 disabled:opacity-70 disabled:cursor-not-allowed overflow-hidden"
            >
              <div className="absolute inset-0 w-full h-full bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:animate-[shimmer_1.5s_infinite]"></div>
              {isLoading ? 'Signing in...' : 'Sign in to account'}
              {!isLoading && <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />}
            </button>
          </form>
          
          <div className="mt-8 text-center text-sm text-gray-500 dark:text-gray-400">
            Don't have an account?{' '}
            <Link to="/register" className="font-semibold text-indigo-600 hover:text-indigo-500 dark:text-indigo-400 transition-colors">
              Create one
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
