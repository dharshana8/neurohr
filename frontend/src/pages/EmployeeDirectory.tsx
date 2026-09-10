import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { Search, Filter, Upload, ChevronLeft, ChevronRight } from 'lucide-react';

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

export default function EmployeeDirectory() {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDept, setSelectedDept] = useState('All');
  const [selectedRole, setSelectedRole] = useState('All');
  
  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  const navigate = useNavigate();

  const fetchEmployees = async () => {
    setIsLoading(true);
    setError('');
    try {
      const response = await axios.get('http://localhost:8000/api/v1/workforce/employees', {
        params: {
          search: searchTerm || undefined,
          department: selectedDept !== 'All' ? selectedDept : undefined,
          role: selectedRole !== 'All' ? selectedRole : undefined
        }
      });
      setEmployees(response.data);
    } catch (err) {
      setError('Unable to load workforce data.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchEmployees();
  }, [searchTerm, selectedDept, selectedRole]);

  // Extract unique departments & roles for filters
  const departments = ['All', ...Array.from(new Set(employees.map(e => e.department))).filter(Boolean)];
  const roles = ['All', ...Array.from(new Set(employees.map(e => e.role))).filter(Boolean)];

  // Pagination logic
  const totalPages = Math.ceil(employees.length / itemsPerPage) || 1;
  const paginatedEmployees = employees.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage);

  if (isLoading) {
    return <div className="p-8 text-center text-gray-500">Loading employees...</div>;
  }

  if (error) {
    return (
      <div className="p-8 text-center text-red-600">
        <p className="font-semibold">{error}</p>
        <button
          onClick={fetchEmployees}
          className="mt-4 px-4 py-2 bg-indigo-600 text-white rounded-md text-sm"
        >
          Retry
        </button>
      </div>
    );
  }

  if (employees.length === 0 && !searchTerm && selectedDept === 'All' && selectedRole === 'All') {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] p-8 text-center">
        <div className="p-4 bg-indigo-50 dark:bg-indigo-900/20 rounded-full mb-4">
          <Upload className="w-10 h-10 text-indigo-600 dark:text-indigo-400" />
        </div>
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">No workforce data available</h2>
        <p className="mt-2 text-sm text-gray-500 max-w-md">
          Upload a CSV file to start analyzing your workforce.
        </p>
        <button 
          onClick={() => navigate('/dashboard/workforce/import')}
          className="mt-6 px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-md text-sm font-medium shadow-sm transition-colors"
        >
          Import CSV
        </button>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Employee Directory</h2>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Total Employees: <span className="font-semibold text-gray-700 dark:text-gray-200">{employees.length}</span>
          </p>
        </div>
        <button 
          onClick={() => navigate('/dashboard/workforce/import')}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-md text-sm font-medium shadow-sm"
        >
          Import Data
        </button>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-100 dark:bg-gray-800 dark:border-gray-700 overflow-hidden">
        {/* Filters bar */}
        <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex flex-wrap items-center justify-between gap-4">
          <div className="relative flex-1 min-w-[240px]">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Search className="h-4 w-4 text-gray-400" />
            </div>
            <input
              type="text"
              placeholder="Search by name, ID, or department..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
              className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md text-sm bg-white dark:bg-gray-700 dark:border-gray-600 dark:text-white placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
          </div>

          <div className="flex items-center space-x-3">
            {/* Department Filter */}
            <div className="flex items-center space-x-2">
              <label className="text-xs font-medium text-gray-500 dark:text-gray-400">Department:</label>
              <select
                value={selectedDept}
                onChange={(e) => {
                  setSelectedDept(e.target.value);
                  setCurrentPage(1);
                }}
                className="px-3 py-2 border border-gray-300 rounded-md text-sm bg-white dark:bg-gray-700 dark:border-gray-600 dark:text-white focus:outline-none"
              >
                {departments.map((dept, idx) => (
                  <option key={idx} value={dept}>{dept}</option>
                ))}
              </select>
            </div>

            {/* Role Filter */}
            <div className="flex items-center space-x-2">
              <label className="text-xs font-medium text-gray-500 dark:text-gray-400">Role:</label>
              <select
                value={selectedRole}
                onChange={(e) => {
                  setSelectedRole(e.target.value);
                  setCurrentPage(1);
                }}
                className="px-3 py-2 border border-gray-300 rounded-md text-sm bg-white dark:bg-gray-700 dark:border-gray-600 dark:text-white focus:outline-none"
              >
                {roles.map((role, idx) => (
                  <option key={idx} value={role}>{role}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Directory Table */}
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700 text-sm">
            <thead className="bg-gray-50 dark:bg-gray-700/50">
              <tr>
                <th className="px-6 py-3 text-left font-semibold text-gray-500 dark:text-gray-400">Employee ID</th>
                <th className="px-6 py-3 text-left font-semibold text-gray-500 dark:text-gray-400">Name</th>
                <th className="px-6 py-3 text-left font-semibold text-gray-500 dark:text-gray-400">Department</th>
                <th className="px-6 py-3 text-left font-semibold text-gray-500 dark:text-gray-400">Role</th>
                <th className="px-6 py-3 text-left font-semibold text-gray-500 dark:text-gray-400">Joining Date</th>
                <th className="px-6 py-3 text-left font-semibold text-gray-500 dark:text-gray-400">Performance</th>
                <th className="px-6 py-3 text-left font-semibold text-gray-500 dark:text-gray-400">Engagement</th>
                <th className="px-6 py-3 text-left font-semibold text-gray-500 dark:text-gray-400">Status</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200 dark:bg-gray-800 dark:divide-gray-700">
              {paginatedEmployees.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-6 py-8 text-center text-gray-500">
                    No employees match your search criteria.
                  </td>
                </tr>
              ) : (
                paginatedEmployees.map((emp) => (
                  <tr 
                    key={emp.id} 
                    onClick={() => navigate(`/dashboard/workforce/employees/${emp.employee_id}`)}
                    className="hover:bg-gray-50 dark:hover:bg-gray-700/50 cursor-pointer transition-colors"
                  >
                    <td className="px-6 py-4 font-medium text-indigo-600 dark:text-indigo-400">{emp.employee_id}</td>
                    <td className="px-6 py-4 font-semibold text-gray-900 dark:text-white">{emp.name}</td>
                    <td className="px-6 py-4 text-gray-700 dark:text-gray-300">{emp.department}</td>
                    <td className="px-6 py-4 text-gray-600 dark:text-gray-400">{emp.role}</td>
                    <td className="px-6 py-4 text-gray-500">
                      {emp.joining_date ? new Date(emp.joining_date).toLocaleDateString() : 'N/A'}
                    </td>
                    <td className="px-6 py-4 font-medium">{emp.performance_score} / 5</td>
                    <td className="px-6 py-4 font-medium">{emp.engagement_score} / 5</td>
                    <td className="px-6 py-4">
                      <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400">
                        {emp.employment_status}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination bar */}
        {totalPages > 1 && (
          <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between">
            <span className="text-xs text-gray-500 dark:text-gray-400">
              Showing page <span className="font-semibold text-gray-700 dark:text-gray-200">{currentPage}</span> of <span className="font-semibold text-gray-700 dark:text-gray-200">{totalPages}</span>
            </span>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                className="p-2 border border-gray-300 rounded-md text-gray-600 hover:bg-gray-50 disabled:opacity-40 dark:border-gray-600 dark:text-gray-300"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
                className="p-2 border border-gray-300 rounded-md text-gray-600 hover:bg-gray-50 disabled:opacity-40 dark:border-gray-600 dark:text-gray-300"
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
