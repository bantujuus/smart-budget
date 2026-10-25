import axios from 'axios';

export const apiClient = axios.create({
    baseURL: '/api/v1',
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request interceptor: attach token from localStorage if present
apiClient.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('smart_budget_token') || localStorage.getItem('token');
        if (token) {
            // DRF TokenAuthentication strictly requires 'Token <key>', not 'Bearer <key>'
            config.headers.Authorization = `Token ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// Response interceptor: auto-logout on 401 Unauthorized
apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response && error.response.status === 401) {
            localStorage.removeItem('smart_budget_token');
            localStorage.removeItem('token');
            if (window.location.pathname !== '/login' && window.location.pathname !== '/register') {
                window.location.href = '/login';
            }
        }
        return Promise.reject(error);
    }
);