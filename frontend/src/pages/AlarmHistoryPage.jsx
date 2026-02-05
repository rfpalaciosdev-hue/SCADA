import React, { useState, useEffect, useMemo } from 'react';
import { useSCADA } from '../contexts/SCADAContext';
import { useAlarms } from '../contexts/AlarmContext';
import { fetchAlarmHistory, acknowledgeAllHistory } from '../services/alarmService';
import { History, Layers, Cog, Search, FileText, Calendar, ShieldCheck, CheckCircle, AlertCircle } from 'lucide-react';

const AlarmHistoryPage = () => {
    const { tags } = useSCADA();
    const { acknowledge, loadAlarms } = useAlarms();
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filterAudited, setFilterAudited] = useState('ALL'); // ALL, PENDING, AUDITED

    // Estados para filtrado jerárquico
    const [selectedArea, setSelectedArea] = useState('All');
    const [selectedMachine, setSelectedMachine] = useState('All');

    const loadHistory = async () => {
        setLoading(true);
        try {
            const data = await fetchAlarmHistory();
            setHistory(data);
        } catch (err) {
            console.error("Error loading alarm history:", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadHistory();
    }, []);

    const handleAcknowledgeAll = async () => {
        if (!window.confirm("¿Desea marcar TODOS los eventos como auditados?")) return;
        try {
            await acknowledgeAllHistory();
            await loadHistory();
            await loadAlarms(); // Sync notifications
            alert("✅ Todos los eventos han sido auditados.");
        } catch (err) {
            alert("❌ Error al auditar.");
        }
    };

    const handleSingleAcknowledge = async (id) => {
        try {
            await acknowledge(id, 'HISTORY');
            await loadHistory();
            await loadAlarms(); // Sync notifications
        } catch (err) {
            console.error("Acknowledge error:", err);
        }
    };

    // Estructura de tags para filtros
    const hierarchy = useMemo(() => {
        const tree = {};
        Object.keys(tags).forEach(path => {
            const parts = path.split('/');
            const area = parts[1] || 'General';
            const machine = parts[2] || 'Common';
            if (!tree[area]) tree[area] = new Set();
            tree[area].add(machine);
        });
        return tree;
    }, [tags]);

    const areas = ['All', ...Object.keys(hierarchy)];
    const machines = selectedArea === 'All'
        ? ['All']
        : ['All', ...Array.from(hierarchy[selectedArea] || [])];

    const filteredHistory = history.filter(log => {
        const parts = log.path.split('/');
        const area = parts[1] || 'General';
        const machine = parts[2] || 'Common';

        const areaMatch = selectedArea === 'All' || area === selectedArea;
        const machineMatch = selectedMachine === 'All' || machine === selectedMachine;

        const auditMatch = filterAudited === 'ALL'
            || (filterAudited === 'PENDING' && !log.ack)
            || (filterAudited === 'AUDITED' && log.ack);

        return areaMatch && machineMatch && auditMatch;
    });

    const getPriorityColor = (p) => {
        switch (p) {
            case 'CRITICAL': return 'var(--accent-red)';
            case 'HIGH': return '#ff8c00';
            case 'MEDIUM': return 'var(--accent-yellow)';
            default: return 'var(--accent-cyan)';
        }
    };

    return (
        <div className="dashboard-grid-container">
            <aside className="sidebar">
                <div className="filter-group">
                    <div className="filter-title"><ShieldCheck size={14} /> Estado de Auditoría</div>
                    <select
                        value={filterAudited}
                        onChange={(e) => setFilterAudited(e.target.value)}
                        style={{ width: '100%', padding: '0.6rem', borderRadius: '8px', background: 'rgba(255,255,255,0.05)', color: 'white', border: '1px solid var(--border-color)' }}
                    >
                        <option value="ALL">Todos los Eventos</option>
                        <option value="PENDING">⚠️ Solo Pendientes</option>
                        <option value="AUDITED">✅ Solo Auditados</option>
                    </select>
                </div>

                <div className="filter-group">
                    <div className="filter-title"><Layers size={14} /> Filtrar por Área</div>
                    {areas.map(area => (
                        <div key={area} className={`filter-option ${selectedArea === area ? 'active' : ''}`} onClick={() => { setSelectedArea(area); setSelectedMachine('All'); }}>
                            {area}
                        </div>
                    ))}
                </div>

                {selectedArea !== 'All' && (
                    <div className="filter-group">
                        <div className="filter-title"><Cog size={14} /> Filtrar por Equipo</div>
                        {machines.map(machine => (
                            <div key={machine} className={`filter-option ${selectedMachine === machine ? 'active' : ''}`} onClick={() => setSelectedMachine(machine)}>
                                {machine}
                            </div>
                        ))}
                    </div>
                )}
            </aside>

            <main className="main-content">
                <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem', flexWrap: 'wrap', gap: '1rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                        <div style={{ background: 'rgba(34, 211, 238, 0.1)', padding: '0.75rem', borderRadius: '12px' }}>
                            <History size={24} color="var(--accent-cyan)" />
                        </div>
                        <div>
                            <h2 style={{ fontSize: '1.5rem', margin: 0 }}>Log de Eventos</h2>
                            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Registro histórico y auditoría de seguridad</p>
                        </div>
                    </div>
                    <div style={{ display: 'flex', gap: '0.75rem' }}>
                        <button
                            onClick={handleAcknowledgeAll}
                            style={{
                                padding: '0.7rem 1.2rem', borderRadius: '8px',
                                background: 'rgba(34, 211, 238, 0.1)', border: '1px solid var(--accent-cyan)',
                                color: 'var(--accent-cyan)', cursor: 'pointer', fontWeight: 'bold',
                                display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.9rem'
                            }}
                        >
                            <ShieldCheck size={18} /> Auditar Todos
                        </button>
                        <button
                            onClick={loadHistory}
                            style={{
                                padding: '0.7rem 1.2rem', borderRadius: '8px',
                                background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-color)',
                                color: 'white', cursor: 'pointer', display: 'flex', alignItems: 'center',
                                justifyContent: 'center', gap: '0.5rem', fontSize: '0.9rem'
                            }}
                        >
                            <Search size={18} /> Actualizar
                        </button>
                    </div>
                </header>

                <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                        <thead>
                            <tr style={{ textAlign: 'left', background: 'rgba(255,255,255,0.02)', borderBottom: '1px solid var(--border-color)', opacity: 0.6, fontSize: '0.75rem' }}>
                                <th style={{ padding: '1rem' }}>SENSOR / PATH</th>
                                <th style={{ padding: '1rem' }}>REGLA</th>
                                <th style={{ padding: '1rem' }}>VALOR EVENTO</th>
                                <th style={{ padding: '1rem' }}>TIEMPOS</th>
                                <th style={{ padding: '1rem' }}>ESTADO</th>
                                <th style={{ padding: '1rem', textAlign: 'right' }}>ACCIONES</th>
                            </tr>
                        </thead>
                        <tbody>
                            {loading ? (
                                <tr><td colSpan="6" style={{ padding: '4rem', textAlign: 'center', opacity: 0.5 }}>Cargando historial...</td></tr>
                            ) : filteredHistory.length === 0 ? (
                                <tr><td colSpan="6" style={{ padding: '4rem', textAlign: 'center', opacity: 0.5 }}>No se encontraron registros.</td></tr>
                            ) : (
                                filteredHistory.map(log => (
                                    <tr key={log.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)', fontSize: '0.9rem', opacity: log.ack ? 0.6 : 1 }}>
                                        <td style={{ padding: '1rem' }}>
                                            <div style={{ fontWeight: 'bold', color: log.ack ? 'var(--text-secondary)' : 'white' }}>{log.path.split('/').pop()}</div>
                                            <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>{log.path}</div>
                                        </td>
                                        <td style={{ padding: '1rem' }}>
                                            <span style={{ color: 'var(--accent-cyan)' }}>{log.operator} {log.threshold}</span>
                                        </td>
                                        <td style={{ padding: '1rem', fontWeight: 'bold', color: getPriorityColor(log.priority) }}>
                                            {log.max_val?.toFixed(2)}
                                        </td>
                                        <td style={{ padding: '1rem' }}>
                                            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Inició: {new Date(log.start).toLocaleString()}</div>
                                            <div style={{ fontSize: '0.75rem', color: 'var(--accent-green)', marginTop: '0.2rem' }}>Cerró: {log.end ? new Date(log.end).toLocaleTimeString() : '---'}</div>
                                        </td>
                                        <td style={{ padding: '1rem' }}>
                                            {log.ack ? (
                                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--accent-green)', fontSize: '0.75rem' }}>
                                                    <CheckCircle size={14} /> Auditada
                                                </div>
                                            ) : (
                                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--accent-yellow)', fontSize: '0.75rem' }}>
                                                    <AlertCircle size={14} /> Pendiente
                                                </div>
                                            )}
                                        </td>
                                        <td style={{ padding: '1rem', textAlign: 'right' }}>
                                            {!log.ack && (
                                                <button
                                                    onClick={() => handleSingleAcknowledge(log.id)}
                                                    style={{ border: '1px solid var(--border-color)', background: 'rgba(255,255,255,0.05)', color: 'white', padding: '0.4rem 0.8rem', borderRadius: '6px', fontSize: '0.75rem', cursor: 'pointer' }}
                                                >
                                                    Auditar
                                                </button>
                                            )}
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </main>
        </div>
    );
};

export default AlarmHistoryPage;
