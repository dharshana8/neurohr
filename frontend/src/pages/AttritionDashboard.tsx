import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { Brain, AlertCircle, Play } from 'lucide-react';

interface Summary {
  total_analyzed: number;
  high_risk: number;
  medium_risk: number;
  low_risk: number;
}

export default function AttritionDashboard() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [highRisk, setHighRisk] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const fetchData = async () => {
    setIsLoading(true);
    setError('');
    try {
      const [sumRes, hrRes] = await Promise.all([
        axios.get('http://localhost:8000/api/v1/attrition/summary'),
        axios.get('http://localhost:8000/api/v1/attrition/high-risk')
      ]);
      setSummary(sumRes.data);
      setHighRisk(hrRes.data);
    } catch (err) {
      setError('Unable to load attrition analysis.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleRunAnalysis = async () => {
    setIsAnalyzing(true);
    setError('');
    try {
      await axios.post('http://localhost:8000/api/v1/attrition/predict-all');
      await fetchData();
    } catch (err) {
      setError('Failed to run bulk attrition analysis.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  if (isLoading) return <div className="p-8 text-center text-gray-500">Loading attrition intelligence...</div>;

  if (!summary || summary.total_analyzed === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] p-8 text-center">
        <div className="p-4 bg-indigo-50 dark:bg-indigo-900/20 rounded-full mb-4">
          <Brain className="w-10 h-10 text-indigo-600 dark:text-indigo-400" />
        </div>
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">No attrition analysis available.</h2>
        <p className="mt-2 text-sm text-gray-500 max-w-md">
          Run an attrition analysis across your imported workforce to evaluate retention risks.
        </p>
        <button 
          onClick={handleRunAnalysis}
          disabled={isAnalyzing}
          className="mt-6 px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-md text-sm font-medium shadow-sm transition-colors flex items-center disabled:opacity-50"
        >
          <Play className="w-4 h-4 mr-2" />
          {isAnalyzing ? 'Running Analysis...' : 'Run Attrition Analysis'}
        </button>
      </div>
    );
  }

  const pieData = [
    { name: 'High Risk', value: summary.high_risk, color: '#ef4444' },
    { name: 'Medium Risk', value: summary.medium_risk, color: '#f59e0b' },
    { name: 'Low Risk', value: summary.low_risk, color: '#10b981' }
  ];

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Attrition Intelligence</h2>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Real-time attrition predictions powered by Trained Random Forest Model (demo-v1)
          </p>
        </div>
        <button 
          onClick={handleRunAnalysis}
          disabled={isAnalyzing}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-md text-sm font-medium shadow-sm flex items-center disabled:opacity-50"
        >
          <Play className="w-4 h-4 mr-2" />
          {isAnalyzing ? 'Running Analysis...' : 'Re-run Analysis'}
        </button>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100 dark:bg-gray-800 dark:border-gray-700">
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider dark:text-gray-400">Total Analyzed</h3>
          <p className="mt-2 text-3xl font-bold text-gray-900 dark:text-white">{summary.total_analyzed}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm border border-red-100 dark:bg-gray-800 dark:border-red-900/30">
          <h3 className="text-xs font-semibold text-red-500 uppercase tracking-wider">High Risk</h3>
          <p className="mt-2 text-3xl font-bold text-red-600">{summary.high_risk}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm border border-amber-100 dark:bg-gray-800 dark:border-amber-900/30">
          <h3 className="text-xs font-semibold text-amber-500 uppercase tracking-wider">Medium Risk</h3>
          <p className="mt-2 text-3xl font-bold text-amber-600">{summary.medium_risk}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm border border-emerald-100 dark:bg-gray-800 dark:border-emerald-900/30">
          <h3 className="text-xs font-semibold text-emerald-500 uppercase tracking-wider">Low Risk</h3>
          <p className="mt-2 text-3xl font-bold text-emerald-600">{summary.low_risk}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Risk Distribution Chart */}
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100 dark:bg-gray-800 dark:border-gray-700 lg:col-span-1">
          <h3 className="text-base font-semibold text-gray-900 dark:text-white mb-4">Risk Distribution</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={pieData} cx="50%" cy="50%" innerRadius={60} outerRadius={85} paddingAngle={5} dataKey="value">
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* High Risk Employees Table */}
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100 dark:bg-gray-800 dark:border-gray-700 lg:col-span-2">
          <h3 className="text-base font-semibold text-gray-900 dark:text-white mb-4">High Risk Workforce List</h3>
          {highRisk.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              No high risk employees identified in the workforce.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700 text-sm">
                <thead className="bg-gray-50 dark:bg-gray-700/50">
                  <tr>
                    <th className="px-6 py-3 text-left font-semibold text-gray-500 dark:text-gray-400">Employee</th>
                    <th className="px-6 py-3 text-left font-semibold text-gray-500 dark:text-gray-400">Department</th>
                    <th className="px-6 py-3 text-left font-semibold text-gray-500 dark:text-gray-400">Role</th>
                    <th className="px-6 py-3 text-left font-semibold text-gray-500 dark:text-gray-400">Estimated Risk</th>
                    <th className="px-6 py-3 text-left font-semibold text-gray-500 dark:text-gray-400">Probability</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200 dark:bg-gray-800 dark:divide-gray-700">
                  {highRisk.map((emp) => (
                    <tr 
                      key={emp.employee_id} 
                      className="hover:bg-gray-50 dark:hover:bg-gray-700/50 cursor-pointer transition-colors" 
                      onClick={() => navigate(`/dashboard/workforce/employees/${emp.employee_id}`)}
                    >
                      <td className="px-6 py-4 font-semibold text-gray-900 dark:text-white">
                        {emp.name} <span className="text-gray-400 text-xs font-normal ml-1">({emp.employee_id})</span>
                      </td>
                      <td className="px-6 py-4 text-gray-700 dark:text-gray-300">{emp.department}</td>
                      <td className="px-6 py-4 text-gray-600 dark:text-gray-400">{emp.role}</td>
                      <td className="px-6 py-4">
                        <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400">
                          HIGH RISK
                        </span>
                      </td>
                      <td className="px-6 py-4 font-bold text-red-600">
                        {Math.round(emp.probability * 100)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
