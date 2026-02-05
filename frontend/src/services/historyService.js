import apiClient from './apiClient';

export const fetchHistory = (tagPath, { hours, start, end } = {}) => {
    return apiClient.get(`/history/${tagPath}`, {
        params: { hours, start, end }
    });
};
export const fetchHistoryStats = (tagPath, { hours, start, end } = {}) => {
    return apiClient.get(`/history/${tagPath}/stats`, {
        params: { hours, start, end }
    });
};
