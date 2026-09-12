import { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { Search, Upload, ChevronLeft, ChevronRight, SlidersHorizontal } from 'lucide-react';

interface Employee {
  id: string;
  employee_id: string;
  name: string;
  department: string;
  role: string;
  joining_date: string;
  performance_score: number;
  engagement_score: number;
  employment_status: string;
}

function ScoreBar({ value, max = 5, color }: { value: number; max?: number; color: string }) {
  const pct = Math.min((value / max) * 100, 100);
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden max-w-[80px]">
        <div className="h-full rounded-full transition-all" style={{ width: `${pct}%`, background: color }} />
      </div>
      <span className="text-xs font-semibold text-gray-600 dark:text-gray-300 tabular-nums">
        {typeof value === 'number' ? value.toFixed(1) : value}
      </span>
    </div>
  );
}

function EmployeeAvatar({ name }: { name: string }) {
  const colors = [
    'from-indigo-400 to-indigo-600',
    'from-purple-400 to-purple-600',
    'from-blue-400 to-blue-600',
    'from-emerald-400 to-emerald-600',
    'from-rose-400 to-rose-600',
    'from-amber-400 to-amber-600',
    'from-teal-400 to-teal-600',
  ];
  const idx = name.charCodeAt(0) % colors.length;
  return (
    <div className={`w-9 h-9 rounded-full bg-gradient-to-br ${colors[idx]} flex items-center justify-center flex-shrink-0 shadow-sm`}>
      <span className="text-white text-xs font-bold">{name?.slice(0, 2).toUpperCase()}</span>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const s = (status || '').toLowerCase();
  const config =
    s === 'active'
      ? 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-900/20 dark:text-emerald-400 dark:border-emerald-800'
      : s === 'resigned' || s === 'terminated'
      ? 'bg-red-50 text-red-700 border-red-200 dark:bg-red-900/20 dark:text-red-400 dark:border-red-800'
      : 'bg-gray-100 text-gray-600 border-gray-200 dark:bg-gray-700 dark:text-gray-400 dark:border-gray-600';
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${config}`}>
      {status}
    </span>
  );
}

export default function EmployeeDirectory() {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDept, setSelectedDept] = useState('All');
  const [selectedRole, setSelectedRole] = useState('All');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 12;
  const navigate = useNavigate();

  const fetchEmployees = async () => {
    setIsLoading(true);
    setError('');
    try {
      const response = await axios.get('http://localhost:8000/api/v1/workforce/employees', {
        params: {
          search: searchTerm || undefined,
          department: selectedDept !== 'All' ? selectedDept : undefined,
          role: selectedRole !== 'All' ? selectedRole : undefined,
        },
      });
      setEmployees(response.data);
    } catch {
      setError('Unable to load workforce data.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => { fetchEmployees(); }, [searchTerm, selectedDept, selectedRole]);

  const departments = ['All', ...Array.from(new Set(employees.map(e => e.department))).filter(Boolean).sort()];
  const roles = ['All', ...Array.from(new Set(employees.map(e => e.role))).filter(Boolean).sort()];
  const totalPages = Math.ceil(employees.length / itemsPerPage) || 1;
  const paginated = employees.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage);

  if (isLoading) {
    return (
      <div className="p-8 max-w-7xl mx-auto space-y-5 page-enter">
        <div className="skeleton h-8 w-48 rounded-xl" />
        <div className="skeleton h-14 rounded-2xl" />
        {[...Array(6)].map((_, i) => <div key={i} className="skeleton h-16 rounded-2xl" />)}
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8 text-center">
        <p className="text-red-600 dark:text-red-400 font-semibold mb-4">{error}</p>
        <button onClick={fetchEmployees} className="px-4 py-2 bg-indigo-600 text-white rounded-xl text-sm font-medium">Retry</button>
      </div>
    );
  }

  if (employees.length === 0 && !searchTerm && selectedDept === 'All' && selectedRole === 'All') {
    return (
      <div className="flex flex-col items-center justify-center min-h-[70vh] p-8 text-center page-enter">
        <div className="w-24 h-24 mx-auto mb-6 rounded-full bg-indigo-50 dark:bg-indigo-900/30 flex items-center justify-center">
          <Upload className="w-11 h-11 text-indigo-400" />
        </div>
        <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">No Employees Yet</h2>
        <p className="text-sm text-gray-500 dark:text-gray-400 max-w-sm mb-8">
          Upload a CSV file to import your employee data and start analyzing your workforce.
        </p>
        <button
          onClick={() => navigate('/dashboard/workforce/import')}
          className="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-sm font-semibold shadow-md shadow-indigo-500/25 transition-all"
        >
          Import CSV
        </button>
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8 max-w-7xl mx-auto page-enter">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Employee Directory</h2>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            <span className="font-semibold text-gray-700 dark:text-gray-200">{employees.length}</span> employees in your workforce
          </p>
        </div>
        <button
          onClick={() => navigate('/dashboard/workforce/import')}
          className="flex items-center gap-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-sm font-semibold shadow-md shadow-indigo-500/20 transition-all"
        >
          <Upload className="w-4 h-4" />
          Import More
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm mb-4">
        <div className="p-4 flex flex-wrap items-center gap-3">
          {/* Search */}
          <div className="relative flex-1 min-w-[220px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search name, ID, department..."
              value={searchTerm}
              onChange={e => { setSearchTerm(e.target.value); setCurrentPage(1); }}
              className="w-full pl-9 pr-4 py-2.5 text-sm bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-xl text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-400 transition-all"
            />
          </div>

          <div className="flex items-center gap-2 text-gray-400">
            <SlidersHorizontal className="w-4 h-4" />
          </div>

          {/* Department */}
          <select
            value={selectedDept}
            onChange={e => { setSelectedDept(e.target.value); setCurrentPage(1); }}
            className="px-3 py-2.5 text-sm bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-xl text-gray-700 dark:text-gray-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/30 transition-all"
          >
            {departments.map((d, i) => <option key={i} value={d}>{d === 'All' ? 'All Departments' : d}</option>)}
          </select>

          {/* Role */}
          <select
            value={selectedRole}
            onChange={e => { setSelectedRole(e.target.value); setCurrentPage(1); }}
            className="px-3 py-2.5 text-sm bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-xl text-gray-700 dark:text-gray-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/30 transition-all"
          >
            {roles.map((r, i) => <option key={i} value={r}>{r === 'All' ? 'All Roles' : r}</option>)}
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="bg-gray-50 dark:bg-gray-700/60">
              <tr>
                <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Employee</th>
                <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Department</th>
                <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Role</th>
                <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Joined</th>
                <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Performance</th>
                <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Engagement</th>
                <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50 dark:divide-gray-700/50">
              {paginated.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-gray-400 text-sm">
                    No employees match your search criteria.
                  </td>
                </tr>
              ) : (
                paginated.map(emp => (
                  <tr
                    key={emp.id}
                    onClick={() => navigate(`/dashboard/workforce/employees/${emp.employee_id}`)}
                    className="hover:bg-indigo-50/30 dark:hover:bg-indigo-900/10 cursor-pointer transition-colors group"
                  >
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <EmployeeAvatar name={emp.name} />
                        <div>
                          <p className="font-semibold text-gray-900 dark:text-white group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">{emp.name}</p>
                          <p className="text-xs text-indigo-500 dark:text-indigo-400 font-medium">{emp.employee_id}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className="px-2.5 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg text-xs font-medium">
                        {emp.department}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-gray-500 dark:text-gray-400 text-xs">{emp.role}</td>
                    <td className="px-6 py-4 text-gray-500 dark:text-gray-400 text-xs">
                      {emp.joining_date ? new Date(emp.joining_date).toLocaleDateString('en-IN', { year: 'numeric', month: 'short', day: 'numeric' }) : 'N/A'}
                    </td>
                    <td className="px-6 py-4">
                      <ScoreBar value={emp.performance_score} color="#6366f1" />
                    </td>
                    <td className="px-6 py-4">
                      <ScoreBar value={emp.engagement_score} color="#10b981" />
                    </td>
                    <td className="px-6 py-4">
                      <StatusBadge status={emp.employment_status} />
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="px-6 py-4 border-t border-gray-100 dark:border-gray-700 flex items-center justify-between">
            <span className="text-xs text-gray-500 dark:text-gray-400">
              Page <span className="font-semibold text-gray-700 dark:text-gray-200">{currentPage}</span> of <span className="font-semibold text-gray-700 dark:text-gray-200">{totalPages}</span>
              {' '}· {employees.length} total
            </span>
            <div className="flex items-center gap-1">
              <button
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                className="p-2 rounded-xl border border-gray-200 dark:border-gray-600 text-gray-500 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-40 transition-all"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
                className="p-2 rounded-xl border border-gray-200 dark:border-gray-600 text-gray-500 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-40 transition-all"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
