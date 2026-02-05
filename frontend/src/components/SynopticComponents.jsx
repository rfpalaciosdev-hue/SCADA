import React from 'react';
import './SynopticComponents.css';

/**
 * Tanque Industrial con nivel y temperatura dinámicos
 */
export const IndustrialTank = ({ level = 0, temperature = 0, label = "Tanque" }) => {
    // Escalar altura del líquido (el tanque interno mide 100 unidades en SVG)
    const fillHeight = Math.min(100, Math.max(0, level));

    // Color según temperatura (frio azul, caliente rojo)
    const getLiquidColor = (temp) => {
        if (temp > 80) return '#e74c3c';
        if (temp > 50) return '#f39c12';
        return '#3498db';
    };

    return (
        <div className="synoptic-item">
            <svg viewBox="0 0 120 160" width="120" height="160">
                {/* Sombras y profundidad */}
                <defs>
                    <linearGradient id="tankGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop offset="0%" stopColor="#2c3e50" />
                        <stop offset="50%" stopColor="#34495e" />
                        <stop offset="100%" stopColor="#2c3e50" />
                    </linearGradient>
                </defs>

                {/* Patas del tanque */}
                <rect x="25" y="140" width="10" height="15" fill="#555" />
                <rect x="85" y="140" width="10" height="15" fill="#555" />

                {/* Cuerpo del tanque */}
                <rect x="20" y="20" width="80" height="120" rx="4" fill="url(#tankGrad)" stroke="#7f8c8d" strokeWidth="2" />

                {/* Ventana de nivel (background) */}
                <rect x="35" y="30" width="15" height="100" fill="#1a1a1a" rx="2" />

                {/* Líquido en la ventana */}
                <rect
                    x="35"
                    y={30 + (100 - fillHeight)}
                    width="15"
                    height={fillHeight}
                    fill={getLiquidColor(temperature)}
                    rx="2"
                    style={{ transition: 'all 0.8s ease' }}
                />

                {/* Graduaciones */}
                {[25, 50, 75].map(tick => (
                    <line key={tick} x1="35" y1={30 + tick} x2="40" y2={30 + tick} stroke="#fff" strokeWidth="1" opacity="0.5" />
                ))}

                {/* Valor de temperatura info panel */}
                <rect x="60" y="40" width="30" height="20" rx="2" fill="#000" />
                <text x="75" y="54" textAnchor="middle" fill="#00ff00" fontSize="8" fontFamily="monospace">
                    {temperature}°C
                </text>
                <text x="75" y="35" textAnchor="middle" fill="#bdc3c7" fontSize="7">TEMP</text>
            </svg>
            <div className="synoptic-label">
                <span className="name">{label}</span>
                <span className="value">{level.toFixed(1)}%</span>
            </div>
        </div>
    );
};

/**
 * Motor Industrial con animación de rotación
 */
export const IndustrialMotor = ({ running = false, current = 0, label = "Motor" }) => {
    return (
        <div className="synoptic-item">
            <svg viewBox="0 0 100 100" width="100" height="100">
                {/* Cuerpo del motor */}
                <rect x="20" y="30" width="60" height="40" rx="2" fill={running ? "#2980b9" : "#7f8c8d"} stroke="#2c3e50" strokeWidth="2" />
                <rect x="15" y="35" width="5" height="30" fill="#34495e" />

                {/* Aletas de refrigeración */}
                {[25, 35, 45, 55, 65].map(x => (
                    <line key={x} x1={x} y1="30" x2={x} y2="70" stroke="#2c3e50" strokeWidth="1" />
                ))}

                {/* Eje y Ventilador */}
                <circle cx="85" cy="50" r="12" fill="#bdc3c7" stroke="#2c3e50" />
                <g className={running ? "fan-animate" : ""}>
                    <line x1="85" y1="40" x2="85" y2="60" stroke="#2c3e50" strokeWidth="3" />
                    <line x1="75" y1="50" x2="95" y2="50" stroke="#2c3e50" strokeWidth="3" />
                </g>

                {/* LED de estado */}
                <circle cx="25" cy="35" r="3" fill={running ? "#00ff00" : "#ff0000"} />
            </svg>
            <div className="synoptic-label">
                <span className="name">{label}</span>
                <span className="value">{current.toFixed(1)} A</span>
            </div>
        </div>
    );
};

/**
 * Medidor de Aguja (Gauge) para Presión
 */
export const IndustrialGauge = ({ value = 0, min = 0, max = 10, label = "Presión", unit = "bar" }) => {
    const percent = (value - min) / (max - min);
    const rotation = -90 + (percent * 180); // de -90 a 90 grados

    return (
        <div className="synoptic-item">
            <svg viewBox="0 0 100 80" width="100" height="80">
                {/* Fondo del dial */}
                <path d="M 10 70 A 40 40 0 0 1 90 70" fill="none" stroke="#333" strokeWidth="8" />
                <path
                    d="M 10 70 A 40 40 0 0 1 90 70"
                    fill="none"
                    stroke={value > max * 0.8 ? "#e74c3c" : "#27ae60"}
                    strokeWidth="8"
                    strokeDasharray={`${percent * 125}, 125`}
                    style={{ transition: 'stroke-dasharray 0.5s ease' }}
                />

                {/* Aguja */}
                <line
                    x1="50" y1="70" x2="50" y2="35"
                    stroke="#fff" strokeWidth="2"
                    style={{
                        transform: `rotate(${rotation}deg)`,
                        transformOrigin: '50px 70px',
                        transition: 'transform 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275)'
                    }}
                />
                <circle cx="50" cy="70" r="4" fill="#fff" />

                <text x="50" y="65" textAnchor="middle" fill="#fff" fontSize="10" fontWeight="bold">{value.toFixed(1)}</text>
                <text x="50" y="78" textAnchor="middle" fill="#bdc3c7" fontSize="7">{unit}</text>
            </svg>
            <div className="synoptic-label">
                <span className="name">{label}</span>
            </div>
        </div>
    );
};

/**
 * Tubería con flujo animado
 */
export const IndustrialPipe = ({ flow = false, vertical = false, length = 100 }) => {
    return (
        <svg
            width={vertical ? 20 : length}
            height={vertical ? length : 20}
            style={{ margin: '-10px' }}
        >
            <rect
                x="0" y="0"
                width={vertical ? 12 : length}
                height={vertical ? length : 12}
                fill="#444"
                rx="2"
            />
            {flow && (
                <line
                    x1="0" y1={vertical ? 0 : 6}
                    x2={vertical ? 0 : length} y2={vertical ? length : 6}
                    stroke="#3498db"
                    strokeWidth="4"
                    strokeDasharray="10, 10"
                    className="pipe-flow-animation"
                />
            )}
        </svg>
    );
};
