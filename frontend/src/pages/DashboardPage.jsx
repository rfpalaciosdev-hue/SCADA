import React, { useState, useMemo } from 'react';
import { useSCADA } from '../contexts/SCADAContext';
import TagCard from '../components/TagCard';
import { Factory, Cog, Layers } from 'lucide-react';

const DashboardPage = () => {
    const { tags } = useSCADA();
    const [selectedArea, setSelectedArea] = useState('All');
    const [selectedMachine, setSelectedMachine] = useState('All');

    // Estructura los tags jerárquicamente para los filtros
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

    // Filtrado de tags
    const filteredTags = Object.entries(tags).filter(([path]) => {
        const parts = path.split('/');
        const area = parts[1] || 'General';
        const machine = parts[2] || 'Common';

        const areaMatch = selectedArea === 'All' || area === selectedArea;
        const machineMatch = selectedMachine === 'All' || machine === selectedMachine;

        return areaMatch && machineMatch;
    });

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
                            <span className="machine-badge">
                                {area === 'All' ? Object.keys(tags).length : Object.values(tags).filter(t => t.path?.includes(`/${area}/`)).length}
                            </span>
                        </div>
                    ))}
                </div>

                {selectedArea !== 'All' && (
                    <div className="filter-group">
                        <div className="filter-title">
                            <Cog size={14} /> Equipos / Máquinas
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

            {/* Grilla Principal de Sensores */}
            <main className="main-content">
                <div style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <div style={{ background: 'var(--panel-color)', padding: '0.5rem 1rem', borderRadius: '8px', border: '1px solid var(--border-color)', fontSize: '0.9rem' }}>
                        <span style={{ color: 'var(--text-secondary)' }}>Navegación:</span> Planta / {selectedArea} / {selectedMachine}
                    </div>
                </div>

                <div className="grid-layout">
                    {filteredTags.length > 0 ? (
                        filteredTags.map(([path, data]) => (
                            <TagCard key={path} path={path} data={data} />
                        ))
                    ) : (
                        <div style={{ textAlign: 'center', padding: '4rem', opacity: 0.5, gridColumn: '1/-1' }}>
                            <Factory size={48} style={{ marginBottom: '1rem' }} />
                            <p>No se encontraron sensores para esta selección.</p>
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
};

export default DashboardPage;
