import { api } from './index';

export const AuthService = {
  /**
   * Login with credentials.
   * @param {Object} credentials - { username, password }
   * @returns {Promise<Object>} User profile and token
   */
  login: async (credentials) => {
    const response = await api.post('/auth/login', credentials);
    return response.data;
  },

  /**
   * Register a new user.
   * @param {Object} userData - User registration data
   * @returns {Promise<Object>} Success response
   */
  register: async (userData) => {
    const response = await api.post('/auth/register', userData);
    return response.data;
  },

  /**
   * Refresh the current session token.
   * @returns {Promise<Object>} New access token
   */
  refreshToken: async () => {
    const response = await api.post('/auth/refresh');
    return response.data;
  },

  /**
   * Logout and invalidate session.
   * @returns {Promise<void>}
   */
  logout: async () => {
    await api.post('/auth/logout');
  }
};
