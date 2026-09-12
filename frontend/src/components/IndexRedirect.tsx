import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function IndexRedirect() {
  const { user, token, isLoading } = useAuth();

  if (isLoading || (token && !user)) return null;

  if (user?.role === 'PLATFORM_ADMIN') {
    return <Navigate to="/platform-admin/overview" replace />;
  }

  if (user) {
    return <Navigate to="/dashboard/overview" replace />;
  }

  return <Navigate to="/login" replace />;
}
