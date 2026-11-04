import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Briefcase, Plus, Search, Filter, Eye, Award, MapPin, Clock } from 'lucide-react';

interface Job {
  id: string;
  job_id: string;
  title: string;
  description: string;
  required_skills: string[];
  minimum_experience: number;
  qualification: string;
  location: string;
  employment_type: string;
  status: string;
  created_by: string;
  created_at: string;
}

export default function JobList() {
  const navigate = useNavigate();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  const fetchJobs = () => {
    setLoading(true);
    axios.get('http://localhost:8000/api/v1/recruitment/jobs')
      .then(res => {
        setJobs(res.data);
        setError(null);
      })
      .catch(err => {
        console.error(err);
        setError('Failed to fetch jobs.');
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchJobs();
  }, []);

  const handleToggleStatus = async (jobId: string, currentStatus: string) => {
    const newStatus = currentStatus === 'Open' ? 'Closed' : 'Open';
    try {
      await axios.put(`http://localhost:8000/api/v1/recruitment/jobs/${jobId}`, { status: newStatus });
      fetchJobs();
    } catch (err) {
      alert('Failed to update job status.');
    }
  };

  const filteredJobs = jobs.filter(j => {
    const matchesSearch = j.title.toLowerCase().includes(search.toLowerCase()) ||
      j.location.toLowerCase().includes(search.toLowerCase()) ||
      j.required_skills.some(s => s.toLowerCase().includes(search.toLowerCase()));
    const matchesStatus = statusFilter === 'all' || j.status.toLowerCase() === statusFilter.toLowerCase();
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <Briefcase className="w-7 h-7 text-indigo-600 dark:text-indigo-400" />
            Job Openings
          </h2>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Manage open positions, requirements, and candidate matching pipelines.
          </p>
        </div>
        <button
          onClick={() => navigate('/dashboard/talent/jobs/new')}
          className="inline-flex items-center justify-center px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-semibold shadow-sm transition-all gap-2"
        >
          <Plus className="w-4 h-4" />
          Create Job
        </button>
      </div>

      {/* Filters Bar */}
      <div className="flex flex-col md:flex-row gap-4 bg-white dark:bg-gray-800 p-4 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700">
        <div className="relative flex-1">
          <Search className="w-4 h-4 absolute left-3 top-3 text-gray-400" />
          <input
            type="text"
            placeholder="Search jobs by title, skills, location..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 text-sm border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-gray-400" />
          <select
            value={statusFilter}
            onChange={e => setStatusFilter(e.target.value)}
            className="px-3 py-2 text-sm border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="all">All Statuses</option>
            <option value="open">Open</option>
            <option value="closed">Closed</option>
          </select>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="p-4 bg-red-50 text-red-700 rounded-lg text-sm border border-red-200">
          {error}
        </div>
      )}

      {/* Loading state */}
      {loading ? (
        <div className="p-12 text-center text-gray-500">Loading jobs...</div>
      ) : filteredJobs.length === 0 ? (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-12 text-center">
          <Briefcase className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">No jobs available</h3>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1 max-w-sm mx-auto">
            {jobs.length === 0 ? 'Create your first job posting to start matching candidate resumes.' : 'No jobs match your filter criteria.'}
          </p>
          {jobs.length === 0 && (
            <button
              onClick={() => navigate('/dashboard/talent/jobs/new')}
              className="mt-5 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-semibold inline-flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              Create Job
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {filteredJobs.map(job => (
            <div
              key={job.id}
              className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6 flex flex-col justify-between hover:shadow-md transition-shadow"
            >
              <div>
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="text-lg font-bold text-gray-900 dark:text-white">{job.title}</h3>
                    <p className="text-xs text-gray-400 font-mono mt-0.5">{job.job_id}</p>
                  </div>
                  <span
                    className={`px-2.5 py-1 text-xs font-semibold rounded-full ${
                      job.status === 'Open'
                        ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800'
                        : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
                    }`}
                  >
                    {job.status}
                  </span>
                </div>

                <div className="mt-4 flex flex-wrap gap-y-2 gap-x-4 text-xs text-gray-600 dark:text-gray-300">
                  <span className="flex items-center gap-1">
                    <MapPin className="w-3.5 h-3.5 text-gray-400" />
                    {job.location || 'Location Not Specified'}
                  </span>
                  <span className="flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5 text-gray-400" />
                    {job.employment_type}
                  </span>
                  <span className="flex items-center gap-1">
                    <Award className="w-3.5 h-3.5 text-gray-400" />
                    Min {job.minimum_experience} yrs exp
                  </span>
                </div>

                <p className="mt-3 text-xs text-gray-500 dark:text-gray-400 line-clamp-2">
                  {job.description}
                </p>

                {/* Required Skills */}
                <div className="mt-4">
                  <p className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider mb-1.5">Required Skills</p>
                  <div className="flex flex-wrap gap-1.5">
                    {job.required_skills.map((skill, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-0.5 text-xs font-medium bg-indigo-50 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300 rounded-md"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Card Footer Actions */}
              <div className="mt-6 pt-4 border-t border-gray-100 dark:border-gray-700 flex items-center justify-between gap-2">
                <button
                  onClick={() => handleToggleStatus(job.job_id, job.status)}
                  className="text-xs font-medium text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                >
                  {job.status === 'Open' ? 'Close Job' : 'Re-open Job'}
                </button>
                <div className="flex gap-2">
                  <button
                    onClick={() => navigate(`/dashboard/talent/jobs/${job.job_id}`)}
                    className="px-3 py-1.5 border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-200 text-xs font-medium rounded-lg inline-flex items-center gap-1.5"
                  >
                    <Eye className="w-3.5 h-3.5" />
                    Details
                  </button>
                  <button
                    onClick={() => navigate(`/dashboard/talent/jobs/${job.job_id}/ranking`)}
                    className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-lg inline-flex items-center gap-1.5 shadow-sm"
                  >
                    <Award className="w-3.5 h-3.5" />
                    AI Ranking
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
