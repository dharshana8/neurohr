import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import axios from 'axios';


interface User {
  id: string;
  email: string;
  role: string;
  organization_id?: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (token: string) => Promise<User | null>;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchUser(token);
    } else {
      setIsLoading(false);
    }
  }, [token]);

  const fetchUser = async (authToken?: string) => {
    const currentToken = authToken || token;
    if (!currentToken) {
      setIsLoading(false);
      return null;
    }
    try {
      axios.defaults.headers.common['Authorization'] = `Bearer ${currentToken}`;
      const response = await axios.get('http://localhost:8000/api/v1/users/me');
      setUser(response.data);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch user', error);
      logout();
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (newToken: string): Promise<User | null> => {
    setIsLoading(true);
    localStorage.setItem('token', newToken);
    setToken(newToken);
    return await fetchUser(newToken);
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    delete axios.defaults.headers.common['Authorization'];
  };

  return (
    <AuthContext.Provider value={{ user, token, login, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
