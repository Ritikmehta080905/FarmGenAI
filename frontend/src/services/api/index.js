import axios from 'axios';

// Replace with your FastAPI backend URL from env vars
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export const api = axios.create({
  baseURL: API_URL,
  withCredentials: true, // Crucial for HttpOnly secure cookies
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request Interceptor: Attach JWT token if stored in localStorage (Fallback if not using HttpOnly cookies)
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('agri_token');
    // If the backend has moved to HttpOnly cookies, this header isn't strictly necessary, 
    // but we keep it here for backward compatibility during the transition.
    if (token && token !== 'mock_token') {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor: Handle 401 Unauthorized globally & Refresh Tokens
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // If 401 and we haven't already retried
    if (error.response && error.response.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        // Attempt to hit the refresh token endpoint
        const res = await axios.post(`${API_URL}/auth/refresh`, {}, { withCredentials: true });
        
        if (res.status === 200) {
          // If the backend returns a new token in the payload (optional, if not using pure cookies)
          if (res.data.access_token) {
             localStorage.setItem('agri_token', res.data.access_token);
             originalRequest.headers.Authorization = `Bearer ${res.data.access_token}`;
          }
          // Retry the original failed request
          return api(originalRequest);
        }
      } catch (refreshError) {
        // Refresh token failed or expired. Force logout.
        localStorage.removeItem('agri_token');
        localStorage.removeItem('agri_user');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    
    // Centralized Global Error Handling
    let errorMessage = 'An unexpected error occurred.';
    if (!error.response) {
      errorMessage = 'Network Error: Cannot connect to server.';
    } else if (error.response.status >= 500) {
      errorMessage = `Server Error (${error.response.status}): The backend failed to process the request.`;
    } else if (error.response.status === 403) {
      errorMessage = 'Forbidden: You do not have permission to access this resource.';
    } else if (error.response.data && error.response.data.detail) {
      const detail = error.response.data.detail;
      if (Array.isArray(detail)) {
        errorMessage = detail.map(err => {
          const field = err.loc ? err.loc.filter(l => l !== 'body' && l !== 'query').join('.') : 'Field';
          return `${field}: ${err.msg}`;
        }).join(', ');
      } else {
        errorMessage = String(detail);
      }
    }

    // Dispatch global event for the NotificationProvider to catch
    window.dispatchEvent(new CustomEvent('api_error', { detail: errorMessage }));
    
    return Promise.reject(error);
  }
);
