import React, { useState, useMemo } from 'react';
import { useHistory } from '../contexts/HistoryContext';
import { useSCADA } from '../contexts/SCADAContext';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid,
    Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import {
    Calendar, Clock, Search, List, Activity,
    Download, Filter, CheckCircle2, Circle,
    ChevronDown, ChevronRight, Layers, Cog, Trash2, TrendingUp
} from 'lucide-react';
import { format } from 'date-fns';

const TrendsPage = () => {
    const { tags } = useSCADA();
    const { histories, tagStats, loadHistories, loadTagStats, isLoading, clearHistory } = useHistory();

    // Filtros
    const [selectedPaths, setSelectedPaths] = useState([]);
    const [dateFrom, setDateFrom] = useState(format(new Date(Date.now() - 3600000), "yyyy-MM-dd'T'HH:mm"));
    const [dateTo, setDateTo] = useState(format(new Date(), "yyyy-MM-dd'T'HH:mm"));
    const [viewMode, setViewMode] = useState('chart');
    const [statsVisible, setStatsVisible] = useState({}); // { [path]: boolean }
    const [statsLoading, setStatsLoading] = useState({}); // { [path]: boolean }

    // ... (rest of helper functions)

    const toggleStats = async (path) => {
        const isVisible = !statsVisible[path];
        setStatsVisible(prev => ({ ...prev, [path]: isVisible }));

        if (isVisible && !tagStats[path]) {
            setStatsLoading(prev => ({ ...prev, [path]: true }));
            try {
                // Asegurar formato ISO para el backend
                const start = dateFrom ? new Date(dateFrom).toISOString() : null;
                const end = dateTo ? new Date(dateTo).toISOString() : null;

                console.log(`Solicitando estadísticas para ${path}...`, { start, end });
                await loadTagStats(path, { start, end });
            } catch (err) {
                console.error("Error al cargar estadísticas:", err);
            } finally {
                setStatsLoading(prev => ({ ...prev, [path]: false }));
            }
        }
    };

    // Estados para la navegación jerárquica
    const [expandedAreas, setExpandedAreas] = useState({ 'planta_central': true });
    const [expandedMachines, setExpandedMachines] = useState({});

    const COLORS = ['#22d3ee', '#f472b6', '#34d399', '#fbbf24', '#a78bfa', '#f87171'];

    const hierarchy = useMemo(() => {
        const tree = {};
        Object.keys(tags).forEach(path => {
            if (!path || typeof path !== 'string') return;
            const parts = path.split('/');
            const area = parts[1] || 'General';
            const machine = parts[2] || 'Common';

            if (!tree[area]) tree[area] = {};
            if (!tree[area][machine]) tree[area][machine] = [];
            tree[area][machine].push(path);
        });
        return tree;
    }, [tags]);

    const handleTogglePath = (path) => {
        setSelectedPaths(prev =>
            prev.includes(path)
                ? prev.filter(p => p !== path)
                : [...prev, path]
        );
    };

    const handleFetch = () => {
        if (selectedPaths.length > 0) {
            // Aseguramos que pasamos ISO strings para evitar ambigüedades de zona horaria
            const startStr = dateFrom ? new Date(dateFrom).toISOString() : null;
            const endStr = dateTo ? new Date(dateTo).toISOString() : null;

            loadHistories(selectedPaths, {
                start: startStr,
                end: endStr
            });
        }
    };

    const allEvents = useMemo(() => {
        const events = [];
        Object.entries(histories).forEach(([path, data]) => {
            if (!data) return;
            data.forEach(point => {
                events.push({ ...point, path });
            });
        });
        return events.sort((a, b) => new Date(b.t) - new Date(a.t));
    }, [histories]);

    return (
        <div className="dashboard-grid-container" style={{ gridTemplateColumns: '320px 1fr', gap: '1.5rem', height: 'calc(100vh - 100px)' }}>
            {/* Sidebar Hierárquico con Scroll Independiente */}
            <aside className="sidebar" style={{ display: 'flex', flexDirection: 'column', height: '100%', background: 'var(--panel-color)', border: '1px solid var(--border-color)', borderRadius: '16px', overflow: 'hidden' }}>
                <div style={{ padding: '1.25rem', borderBottom: '1px solid var(--border-color)', background: 'rgba(255,255,255,0.02)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', color: 'var(--accent-cyan)' }}>
                            <Layers size={20} />
                            <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: '800', letterSpacing: '0.5px' }}>SENSORES</h3>
                        </div>
                        {selectedPaths.length > 0 && (
                            <button
                                onClick={() => { setSelectedPaths([]); clearHistory(); }}
                                style={{ background: 'none', border: 'none', color: 'var(--accent-red)', cursor: 'pointer', padding: '4px' }}
                                title="Limpiar selección"
                            >
                                <Trash2 size={16} />
                            </button>
                        )}
                    </div>
                    <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Navegue y seleccione para analizar</p>
                </div>

                <div style={{ flex: 1, overflowY: 'auto', padding: '1rem', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                    {Object.keys(hierarchy).sort().map(area => (
                        <div key={area} style={{ marginBottom: '0.25rem' }}>
                            <div
                                onClick={() => setExpandedAreas(p => ({ ...p, [area]: !p[area] }))}
                                style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', cursor: 'pointer', padding: '0.6rem', borderRadius: '8px', background: expandedAreas[area] ? 'rgba(34, 211, 238, 0.05)' : 'transparent', border: expandedAreas[area] ? '1px solid rgba(34, 211, 238, 0.2)' : '1px solid transparent', fontSize: '0.85rem', fontWeight: 'bold', transition: 'all 0.2s' }}
                            >
                                {expandedAreas[area] ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                                <Filter size={14} color={expandedAreas[area] ? 'var(--accent-cyan)' : 'var(--text-secondary)'} />
                                {area}
                            </div>

                            {expandedAreas[area] && (
                                <div style={{ marginLeft: '1rem', marginTop: '0.4rem', paddingLeft: '0.5rem', borderLeft: '1px solid rgba(255,255,255,0.05)', display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                                    {Object.keys(hierarchy[area]).sort().map(machine => (
                                        <div key={machine}>
                                            <div
                                                onClick={() => setExpandedMachines(p => ({ ...p, [machine]: !p[machine] }))}
                                                style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', padding: '0.4rem', borderRadius: '6px', fontSize: '0.8rem', color: expandedMachines[machine] ? 'white' : 'var(--text-secondary)' }}
                                            >
                                                {expandedMachines[machine] ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                                                <Cog size={12} />
                                                {machine}
                                            </div>

                                            {expandedMachines[machine] && (
                                                <div style={{ marginLeft: '1.2rem', marginTop: '0.2rem', display: 'flex', flexDirection: 'column', gap: '0.1rem' }}>
                                                    {hierarchy[area][machine].map(path => (
                                                        <div
                                                            key={path}
                                                            onClick={() => handleTogglePath(path)}
                                                            className={`filter-option ${selectedPaths.includes(path) ? 'active' : ''}`}
                                                            style={{
                                                                display: 'flex', alignItems: 'center', gap: '0.5rem',
                                                                padding: '0.4rem 0.6rem', borderRadius: '4px', cursor: 'pointer',
                                                                fontSize: '0.75rem', marginBottom: '1px'
                                                            }}
                                                        >
                                                            {selectedPaths.includes(path)
                                                                ? <CheckCircle2 size={12} color="var(--accent-cyan)" />
                                                                : <Circle size={12} style={{ opacity: 0.2 }} />
                                                            }
                                                            <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                                                {path.split('/').pop()}
                                                            </span>
                                                        </div>
                                                    ))}
                                                </div>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    ))}
                </div>

                <div style={{ padding: '1rem', background: 'rgba(0,0,0,0.2)', borderTop: '1px solid var(--border-color)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.75rem' }}>
                        <span style={{ color: 'var(--text-secondary)' }}>Seleccionados:</span>
                        <span style={{ color: 'var(--accent-cyan)', fontWeight: 'bold' }}>{selectedPaths.length}</span>
                    </div>
                </div>
            </aside>

            {/* Contenido Principal con el visor de tendencias */}
            <main style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', overflowY: 'auto', paddingRight: '0.5rem' }}>
                <header className="card" style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '1.5rem',
                    position: 'sticky',
                    top: 0,
                    zIndex: 10,
                    background: 'var(--panel-color)',
                    border: '1px solid var(--border-color)',
                    width: '100%',
                    flexShrink: 0,
                    boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
                    marginBottom: '1rem'
                }}>
                    <div style={{ display: 'flex', gap: '1.25rem', alignItems: 'center' }}>
                        <div style={{ background: 'rgba(34, 211, 238, 0.1)', padding: '0.75rem', borderRadius: '12px' }}>
                            <Activity size={26} color="var(--accent-cyan)" />
                        </div>
                        <div>
                            <h2 style={{ fontSize: '1.4rem', margin: 0, letterSpacing: '-0.5px' }}>Tendencias e Históricos</h2>
                            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', margin: 0 }}>Análisis de registros temporales</p>
                        </div>
                    </div>

                    <div style={{ display: 'flex', gap: '1.5rem', alignItems: 'flex-end' }}>
                        <div style={{ display: 'flex', gap: '1rem' }}>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                                <label style={{ fontSize: '0.7rem', color: 'var(--accent-cyan)', fontWeight: 'bold', textTransform: 'uppercase', marginLeft: '0.2rem' }}>Desde</label>
                                <input
                                    type="datetime-local"
                                    value={dateFrom}
                                    onChange={(e) => setDateFrom(e.target.value)}
                                    style={{ background: 'var(--bg-color)', color: 'white', border: '1px solid var(--border-color)', padding: '0.6rem 0.8rem', borderRadius: '8px', fontSize: '0.9rem', outline: 'none', transition: 'border-color 0.2s' }}
                                />
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                                <label style={{ fontSize: '0.7rem', color: 'var(--accent-cyan)', fontWeight: 'bold', textTransform: 'uppercase', marginLeft: '0.2rem' }}>Hasta</label>
                                <input
                                    type="datetime-local"
                                    value={dateTo}
                                    onChange={(e) => setDateTo(e.target.value)}
                                    style={{ background: 'var(--bg-color)', color: 'white', border: '1px solid var(--border-color)', padding: '0.6rem 0.8rem', borderRadius: '8px', fontSize: '0.9rem', outline: 'none', transition: 'border-color 0.2s' }}
                                />
                            </div>
                        </div>
                        <button
                            onClick={handleFetch}
                            disabled={selectedPaths.length === 0 || isLoading}
                            style={{
                                background: 'var(--accent-cyan)',
                                color: 'black',
                                padding: '0 1.5rem',
                                height: '45px',
                                borderRadius: '8px',
                                border: 'none',
                                fontWeight: 'bold',
                                cursor: 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.6rem',
                                opacity: (selectedPaths.length === 0 || isLoading) ? 0.5 : 1,
                                transition: 'all 0.2s',
                                boxShadow: '0 4px 10px rgba(34, 211, 238, 0.2)'
                            }}
                        >
                            <Search size={18} /> Consultar
                        </button>
                    </div>
                </header>

                <div style={{ display: 'flex', gap: '0.75rem' }}>
                    <button onClick={() => setViewMode('chart')} className={`status-badge ${viewMode === 'chart' ? 'active' : ''}`} style={{ cursor: 'pointer', padding: '0.5rem 1rem', border: viewMode === 'chart' ? '1px solid var(--accent-cyan)' : '1px solid var(--border-color)', background: viewMode === 'chart' ? 'rgba(34, 211, 238, 0.1)' : 'transparent', color: viewMode === 'chart' ? 'var(--accent-cyan)' : 'var(--text-secondary)' }}> <Activity size={16} /> Gráficos </button>
                    <button onClick={() => setViewMode('list')} className={`status-badge ${viewMode === 'list' ? 'active' : ''}`} style={{ cursor: 'pointer', padding: '0.5rem 1rem', border: viewMode === 'list' ? '1px solid var(--accent-cyan)' : '1px solid var(--border-color)', background: viewMode === 'list' ? 'rgba(34, 211, 238, 0.1)' : 'transparent', color: viewMode === 'list' ? 'var(--accent-cyan)' : 'var(--text-secondary)' }}> <List size={16} /> Lista </button>
                </div>

                {isLoading ? (
                    <div className="card" style={{ height: '400px', display: 'flex', justifyContent: 'center', alignItems: 'center', flexDirection: 'column', gap: '1.5rem' }}>
                        <div className="pulse-animation" style={{ width: '50px', height: '50px', borderRadius: '50%', background: 'var(--accent-cyan)', boxShadow: '0 0 20px var(--accent-cyan)' }}></div>
                        <p style={{ letterSpacing: '1px', opacity: 0.6 }}>PROCESANDO DATOS HISTÓRICOS...</p>
                    </div>
                ) : Object.keys(histories).length > 0 ? (
                    viewMode === 'chart' ? (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                            {Object.entries(histories).map(([path, data], idx) => (
                                <div key={path} className="card" style={{ padding: '1.5rem', borderLeft: `4px solid ${COLORS[idx % COLORS.length]}` }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
                                        <div>
                                            <h3 style={{ fontSize: '1.1rem', color: COLORS[idx % COLORS.length], margin: 0, fontWeight: 'bold' }}>{path.split('/').pop()}</h3>
                                            <p style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', margin: 0 }}>{path}</p>
                                        </div>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                                            <button
                                                onClick={() => toggleStats(path)}
                                                style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', background: statsVisible[path] ? 'var(--accent-cyan)' : 'transparent', color: statsVisible[path] ? 'black' : 'var(--accent-cyan)', border: '1px solid var(--accent-cyan)', padding: '0.3rem 0.7rem', borderRadius: '6px', fontSize: '0.75rem', fontWeight: 'bold', cursor: 'pointer', transition: 'all 0.2s' }}
                                            >
                                                <TrendingUp size={14} />
                                                Estadísticas
                                            </button>
                                            <div style={{ background: 'rgba(255,255,255,0.03)', padding: '0.4rem 0.8rem', borderRadius: '6px', fontSize: '0.75rem', color: 'var(--text-secondary)', border: '1px solid var(--border-color)' }}>
                                                Total: <strong>{data.length}</strong> muestras
                                            </div>
                                        </div>
                                    </div>

                                    {/* Panel de Estadísticas (Backend Calculated) */}
                                    {statsVisible[path] && (
                                        statsLoading[path] ? (
                                            <div style={{ background: 'rgba(0,0,0,0.1)', padding: '1.5rem', borderRadius: '12px', marginBottom: '1.5rem', textAlign: 'center', border: '1px dashed var(--border-color)' }}>
                                                <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--accent-cyan)', letterSpacing: '1px' }}>RECOPILANDO ANALÍTICA...</p>
                                            </div>
                                        ) : tagStats[path] ? (
                                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '1rem', background: 'rgba(0,0,0,0.2)', padding: '1.25rem', borderRadius: '12px', marginBottom: '1.5rem', border: '1px solid rgba(255,255,255,0.05)' }}>
                                                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
                                                    <span style={{ fontSize: '0.65rem', color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Mínimo</span>
                                                    <span style={{ fontSize: '1.1rem', fontWeight: 'bold', color: 'white' }}>{tagStats[path].min.toFixed(3)}</span>
                                                </div>
                                                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
                                                    <span style={{ fontSize: '0.65rem', color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Máximo</span>
                                                    <span style={{ fontSize: '1.1rem', fontWeight: 'bold', color: 'white' }}>{tagStats[path].max.toFixed(3)}</span>
                                                </div>
                                                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
                                                    <span style={{ fontSize: '0.65rem', color: 'var(--accent-cyan)', textTransform: 'uppercase', letterSpacing: '0.5px', fontWeight: 'bold' }}>Media (Avg)</span>
                                                    <span style={{ fontSize: '1.1rem', fontWeight: 'bold', color: 'var(--accent-cyan)' }}>{tagStats[path].avg.toFixed(3)}</span>
                                                </div>
                                                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
                                                    <span style={{ fontSize: '0.65rem', color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Mediana</span>
                                                    <span style={{ fontSize: '1.1rem', fontWeight: 'bold', color: 'white' }}>{tagStats[path].median.toFixed(3)}</span>
                                                </div>
                                                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
                                                    <span style={{ fontSize: '0.65rem', color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Amplitud (Range)</span>
                                                    <span style={{ fontSize: '1.1rem', fontWeight: 'bold', color: '#fbbf24' }}>{tagStats[path].range.toFixed(3)}</span>
                                                </div>
                                                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
                                                    <span style={{ fontSize: '0.65rem', color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Desviación Std</span>
                                                    <span style={{ fontSize: '1.1rem', fontWeight: 'bold', color: 'rgba(255,255,255,0.7)' }}>{tagStats[path].stddev.toFixed(3)}</span>
                                                </div>
                                                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
                                                    <span style={{ fontSize: '0.65rem', color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Varianza</span>
                                                    <span style={{ fontSize: '1.1rem', fontWeight: 'bold', color: 'rgba(255,255,255,0.7)' }}>{tagStats[path].variance.toFixed(3)}</span>
                                                </div>
                                                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
                                                    <span style={{ fontSize: '0.65rem', color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Muestras (DB)</span>
                                                    <span style={{ fontSize: '1.1rem', fontWeight: 'bold', color: 'white' }}>{tagStats[path].count}</span>
                                                </div>
                                            </div>
                                        ) : null
                                    )}
                                    <div style={{ width: '100%', height: '300px' }}>
                                        <ResponsiveContainer width="100%" height="100%">
                                            <LineChart data={data.map(p => ({ ...p, time: new Date(p.t).getTime() }))}>
                                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" vertical={false} />
                                                <XAxis
                                                    dataKey="time"
                                                    type="number"
                                                    domain={['dataMin', 'dataMax']}
                                                    stroke="rgba(255,255,255,0.3)"
                                                    tickFormatter={(t) => format(new Date(t), 'HH:mm:ss')}
                                                    fontSize={10}
                                                    tick={{ fill: 'var(--text-secondary)' }}
                                                />
                                                <YAxis
                                                    stroke="rgba(255,255,255,0.3)"
                                                    fontSize={10}
                                                    domain={['auto', 'auto']}
                                                    tick={{ fill: 'var(--text-secondary)' }}
                                                    padding={{ top: 20, bottom: 20 }}
                                                />
                                                <Tooltip
                                                    contentStyle={{ background: '#111827', border: '1px solid var(--border-color)', borderRadius: '12px', boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.5)' }}
                                                    labelStyle={{ color: 'var(--accent-cyan)', fontWeight: 'bold', marginBottom: '5px' }}
                                                    labelFormatter={(t) => format(new Date(t), 'dd/MM/yyyy HH:mm:ss')}
                                                />
                                                <Line
                                                    type="monotone"
                                                    dataKey="v"
                                                    stroke={COLORS[idx % COLORS.length]}
                                                    strokeWidth={3}
                                                    dot={false}
                                                    activeDot={{ r: 6, stroke: 'white', strokeWidth: 2 }}
                                                    animationDuration={500}
                                                />
                                            </LineChart>
                                        </ResponsiveContainer>
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                            <div className="card" style={{ padding: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem' }}>
                                    <List size={20} color="var(--accent-cyan)" />
                                    <span style={{ fontWeight: 'bold' }}>Registros Históricos</span>
                                </div>
                                <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                                    Mostrando <strong>{allEvents.length}</strong> muestras en total
                                </div>
                            </div>

                            <div className="card" style={{ padding: 0, overflow: 'auto', maxHeight: '600px' }}>
                                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                                    <thead style={{ position: 'sticky', top: 0, background: 'var(--panel-color)', zIndex: 5 }}>
                                        <tr style={{ textAlign: 'left', borderBottom: '1px solid var(--border-color)', opacity: 0.6, fontSize: '0.75rem' }}>
                                            <th style={{ padding: '1.25rem' }}>TIMESTAMP (LOCAL)</th>
                                            <th style={{ padding: '1.25rem' }}>SITIO / SENSOR</th>
                                            <th style={{ padding: '1.25rem' }}>VALOR</th>
                                            <th style={{ padding: '1.25rem' }}>CALIDAD</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {allEvents.map((ev, i) => (
                                            <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)', fontSize: '0.85rem' }}>
                                                <td style={{ padding: '1rem', fontVariantNumeric: 'tabular-nums' }}>{new Date(ev.t).toLocaleString()}</td>
                                                <td style={{ padding: '1rem', color: 'var(--text-secondary)' }}>{ev.path}</td>
                                                <td style={{ padding: '1rem', color: 'var(--accent-cyan)', fontWeight: 'bold' }}>{typeof ev.v === 'number' ? ev.v.toFixed(3) : ev.v}</td>
                                                <td style={{ padding: '1rem' }}>
                                                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                                        <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: ev.q === 192 ? 'var(--accent-green)' : 'var(--accent-red)' }}></div>
                                                        <span style={{ fontSize: '0.75rem', color: ev.q === 192 ? 'var(--accent-green)' : 'var(--accent-red)' }}>
                                                            {ev.q === 192 ? 'Buena' : 'Mala'}
                                                        </span>
                                                    </div>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )
                ) : (
                    <div className="card" style={{ flex: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', flexDirection: 'column', gap: '1.5rem', opacity: 0.3, minHeight: '400px' }}>
                        <Search size={64} color="var(--text-secondary)" />
                        <div style={{ textAlign: 'center' }}>
                            <h3 style={{ margin: '0 0 0.5rem 0' }}>Sin datos para mostrar</h3>
                            <p style={{ margin: 0 }}>Seleccione sensores en el panel izquierdo y defina el rango horario.</p>
                        </div>
                    </div>
                )}
            </main>
        </div>
    );
};

export default TrendsPage;
