import { createContext, useContext, useReducer, useEffect } from 'react';
import { AuthService } from '../services/api/AuthService';
import { authReducer, initialAuthState, AUTH_ACTIONS } from '../reducers/authReducer';

const AuthContext = createContext(null);

const DEFAULT_DEMO_USER = { id: 1, name: 'Demo User', role: 'farmer' };

export function AuthProvider({ children }) {
  const [state, dispatch] = useReducer(authReducer, initialAuthState);

  useEffect(() => {
    // Check for existing token and user data on load
    const token = localStorage.getItem('agri_token');
    const storedUser = localStorage.getItem('agri_user');
    
    if (token && storedUser) {
      try {
        dispatch({ type: AUTH_ACTIONS.LOGIN_SUCCESS, payload: JSON.parse(storedUser) });
      } catch (e) {
        localStorage.removeItem('agri_token');
        localStorage.removeItem('agri_user');
        dispatch({ type: AUTH_ACTIONS.LOGOUT });
      }
    } else {
      localStorage.removeItem('agri_token');
      localStorage.removeItem('agri_user');
      dispatch({ type: AUTH_ACTIONS.LOGOUT });
    }

    // Cross-Tab Logout Synchronization
    const handleStorageChange = (e) => {
      if (e.key === 'agri_token' && e.newValue === null) {
        dispatch({ type: AUTH_ACTIONS.LOGOUT });
        window.location.href = '/login';
      }
    };
    window.addEventListener('storage', handleStorageChange);

    return () => window.removeEventListener('storage', handleStorageChange);
  }, []);

  const login = async ({ phone, email, password }) => {
    dispatch({ type: AUTH_ACTIONS.LOGIN_REQUEST });
    
    const identifier = (email || phone || '').trim();
    const cleanPass = (password || '').trim();

    try {
      const res = await AuthService.login({ email: identifier, password: cleanPass });
      if (res && res.token) {
        const userObj = {
          id: res.user_id || Date.now(),
          name: res.name || 'User',
          role: (res.role || 'farmer').toLowerCase()
        };
        localStorage.setItem('agri_user', JSON.stringify(userObj));
        localStorage.setItem('agri_token', res.token);
        dispatch({ type: AUTH_ACTIONS.LOGIN_SUCCESS, payload: userObj });
        return { success: true, role: userObj.role };
      }
      return { success: false, error: res?.error || 'Invalid credentials' };
    } catch (err) {
      console.error('API login failed:', err);
      return { success: false, error: err.response?.data?.detail || err.message || 'Login failed. Please check your credentials.' };
    }
  };

  const register = async (userData) => {
    try {
      const res = await AuthService.register(userData);
      if (res && res.token) {
        const userObj = {
          id: res.user_id || Date.now(),
          name: res.name || userData?.name || 'Registered User',
          role: (res.role || userData?.role || 'farmer').toLowerCase()
        };
        localStorage.setItem('agri_user', JSON.stringify(userObj));
        localStorage.setItem('agri_token', res.token);
        dispatch({ type: AUTH_ACTIONS.LOGIN_SUCCESS, payload: userObj });
        return { success: true, user: userObj };
      }
      return { success: false, error: res?.error || 'Registration failed' };
    } catch (err) {
      console.error('API register failed:', err);
      return { success: false, error: err.response?.data?.detail || err.message || 'Registration failed' };
    }
  };

  const logout = () => {
    localStorage.removeItem('agri_user');
    localStorage.removeItem('agri_token');
    dispatch({ type: AUTH_ACTIONS.LOGOUT });
    window.location.href = '/login';
  };

  const triggerSessionExpired = () => {
    localStorage.removeItem('agri_user');
    localStorage.removeItem('agri_token');
    dispatch({ type: AUTH_ACTIONS.SESSION_EXPIRED });
  };

  return (
    <AuthContext.Provider value={{ 
      ...state, 
      login, 
      logout, 
      register,
      triggerSessionExpired
    }}>
      {!state.loading && children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
