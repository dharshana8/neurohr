import { useState, useEffect } from 'react';

import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { ArrowLeft, Award } from 'lucide-react';


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

export default function JobDetail() {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();
  const [job, setJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!jobId) return;
    setLoading(true);
    axios.get(`http://localhost:8000/api/v1/recruitment/jobs/${jobId}`)
      .then(res => setJob(res.data))
      .catch(err => {
        console.error(err);
        setError('Job not found.');
      })
      .finally(() => setLoading(false));
  }, [jobId]);

  const handleToggleStatus = async () => {
    if (!job) return;
    const newStatus = job.status === 'Open' ? 'Closed' : 'Open';
    try {
      const res = await axios.put(`http://localhost:8000/api/v1/recruitment/jobs/${job.job_id}`, { status: newStatus });
      setJob(res.data);
    } catch (err) {
      alert('Failed to update job status.');
    }
  };

  if (loading) {
    return <div className="p-12 text-center text-gray-500">Loading job details...</div>;
  }

  if (error || !job) {
    return (
      <div className="p-8 max-w-4xl mx-auto space-y-4">
        <button
          onClick={() => navigate('/dashboard/talent/jobs')}
          className="inline-flex items-center text-xs font-medium text-gray-500 hover:text-gray-700 gap-1"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Jobs
        </button>
        <div className="p-6 bg-red-50 text-red-700 rounded-xl text-sm border border-red-200">
          {error || 'Job not found.'}
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <button
          onClick={() => navigate('/dashboard/talent/jobs')}
          className="inline-flex items-center text-xs font-medium text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 mb-3 gap-1"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Jobs
        </button>
        
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">{job.title}</h2>
              <span
                className={`px-3 py-1 text-xs font-semibold rounded-full ${
                  job.status === 'Open'
                    ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800'
                    : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
                }`}
              >
                {job.status}
              </span>
            </div>
            <p className="text-xs text-gray-400 font-mono mt-1">Job ID: {job.job_id} • Created by {job.created_by}</p>
          </div>

          <div className="flex gap-3">
            <button
              onClick={handleToggleStatus}
              className="px-4 py-2 border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-200 text-sm font-semibold rounded-lg"
            >
              {job.status === 'Open' ? 'Close Job' : 'Re-open Job'}
            </button>
            <button
              onClick={() => navigate(`/dashboard/talent/jobs/${job.job_id}/ranking`)}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold rounded-lg shadow-sm inline-flex items-center gap-2"
            >
              <Award className="w-4 h-4" />
              View AI Ranking
            </button>
          </div>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Description & Skills */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6 space-y-4">
            <h3 className="text-sm font-semibold uppercase text-gray-400 tracking-wider">Description</h3>
            <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-line leading-relaxed">
              {job.description}
            </p>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6 space-y-4">
            <h3 className="text-sm font-semibold uppercase text-gray-400 tracking-wider">Required Skills</h3>
            <div className="flex flex-wrap gap-2">
              {job.required_skills.map((skill, idx) => (
                <span
                  key={idx}
                  className="px-3 py-1 bg-indigo-50 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300 text-xs font-semibold rounded-full"
                >
                  {skill}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Sidebar specs */}
        <div className="space-y-6">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6 space-y-4">
            <h3 className="text-sm font-semibold uppercase text-gray-400 tracking-wider">Job Summary</h3>
            <div className="space-y-3 text-xs">
              <div>
                <span className="text-gray-400 block">Minimum Experience</span>
                <span className="font-semibold text-gray-800 dark:text-gray-200">{job.minimum_experience} Years</span>
              </div>
              <div>
                <span className="text-gray-400 block">Qualification</span>
                <span className="font-semibold text-gray-800 dark:text-gray-200">{job.qualification || 'Not specified'}</span>
              </div>
              <div>
                <span className="text-gray-400 block">Location</span>
                <span className="font-semibold text-gray-800 dark:text-gray-200">{job.location || 'Not specified'}</span>
              </div>
              <div>
                <span className="text-gray-400 block">Employment Type</span>
                <span className="font-semibold text-gray-800 dark:text-gray-200">{job.employment_type}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
