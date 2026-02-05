import apiClient from './apiClient';

export const fetchTags = () => {
    return apiClient.get('/tags');
};

// Aquí podrías añadir otros como fetchHistorians, updateTagConfig, etc.
