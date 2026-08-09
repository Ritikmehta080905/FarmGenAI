import { api } from '@/services/api';

export const authService = {
  login: async (credentials) => {
    const response = await api.post('/auth/login', credentials);
    return response.data;
  },

  register: async (userData) => {
    const response = await api.post('/auth/register', userData);
    return response.data;
  },

  refreshToken: async () => {
    const response = await api.post('/auth/refresh');
    return response.data;
  },

  logout: async () => {
    await api.post('/auth/logout');
  }
};

export default authService;
