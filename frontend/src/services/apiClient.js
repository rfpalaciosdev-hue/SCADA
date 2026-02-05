import axios from 'axios';
import config from '../config';

const apiClient = axios.create({
    baseURL: config.API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Interceptor para peticiones
apiClient.interceptors.request.use(
    (config) => {
        // Aquí podrías añadir tokens de auth o logs
        console.log(`📡 [API Request] ${config.method.toUpperCase()} ${config.url}`);
        return config;
    },
    (error) => Promise.reject(error)
);

// Interceptor para respuestas
apiClient.interceptors.response.use(
    (response) => {
        return response.data;
    },
    (error) => {
        console.error(`❌ [API Error]`, error.response?.data || error.message);
        return Promise.reject(error);
    }
);

export default apiClient;
