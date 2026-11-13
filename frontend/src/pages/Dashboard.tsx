import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { useNavigate, Link, Outlet, useLocation } from 'react-router-dom';
import axios from 'axios';
import {
  LayoutDashboard, Users, Brain, Upload, Briefcase, UserCheck,
  LogOut, Sun, Moon, ChevronRight, TrendingUp, TrendingDown,
  AlertTriangle, Activity, Bell, Menu, X, Play, Target, Compass, Sparkles,
  Smile, MessageSquare, Settings as SettingsIcon, Building2, Layers, FlaskConical, Calendar
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  AreaChart, Area, PieChart, Pie, Cell,
} from 'recharts';

// ─── Types ───────────────────────────────────────────────────────────────────
interface Stats {
  total_employees: number;
  high_attrition_risk: number;
  avg_performance: number;
  avg_engagement: number;
}

interface Employee {
  department: string;
  joining_date: string;
  performance_score: number;
  engagement_score: number;
}

// ─── Helpers ─────────────────────────────────────────────────────────────────
function getInitials(email: string) {
  return email?.split('@')[0]?.slice(0, 2).toUpperCase() ?? 'U';
}

function getGreeting() {
  const h = new Date().getHours();
  if (h < 12) return 'Good morning';
  if (h < 17) return 'Good afternoon';
  return 'Good evening';
}

// ─── Stat Card ───────────────────────────────────────────────────────────────
function StatCard({
  label, value, icon, gradient, trend, trendLabel, loading,
}: {
  label: string;
  value: string | number;
  icon: React.ReactNode;
  gradient: string;
  trend?: 'up' | 'down' | 'neutral';
  trendLabel?: string;
  loading?: boolean;
}) {
  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 border border-gray-100 dark:border-gray-700 shadow-sm">
        <div className="skeleton h-4 w-24 mb-4" />
        <div className="skeleton h-8 w-16 mb-2" />
        <div className="skeleton h-3 w-20" />
      </div>
    );
  }
  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 border border-gray-100 dark:border-gray-700 shadow-sm card-hover group">
      <div className="flex items-start justify-between mb-4">
        <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">{label}</p>
        <div className={`p-2.5 rounded-xl ${gradient} shadow-sm`}>
          {icon}
        </div>
      </div>
      <p className="text-3xl font-bold text-gray-900 dark:text-white count-animate">{value}</p>
      {trendLabel && (
        <div className="flex items-center gap-1 mt-2">
          {trend === 'up' && <TrendingUp className="w-3.5 h-3.5 text-emerald-500" />}
          {trend === 'down' && <TrendingDown className="w-3.5 h-3.5 text-red-500" />}
          <span className={`text-xs font-medium ${trend === 'up' ? 'text-emerald-600' : trend === 'down' ? 'text-red-500' : 'text-gray-400'}`}>
            {trendLabel}
          </span>
        </div>
      )}
    </div>
  );
}

// ─── Nav Item ────────────────────────────────────────────────────────────────
function NavItem({ to, icon, label, active }: { to: string; icon: React.ReactNode; label: string; active: boolean }) {
  return (
    <Link
      to={to}
      className={`nav-item flex items-center gap-3 px-4 py-2.5 mx-3 rounded-xl text-sm font-medium transition-all ${
        active
          ? 'bg-indigo-500/20 text-indigo-300 shadow-sm'
          : 'text-slate-400 hover:text-white hover:bg-white/5'
      }`}
    >
      <span className={`flex-shrink-0 ${active ? 'text-indigo-400' : ''}`}>{icon}</span>
      <span>{label}</span>
      {active && <ChevronRight className="w-3.5 h-3.5 ml-auto text-indigo-400" />}
    </Link>
  );
}

// ─── Section Label ───────────────────────────────────────────────────────────
function SectionLabel({ label }: { label: string }) {
  return (
    <div className="px-7 pt-5 pb-1">
      <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">{label}</p>
    </div>
  );
}

