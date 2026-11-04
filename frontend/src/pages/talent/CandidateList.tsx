import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { UserCheck, Upload, Search, Filter, FileText, ChevronLeft, ChevronRight, AlertCircle, Eye, Trash2 } from 'lucide-react';

interface Candidate {
  id: string;
  candidate_id: string;
  name: string;
  email: string | null;
  phone: string | null;
  education: string | null;
  degree: string | null;
  experience: number;
  skills: string[];
  resume_file: string;
  parsing_status: string;
  parsing_warning: string | null;
  created_at: string;
}

export default function CandidateList() {
  const navigate = useNavigate();
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [candidateToDelete, setCandidateToDelete] = useState<Candidate | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [showClearAllModal, setShowClearAllModal] = useState(false);
  const [isClearingAll, setIsClearingAll] = useState(false);
  const [actionFeedback, setActionFeedback] = useState<string | null>(null);
  
  // Filters & Pagination
  const [search, setSearch] = useState('');
  const [skillFilter, setSkillFilter] = useState('all');
  const [minExpFilter, setMinExpFilter] = useState<number>(0);
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 8;

  const fetchCandidates = () => {
    setLoading(true);
    axios.get('http://localhost:8000/api/v1/recruitment/candidates')
      .then(res => {
        setCandidates(res.data);
        setError(null);
      })
      .catch(err => {
        console.error(err);
        setError('Failed to fetch candidate profiles.');
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchCandidates();
  }, []);

  const handleDeleteCandidate = async () => {
    if (!candidateToDelete) return;
    setIsDeleting(true);
    try {
      await axios.delete(`http://localhost:8000/api/v1/recruitment/candidates/${candidateToDelete.candidate_id}`);
      setCandidates(prev => prev.filter(c => c.candidate_id !== candidateToDelete.candidate_id));
      setActionFeedback(`Candidate ${candidateToDelete.name} and resume file removed.`);
      setTimeout(() => setActionFeedback(null), 4000);
      setCandidateToDelete(null);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete candidate.');
    } finally {
      setIsDeleting(false);
    }
  };

  const handleClearAllCandidates = async () => {
    setIsClearingAll(true);
    try {
      const res = await axios.delete('http://localhost:8000/api/v1/recruitment/candidates/actions/clear-all');
      setCandidates([]);
      setActionFeedback(res.data?.message || 'All candidates and physical resume files cleared.');
      setTimeout(() => setActionFeedback(null), 4000);
      setShowClearAllModal(false);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to clear all candidates.');
    } finally {
      setIsClearingAll(false);
    }
  };

  // Collect all unique skills for filter dropdown
  const allSkills = Array.from(
    new Set(candidates.flatMap(c => c.skills))
  ).sort();

  const filteredCandidates = candidates.filter(c => {
    const matchesSearch = c.name.toLowerCase().includes(search.toLowerCase()) ||
      (c.email && c.email.toLowerCase().includes(search.toLowerCase())) ||
      (c.degree && c.degree.toLowerCase().includes(search.toLowerCase())) ||
      c.skills.some(s => s.toLowerCase().includes(search.toLowerCase()));
    
    const matchesSkill = skillFilter === 'all' || c.skills.some(s => s.toLowerCase() === skillFilter.toLowerCase());
    const matchesExp = c.experience >= minExpFilter;

    return matchesSearch && matchesSkill && matchesExp;
  });

  const totalPages = Math.ceil(filteredCandidates.length / itemsPerPage) || 1;
  const paginatedCandidates = filteredCandidates.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Feedback Alert */}
      {actionFeedback && (
        <div className="p-3 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-emerald-700 dark:text-emerald-300 rounded-xl text-sm flex items-center justify-between">
          <span>{actionFeedback}</span>
          <button onClick={() => setActionFeedback(null)} className="text-emerald-500 font-bold ml-4">✕</button>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <UserCheck className="w-7 h-7 text-indigo-600 dark:text-indigo-400" />
            Candidate Pool
          </h2>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Parsed resume profiles ready for job matching and ranking evaluation.
          </p>
        </div>
        <div className="flex items-center gap-3">
          {candidates.length > 0 && (
            <button
              onClick={() => setShowClearAllModal(true)}
              className="inline-flex items-center justify-center px-4 py-2.5 bg-red-50 hover:bg-red-100 dark:bg-red-900/20 dark:hover:bg-red-900/40 text-red-600 dark:text-red-400 border border-red-200 dark:border-red-800 rounded-lg text-sm font-semibold transition-all gap-2"
            >
              <Trash2 className="w-4 h-4" />
              Clear All Candidates
            </button>
          )}
          <button
            onClick={() => navigate('/dashboard/talent/candidates/upload')}
            className="inline-flex items-center justify-center px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-semibold shadow-sm transition-all gap-2"
          >
            <Upload className="w-4 h-4" />
            Upload Resume
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col md:flex-row gap-4 bg-white dark:bg-gray-800 p-4 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700">
        <div className="relative flex-1">
          <Search className="w-4 h-4 absolute left-3 top-3 text-gray-400" />
          <input
            type="text"
            placeholder="Search candidates by name, email, skills, degree..."
            value={search}
            onChange={e => {
              setSearch(e.target.value);
              setCurrentPage(1);
            }}
            className="w-full pl-9 pr-4 py-2 text-sm border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-gray-400" />
            <select
              value={skillFilter}
              onChange={e => {
                setSkillFilter(e.target.value);
                setCurrentPage(1);
              }}
              className="px-3 py-2 text-sm border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="all">All Skills</option>
              {allSkills.map((sk, idx) => (
                <option key={idx} value={sk}>{sk}</option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500">Min Exp:</span>
            <select
              value={minExpFilter}
              onChange={e => {
                setMinExpFilter(Number(e.target.value));
                setCurrentPage(1);
              }}
              className="px-3 py-2 text-sm border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value={0}>Any Experience</option>
              <option value={1}>1+ Years</option>
              <option value={2}>2+ Years</option>
              <option value={3}>3+ Years</option>
              <option value={5}>5+ Years</option>
            </select>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-50 text-red-700 rounded-lg text-sm border border-red-200">
          {error}
        </div>
      )}

      {loading ? (
        <div className="p-12 text-center text-gray-500">Loading candidate pool...</div>
      ) : filteredCandidates.length === 0 ? (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-12 text-center">
          <UserCheck className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">No candidates available</h3>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1 max-w-sm mx-auto">
            {candidates.length === 0 ? 'Upload PDF or DOCX candidate resumes to parse and build your candidate database.' : 'No candidates match your current filter parameters.'}
          </p>
          {candidates.length === 0 && (
            <button
              onClick={() => navigate('/dashboard/talent/candidates/upload')}
              className="mt-5 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-semibold inline-flex items-center gap-2"
            >
              <Upload className="w-4 h-4" />
              Upload Resume
            </button>
          )}
        </div>
      ) : (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-gray-600 dark:text-gray-300">
              <thead className="bg-gray-50 dark:bg-gray-900 text-xs uppercase font-semibold text-gray-400 border-b border-gray-100 dark:border-gray-700">
                <tr>
                  <th className="px-6 py-4">Candidate</th>
                  <th className="px-6 py-4">Experience</th>
                  <th className="px-6 py-4">Skills</th>
                  <th className="px-6 py-4">Education / Degree</th>
                  <th className="px-6 py-4">Parsing Status</th>
                  <th className="px-6 py-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                {paginatedCandidates.map(cand => (
                  <tr key={cand.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                    <td className="px-6 py-4">
                      <div>
                        <Link
                          to={`/dashboard/talent/candidates/${cand.candidate_id}`}
                          className="font-bold text-gray-900 dark:text-white hover:text-indigo-600 dark:hover:text-indigo-400"
                        >
                          {cand.name}
                        </Link>
                        <p className="text-xs text-gray-400">{cand.email || 'No email extracted'}</p>
                      </div>
                    </td>

                    <td className="px-6 py-4 font-semibold text-gray-800 dark:text-gray-200">
                      {cand.experience > 0 ? `${cand.experience} yrs` : 'Entry / N/A'}
                    </td>

                    <td className="px-6 py-4">
                      <div className="flex flex-wrap gap-1 max-w-xs">
                        {cand.skills.slice(0, 4).map((sk, idx) => (
                          <span
                            key={idx}
                            className="px-2 py-0.5 text-[11px] font-medium bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300 rounded"
                          >
                            {sk}
                          </span>
                        ))}
                        {cand.skills.length > 4 && (
                          <span className="text-[10px] text-gray-400 font-semibold py-0.5">
                            +{cand.skills.length - 4} more
                          </span>
                        )}
                      </div>
                    </td>

                    <td className="px-6 py-4 text-xs">
                      {cand.degree || cand.education || 'Not specified'}
                    </td>

                    <td className="px-6 py-4">
                      <span
                        className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          cand.parsing_status === 'Completed'
                            ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400'
                            : 'bg-amber-50 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
                        }`}
                      >
                        {cand.parsing_status === 'Partial' && <AlertCircle className="w-3 h-3" />}
                        {cand.parsing_status}
                      </span>
                    </td>

                    <td className="px-6 py-4 text-right space-x-2">
                      <a
                        href={`http://localhost:8000/api/v1/recruitment/candidates/${cand.candidate_id}/resume`}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold text-gray-700 hover:text-indigo-600 dark:text-gray-300 dark:hover:text-indigo-400 bg-gray-100 dark:bg-gray-700 rounded-md"
                      >
                        <FileText className="w-3.5 h-3.5" />
                        Resume
                      </a>
                      <button
                        onClick={() => navigate(`/dashboard/talent/candidates/${cand.candidate_id}`)}
                        className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold text-indigo-600 hover:text-indigo-800 dark:text-indigo-400 dark:hover:text-indigo-300"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        Profile
                      </button>
                      <button
                        onClick={() => setCandidateToDelete(cand)}
                        title="Delete candidate and remove resume file"
                        className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300 hover:bg-red-50 dark:hover:bg-red-950/30 rounded-md transition-colors"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination Footer */}
          <div className="px-6 py-4 bg-gray-50 dark:bg-gray-900 border-t border-gray-100 dark:border-gray-700 flex items-center justify-between">
            <span className="text-xs text-gray-500 dark:text-gray-400">
              Showing {filteredCandidates.length === 0 ? 0 : (currentPage - 1) * itemsPerPage + 1} to{' '}
              {Math.min(currentPage * itemsPerPage, filteredCandidates.length)} of {filteredCandidates.length} candidates
            </span>

            <div className="flex gap-2">
              <button
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                className="p-1.5 border border-gray-200 dark:border-gray-700 rounded-md text-gray-600 dark:text-gray-400 disabled:opacity-30"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="px-3 py-1 text-xs font-semibold text-gray-700 dark:text-gray-300 flex items-center">
                Page {currentPage} of {totalPages}
              </span>
              <button
                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
                className="p-1.5 border border-gray-200 dark:border-gray-700 rounded-md text-gray-600 dark:text-gray-400 disabled:opacity-30"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Single Candidate Modal */}
      {candidateToDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className="bg-white dark:bg-gray-800 rounded-2xl max-w-md w-full p-6 shadow-xl border border-gray-100 dark:border-gray-700 space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-red-100 dark:bg-red-900/40 flex items-center justify-center text-red-600 dark:text-red-400 shrink-0">
                <Trash2 className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-gray-900 dark:text-white">Delete Candidate Profile</h3>
                <p className="text-xs text-gray-500 dark:text-gray-400">Physical resume removal & candidate purge</p>
              </div>
            </div>

            <p className="text-sm text-gray-600 dark:text-gray-300">
              Are you sure you want to delete candidate <strong className="text-gray-900 dark:text-white">{candidateToDelete.name}</strong>?
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-700/50 p-3 rounded-xl">
              This permanently deletes the profile, rankings, and removes the uploaded resume document (<code className="text-xs">{candidateToDelete.resume_file}</code>) from disk.
            </p>

            <div className="flex justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setCandidateToDelete(null)}
                disabled={isDeleting}
                className="px-4 py-2 text-xs font-semibold text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-xl transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleDeleteCandidate}
                disabled={isDeleting}
                className="px-4 py-2 text-xs font-semibold text-white bg-red-600 hover:bg-red-700 rounded-xl transition-colors shadow-sm disabled:opacity-50"
              >
                {isDeleting ? 'Deleting...' : 'Confirm Delete'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Clear All Candidates Modal */}
      {showClearAllModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className="bg-white dark:bg-gray-800 rounded-2xl max-w-md w-full p-6 shadow-xl border border-red-200 dark:border-red-900 space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-red-100 dark:bg-red-900/40 flex items-center justify-center text-red-600 dark:text-red-400 shrink-0">
                <AlertCircle className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-red-600 dark:text-red-400">Clear All Candidates</h3>
                <p className="text-xs text-gray-500 dark:text-gray-400">Complete recruitment pool reset</p>
              </div>
            </div>

            <p className="text-sm text-gray-600 dark:text-gray-300">
              Are you sure you want to remove <strong className="text-gray-900 dark:text-white">all {candidates.length} candidate profiles</strong>?
            </p>
            <div className="p-3 bg-red-50 dark:bg-red-950/40 rounded-xl text-xs text-red-700 dark:text-red-300 space-y-1">
              <p className="font-semibold">⚠️ This action cannot be undone:</p>
              <ul className="list-disc list-inside space-y-0.5">
                <li>All candidate records will be erased</li>
                <li>All physical resume PDF and DOCX files will be deleted from storage</li>
                <li>All job match rankings will be purged</li>
              </ul>
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setShowClearAllModal(false)}
                disabled={isClearingAll}
                className="px-4 py-2 text-xs font-semibold text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-xl transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleClearAllCandidates}
                disabled={isClearingAll}
                className="px-4 py-2 text-xs font-semibold text-white bg-red-600 hover:bg-red-700 rounded-xl transition-colors shadow-sm disabled:opacity-50"
              >
                {isClearingAll ? 'Clearing Pool...' : 'Yes, Delete Everything'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
