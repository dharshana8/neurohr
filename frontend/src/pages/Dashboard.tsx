import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate, Link, Outlet, useLocation } from 'react-router-dom';
import { LogOut, LayoutDashboard, Users, Brain, Upload, Shield } from 'lucide-react';
import axios from 'axios';

export default function Dashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [stats, setStats] = useState({ total_employees: 0, high_attrition_risk: 0, avg_performance: 0, avg_engagement: 0 });
  const [isLoadingStats, setIsLoadingStats] = useState(false);

  useEffect(() => {
    if (location.pathname === '/dashboard/overview' || location.pathname === '/dashboard') {
      setIsLoadingStats(true);
      axios.get('http://localhost:8000/api/v1/workforce/stats')
        .then(res => setStats(res.data))
        .catch(() => {})
        .finally(() => setIsLoadingStats(false));
    }
  }, [location.pathname]);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900 font-sans">
      {/* Sidebar */}
      <aside className="w-64 bg-white shadow-md dark:bg-gray-800 flex flex-col justify-between">
        <div>
          <div className="p-6">
            <h1 className="text-2xl font-extrabold text-indigo-600 dark:text-indigo-400 tracking-tight">NeuroHR X</h1>
            <p className="text-xs text-gray-500 mt-1">{user?.role || 'User'} Portal</p>
          </div>
          
          <nav className="mt-2 space-y-1">
            <div className="px-4 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider">
              Overview
            </div>
            <Link 
              to="/dashboard/overview" 
              className={`flex items-center px-6 py-2.5 text-sm font-medium transition-colors ${
                location.pathname.includes('/overview') || location.pathname === '/dashboard' 
                  ? 'bg-indigo-50 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300 font-semibold border-r-4 border-indigo-600' 
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700'
              }`}
            >
              <LayoutDashboard className="w-4 h-4 mr-3" />
              Dashboard
            </Link>

            <div className="px-4 py-2 mt-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">
              Workforce
            </div>
            <Link 
              to="/dashboard/workforce/employees" 
              className={`flex items-center px-6 py-2.5 text-sm font-medium transition-colors ${
                location.pathname.includes('/employees') 
                  ? 'bg-indigo-50 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300 font-semibold border-r-4 border-indigo-600' 
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700'
              }`}
            >
              <Users className="w-4 h-4 mr-3" />
              Employees
            </Link>
            <Link 
              to="/dashboard/workforce/import" 
              className={`flex items-center px-6 py-2.5 text-sm font-medium transition-colors ${
                location.pathname.includes('/import') 
                  ? 'bg-indigo-50 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300 font-semibold border-r-4 border-indigo-600' 
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700'
              }`}
            >
              <Upload className="w-4 h-4 mr-3" />
              Import Data
            </Link>

            <div className="px-4 py-2 mt-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">
              Intelligence
            </div>
            <Link 
              to="/dashboard/intelligence/attrition" 
              className={`flex items-center px-6 py-2.5 text-sm font-medium transition-colors ${
                location.pathname.includes('/attrition') 
                  ? 'bg-indigo-50 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300 font-semibold border-r-4 border-indigo-600' 
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700'
              }`}
            >
              <Brain className="w-4 h-4 mr-3" />
              Attrition
            </Link>
          </nav>
        </div>

        {/* User Info footer */}
        <div className="p-4 border-t border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div className="truncate">
              <p className="text-xs font-medium text-gray-900 dark:text-white truncate">{user?.email}</p>
              <p className="text-[10px] text-gray-400 uppercase tracking-wider mt-0.5">{user?.role}</p>
            </div>
            <button
              onClick={handleLogout}
              className="p-1.5 text-gray-400 hover:text-red-600 dark:hover:text-red-400 rounded-md transition-colors"
              title="Logout"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto">
        {/* Dynamic Nested Routes */}
        {location.pathname === '/dashboard/overview' || location.pathname === '/dashboard' ? (
          <div className="p-8 max-w-7xl mx-auto space-y-8">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Overview</h2>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                Workforce statistics and intelligence summary
              </p>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100 dark:bg-gray-800 dark:border-gray-700">
                <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider dark:text-gray-400">Total Employees</h3>
                <p className="mt-2 text-3xl font-bold text-gray-900 dark:text-white">{stats.total_employees}</p>
              </div>

              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100 dark:bg-gray-800 dark:border-gray-700">
                <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider dark:text-gray-400">High Attrition Risk</h3>
                <p className="mt-2 text-3xl font-bold text-red-600">{stats.high_attrition_risk}</p>
              </div>

              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100 dark:bg-gray-800 dark:border-gray-700">
                <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider dark:text-gray-400">Avg Engagement</h3>
                <p className="mt-2 text-3xl font-bold text-emerald-600">
                  {stats.total_employees > 0 ? stats.avg_engagement.toFixed(1) : '-'}
                </p>
              </div>

              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100 dark:bg-gray-800 dark:border-gray-700">
                <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider dark:text-gray-400">Avg Performance</h3>
                <p className="mt-2 text-3xl font-bold text-indigo-600">
                  {stats.total_employees > 0 ? stats.avg_performance.toFixed(1) : '-'}
                </p>
              </div>
            </div>

            {stats.total_employees === 0 ? (
              <div className="bg-white rounded-lg shadow-sm border border-gray-100 p-8 text-center dark:bg-gray-800 dark:border-gray-700">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Welcome to NeuroHR X</h3>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-2 max-w-lg mx-auto">
                  No workforce data has been loaded yet into MongoDB. Go to <strong>Workforce &rarr; Import Data</strong> to upload your employee CSV file.
                </p>
                <button
                  onClick={() => navigate('/dashboard/workforce/import')}
                  className="mt-6 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-md text-sm font-medium shadow-sm"
                >
                  Import Workforce Data
                </button>
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow-sm border border-gray-100 p-6 dark:bg-gray-800 dark:border-gray-700 flex justify-between items-center">
                <div>
                  <h3 className="text-base font-semibold text-gray-900 dark:text-white">Workforce Data Active</h3>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    Organization ID: <span className="font-mono text-gray-700 dark:text-gray-300">{user?.organization_id}</span>
                  </p>
                </div>
                <button
                  onClick={() => navigate('/dashboard/workforce/employees')}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-md text-xs font-medium"
                >
                  View Directory
                </button>
              </div>
            )}
          </div>
        ) : (
          <Outlet />
        )}
      </main>
    </div>
  );
}
