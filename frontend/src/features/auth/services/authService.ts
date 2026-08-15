import { api } from '@/services/api';
import { AuthResponse } from '@/types/models';

export const authService = {
  login: async (credentials: any): Promise<AuthResponse> => {
    const response = await api.post('/auth/login', credentials);
    return response.data;
  },

  register: async (userData: any): Promise<AuthResponse> => {
    const response = await api.post('/auth/register', userData);
    return response.data;
  },

  refreshToken: async (): Promise<{ access_token: string }> => {
    const response = await api.post('/auth/refresh');
    return response.data;
  },

  logout: async (): Promise<void> => {
    await api.post('/auth/logout');
  }
};

export default authService;
