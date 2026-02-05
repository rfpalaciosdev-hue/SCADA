import React from 'react';
import { Outlet } from 'react-router-dom';
import Header from '../components/Header';

const MainLayout = () => {
    return (
        <div className="scada-layout">
            <Header />
            <main className="dashboard-container">
                <Outlet />
            </main>
        </div>
    );
};

export default MainLayout;
