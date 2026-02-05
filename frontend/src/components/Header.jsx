import React, { useState } from 'react';
import { Cpu, LayoutDashboard, LineChart, Settings, Bell, History } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';
import { useSCADA } from '../contexts/SCADAContext';
import { useAlarms } from '../contexts/AlarmContext';
import AlarmsModal from './AlarmsModal';

const Header = () => {
    const { connected, lastUpdate } = useSCADA();
    const { unreadCount, resetUnread, activeAlarms } = useAlarms();
    const [isAlarmsOpen, setIsAlarmsOpen] = useState(false);
    const location = useLocation();

    const isActive = (path) => location.pathname === path;

    const handleBellClick = () => {
        setIsAlarmsOpen(true);
        resetUnread();
    };

    return (
        <>
            <header className="header" style={{ padding: '1rem 2rem' }}>
                <div style={{ display: 'flex', gap: '3rem', alignItems: 'center' }}>
                    <div>
                        <h1 style={{ fontSize: '1.25rem' }}>SCADA Professional</h1>
                        <p style={{ color: 'var(--text-secondary)', fontSize: '0.7rem' }}>
                            Manufacturing Intelligence
                        </p>
                    </div>

                    <nav style={{ display: 'flex', gap: '1rem' }}>
                        <Link to="/dashboard" style={{
                            display: 'flex', alignItems: 'center', gap: '0.5rem',
                            textDecoration: 'none', color: isActive('/dashboard') ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                            fontSize: '0.9rem', fontWeight: '500', transition: 'all 0.2s'
                        }}>
                            <LayoutDashboard size={18} /> Dashboard
                        </Link>
                        <Link to="/trends" style={{
                            display: 'flex', alignItems: 'center', gap: '0.5rem',
                            textDecoration: 'none', color: isActive('/trends') ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                            fontSize: '0.9rem', fontWeight: '500', transition: 'all 0.2s'
                        }}>
                            <LineChart size={18} /> Trends
                        </Link>
                        <Link to="/admin/alarms" style={{
                            display: 'flex', alignItems: 'center', gap: '0.5rem',
                            textDecoration: 'none', color: isActive('/admin/alarms') ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                            fontSize: '0.9rem', fontWeight: '500', transition: 'all 0.2s'
                        }}>
                            <Settings size={18} /> Config
                        </Link>
                        <Link to="/admin/alarm-history" style={{
                            display: 'flex', alignItems: 'center', gap: '0.5rem',
                            textDecoration: 'none', color: isActive('/admin/alarm-history') ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                            fontSize: '0.9rem', fontWeight: '500', transition: 'all 0.2s'
                        }}>
                            <History size={18} /> Log
                        </Link>
                    </nav>
                </div>
                <div style={{ display: 'flex', gap: '1.5rem', alignItems: 'center' }}>
                    <div style={{ position: 'relative', cursor: 'pointer', display: 'flex', alignItems: 'center' }} onClick={handleBellClick}>
                        <Bell size={20} color={activeAlarms.length > 0 ? 'var(--accent-red)' : 'var(--text-secondary)'} className={unreadCount > 0 ? 'pulse-animation' : ''} />
                        {activeAlarms.filter(a => !a.ack).length > 0 && (
                            <span style={{
                                position: 'absolute', top: '-8px', right: '-8px',
                                background: 'var(--accent-red)', color: 'white',
                                fontSize: '0.65rem', padding: '2px 5px', borderRadius: '10px',
                                fontWeight: 'bold', border: '2px solid var(--bg-color)'
                            }}>
                                {activeAlarms.filter(a => !a.ack).length}
                            </span>
                        )}
                    </div>
                    {lastUpdate && (
                        <span style={{ fontSize: '0.75rem', opacity: 0.6, fontVariantNumeric: 'tabular-nums' }}>
                            LMT: {lastUpdate}
                        </span>
                    )}
                    <div className={`status-badge ${!connected ? 'disconnected' : ''}`}>
                        <Cpu size={14} />
                        {connected ? 'SYSTEM ONLINE' : 'SYSTEM OFFLINE'}
                    </div>
                </div>
            </header>

            <AlarmsModal isOpen={isAlarmsOpen} onClose={() => setIsAlarmsOpen(false)} />
        </>
    );
};

export default Header;
