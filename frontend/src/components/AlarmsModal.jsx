import React from 'react';
import { X, Bell, CheckCircle, Info, AlertTriangle, ShieldOff } from 'lucide-react';
import { useAlarms } from '../contexts/AlarmContext';

const AlarmsModal = ({ isOpen, onClose }) => {
    const { activeAlarms, acknowledge } = useAlarms();

    if (!isOpen) return null;

    const getPriorityColor = (p) => {
        switch (p) {
            case 'CRITICAL': return 'var(--accent-red)';
            case 'HIGH': return '#ff8c00';
            case 'MEDIUM': return 'var(--accent-yellow)';
            default: return 'var(--accent-cyan)';
        }
    };

    return (
        <div style={{
            position: 'fixed', top: 0, left: 0, width: '100%', height: '100%',
            background: 'rgba(0,0,0,0.8)', backdropFilter: 'blur(8px)',
            display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 10000
        }} onClick={onClose}>
            <div style={{
                width: '600px', maxHeight: '80vh', background: 'var(--bg-color)',
                border: '1px solid var(--border-color)', borderRadius: '16px',
                display: 'flex', flexDirection: 'column', overflow: 'hidden'
            }} onClick={e => e.stopPropagation()}>

                <header style={{
                    padding: '1.5rem', borderBottom: '1px solid var(--border-color)',
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    background: 'rgba(255,255,255,0.02)'
                }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        <Bell size={20} color="var(--accent-red)" />
                        <h2 style={{ fontSize: '1.25rem', margin: 0 }}>Alarmas Activas</h2>
                    </div>
                    <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer' }}>
                        <X size={24} />
                    </button>
                </header>

                <div style={{ flexGrow: 1, overflowY: 'auto', padding: '1rem' }}>
                    {activeAlarms.length === 0 ? (
                        <div style={{ textAlign: 'center', padding: '4rem', opacity: 0.5 }}>
                            <CheckCircle size={48} color="var(--accent-green)" style={{ marginBottom: '1rem' }} />
                            <p>No hay alarmas activas en el sistema.</p>
                        </div>
                    ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                            {activeAlarms.map(alarm => (
                                <div key={alarm.id} style={{
                                    background: 'rgba(255,255,255,0.03)',
                                    border: `1px solid ${alarm.ack ? 'var(--border-color)' : getPriorityColor(alarm.priority)}`,
                                    borderRadius: '12px', padding: '1rem',
                                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                                    borderLeft: `4px solid ${getPriorityColor(alarm.priority)}`
                                }}>
                                    <div style={{ flexGrow: 1 }}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                                            <span style={{
                                                fontSize: '0.65rem', fontWeight: 'bold', padding: '2px 6px',
                                                borderRadius: '4px', background: getPriorityColor(alarm.priority), color: 'black'
                                            }}>
                                                {alarm.priority}
                                            </span>
                                            <span style={{ fontSize: '0.85rem', fontWeight: 'bold' }}>{alarm.path}</span>
                                        </div>
                                        <div style={{ fontSize: '0.9rem', color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
                                            Valor: <span style={{ color: 'var(--accent-red)', fontWeight: 'bold' }}>{typeof alarm.val === 'number' ? alarm.val.toFixed(2) : alarm.val}</span>
                                            <span style={{ margin: '0 0.5rem', opacity: 0.3 }}>|</span>
                                            Condición: <span style={{ opacity: 0.8 }}>{alarm.operator} {alarm.threshold}</span>
                                        </div>
                                        <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>
                                            Desde: {new Date(alarm.since).toLocaleString()}
                                        </div>
                                    </div>

                                    {!alarm.ack ? (
                                        <button
                                            onClick={() => acknowledge(alarm.raw_id, alarm.source)}
                                            style={{
                                                background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-color)',
                                                color: 'var(--text-primary)', padding: '0.5rem 1rem', borderRadius: '8px',
                                                cursor: 'pointer', fontSize: '0.8rem', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '0.5rem'
                                            }}
                                        >
                                            <ShieldOff size={14} /> Reconocer {alarm.source === 'HISTORY' ? '(Pasada)' : ''}
                                        </button>
                                    ) : (
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--accent-green)', fontSize: '0.8rem' }}>
                                            <CheckCircle size={14} /> Reconocida
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {activeAlarms.length > 0 && (
                    <footer style={{ padding: '1rem', borderTop: '1px solid var(--border-color)', textAlign: 'center', fontSize: '0.75rem', opacity: 0.6 }}>
                        Resuelva la condición física para que la alarma desaparezca de la lista.
                    </footer>
                )}
            </div>
        </div>
    );
};

export default AlarmsModal;
