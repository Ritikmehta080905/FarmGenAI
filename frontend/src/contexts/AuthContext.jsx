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
        dispatch({ type: AUTH_ACTIONS.LOGIN_SUCCESS, payload: DEFAULT_DEMO_USER });
      }
    } else {
      // Default to demo session for instant evaluation
      localStorage.setItem('agri_token', 'mock_token');
      localStorage.setItem('agri_user', JSON.stringify(DEFAULT_DEMO_USER));
      dispatch({ type: AUTH_ACTIONS.LOGIN_SUCCESS, payload: DEFAULT_DEMO_USER });
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

  const login = async ({ phone, password }) => {
    dispatch({ type: AUTH_ACTIONS.LOGIN_REQUEST });
    
    const cleanPhone = (phone || '').toLowerCase().trim();
    const cleanPass = (password || '').toLowerCase().trim();

    // Determine target role from input or default to farmer
    let targetRole = 'farmer';
    const roles = ['admin', 'farmer', 'buyer', 'warehouse', 'transport', 'processor'];
    
    if (roles.includes(cleanPhone)) {
      targetRole = cleanPhone;
    } else if (roles.includes(cleanPass)) {
      targetRole = cleanPass;
    }

    const mockUser = {
      id: Date.now(),
      name: `Demo ${targetRole.charAt(0).toUpperCase() + targetRole.slice(1)}`,
      role: targetRole
    };

    localStorage.setItem('agri_user', JSON.stringify(mockUser));
    localStorage.setItem('agri_token', 'mock_token');
    dispatch({ type: AUTH_ACTIONS.LOGIN_SUCCESS, payload: mockUser });
    return { success: true, role: targetRole };
  };

  const register = async (userData) => {
    const role = userData?.role || 'farmer';
    const mockUser = {
      id: Date.now(),
      name: userData?.name || 'Registered User',
      role: role
    };
    localStorage.setItem('agri_user', JSON.stringify(mockUser));
    localStorage.setItem('agri_token', 'mock_token');
    dispatch({ type: AUTH_ACTIONS.LOGIN_SUCCESS, payload: mockUser });
    return { success: true, user: mockUser };
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
