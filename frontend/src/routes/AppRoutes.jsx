import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import MainLayout from '../layouts/MainLayout';
import DashboardPage from '../pages/DashboardPage';
import TrendsPage from '../pages/TrendsPage';
import AdminAlarmsPage from '../pages/AdminAlarmsPage';
import AlarmHistoryPage from '../pages/AlarmHistoryPage';

const AppRoutes = () => {
    return (
        <Routes>
            <Route element={<MainLayout />}>
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route path="/dashboard" element={<DashboardPage />} />
                <Route path="/trends" element={<TrendsPage />} />
                <Route path="/admin/alarms" element={<AdminAlarmsPage />} />
                <Route path="/admin/alarm-history" element={<AlarmHistoryPage />} />
                <Route path="*" element={<div>404 - Not Found</div>} />
            </Route>
        </Routes>
    );
};

export default AppRoutes;
