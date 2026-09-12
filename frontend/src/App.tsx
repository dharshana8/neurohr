import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import { ToastProvider } from './context/ToastContext';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Import from './pages/Import';
import EmployeeDirectory from './pages/EmployeeDirectory';
import EmployeeProfile from './pages/EmployeeProfile';
import AttritionDashboard from './pages/AttritionDashboard';
import ProtectedRoute from './components/ProtectedRoute';

import JobList from './pages/talent/JobList';
import JobCreate from './pages/talent/JobCreate';
import JobDetail from './pages/talent/JobDetail';
import CandidateList from './pages/talent/CandidateList';
import CandidateProfile from './pages/talent/CandidateProfile';
import ResumeUpload from './pages/talent/ResumeUpload';
import CandidateRanking from './pages/talent/CandidateRanking';
import Integrations from './pages/Settings/Integrations';
import SkillGapDashboard from './pages/intelligence/SkillGapDashboard';
import SkillGapEmployeeDetail from './pages/intelligence/SkillGapEmployeeDetail';
import CareerPathDashboard from './pages/intelligence/CareerPathDashboard';
import WorkplaceSentimentDashboard from './pages/intelligence/WorkplaceSentimentDashboard';
import FeedbackManagement from './pages/intelligence/FeedbackManagement';
import SentimentDetail from './pages/intelligence/SentimentDetail';
import AICopilot from './pages/ai/AICopilot';

import IndexRedirect from './components/IndexRedirect';
import RoleProtectedRoute from './components/RoleProtectedRoute';
import PlatformAdminDashboard from './pages/PlatformAdminDashboard';

function App() {
  return (
    <ThemeProvider>
      <ToastProvider>
        <AuthProvider>
          <BrowserRouter>
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              
              <Route element={<ProtectedRoute />}>
                <Route path="/" element={<IndexRedirect />} />
                
                {/* SuperAdmin Routes */}
                <Route element={<RoleProtectedRoute allowedRoles={['PLATFORM_ADMIN']} />}>
                  <Route path="/platform-admin/overview" element={<PlatformAdminDashboard />} />
                </Route>

                {/* Tenant / HR Routes */}
                <Route element={<RoleProtectedRoute allowedRoles={['ORGANIZATION_ADMIN', 'HR_MANAGER', 'RECRUITER', 'HR_ANALYST']} />}>
                  <Route path="/dashboard" element={<Dashboard />}>
                    <Route path="overview" element={<div />} />
                    <Route path="ai/copilot" element={<AICopilot />} />
                    <Route path="workforce/import" element={<Import />} />
                    <Route path="workforce/employees" element={<EmployeeDirectory />} />
                    <Route path="workforce/employees/:employeeId" element={<EmployeeProfile />} />
                    <Route path="intelligence/attrition" element={<AttritionDashboard />} />
                    <Route path="intelligence/skill-gaps" element={<SkillGapDashboard />} />
                    <Route path="intelligence/skill-gaps/:employeeId" element={<SkillGapEmployeeDetail />} />
                    <Route path="intelligence/career-paths" element={<CareerPathDashboard />} />
                    <Route path="intelligence/sentiment" element={<WorkplaceSentimentDashboard />} />
                    <Route path="intelligence/sentiment/feedback" element={<FeedbackManagement />} />
                    <Route path="intelligence/sentiment/:feedbackId" element={<SentimentDetail />} />
                    
                    {/* Talent Recruitment Routes */}
                    <Route path="talent/jobs" element={<JobList />} />
                    <Route path="talent/jobs/new" element={<JobCreate />} />
                    <Route path="talent/jobs/:jobId" element={<JobDetail />} />
                    <Route path="talent/candidates" element={<CandidateList />} />
                    <Route path="talent/candidates/upload" element={<ResumeUpload />} />
                    <Route path="talent/candidates/:candidateId" element={<CandidateProfile />} />
                    <Route path="talent/jobs/:jobId/ranking" element={<CandidateRanking />} />
                    
                    {/* Settings Routes */}
                    <Route path="settings/integrations" element={<Integrations />} />
                  </Route>
                </Route>
              </Route>

              <Route path="*" element={<Navigate to="/login" replace />} />
            </Routes>
          </BrowserRouter>
        </AuthProvider>
      </ToastProvider>
    </ThemeProvider>
  );
}

export default App;
