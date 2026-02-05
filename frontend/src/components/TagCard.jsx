import React from 'react';
import { Thermometer, Droplets, Zap, Gauge, Activity, Box, Bell } from 'lucide-react';
import { useAlarms } from '../contexts/AlarmContext';

const TAG_ICONS = {
    'temperatura': Thermometer,
    'nivel': Droplets,
    'corriente': Zap,
    'presion': Gauge,
    'estado': Activity,
    'default': Box
};

const getIcon = (path) => {
    const lower = path.toLowerCase();
    for (const key in TAG_ICONS) {
        if (lower.includes(key)) return TAG_ICONS[key];
    }
    return TAG_ICONS.default;
};

const TagCard = ({ path, data }) => {
    const { activeAlarms } = useAlarms();
    const Icon = getIcon(path);
    const isBinary = path.includes('estado');
    const pathParts = path.split('/');
    const area = pathParts[1] || 'General';
    const sensorName = pathParts.pop();
    const equipment = pathParts.pop() || area;

    const isBadQuality = data.q !== 192;

    // Buscar cualquier alarma sin auditar (pendiente de reconocimiento)
    const pendingAlarm = activeAlarms.find(a => a.path === path && !a.ack);
    const hasAlarm = !!pendingAlarm;

    return (
        <div className={`card ${hasAlarm ? 'alarm-glow' : ''}`} style={{
            opacity: isBadQuality ? 0.6 : 1,
            transition: 'all 0.3s ease',
            border: hasAlarm ? '1px solid var(--accent-red)' : '1px solid var(--border-color)',
            boxShadow: hasAlarm ? '0 0 15px rgba(255, 62, 62, 0.3)' : 'none'
        }}>
            <div className="tag-path" style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>{area} • {equipment}</span>
                {hasAlarm && <Bell size={12} color="var(--accent-red)" className="pulse-animation" />}
            </div>
            <div className="tag-name" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Icon size={18} color={isBadQuality ? 'var(--text-secondary)' : (hasAlarm ? 'var(--accent-red)' : 'var(--accent-cyan)')} />
                {sensorName}
            </div>

            {hasAlarm && (
                <div style={{
                    fontSize: '0.7rem',
                    color: 'var(--accent-red)',
                    fontWeight: 'bold',
                    background: 'rgba(255,62,62,0.1)',
                    padding: '4px 8px',
                    borderRadius: '4px',
                    margin: '0.5rem 0'
                }}>
                    ⚠️ ALARMA {pendingAlarm.source === 'HISTORY' ? '(Pasada)' : ''}: {pendingAlarm.operator} {pendingAlarm.threshold}
                </div>
            )}

            {isBadQuality ? (
                <div style={{ color: 'var(--accent-red)', fontSize: '0.8rem', fontWeight: 'bold', margin: '0.5rem 0' }}>
                    ⚠️ DATO NO CONFIABLE (OFFLINE)
                </div>
            ) : isBinary ? (
                <div className={`status-active ${data.v === 0 ? 'status-idle' : ''}`}>
                    <div style={{
                        width: '8px',
                        height: '8px',
                        borderRadius: '50%',
                        background: data.v === 1 ? 'var(--accent-green)' : 'var(--text-secondary)',
                        boxShadow: data.v === 1 ? '0 0 8px var(--accent-green)' : 'none'
                    }} />
                    {data.v === 1 ? 'RUNNING' : 'STOPPED'}
                </div>
            ) : (
                <div className="value-container">
                    <span className="value" style={{ color: isBadQuality ? 'var(--text-secondary)' : (hasAlarm ? 'var(--accent-red)' : 'var(--accent-cyan)') }}>
                        {typeof data.v === 'number' ? data.v.toFixed(2) : data.v}
                    </span>
                    <span className="unit">{data.u || ''}</span>
                </div>
            )}

            <div className="quality-indicator"
                style={{ background: isBadQuality ? 'var(--accent-red)' : (hasAlarm ? 'var(--accent-red)' : 'var(--accent-green)') }}
            />
        </div>
    );
};

export default TagCard;
