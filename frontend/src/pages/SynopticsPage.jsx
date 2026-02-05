import React from 'react';
import { useSCADA } from '../contexts/SCADAContext';
import { IndustrialTank, IndustrialMotor, IndustrialGauge, IndustrialPipe } from '../components/SynopticComponents';
import { Activity, Shield } from 'lucide-react';

const SynopticsPage = () => {
    const { tags } = useSCADA();

    // Mapeo manual de tags a los componentes
    const cocimiento = {
        nivel: tags['planta_central/cocimiento/tanque_01/nivel']?.v || 0,
        temp: tags['planta_central/cocimiento/tanque_01/temperatura']?.v || 0
    };

    const empaquetado = {
        corriente: tags['planta_central/empaquetado/linea_01/motor_principal/corriente']?.v || 0,
        estado: tags['planta_central/empaquetado/linea_01/motor_principal/estado']?.v === 1
    };

    const servicios = {
        presion: tags['planta_central/servicios/caldera/presion']?.v || 0
    };

    return (
        <div style={{ padding: '2rem' }}>
            <header style={{ marginBottom: '2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                    <h1 style={{ margin: 0, fontSize: '1.8rem', color: '#fff' }}>Vista de Proceso</h1>
                    <p style={{ margin: 0, color: 'var(--text-secondary)' }}>Sinóptico interactivo en tiempo real</p>
                </div>
                <div style={{ display: 'flex', gap: '1rem' }}>
                    <div className="status-badge">
                        <Activity size={16} color="#00ff00" />
                        SISTEMA ONLINE
                    </div>
                </div>
            </header>

            <div className="synoptic-layout">
                {/* Sección de Cocimiento */}
                <div className="process-section">
                    <div className="section-title">Cocimiento (Área 01)</div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0' }}>
                        <IndustrialTank
                            level={cocimiento.nivel}
                            temperature={cocimiento.temp}
                            label="Tanque Mixtura"
                        />
                        <div style={{ display: 'flex', flexDirection: 'column', marginTop: '20px' }}>
                            <IndustrialPipe flow={cocimiento.nivel > 5} length={80} />
                            <div style={{ height: '40px' }} />
                        </div>
                        <IndustrialMotor
                            running={empaquetado.estado}
                            current={empaquetado.corriente}
                            label="Bomba de Trasvase"
                        />
                    </div>
                </div>

                {/* Sección de Servicios */}
                <div className="process-section">
                    <div className="section-title">Servicios Auxiliares</div>
                    <div style={{ display: 'flex', gap: '2rem' }}>
                        <IndustrialGauge
                            value={servicios.presion}
                            label="Presión Caldera"
                        />
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                            <div className="synoptic-item" style={{ width: '120px' }}>
                                <Shield size={24} color={servicios.presion < 7.5 ? "#27ae60" : "#e74c3c"} />
                                <div className="synoptic-label">
                                    <span className="name">Seguridad</span>
                                    <span className="value" style={{ color: servicios.presion < 7.5 ? "#27ae60" : "#e74c3c" }}>
                                        {servicios.presion < 7.5 ? "NORMAL" : "ALERTA"}
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Leyenda y Notas Técnicas */}
                <div className="process-section" style={{ maxWidth: '300px' }}>
                    <div className="section-title">Leyenda de Control</div>
                    <ul style={{ color: '#bdc3c7', fontSize: '0.85rem', paddingLeft: '20px', lineHeight: '1.6' }}>
                        <li><span style={{ color: '#3498db' }}>●</span> Flujo activo en tuberías</li>
                        <li><span style={{ color: '#00ff00' }}>●</span> Motores en régimen nominal</li>
                        <li><span style={{ color: '#e74c3c' }}>●</span> Alerta de sobrepresión &gt; 7.5 bar</li>
                    </ul>
                </div>
            </div>

            <style>{`
                .status-badge {
                    background: rgba(0, 255, 0, 0.1);
                    border: 1px solid rgba(0, 255, 0, 0.3);
                    color: #00ff00;
                    padding: 0.5rem 1rem;
                    border-radius: 20px;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    font-size: 0.8rem;
                    font-weight: bold;
                    letter-spacing: 1px;
                }
            `}</style>
        </div>
    );
};

export default SynopticsPage;
