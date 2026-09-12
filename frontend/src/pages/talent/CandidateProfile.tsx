import { useState, useEffect } from 'react';

import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { ArrowLeft, Mail, Phone, Briefcase, FileText, AlertTriangle, Sparkles } from 'lucide-react';


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
  projects: string[];
  certifications: string[];
  previous_companies: string[];
  job_titles: string[];
  resume_file: string;
  parsing_status: string;
  parsing_warning: string | null;
  created_at: string;
}

interface JobMatch {
  job_id: string;
  job_title: string;
  match_score: number;
  matched_skills: string[];
  missing_skills: string[];
  explanation: string;
}

export default function CandidateProfile() {
  const { candidateId } = useParams<{ candidateId: string }>();
  const navigate = useNavigate();
  const [candidate, setCandidate] = useState<Candidate | null>(null);
  const [matches, setMatches] = useState<JobMatch[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'profile' | 'matches' | 'resume'>('profile');

  useEffect(() => {
    if (!candidateId) return;
    setLoading(true);
    axios.get(`http://localhost:8000/api/v1/recruitment/candidates/${candidateId}`)
      .then(res => {
        setCandidate(res.data);
        setError(null);
        
        // Fetch jobs to calculate matching context for this candidate
        axios.get('http://localhost:8000/api/v1/recruitment/jobs')
          .then(async jobsRes => {
            const jobs = jobsRes.data;
            const matchList: JobMatch[] = [];
            for (const j of jobs) {
              try {
                const rankRes = await axios.get(`http://localhost:8000/api/v1/recruitment/jobs/${j.job_id}/ranking`);
                const rankingItem = rankRes.data.rankings.find((r: any) => r.candidate_id === candidateId);
                if (rankingItem) {
                  matchList.push({
                    job_id: j.job_id,
                    job_title: j.title,
                    match_score: rankingItem.match_score,
                    matched_skills: rankingItem.matched_skills,
                    missing_skills: rankingItem.missing_skills,
                    explanation: rankingItem.explanation
                  });
                }
              } catch (e) {
                // skip if match failed
              }
            }
            matchList.sort((a, b) => b.match_score - a.match_score);
            setMatches(matchList);
          });
      })
      .catch(err => {
        console.error(err);
        setError('Candidate profile not found.');
      })
      .finally(() => setLoading(false));
  }, [candidateId]);

  if (loading) {
    return <div className="p-12 text-center text-gray-500">Loading candidate profile...</div>;
  }

  if (error || !candidate) {
    return (
      <div className="p-8 max-w-4xl mx-auto space-y-4">
        <button
          onClick={() => navigate('/dashboard/talent/candidates')}
          className="inline-flex items-center text-xs font-medium text-gray-500 hover:text-gray-700 gap-1"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Candidates
        </button>
        <div className="p-6 bg-red-50 text-red-700 rounded-xl text-sm border border-red-200">
          {error || 'Candidate profile not found.'}
        </div>
      </div>
    );
  }

  const bestMatch = matches.length > 0 ? matches[0] : null;

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-6">
      {/* Back Button */}
      <button
        onClick={() => navigate('/dashboard/talent/candidates')}
        className="inline-flex items-center text-xs font-medium text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 gap-1"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Candidates
      </button>

      {/* Warning banner if partial parsing */}
      {candidate.parsing_status === 'Partial' && (
        <div className="p-4 bg-amber-50 text-amber-800 dark:bg-amber-950/40 dark:text-amber-300 rounded-xl text-xs border border-amber-200 dark:border-amber-800 flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0" />
          <div>
            <p className="font-semibold">Some information could not be extracted automatically.</p>
            <p className="text-amber-700 dark:text-amber-400 mt-0.5">{candidate.parsing_warning || 'Please review the parsed details below.'}</p>
          </div>
        </div>
      )}

      {/* Hero Profile Card */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-8">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-full bg-indigo-100 dark:bg-indigo-900/50 text-indigo-600 dark:text-indigo-300 flex items-center justify-center font-bold text-2xl">
              {candidate.name.charAt(0)}
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">{candidate.name}</h2>
              <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-500 dark:text-gray-400 mt-1">
                {candidate.email && (
                  <span className="flex items-center gap-1">
                    <Mail className="w-3.5 h-3.5" />
                    {candidate.email}
                  </span>
                )}
                {candidate.phone && (
                  <span className="flex items-center gap-1">
                    <Phone className="w-3.5 h-3.5" />
                    {candidate.phone}
                  </span>
                )}
                <span className="flex items-center gap-1 font-semibold text-gray-700 dark:text-gray-300">
                  <Briefcase className="w-3.5 h-3.5" />
                  {candidate.experience > 0 ? `${candidate.experience} Years Exp` : 'Entry Level'}
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <a
              href={`http://localhost:8000/api/v1/recruitment/candidates/${candidate.candidate_id}/resume`}
              target="_blank"
              rel="noreferrer"
              className="px-4 py-2 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-800 dark:text-gray-200 text-xs font-semibold rounded-lg inline-flex items-center gap-2"
            >
              <FileText className="w-4 h-4" />
              View Resume
            </a>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="mt-8 border-b border-gray-100 dark:border-gray-700 flex gap-6 text-xs font-semibold text-gray-400">
          <button
            onClick={() => setActiveTab('profile')}
            className={`pb-3 border-b-2 transition-colors ${
              activeTab === 'profile'
                ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400 font-bold'
                : 'border-transparent hover:text-gray-700'
            }`}
          >
            Candidate Overview
          </button>
          <button
            onClick={() => setActiveTab('matches')}
            className={`pb-3 border-b-2 transition-colors inline-flex items-center gap-1.5 ${
              activeTab === 'matches'
                ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400 font-bold'
                : 'border-transparent hover:text-gray-700'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            AI Job Matching ({matches.length})
          </button>
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === 'profile' && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Main Details */}
          <div className="md:col-span-2 space-y-6">
            {/* Skills */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6 space-y-3">
              <h3 className="text-xs font-semibold uppercase text-gray-400 tracking-wider">Extracted Skills</h3>
              <div className="flex flex-wrap gap-2">
                {candidate.skills.length > 0 ? (
                  candidate.skills.map((skill, idx) => (
                    <span
                      key={idx}
                      className="px-3 py-1 bg-indigo-50 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300 text-xs font-medium rounded-full"
                    >
                      {skill}
                    </span>
                  ))
                ) : (
                  <span className="text-xs text-gray-400">No skills extracted</span>
                )}
              </div>
            </div>

            {/* Education & Degree */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6 space-y-3">
              <h3 className="text-xs font-semibold uppercase text-gray-400 tracking-wider">Education & Qualification</h3>
              <div>
                <p className="text-sm font-semibold text-gray-900 dark:text-white">
                  {candidate.degree || 'Degree details not specified'}
                </p>
                {candidate.education && (
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{candidate.education}</p>
                )}
              </div>
            </div>

            {/* Projects if present */}
            {candidate.projects.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6 space-y-3">
                <h3 className="text-xs font-semibold uppercase text-gray-400 tracking-wider">Projects</h3>
                <ul className="list-disc list-inside space-y-1 text-xs text-gray-700 dark:text-gray-300">
                  {candidate.projects.map((proj, idx) => (
                    <li key={idx}>{proj}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Sidebar Info */}
          <div className="space-y-6">
            {/* Best Match Summary */}
            {bestMatch && (
              <div className="bg-gradient-to-br from-indigo-50 to-purple-50 dark:from-indigo-950/40 dark:to-purple-950/30 border border-indigo-100 dark:border-indigo-800 rounded-xl p-6 space-y-3">
                <div className="flex items-center gap-2 text-indigo-700 dark:text-indigo-300 font-semibold text-xs uppercase tracking-wider">
                  <Sparkles className="w-4 h-4" />
                  Best Job Match
                </div>
                <div>
                  <h4 className="text-base font-bold text-gray-900 dark:text-white">{bestMatch.job_title}</h4>
                  <div className="mt-2 flex items-baseline gap-2">
                    <span className="text-3xl font-extrabold text-indigo-600 dark:text-indigo-400">
                      {Math.round(bestMatch.match_score)}%
                    </span>
                    <span className="text-xs text-gray-500">Match Score</span>
                  </div>
                </div>
                <button
                  onClick={() => navigate(`/dashboard/talent/jobs/${bestMatch.job_id}/ranking`)}
                  className="w-full mt-2 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-lg shadow-sm"
                >
                  View Full Ranking
                </button>
              </div>
            )}

            {/* Certifications & Work History */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6 space-y-4">
              {candidate.previous_companies.length > 0 && (
                <div>
                  <h3 className="text-xs font-semibold uppercase text-gray-400 tracking-wider mb-2">Previous Companies</h3>
                  <div className="space-y-1">
                    {candidate.previous_companies.map((c, idx) => (
                      <p key={idx} className="text-xs text-gray-700 dark:text-gray-300 font-medium">{c}</p>
                    ))}
                  </div>
                </div>
              )}

              {candidate.certifications.length > 0 && (
                <div>
                  <h3 className="text-xs font-semibold uppercase text-gray-400 tracking-wider mb-2">Certifications</h3>
                  <div className="space-y-1">
                    {candidate.certifications.map((cert, idx) => (
                      <p key={idx} className="text-xs text-gray-700 dark:text-gray-300">{cert}</p>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* AI Matches Tab */}
      {activeTab === 'matches' && (
        <div className="space-y-4">
          {matches.length === 0 ? (
            <div className="bg-white dark:bg-gray-800 rounded-xl p-8 text-center text-gray-500 text-sm">
              No active job positions found for comparison matching. Create job openings first.
            </div>
          ) : (
            matches.map((m, idx) => (
              <div
                key={idx}
                className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6 flex flex-col md:flex-row md:items-center justify-between gap-4"
              >
                <div>
                  <h4 className="text-lg font-bold text-gray-900 dark:text-white">{m.job_title}</h4>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{m.explanation}</p>
                  
                  <div className="mt-3 flex flex-wrap gap-2">
                    {m.matched_skills.map((s, i) => (
                      <span key={i} className="px-2 py-0.5 bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 text-[11px] font-semibold rounded">
                        ✓ {s}
                      </span>
                    ))}
                    {m.missing_skills.map((s, i) => (
                      <span key={i} className="px-2 py-0.5 bg-red-50 text-red-700 dark:bg-red-950/40 text-[11px] font-semibold rounded">
                        ✗ Missing: {s}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="flex items-center gap-4 border-t md:border-t-0 pt-4 md:pt-0 border-gray-100 dark:border-gray-700">
                  <div className="text-right">
                    <span className="text-2xl font-extrabold text-indigo-600 dark:text-indigo-400">
                      {Math.round(m.match_score)}%
                    </span>
                    <span className="text-xs text-gray-400 block">Match Score</span>
                  </div>
                  <button
                    onClick={() => navigate(`/dashboard/talent/jobs/${m.job_id}/ranking`)}
                    className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-lg shrink-0"
                  >
                    View Ranking
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
