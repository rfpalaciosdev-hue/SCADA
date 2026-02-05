import apiClient from './apiClient';

export const fetchAlarmConfigs = () => apiClient.get('/alarms/config');
export const saveAlarmConfig = (config) => apiClient.post('/alarms/config', config);
export const deleteAlarmConfig = (id) => apiClient.delete(`/alarms/config/${id}`);
export const fetchActiveAlarms = () => apiClient.get('/alarms/active');
export const acknowledgeAlarm = (id, source = 'ACTIVE') => apiClient.post(`/alarms/acknowledge/${id}?source=${source}`);
export const fetchAlarmHistory = () => apiClient.get('/alarms/history');
export const acknowledgeAllHistory = () => apiClient.post('/alarms/history/acknowledge-all');
