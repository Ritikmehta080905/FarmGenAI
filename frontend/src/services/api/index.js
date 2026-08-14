import axios from 'axios';
import { API_CONFIG } from '@/config/api';

const API_URL = API_CONFIG.BASE_URL;

export const api = axios.create({
  baseURL: API_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('agri_token');
    if (token && token !== 'mock_token') {
      config.headers.Authorization = `Bearer ${token}`;
    }
    if (config.data instanceof FormData) {
      delete config.headers['Content-Type'];
    }
    return config;
  },
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response && error.response.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const res = await axios.post(`${API_URL}/auth/refresh`, {}, { withCredentials: true });

        if (res.status === 200 && res.data.access_token) {
          localStorage.setItem('agri_token', res.data.access_token);
          originalRequest.headers.Authorization = `Bearer ${res.data.access_token}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        localStorage.removeItem('agri_token');
        localStorage.removeItem('agri_user');
        return Promise.reject(refreshError);
      }
    }

    let errorMessage = 'An unexpected error occurred.';
    if (!error.response) {
      // Do not spam popups if page is loading public data
      if (originalRequest?.url?.includes('/auth/refresh')) {
        return Promise.reject(error);
      }
      errorMessage = 'Connecting to background server...';
    } else if (error.response.status >= 500) {
      errorMessage = `Server Error (${error.response.status}): The backend failed to process the request.`;
    } else if (error.response.status === 403) {
      errorMessage = 'Forbidden: You do not have permission to access this resource.';
    } else if (error.response.data && error.response.data.detail) {
      errorMessage = typeof error.response.data.detail === 'string' 
        ? error.response.data.detail 
        : 'Validation error';
    }

    if (error.response && error.response.status >= 400 && error.response.status !== 401) {
      window.dispatchEvent(new CustomEvent('api_error', { detail: errorMessage }));
    }

    return Promise.reject(error);
  }
);

export { AuthService } from './AuthService';
export { NegotiationService } from './NegotiationService';
