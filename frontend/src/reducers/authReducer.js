/**
 * Authentication Action Types
 */
export const AUTH_ACTIONS = {
  LOGIN_REQUEST: 'LOGIN_REQUEST',
  LOGIN_SUCCESS: 'LOGIN_SUCCESS',
  LOGIN_FAILURE: 'LOGIN_FAILURE',
  LOGOUT: 'LOGOUT',
  TOKEN_REFRESH: 'TOKEN_REFRESH',
  PROFILE_UPDATE: 'PROFILE_UPDATE',
  SESSION_EXPIRED: 'SESSION_EXPIRED',
  CLEAR_AUTH: 'CLEAR_AUTH',
  ERROR: 'ERROR',
  RESET: 'RESET'
};

/**
 * Initial Authentication State
 */
export const initialAuthState = {
  user: null,
  isAuthenticated: false,
  loading: true,
  error: null,
  sessionExpired: false
};

/**
 * Authentication Reducer
 */
export function authReducer(state, action) {
  switch (action.type) {
    case AUTH_ACTIONS.LOGIN_REQUEST:
      return { ...state, loading: true, error: null };
    case AUTH_ACTIONS.LOGIN_SUCCESS:
      return {
        ...state,
        loading: false,
        isAuthenticated: true,
        user: action.payload,
        error: null,
        sessionExpired: false
      };
    case AUTH_ACTIONS.LOGIN_FAILURE:
    case AUTH_ACTIONS.ERROR:
      return { ...state, loading: false, error: action.payload };
    case AUTH_ACTIONS.LOGOUT:
    case AUTH_ACTIONS.CLEAR_AUTH:
      return {
        ...state,
        user: null,
        isAuthenticated: false,
        loading: false,
        error: null,
        sessionExpired: false
      };
    case AUTH_ACTIONS.SESSION_EXPIRED:
      return {
        ...state,
        user: null,
        isAuthenticated: false,
        loading: false,
        sessionExpired: true
      };
    case AUTH_ACTIONS.PROFILE_UPDATE:
      return {
        ...state,
        user: { ...state.user, ...action.payload }
      };
    case AUTH_ACTIONS.RESET:
      return initialAuthState;
    default:
      return state;
  }
}
