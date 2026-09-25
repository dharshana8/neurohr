import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { 
  Mail, Lock, ArrowRight, BrainCircuit, ShieldCheck, 
  Building2, CheckCircle2, Sparkles, X, Info
} from 'lucide-react';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isDemoModalOpen, setIsDemoModalOpen] = useState(false);
  const [demoSubmitted, setDemoSubmitted] = useState(false);
  const [demoForm, setDemoForm] = useState({
    fullName: '',
    workEmail: '',
    companyName: '',
    teamSize: '51-200',
    notes: ''
  });

  const { login } = useAuth();
  const navigate = useNavigate();

  const handleQuickFill = (roleEmail: string, rolePass: string) => {
    setEmail(roleEmail);
    setPassword(rolePass);
    setError('');
  };

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

  const handleDemoSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setDemoSubmitted(true);
    setTimeout(() => {
      setDemoSubmitted(false);
      setIsDemoModalOpen(false);
      setDemoForm({ fullName: '', workEmail: '', companyName: '', teamSize: '51-200', notes: '' });
    }, 2500);
  };

  return (
    <div className="flex min-h-screen bg-gray-50 dark:bg-gray-950 selection:bg-indigo-500/30">
      {/* Left Panel - Enterprise Branding */}
      <div className="relative hidden w-1/2 lg:block overflow-hidden bg-indigo-900">
        <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1550751827-4bd374c3f58b?q=80&w=2070&auto=format&fit=crop')] bg-cover bg-center opacity-25 mix-blend-overlay"></div>
        <div className="absolute inset-0 bg-gradient-to-t from-indigo-950/95 via-indigo-900/85 to-indigo-800/80"></div>
        
        <div className="relative z-10 flex h-full flex-col justify-between p-12 text-white">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-white/20 backdrop-blur-md shadow-inner">
              <BrainCircuit className="h-7 w-7 text-white" />
            </div>
            <span className="text-2xl font-bold tracking-tight">NeuroHR <span className="text-indigo-300">X</span></span>
          </div>

          <div className="max-w-xl space-y-6">
            <div className="inline-flex items-center gap-2 rounded-full border border-indigo-400/30 bg-indigo-500/20 px-3.5 py-1 text-xs font-semibold tracking-wide text-indigo-200 backdrop-blur-md">
              <ShieldCheck className="h-4 w-4 text-emerald-400" />
              ENTERPRISE MULTI-TENANT ARCHITECTURE
            </div>

            <h1 className="text-5xl font-extrabold leading-tight tracking-tight text-white drop-shadow-md">
              Intelligent Workforce <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-200 via-white to-purple-200">Governance Platform</span>
            </h1>
            <p className="text-lg text-indigo-100/90 leading-relaxed max-w-lg font-medium">
              High-precision predictive attrition modeling, talent pipeline intelligence, and automated HR operations secured by tenant isolation.
            </p>

            <div className="grid grid-cols-2 gap-4 pt-4 border-t border-indigo-700/50">
              <div className="rounded-xl bg-white/5 p-4 border border-white/10 backdrop-blur-sm">
                <div className="text-2xl font-bold text-white">99.98%</div>
                <div className="text-xs font-medium text-indigo-200/80 mt-1">Tenant Data Isolation</div>
              </div>
              <div className="rounded-xl bg-white/5 p-4 border border-white/10 backdrop-blur-sm">
                <div className="text-2xl font-bold text-white">AI-Powered</div>
                <div className="text-xs font-medium text-indigo-200/80 mt-1">Skill Gap & Sentiment Analytics</div>
              </div>
            </div>
          </div>
          
          <div className="flex items-center justify-between text-xs font-medium text-indigo-200/60 border-t border-indigo-800/60 pt-4">
            <span>&copy; {new Date().getFullYear()} NeuroHR X. All rights reserved.</span>
            <span>Restricted Access &bull; SOC-2 Compliant</span>
          </div>
        </div>
      </div>

      {/* Right Panel - Login Form */}
      <div className="flex w-full items-center justify-center p-6 lg:w-1/2">
        <div className="w-full max-w-md space-y-8">
          
          {/* Mobile Header */}
          <div className="flex flex-col items-center justify-center lg:hidden mb-8">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-600 shadow-xl mb-4">
              <BrainCircuit className="h-8 w-8 text-white" />
            </div>
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white">NeuroHR X</h2>
            <p className="text-gray-500 dark:text-gray-400 mt-1 font-medium text-center text-sm">Enterprise HR Intelligence</p>
          </div>

          <div className="space-y-2">
            <div className="inline-flex items-center gap-1.5 rounded-md bg-indigo-50 dark:bg-indigo-950/60 px-2.5 py-1 text-xs font-medium text-indigo-700 dark:text-indigo-300 border border-indigo-200/60 dark:border-indigo-800/60">
              <ShieldCheck className="h-3.5 w-3.5" />
              Invitation &bull; Enterprise Access
            </div>
            <h2 className="text-3xl font-bold tracking-tight text-gray-900 dark:text-white lg:text-4xl">
              Workspace Sign In
            </h2>
            <p className="text-gray-500 dark:text-gray-400 text-sm">
              Enter the credentials provisioned for your organization.
            </p>
          </div>

          {/* Quick Credential Helper Banner */}
          <div className="rounded-xl border border-indigo-100 dark:border-indigo-900/60 bg-indigo-50/70 dark:bg-indigo-950/40 p-3.5 text-xs text-indigo-950 dark:text-indigo-200 space-y-2">
            <div className="flex items-center justify-between font-semibold">
              <span className="flex items-center gap-1.5 text-indigo-700 dark:text-indigo-300">
                <Info className="h-3.5 w-3.5" /> Demo &amp; Sandbox Quick Fill:
              </span>
              <span className="text-[10px] text-gray-500 dark:text-gray-400 font-mono">pwd: admin</span>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => handleQuickFill('admin@neurohr.com', 'admin')}
                className="rounded-lg bg-white dark:bg-gray-800 px-2.5 py-1.5 font-medium text-gray-700 dark:text-gray-200 shadow-sm border border-gray-200 dark:border-gray-700 hover:border-indigo-500 text-left transition-all hover:scale-[1.02] active:scale-[0.98]"
              >
                <div className="text-[10px] font-bold text-indigo-600 dark:text-indigo-400 uppercase tracking-wider">SuperAdmin</div>
                <div className="truncate text-[11px]">admin@neurohr.com</div>
              </button>
              <button
                type="button"
                onClick={() => handleQuickFill('admin@acme.com', 'admin')}
                className="rounded-lg bg-white dark:bg-gray-800 px-2.5 py-1.5 font-medium text-gray-700 dark:text-gray-200 shadow-sm border border-gray-200 dark:border-gray-700 hover:border-indigo-500 text-left transition-all hover:scale-[1.02] active:scale-[0.98]"
              >
                <div className="text-[10px] font-bold text-emerald-600 dark:text-emerald-400 uppercase tracking-wider">Acme HR Admin</div>
                <div className="truncate text-[11px]">admin@acme.com</div>
              </button>
            </div>
          </div>

          <form className="space-y-5" onSubmit={handleSubmit}>
            {error && (
              <div className="rounded-xl bg-red-50 dark:bg-red-900/20 p-3.5 border border-red-200 dark:border-red-800/50 flex items-center gap-2 text-xs text-red-600 dark:text-red-400 font-medium animate-in fade-in">
                {error}
              </div>
            )}
            
            <div className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-gray-700 dark:text-gray-300" htmlFor="email">
                  Work Email Address
                </label>
                <div className="relative">
                  <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                    <Mail className="h-4 w-4 text-gray-400" />
                  </div>
                  <input
                    id="email"
                    type="email"
                    required
                    className="block w-full rounded-xl border border-gray-200 bg-white px-9 py-2.5 text-sm text-gray-900 placeholder-gray-400 transition-all focus:border-indigo-500 focus:outline-none focus:ring-4 focus:ring-indigo-500/10 dark:border-gray-800 dark:bg-gray-900 dark:text-white"
                    placeholder="admin@company.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-semibold text-gray-700 dark:text-gray-300" htmlFor="password">
                    Password
                  </label>
                  <span className="text-xs text-gray-400 cursor-not-allowed">
                    Managed by Org Admin
                  </span>
                </div>
                <div className="relative">
                  <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                    <Lock className="h-4 w-4 text-gray-400" />
                  </div>
                  <input
                    id="password"
                    type="password"
                    required
                    className="block w-full rounded-xl border border-gray-200 bg-white px-9 py-2.5 text-sm text-gray-900 placeholder-gray-400 transition-all focus:border-indigo-500 focus:outline-none focus:ring-4 focus:ring-indigo-500/10 dark:border-gray-800 dark:bg-gray-900 dark:text-white"
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                  />
                </div>
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="group relative flex w-full items-center justify-center gap-2 rounded-xl bg-indigo-600 px-4 py-3 text-sm font-semibold text-white transition-all hover:bg-indigo-700 hover:shadow-lg hover:shadow-indigo-500/25 focus:outline-none focus:ring-4 focus:ring-indigo-500/50 disabled:opacity-70 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Signing in...' : 'Sign In to Workspace'}
              {!isLoading && <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />}
            </button>
          </form>
          
          {/* Restricted Enterprise Onboarding Notice */}
          <div className="pt-4 border-t border-gray-100 dark:border-gray-800/80 text-center space-y-2">
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Accounts are created exclusively by NeuroHR Platform Administrators.
            </p>
            <div className="flex items-center justify-center gap-1.5 text-xs">
              <span className="text-gray-600 dark:text-gray-400">Want to onboard your organization?</span>
              <button
                type="button"
                onClick={() => setIsDemoModalOpen(true)}
                className="font-semibold text-indigo-600 hover:text-indigo-500 dark:text-indigo-400 hover:underline flex items-center gap-1"
              >
                <Sparkles className="h-3 w-3" />
                Request Enterprise Access
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Enterprise Request Access / Demo Modal */}
      {isDemoModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in">
          <div className="relative w-full max-w-lg rounded-2xl bg-white dark:bg-gray-900 p-6 shadow-2xl border border-gray-200 dark:border-gray-800 space-y-6">
            <button
              onClick={() => setIsDemoModalOpen(false)}
              className="absolute right-4 top-4 rounded-lg p-1.5 text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-600 transition-colors"
            >
              <X className="h-5 w-5" />
            </button>

            {demoSubmitted ? (
              <div className="py-8 text-center space-y-4">
                <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400">
                  <CheckCircle2 className="h-8 w-8" />
                </div>
                <h3 className="text-xl font-bold text-gray-900 dark:text-white">Request Submitted</h3>
                <p className="text-sm text-gray-500 dark:text-gray-400 max-w-sm mx-auto">
                  Thank you! A NeuroHR Enterprise Onboarding Specialist will contact you within 24 hours to provision your company tenant.
                </p>
              </div>
            ) : (
              <>
                <div className="space-y-1.5">
                  <div className="inline-flex items-center gap-1.5 text-xs font-semibold text-indigo-600 dark:text-indigo-400">
                    <Building2 className="h-4 w-4" />
                    ENTERPRISE ONBOARDING INQUIRY
                  </div>
                  <h3 className="text-2xl font-bold text-gray-900 dark:text-white">
                    Request Workspace Provisioning
                  </h3>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    Leave your organization details and our team will set up your dedicated tenant workspace.
                  </p>
                </div>

                <form onSubmit={handleDemoSubmit} className="space-y-4">
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1">
                      <label className="text-xs font-medium text-gray-700 dark:text-gray-300">Your Full Name</label>
                      <input
                        type="text"
                        required
                        className="w-full rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                        placeholder="Sarah Jenkins"
                        value={demoForm.fullName}
                        onChange={(e) => setDemoForm({ ...demoForm, fullName: e.target.value })}
                      />
                    </div>
                    <div className="space-y-1">
                      <label className="text-xs font-medium text-gray-700 dark:text-gray-300">Work Email</label>
                      <input
                        type="email"
                        required
                        className="w-full rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                        placeholder="sarah@enterprise.com"
                        value={demoForm.workEmail}
                        onChange={(e) => setDemoForm({ ...demoForm, workEmail: e.target.value })}
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1">
                      <label className="text-xs font-medium text-gray-700 dark:text-gray-300">Company Name</label>
                      <input
                        type="text"
                        required
                        className="w-full rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                        placeholder="Global Dynamics Inc."
                        value={demoForm.companyName}
                        onChange={(e) => setDemoForm({ ...demoForm, companyName: e.target.value })}
                      />
                    </div>
                    <div className="space-y-1">
                      <label className="text-xs font-medium text-gray-700 dark:text-gray-300">Workforce Size</label>
                      <select
                        className="w-full rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                        value={demoForm.teamSize}
                        onChange={(e) => setDemoForm({ ...demoForm, teamSize: e.target.value })}
                      >
                        <option value="1-50">1 - 50 Employees</option>
                        <option value="51-200">51 - 200 Employees</option>
                        <option value="201-1000">201 - 1,000 Employees</option>
                        <option value="1000+">1,000+ Enterprise</option>
                      </select>
                    </div>
                  </div>

                  <div className="space-y-1">
                    <label className="text-xs font-medium text-gray-700 dark:text-gray-300">Key Priorities / Notes (Optional)</label>
                    <textarea
                      rows={2}
                      className="w-full rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      placeholder="e.g., Attrition forecasting, recruitment automation, ERP sync..."
                      value={demoForm.notes}
                      onChange={(e) => setDemoForm({ ...demoForm, notes: e.target.value })}
                    />
                  </div>

                  <button
                    type="submit"
                    className="w-full rounded-xl bg-indigo-600 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-600/20 hover:bg-indigo-700 transition-all flex items-center justify-center gap-2"
                  >
                    Submit Access Request
                    <ArrowRight className="h-4 w-4" />
                  </button>
                </form>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