// ─── Overview Page ───────────────────────────────────────────────────────────
function OverviewPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState<Stats>({ total_employees: 0, high_attrition_risk: 0, avg_performance: 0, avg_engagement: 0 });
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [loadingStats, setLoadingStats] = useState(true);
  const [loadingEmployees, setLoadingEmployees] = useState(true);

  useEffect(() => {
    axios.get('http://localhost:8000/api/v1/workforce/stats')
      .then(r => setStats(r.data))
      .catch(() => {})
      .finally(() => setLoadingStats(false));

    axios.get('http://localhost:8000/api/v1/workforce/employees')
      .then(r => setEmployees(r.data))
      .catch(() => {})
      .finally(() => setLoadingEmployees(false));
  }, []);

  // Department breakdown
  const deptMap: Record<string, number> = {};
  employees.forEach(e => {
    deptMap[e.department] = (deptMap[e.department] || 0) + 1;
  });
  const deptData = Object.entries(deptMap)
    .map(([dept, count]) => ({ dept: dept.length > 12 ? dept.slice(0, 12) + '…' : dept, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 8);

  // Hiring trend (group by year-month of joining_date)
  const hireMap: Record<string, number> = {};
  employees.forEach(e => {
    if (e.joining_date) {
      const d = new Date(e.joining_date);
      const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
      hireMap[key] = (hireMap[key] || 0) + 1;
    }
  });
  const hireData = Object.entries(hireMap)
    .sort(([a], [b]) => a.localeCompare(b))
    .slice(-12)
    .map(([month, hires]) => ({ month: month.slice(5), hires }));

  // Performance distribution
  const perfBuckets = [
    { range: '1-2', count: 0, color: '#ef4444' },
    { range: '2-3', count: 0, color: '#f59e0b' },
    { range: '3-4', count: 0, color: '#6366f1' },
    { range: '4-5', count: 0, color: '#10b981' },
  ];
  employees.forEach(e => {
    if (e.performance_score <= 2) perfBuckets[0].count++;
    else if (e.performance_score <= 3) perfBuckets[1].count++;
    else if (e.performance_score <= 4) perfBuckets[2].count++;
    else perfBuckets[3].count++;
  });
  const hasData = stats.total_employees > 0;

  return (
    <div className="p-6 lg:p-8 max-w-7xl mx-auto space-y-8 page-enter">
      {/* Welcome Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            {getGreeting()}, <span className="gradient-text">{user?.email?.split('@')[0]}</span> 👋
          </h2>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Here's what's happening across your workforce today.
          </p>
        </div>
        {hasData && (
          <button
            onClick={() => navigate('/dashboard/intelligence/attrition')}
            className="flex items-center gap-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-sm font-medium shadow-md shadow-indigo-500/25 transition-all hover:shadow-lg hover:shadow-indigo-500/30"
          >
            <Play className="w-4 h-4" />
            Run Attrition Analysis
          </button>
        )}
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <StatCard
          label="Total Employees"
          value={stats.total_employees}
          icon={<Users className="w-5 h-5 text-indigo-600" />}
          gradient="bg-indigo-100 dark:bg-indigo-500/20"
          trend="neutral"
          trendLabel={hasData ? "Active workforce" : "No data yet"}
          loading={loadingStats}
        />
        <StatCard
          label="High Attrition Risk"
          value={stats.high_attrition_risk}
          icon={<AlertTriangle className="w-5 h-5 text-red-500" />}
          gradient="bg-red-100 dark:bg-red-500/20"
          trend={stats.high_attrition_risk > 0 ? 'down' : 'neutral'}
          trendLabel={stats.high_attrition_risk > 0 ? `${Math.round((stats.high_attrition_risk / Math.max(stats.total_employees, 1)) * 100)}% of workforce` : 'No risk detected'}
          loading={loadingStats}
        />
        <StatCard
          label="Avg Engagement"
          value={hasData ? stats.avg_engagement.toFixed(2) : '—'}
          icon={<Activity className="w-5 h-5 text-emerald-500" />}
          gradient="bg-emerald-100 dark:bg-emerald-500/20"
          trend="up"
          trendLabel="Out of 5.0"
          loading={loadingStats}
        />
        <StatCard
          label="Avg Performance"
          value={hasData ? stats.avg_performance.toFixed(2) : '—'}
          icon={<TrendingUp className="w-5 h-5 text-purple-500" />}
          gradient="bg-purple-100 dark:bg-purple-500/20"
          trend="up"
          trendLabel="Out of 5.0"
          loading={loadingStats}
        />
      </div>

      {!hasData && !loadingStats ? (
        /* Empty state */
        <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm p-12 text-center">
          <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-indigo-50 dark:bg-indigo-900/30 flex items-center justify-center">
            <Upload className="w-9 h-9 text-indigo-500" />
          </div>
          <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">No workforce data yet</h3>
          <p className="text-gray-500 dark:text-gray-400 text-sm max-w-md mx-auto mb-8">
            Upload your employee CSV file to unlock AI-powered attrition predictions, department analytics, and workforce intelligence.
          </p>
          <div className="flex flex-wrap justify-center gap-3">
            <button
              onClick={() => navigate('/dashboard/workforce/import')}
              className="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-sm font-semibold shadow-md shadow-indigo-500/25 transition-all"
            >
              Import Workforce Data
            </button>
            <button
              onClick={() => navigate('/dashboard/talent/jobs')}
              className="px-6 py-3 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-600 rounded-xl text-sm font-semibold transition-all"
            >
              Post a Job Opening
            </button>
          </div>
        </div>
      ) : (
        <>
          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Department Bar Chart */}
            <div className="lg:col-span-2 bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm p-6">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="text-base font-bold text-gray-900 dark:text-white">Employees by Department</h3>
                  <p className="text-xs text-gray-400 mt-0.5">Headcount distribution across departments</p>
                </div>
              </div>
              {loadingEmployees ? (
                <div className="h-56 flex items-center justify-center">
                  <div className="skeleton h-full w-full rounded-xl" />
                </div>
              ) : deptData.length > 0 ? (
                <div className="h-56">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={deptData} barSize={28}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" vertical={false} />
                      <XAxis dataKey="dept" tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
                      <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
                      <Tooltip
                        contentStyle={{ background: '#1e293b', border: 'none', borderRadius: 12, color: '#f8fafc', fontSize: 12 }}
                        cursor={{ fill: 'rgba(99,102,241,0.06)' }}
                      />
                      <Bar dataKey="count" name="Employees" fill="url(#barGradient)" radius={[6, 6, 0, 0]} />
                      <defs>
                        <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#6366f1" />
                          <stop offset="100%" stopColor="#818cf8" />
                        </linearGradient>
                      </defs>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="h-56 flex items-center justify-center text-gray-400 text-sm">No department data</div>
              )}
            </div>

            {/* Performance Distribution Donut */}
            <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm p-6">
              <div className="mb-6">
                <h3 className="text-base font-bold text-gray-900 dark:text-white">Performance Spread</h3>
                <p className="text-xs text-gray-400 mt-0.5">Score distribution (out of 5)</p>
              </div>
              {loadingEmployees ? (
                <div className="h-48 skeleton rounded-xl" />
              ) : employees.length > 0 ? (
                <div className="h-48">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie data={perfBuckets} cx="50%" cy="50%" innerRadius={48} outerRadius={72} paddingAngle={3} dataKey="count">
                        {perfBuckets.map((entry, i) => (
                          <Cell key={i} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip
                        contentStyle={{ background: '#1e293b', border: 'none', borderRadius: 12, color: '#f8fafc', fontSize: 12 }}
                        formatter={(val: any) => [`${val} employees`, '']}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="grid grid-cols-2 gap-1 mt-2">
                    {perfBuckets.map(b => (
                      <div key={b.range} className="flex items-center gap-1.5 text-xs text-gray-500 dark:text-gray-400">
                        <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ background: b.color }} />
                        {b.range} ({b.count})
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="h-48 flex items-center justify-center text-gray-400 text-sm">No data</div>
              )}
            </div>
          </div>

          {/* Hiring Trend Area Chart */}
          {hireData.length > 1 && (
            <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm p-6">
              <div className="mb-6">
                <h3 className="text-base font-bold text-gray-900 dark:text-white">Hiring Trend</h3>
                <p className="text-xs text-gray-400 mt-0.5">New hires by joining month (last 12 months)</p>
              </div>
              <div className="h-48">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={hireData}>
                    <defs>
                      <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#6366f1" stopOpacity={0.3} />
                        <stop offset="100%" stopColor="#6366f1" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" vertical={false} />
                    <XAxis dataKey="month" tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
                    <Tooltip
                      contentStyle={{ background: '#1e293b', border: 'none', borderRadius: 12, color: '#f8fafc', fontSize: 12 }}
                    />
                    <Area type="monotone" dataKey="hires" name="New Hires" stroke="#6366f1" strokeWidth={2.5} fill="url(#areaGradient)" dot={{ fill: '#6366f1', r: 3 }} activeDot={{ r: 5, fill: '#6366f1' }} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* Quick Actions */}
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">
            {[
              { label: 'AI Copilot', desc: 'Ask HR assistant', icon: <Sparkles className="w-5 h-5" />, to: '/dashboard/ai/copilot', color: 'text-purple-500 bg-purple-50 dark:bg-purple-900/30' },
              { label: 'View Employees', desc: 'Browse directory', icon: <Users className="w-5 h-5" />, to: '/dashboard/workforce/employees', color: 'text-indigo-500 bg-indigo-50 dark:bg-indigo-900/30' },
              { label: 'Import Data', desc: 'Upload CSV file', icon: <Upload className="w-5 h-5" />, to: '/dashboard/workforce/import', color: 'text-emerald-500 bg-emerald-50 dark:bg-emerald-900/30' },
              { label: 'Attrition AI', desc: 'Risk predictions', icon: <Brain className="w-5 h-5" />, to: '/dashboard/intelligence/attrition', color: 'text-red-500 bg-red-50 dark:bg-red-900/30' },
              { label: 'Post a Job', desc: 'Recruit talent', icon: <Briefcase className="w-5 h-5" />, to: '/dashboard/talent/jobs', color: 'text-amber-500 bg-amber-50 dark:bg-amber-900/30' },
            ].map(action => (
              <Link
                key={action.label}
                to={action.to}
                className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm p-5 card-hover flex flex-col gap-3 group"
              >
                <div className={`p-2.5 rounded-xl w-fit ${action.color}`}>{action.icon}</div>
                <div>
                  <p className="text-sm font-semibold text-gray-900 dark:text-white group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">{action.label}</p>
                  <p className="text-xs text-gray-400 mt-0.5">{action.desc}</p>
                </div>
              </Link>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

// ─── Main Dashboard ───────────────────────────────────────────────────────────
export default function Dashboard() {
  const { user, logout } = useAuth();
  const { isDark, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const isOverview = location.pathname === '/dashboard/overview' || location.pathname === '/dashboard';

  // Breadcrumb
  const breadcrumb = (() => {
    const p = location.pathname.replace('/dashboard/', '');
    if (p === '/dashboard' || p === 'overview') return 'Overview';
    return p.split('/').map(s => s.charAt(0).toUpperCase() + s.slice(1)).join(' › ');
  })();

  const planTier = (user?.plan_tier || 'ENTERPRISE').toUpperCase();

  const navItems = [
    { section: 'Core AI Engine', allowedRoles: ['ORGANIZATION_ADMIN', 'HR_MANAGER', 'HR_ANALYST'], items: [
      { to: '/dashboard/overview', icon: <LayoutDashboard className="w-4 h-4" />, label: 'Overview', match: ['/dashboard/overview', '/dashboard'] },
      { to: '/dashboard/intelligence/attrition', icon: <Brain className="w-4 h-4 text-red-400" />, label: 'Attrition AI (Core Focus)', match: ['/attrition'] },
      { to: '/dashboard/workforce/import', icon: <Upload className="w-4 h-4 text-indigo-400" />, label: 'Import CSV / API Sync', match: ['/import'] },
      { to: '/dashboard/workforce/employees', icon: <Users className="w-4 h-4" />, label: 'Employee Records', match: ['/employees'] },
    ]},
    { section: 'Enterprise Portals', allowedRoles: ['ORGANIZATION_ADMIN', 'HR_MANAGER'], items: [
      { to: '/dashboard/hris', icon: <Building2 className="w-4 h-4 text-indigo-400" />, label: 'HRIS People Portal', match: ['/dashboard/hris'], minPlan: 'PROFESSIONAL' },
      { to: '/dashboard/erp', icon: <Layers className="w-4 h-4 text-emerald-400" />, label: 'ERP Operations & Sync', match: ['/dashboard/erp'], minPlan: 'ENTERPRISE' },
      { to: '/dashboard/ai/copilot', icon: <Sparkles className="w-4 h-4 text-amber-400" />, label: 'Gemini AI Copilot', match: ['/ai/copilot'], minPlan: 'PROFESSIONAL' },
      { to: '/dashboard/ai/evaluation', icon: <FlaskConical className="w-4 h-4 text-purple-400" />, label: 'AI Model Testing Lab', match: ['/dashboard/ai/evaluation'], minPlan: 'ENTERPRISE' },
    ].filter(item => {
      if (item.minPlan === 'ENTERPRISE') return planTier === 'ENTERPRISE';
      if (item.minPlan === 'PROFESSIONAL') return planTier === 'PROFESSIONAL' || planTier === 'ENTERPRISE';
      return true;
    })},
  ].filter(section => section.items.length > 0);

  const isActive = (matchPaths: string[]) =>
    matchPaths.some(mp =>
      mp.startsWith('/') ? location.pathname === mp : location.pathname.includes(mp)
    );

  const Sidebar = (
    <aside className="w-64 bg-slate-900 flex flex-col h-full">
      {/* Logo */}
      <div className="px-6 py-6 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-indigo-500 flex items-center justify-center shadow-lg shadow-indigo-500/30">
            <Brain className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-base font-bold text-white tracking-tight leading-none">NeuroHR</h1>
            <div className="flex items-center gap-1.5 mt-1">
              <span className="text-[10px] font-semibold text-indigo-400 uppercase tracking-widest">X Platform</span>
              <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 uppercase">
                {planTier}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto py-4 space-y-0.5">
        {navItems.filter(group => !group.allowedRoles || group.allowedRoles.includes(user?.role || '')).map(group => (
          <div key={group.section}>
            <SectionLabel label={group.section} />
            {group.items.map(item => (
              <NavItem
                key={item.to}
                to={item.to}
                icon={item.icon}
                label={item.label}
                active={isActive(item.match)}
              />
            ))}
          </div>
        ))}
      </nav>

      {/* User Footer */}
      <div className="p-4 border-t border-slate-800">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center flex-shrink-0 shadow-md">
            <span className="text-white text-xs font-bold">{getInitials(user?.email ?? '')}</span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-semibold text-white truncate">{user?.email?.split('@')[0]}</p>
            <p className="text-[10px] text-slate-400 font-medium">{user?.role}</p>
          </div>
          <button
            onClick={handleLogout}
            title="Sign out"
            className="p-1.5 rounded-lg text-slate-500 hover:text-red-400 hover:bg-red-400/10 transition-all"
          >
            <LogOut className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </aside>
  );

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-950 font-sans overflow-hidden">
      {/* Desktop Sidebar */}
      <div className="hidden lg:flex flex-col h-full">
        {Sidebar}
      </div>

      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-50 flex lg:hidden">
          <div className="fixed inset-0 bg-black/50" onClick={() => setSidebarOpen(false)} />
          <div className="relative flex flex-col h-full">
            {Sidebar}
          </div>
          <button className="absolute top-4 right-4 z-10 text-white" onClick={() => setSidebarOpen(false)}>
            <X className="w-6 h-6" />
          </button>
        </div>
      )}

      {/* Main */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Header */}
        <header className="h-16 bg-white dark:bg-gray-900 border-b border-gray-100 dark:border-gray-800 flex items-center px-6 gap-4 flex-shrink-0">
          {/* Mobile menu button */}
          <button
            className="lg:hidden p-2 rounded-lg text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="w-5 h-5" />
          </button>

          {/* Breadcrumb */}
          <div className="flex items-center gap-2 text-sm">
            <span className="text-gray-400 dark:text-gray-500 font-medium hidden sm:inline">NeuroHR X</span>
            <ChevronRight className="w-4 h-4 text-gray-300 dark:text-gray-600 hidden sm:inline" />
            <span className="font-semibold text-gray-800 dark:text-gray-100">{breadcrumb}</span>
          </div>

          {/* Unified Portal Switcher */}
          <div className="hidden md:flex items-center gap-1.5 p-1 bg-gray-100 dark:bg-gray-800/80 rounded-xl ml-4">
            <Link
              to="/dashboard/overview"
              className={`px-3 py-1 text-xs font-semibold rounded-lg transition-all ${
                location.pathname === '/dashboard/overview' || location.pathname === '/dashboard'
                  ? 'bg-white dark:bg-gray-700 text-indigo-600 dark:text-indigo-400 shadow-sm'
                  : 'text-gray-500 hover:text-gray-900 dark:hover:text-white'
              }`}
            >
              Overview
            </Link>
            <Link
              to="/dashboard/hris"
              className={`px-3 py-1 text-xs font-semibold rounded-lg transition-all flex items-center gap-1.5 ${
                location.pathname.startsWith('/dashboard/hris')
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
              }`}
            >
              <Building2 className="w-3.5 h-3.5" />
              HRIS Portal
            </Link>
            <Link
              to="/dashboard/erp"
              className={`px-3 py-1 text-xs font-semibold rounded-lg transition-all flex items-center gap-1.5 ${
                location.pathname.startsWith('/dashboard/erp')
                  ? 'bg-emerald-600 text-white shadow-sm'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              ERP Portal
            </Link>
            <Link
              to="/dashboard/ai/evaluation"
              className={`px-3 py-1 text-xs font-semibold rounded-lg transition-all flex items-center gap-1.5 ${
                location.pathname.startsWith('/dashboard/ai/evaluation')
                  ? 'bg-purple-600 text-white shadow-sm'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
              }`}
            >
              <FlaskConical className="w-3.5 h-3.5" />
              AI Evaluation Lab
            </Link>
          </div>

          <div className="flex items-center gap-2 ml-auto">
            {/* Dark mode toggle */}
            <button
              onClick={toggleTheme}
              className="p-2 rounded-xl text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-all"
              title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
            >
              {isDark ? <Sun className="w-4.5 h-4.5" /> : <Moon className="w-4.5 h-4.5" />}
            </button>

            {/* Notification bell */}
            <button className="p-2 rounded-xl text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-all relative">
              <Bell className="w-4.5 h-4.5" />
              {/* Red dot */}
              <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full pulse-dot border-2 border-white dark:border-gray-900" />
            </button>

            {/* Avatar */}
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-md ml-1">
              <span className="text-white text-xs font-bold">{getInitials(user?.email ?? '')}</span>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto">
          {isOverview ? <OverviewPage /> : <Outlet />}
        </main>
      </div>
    </div>
  );
}
