import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { UserCircle, Briefcase, TrendingUp, AlertTriangle, ArrowLeft, Brain, Sparkles } from 'lucide-react';

interface SHAPFactor {
  feature: string;
  impact: string;
  shap_value?: number;
  description: string;
}

interface ExplanationData {
  available: boolean;
  top_factors: SHAPFactor[];
}

export default function EmployeeProfile() {
  const { employeeId } = useParams();
  const navigate = useNavigate();
  const [employee, setEmployee] = useState<any>(null);
  const [prediction, setPrediction] = useState<any>(null);
  const [explanation, setExplanation] = useState<ExplanationData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isPredicting, setIsPredicting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchProfile = async () => {
      setIsLoading(true);
      setError('');
      try {
        const empRes = await axios.get(`http://localhost:8000/api/v1/workforce/employees/${employeeId}`);
        setEmployee(empRes.data);
        
        // Fetch SHAP explanation & prediction
        try {
          const expRes = await axios.get(`http://localhost:8000/api/v1/attrition/explain/${employeeId}`);
          setPrediction({
            probability: expRes.data.probability,
            risk_level: expRes.data.risk_level
          });
          setExplanation(expRes.data.explanation);
        } catch (e) {
          // If prediction hasn't been run yet, that's fine
        }
      } catch (err) {
        setError('Employee not found or failed to fetch profile.');
      } finally {
        setIsLoading(false);
      }
    };
    if (employeeId) fetchProfile();
  }, [employeeId]);

  const handleRunPrediction = async () => {
    if (!employeeId) return;
    setIsPredicting(true);
    try {
      const predRes = await axios.post(`http://localhost:8000/api/v1/attrition/predict/${employeeId}`);
      setPrediction(predRes.data);
      
      const expRes = await axios.get(`http://localhost:8000/api/v1/attrition/explain/${employeeId}`);
      setExplanation(expRes.data.explanation);
    } catch (e) {
      console.error(e);
    } finally {
      setIsPredicting(false);
    }
  };

  if (isLoading) return <div className="p-8 text-center text-gray-500">Loading employee profile...</div>;
  if (error || !employee) {
    return (
      <div className="p-8 text-center text-red-600">
        <p>{error || 'Employee profile unavailable.'}</p>
        <button onClick={() => navigate('/dashboard/workforce/employees')} className="mt-4 px-4 py-2 bg-indigo-600 text-white rounded-md text-sm">
          Return to Directory
        </button>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-6">
      <button 
        onClick={() => navigate('/dashboard/workforce/employees')} 
        className="inline-flex items-center text-indigo-600 dark:text-indigo-400 hover:text-indigo-800 text-sm font-medium transition-colors"
      >
        <ArrowLeft className="w-4 h-4 mr-1" /> Back to Employee Directory
      </button>

      {/* Profile Overview Header Card */}
      <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm border border-gray-100 dark:border-gray-700 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div className="flex items-center space-x-6">
          <div className="p-4 bg-indigo-50 dark:bg-indigo-900/30 rounded-full">
            <UserCircle className="w-16 h-16 text-indigo-600 dark:text-indigo-400" />
          </div>
          <div>
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white">{employee.name}</h2>
            <p className="text-base text-gray-500 dark:text-gray-400 mt-0.5">{employee.role} &middot; <span className="font-semibold text-gray-700 dark:text-gray-300">{employee.department}</span></p>
            <div className="mt-3 flex flex-wrap gap-4 text-xs text-gray-500 dark:text-gray-400">
              <div>Employee ID: <span className="font-semibold text-gray-900 dark:text-white">{employee.employee_id}</span></div>
              <div>Joined: <span className="font-semibold text-gray-900 dark:text-white">{employee.joining_date ? new Date(employee.joining_date).toLocaleDateString() : 'N/A'}</span></div>
              <div>Status: <span className="px-2 py-0.5 rounded-full font-semibold bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400">{employee.employment_status}</span></div>
            </div>
          </div>
        </div>

        <button
          onClick={handleRunPrediction}
          disabled={isPredicting}
          className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-md text-sm font-medium shadow-sm flex items-center disabled:opacity-50"
        >
          <Brain className="w-4 h-4 mr-2" />
          {isPredicting ? 'Running AI Model...' : 'Calculate Attrition Risk'}
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Metrics & Career Details */}
        <div className="space-y-6 lg:col-span-1">
          {/* Performance & Engagement */}
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm border border-gray-100 dark:border-gray-700">
            <h3 className="font-semibold text-gray-900 dark:text-white flex items-center mb-4 text-sm">
              <TrendingUp className="w-4 h-4 mr-2 text-indigo-500" /> Performance & Engagement
            </h3>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-xs font-medium mb-1">
                  <span className="text-gray-500 dark:text-gray-400">Performance Rating</span>
                  <span className="text-gray-900 dark:text-white font-bold">{employee.performance_score} / 5</span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div className="bg-indigo-600 h-2 rounded-full" style={{ width: `${(employee.performance_score / 5) * 100}%` }}></div>
                </div>
              </div>

              <div>
                <div className="flex justify-between text-xs font-medium mb-1">
                  <span className="text-gray-500 dark:text-gray-400">Engagement Score</span>
                  <span className="text-gray-900 dark:text-white font-bold">{employee.engagement_score} / 5</span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div className="bg-emerald-500 h-2 rounded-full" style={{ width: `${(employee.engagement_score / 5) * 100}%` }}></div>
                </div>
              </div>
            </div>
          </div>

          {/* Key Employee Attributes */}
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm border border-gray-100 dark:border-gray-700">
            <h3 className="font-semibold text-gray-900 dark:text-white flex items-center mb-4 text-sm">
              <Briefcase className="w-4 h-4 mr-2 text-indigo-500" /> Career Information
            </h3>
            <dl className="space-y-3 text-xs">
              <div className="flex justify-between">
                <dt className="text-gray-500 dark:text-gray-400">Total Experience</dt>
                <dd className="font-semibold text-gray-900 dark:text-white">{employee.experience} yrs</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500 dark:text-gray-400">Compensation</dt>
                <dd className="font-semibold text-gray-900 dark:text-white">${employee.salary?.toLocaleString()}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500 dark:text-gray-400">Weekly Overtime</dt>
                <dd className="font-semibold text-gray-900 dark:text-white">{employee.overtime} hrs/wk</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500 dark:text-gray-400">Promotions</dt>
                <dd className="font-semibold text-gray-900 dark:text-white">{employee.promotion_history}</dd>
              </div>
            </dl>
          </div>
        </div>

        {/* Right Column: Trained Attrition Model Intelligence & SHAP Explanation */}
        <div className="lg:col-span-2 space-y-6">
          {/* Attrition Risk Card */}
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm border border-gray-100 dark:border-gray-700">
            <h3 className="text-base font-semibold text-gray-900 dark:text-white flex items-center mb-4">
              <AlertTriangle className="w-5 h-5 mr-2 text-amber-500" /> Trained Attrition Model Analysis
            </h3>
            
            {prediction ? (
              <div className="space-y-6">
                <div className="flex items-end space-x-6 bg-gray-50 dark:bg-gray-700/40 p-5 rounded-lg border border-gray-200 dark:border-gray-600">
                  <div>
                    <span className="text-xs text-gray-500 dark:text-gray-400 block mb-1">Estimated Attrition Risk</span>
                    <div className="text-4xl font-bold text-gray-900 dark:text-white">
                      {Math.round(prediction.probability * 100)}%
                    </div>
                  </div>
                  <div className="pb-1">
                    <span className={`inline-flex px-3 py-1 text-xs font-bold rounded-full ${
                      prediction.risk_level === 'HIGH' ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400' :
                      prediction.risk_level === 'MEDIUM' ? 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400' :
                      'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                    }`}>
                      {prediction.risk_level} RISK
                    </span>
                  </div>
                </div>

                {/* SHAP Factors Section */}
                <div>
                  <h4 className="text-sm font-semibold text-gray-900 dark:text-white flex items-center mb-2">
                    <Sparkles className="w-4 h-4 mr-2 text-indigo-500" /> Why this prediction?
                  </h4>
                  
                  {explanation && explanation.available && explanation.top_factors.length > 0 ? (
                    <div className="space-y-2.5 mt-3">
                      {explanation.top_factors.map((factor, idx) => (
                        <div key={idx} className="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-md border border-gray-100 dark:border-gray-700 flex items-center justify-between text-xs">
                          <div className="flex items-center space-x-2.5">
                            <span className={`w-2.5 h-2.5 rounded-full ${factor.impact === 'negative' ? 'bg-red-500' : 'bg-green-500'}`}></span>
                            <span className="font-medium text-gray-800 dark:text-gray-200">{factor.description}</span>
                          </div>
                          {factor.shap_value !== undefined && (
                            <span className="text-gray-400 font-mono text-[11px]">SHAP: {factor.shap_value}</span>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-2 italic">
                      Explanation unavailable for this model prediction.
                    </p>
                  )}
                </div>
              </div>
            ) : (
              <div className="p-6 bg-gray-50 dark:bg-gray-700/40 rounded-lg text-center">
                <p className="text-sm text-gray-600 dark:text-gray-300 mb-4">
                  No attrition prediction generated yet for this employee.
                </p>
                <button
                  onClick={handleRunPrediction}
                  disabled={isPredicting}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-md text-xs font-medium"
                >
                  Run Prediction Now
                </button>
              </div>
            )}
          </div>

          {/* Feedback & Skills */}
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm border border-gray-100 dark:border-gray-700">
            <h3 className="font-semibold text-gray-900 dark:text-white mb-4 text-sm">Manager Feedback & Skills</h3>
            <div className="mb-4">
              <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Manager Feedback</h4>
              <p className="text-xs text-gray-700 dark:text-gray-300 italic bg-gray-50 dark:bg-gray-700/50 p-3 rounded border border-gray-100 dark:border-gray-700">
                "{employee.manager_feedback || 'No feedback recorded.'}"
              </p>
            </div>
            <div>
              <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Skills & Competencies</h4>
              <div className="flex flex-wrap gap-2">
                {employee.skills ? employee.skills.split(';').map((s: string, i: number) => (
                  <span key={i} className="px-3 py-1 bg-indigo-50 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300 rounded-full text-xs font-medium border border-indigo-100 dark:border-indigo-800">
                    {s.trim()}
                  </span>
                )) : <span className="text-xs text-gray-400">None listed</span>}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
