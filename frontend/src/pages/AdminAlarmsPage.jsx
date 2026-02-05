import React, { useState, useMemo } from 'react';
import { useAlarms } from '../contexts/AlarmContext';
import { useSCADA } from '../contexts/SCADAContext';
import { Settings, Plus, Layers, Cog, Activity, Bell, Info } from 'lucide-react';

const AdminAlarmsPage = () => {
    const { tags } = useSCADA();
    const { alarmConfigs, updateConfig, deleteConfig } = useAlarms();
    const [editingConfig, setEditingConfig] = useState(null);

    // Estados para filtrado jerárquico
    const [selectedArea, setSelectedArea] = useState('All');
    const [selectedMachine, setSelectedMachine] = useState('All');

    const PRIORITIES = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'];
    const OPERATORS = ['>', '<', '>=', '<=', '==', '!='];

    // Estructura los tags jerárquicamente
    const hierarchy = useMemo(() => {
        const tree = {};
        Object.keys(tags).forEach(path => {
            const parts = path.split('/');
            const area = parts[1] || 'General';
            const machine = parts[2] || 'Common';

            if (!tree[area]) tree[area] = {};
            if (!tree[area][machine]) tree[area][machine] = [];
            tree[area][machine].push({ path, ...tags[path] });
        });
        return tree;
    }, [tags]);

    const areas = ['All', ...Object.keys(hierarchy)];
    const machinesSource = selectedArea === 'All' ? {} : (hierarchy[selectedArea] || {});
    const machines = ['All', ...Object.keys(machinesSource)];

    // Filtrado de configuraciones de alarma
    const filteredConfigs = alarmConfigs.filter(config => {
        const path = config.tag_path || '';
        const parts = path.split('/');
        const area = parts[1] || 'General';
        const machine = parts[2] || 'Common';

        const areaMatch = selectedArea === 'All' || area === selectedArea;
        const machineMatch = selectedMachine === 'All' || machine === selectedMachine;

        return areaMatch && machineMatch;
    });

    const handleSave = async (e) => {
        e.preventDefault();
        try {
            const formData = new FormData(e.target);
            const tagIdRaw = formData.get('tag_id');
            const tagId = parseInt(tagIdRaw);

            if (!tagIdRaw || isNaN(tagId)) {
                alert("❌ Error: Debe seleccionar un sensor válido. (El sensor seleccionado no tiene un ID asociado en el sistema)");
                return;
            }

            const config = {
                tag_id: tagId,
                operator: formData.get('operator'),
                threshold: parseFloat(formData.get('threshold')) || 0,
                priority: formData.get('priority'),
                enabled: formData.get('enabled') === 'on',
                message: formData.get('message')
            };

            if (editingConfig && editingConfig.id) {
                config.id = editingConfig.id;
            }

            console.log("🚀 Enviando Configuración:", config);
            const response = await updateConfig(config);

            if (response && response.error) {
                throw new Error(response.error);
            }

            setEditingConfig(null);
            alert("✅ Alarma guardada con éxito");
        } catch (err) {
            console.error("❌ Save Error:", err);
            const errorMsg = err.response?.data?.detail
                ? JSON.stringify(err.response.data.detail)
                : (err.response?.data?.error || err.message);
            alert("⚠️ Error al guardar: " + errorMsg);
        }
    };

    return (
        <div className="dashboard-grid-container">
            {/* Sidebar de Navegación Jerárquica */}
            <aside className="sidebar">
                <div className="filter-group">
                    <div className="filter-title">
                        <Layers size={14} /> Áreas de Planta
                    </div>
                    {areas.map(area => (
                        <div
                            key={area}
                            className={`filter-option ${selectedArea === area ? 'active' : ''}`}
                            onClick={() => {
                                setSelectedArea(area);
                                setSelectedMachine('All');
                            }}
                        >
                            {area}
                        </div>
                    ))}
                </div>

                {selectedArea !== 'All' && (
                    <div className="filter-group">
                        <div className="filter-title">
                            <Cog size={14} /> Equipos
                        </div>
                        {machines.map(machine => (
                            <div
                                key={machine}
                                className={`filter-option ${selectedMachine === machine ? 'active' : ''}`}
                                onClick={() => setSelectedMachine(machine)}
                            >
                                {machine}
                            </div>
                        ))}
                    </div>
                )}
            </aside>

            {/* Panel Principal */}
            <main className="main-content">
                <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
                    <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                        <Settings color="var(--accent-cyan)" />
                        <div>
                            <h2 style={{ fontSize: '1.25rem' }}>Administración de Alarmas</h2>
                            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                                {selectedArea} / {selectedMachine}
                            </p>
                        </div>
                    </div>
                    <button
                        onClick={() => setEditingConfig({})}
                        className="status-badge"
                        style={{ cursor: 'pointer', border: '1px solid var(--accent-cyan)', color: 'var(--accent-cyan)', background: 'transparent' }}
                    >
                        <Plus size={16} /> Configurar Nueva
                    </button>
                </header>

                <div className="card" style={{ padding: '0', overflow: 'hidden' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                        <thead>
                            <tr style={{ textAlign: 'left', background: 'rgba(255,255,255,0.02)', borderBottom: '1px solid var(--border-color)', opacity: 0.6, fontSize: '0.75rem' }}>
                                <th style={{ padding: '1rem' }}>SENSOR</th>
                                <th style={{ padding: '1rem' }}>REGLA</th>
                                <th style={{ padding: '1rem' }}>UMBRAL</th>
                                <th style={{ padding: '1rem' }}>PRIORIDAD</th>
                                <th style={{ padding: '1rem' }}>ESTADO</th>
                                <th style={{ padding: '1rem', textAlign: 'right' }}>ACCIONES</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredConfigs.map(config => (
                                <tr key={config.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                                    <td style={{ padding: '1rem' }}>
                                        <div style={{ fontSize: '0.85rem', fontWeight: 'bold' }}>{config.tag_path?.split('/').pop() || 'Desconocido'}</div>
                                        <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>{config.tag_path}</div>
                                    </td>
                                    <td style={{ padding: '1rem' }}>
                                        <span style={{ color: 'var(--accent-cyan)', fontSize: '0.8rem', fontWeight: 'bold' }}>{config.operator}</span>
                                    </td>
                                    <td style={{ padding: '1rem', fontWeight: 'bold' }}>{config.threshold}</td>
                                    <td style={{ padding: '1rem' }}>
                                        <span style={{
                                            padding: '2px 8px', borderRadius: '4px', fontSize: '0.7rem', fontWeight: 'bold',
                                            background: config.priority === 'CRITICAL' ? 'var(--accent-red)' : 'rgba(255,255,255,0.1)'
                                        }}>
                                            {config.priority}
                                        </span>
                                    </td>
                                    <td style={{ padding: '1rem' }}>
                                        {config.enabled ? '🟢 ON' : '⚫ OFF'}
                                    </td>
                                    <td style={{ padding: '1rem', textAlign: 'right' }}>
                                        <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
                                            <button
                                                onClick={() => setEditingConfig(config)}
                                                style={{ background: 'none', border: 'none', color: 'var(--accent-cyan)', cursor: 'pointer', fontSize: '0.85rem' }}
                                            >
                                                Editar
                                            </button>
                                            <button
                                                onClick={async () => {
                                                    if (window.confirm("¿Está seguro de eliminar esta configuración de alarma?")) {
                                                        try {
                                                            await deleteConfig(config.id);
                                                            alert("✅ Alarma eliminada");
                                                        } catch (err) {
                                                            alert("❌ Error al eliminar");
                                                        }
                                                    }
                                                }}
                                                style={{ background: 'none', border: 'none', color: 'var(--accent-red)', cursor: 'pointer', fontSize: '0.85rem' }}
                                            >
                                                Eliminar
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </main>

            {/* Modal de Configuración - EL CORREGIDO */}
            {editingConfig && (
                <div style={{ position: 'fixed', top: 0, left: 0, width: '100%', height: '100%', background: 'rgba(0,0,0,0.85)', backdropFilter: 'blur(4px)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000 }}>
                    <form
                        key={editingConfig?.id || 'new'}
                        onSubmit={handleSave}
                        className="card"
                        style={{ width: '500px', background: 'var(--bg-color)', border: '1px solid var(--accent-cyan)' }}
                    >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem' }}>
                            <Bell size={20} color="var(--accent-cyan)" />
                            <h3 style={{ margin: 0 }}>Configuración de Alarma</h3>
                        </div>

                        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                            <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                                <div style={{ marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                                    <Activity size={14} /> Seleccionar Sensor de la Planta:
                                </div>
                                <select
                                    name="tag_id"
                                    defaultValue={editingConfig.tag_id}
                                    required
                                    style={{ width: '100%', padding: '0.8rem', background: 'rgba(255,255,255,0.05)', color: 'white', border: '1px solid var(--border-color)', borderRadius: '8px', fontSize: '0.9rem' }}
                                >
                                    <option value="">-- Buscar Sensor... --</option>
                                    {Object.keys(hierarchy).sort().map(area => (
                                        <optgroup key={area} label={`📍 AREA: ${area}`}>
                                            {Object.keys(hierarchy[area]).sort().map(machine => (
                                                hierarchy[area][machine].map(tag => (
                                                    <option key={tag.path || tag.id} value={tag.id || ''}>
                                                        {machine} ⮕ {tag.path?.split('/').pop() || 'Sensor'} ({tag.path})
                                                    </option>
                                                ))
                                            ))}
                                        </optgroup>
                                    ))}
                                </select>
                            </label>

                            <div style={{ display: 'flex', gap: '1rem' }}>
                                <label style={{ flex: 1, fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                                    Condición (Operador):
                                    <select name="operator" defaultValue={editingConfig.operator || '>'} style={{ width: '100%', padding: '0.7rem', marginTop: '0.4rem', background: 'rgba(255,255,255,0.05)', color: 'white', border: '1px solid var(--border-color)', borderRadius: '8px' }}>
                                        {OPERATORS.map(op => <option key={op} value={op}>{op}</option>)}
                                    </select>
                                </label>
                                <label style={{ flex: 1, fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                                    Prioridad:
                                    <select name="priority" defaultValue={editingConfig.priority || 'MEDIUM'} style={{ width: '100%', padding: '0.7rem', marginTop: '0.4rem', background: 'rgba(255,255,255,0.05)', color: 'white', border: '1px solid var(--border-color)', borderRadius: '8px' }}>
                                        {PRIORITIES.map(p => <option key={p} value={p}>{p}</option>)}
                                    </select>
                                </label>
                            </div>

                            <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                                Umbral (Threshold):
                                <input name="threshold" type="number" step="0.01" required defaultValue={editingConfig.threshold} style={{ width: '100%', padding: '0.7rem', marginTop: '0.4rem', background: 'rgba(255,255,255,0.05)', color: 'white', border: '1px solid var(--border-color)', borderRadius: '8px' }} />
                            </label>

                            <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                                Mensaje de Alerta:
                                <input name="message" type="text" defaultValue={editingConfig.message} placeholder="Ej: ¡Temperatura Crítica!" style={{ width: '100%', padding: '0.7rem', marginTop: '0.4rem', background: 'rgba(255,255,255,0.05)', color: 'white', border: '1px solid var(--border-color)', borderRadius: '8px' }} />
                            </label>

                            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                                <input name="enabled" type="checkbox" defaultChecked={editingConfig.enabled !== false} />
                                Monitoreo habilitado
                            </label>

                            <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                                <button type="button" onClick={() => setEditingConfig(null)} style={{ flex: 1, padding: '0.8rem', borderRadius: '8px', border: '1px solid var(--border-color)', background: 'transparent', color: 'white', cursor: 'pointer' }}>Cerrar</button>
                                <button type="submit" style={{ flex: 1, padding: '0.8rem', borderRadius: '8px', border: 'none', background: 'var(--accent-cyan)', color: 'black', fontWeight: 'bold', cursor: 'pointer' }}>Guardar</button>
                            </div>
                        </div>
                    </form>
                </div>
            )}
        </div>
    );
};

export default AdminAlarmsPage;
