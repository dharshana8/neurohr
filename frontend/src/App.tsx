import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Import from './pages/Import';
import EmployeeDirectory from './pages/EmployeeDirectory';
import EmployeeProfile from './pages/EmployeeProfile';
import AttritionDashboard from './pages/AttritionDashboard';
import ProtectedRoute from './components/ProtectedRoute';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          
          <Route element={<ProtectedRoute />}>
            <Route path="/dashboard" element={<Dashboard />}>
              <Route path="overview" element={<div className="p-8"><h2 className="text-2xl font-bold">Overview</h2><p>Select an option from the sidebar.</p></div>} />
              <Route path="workforce/import" element={<Import />} />
              <Route path="workforce/employees" element={<EmployeeDirectory />} />
              <Route path="workforce/employees/:employeeId" element={<EmployeeProfile />} />
              <Route path="intelligence/attrition" element={<AttritionDashboard />} />
            </Route>
            <Route path="/" element={<Navigate to="/dashboard/overview" replace />} />
          </Route>
          
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
