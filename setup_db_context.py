import psycopg2
import os

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "user": os.getenv("DB_USER", "scada_user"),
    "password": os.getenv("DB_PASS", "scada_admin"),
    "dbname": os.getenv("DB_NAME", "scada_db")
}

def main():
    try:
        print(f"Connecting to {DB_CONFIG['host']}...")
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        print("Creating table sensor_metadata...")
        cur.execute('''
        CREATE TABLE IF NOT EXISTS sensor_metadata (
            tag_id INTEGER PRIMARY KEY REFERENCES tag_definition(id) ON DELETE CASCADE,
            description TEXT,
            process_role TEXT,
            normal_range_min DOUBLE PRECISION,
            normal_range_max DOUBLE PRECISION,
            critical_range_min DOUBLE PRECISION,
            critical_range_max DOUBLE PRECISION,
            physical_location TEXT,
            related_system TEXT,
            failure_impact TEXT,
            operating_notes TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
        ''')

        metadata = [
            # Tanque 01
            ('planta_central/cocimiento/tanque_01/nivel', 'Nivel de cocimiento', 'Control de llenado', 40, 80, 0, 95, 'Tanque 01 Ara 1', 'Sistema de Cocimiento', 'Riesgo de desborde', 'Vigilar espumas'),
            ('planta_central/cocimiento/tanque_01/temperatura', 'Temperatura de cocimiento', 'Control térmico', 85, 95, 0, 105, 'Tanque 01 Ara 1', 'Sistema de Cocimiento', 'Calidad comprometida', 'Mantener estable'),
            ('planta_central/cocimiento/tanque_01/presion', 'Presión de cocimiento', 'Seguridad presión', 1.2, 2.0, 0, 2.5, 'Tanque 01 Ara 1', 'Sistema de Cocimiento', 'Riesgo estructural', 'Válvula alivio check'),
            
            # Caldera
            ('planta_central/servicios/caldera/presion', 'Presión vapor caldera', 'Generación Vapor', 6, 8, 0, 10, 'Sala Máquinas', 'Servicios', 'Parada de planta', 'Mantener suministro'),
            ('planta_central/servicios/caldera/temperatura', 'Temperatura caldera', 'Seguridad caldera', 160, 180, 0, 200, 'Sala Máquinas', 'Servicios', 'Falla caldera', 'Check sobrecalentamiento'),
            
            # Línea 01
            ('planta_central/empaquetado/linea_01/motor_principal/corriente', 'Corriente motor emp', 'Estado motor', 8, 15, 0, 20, 'Línea 01 Empaque', 'Empaquetado', 'Trascamiento mecánico', 'Check rodamientos'),
            ('planta_central/empaquetado/linea_01/motor_principal/estado', 'Estado motor emp', 'Operación', 0, 1, 0, 1, 'Línea 01 Empaque', 'Empaquetado', 'Línea detenida', '0=Off, 1=On'),
            ('planta_central/empaquetado/linea_01/velocidad', 'Velocidad línea', 'Productividad', 40, 60, 0, 70, 'Línea 01 Empaque', 'Empaquetado', 'Inestabilidad', 'Ajustar según material'),
            
            # Energía
            ('planta_central/servicios/energia/consumo', 'Consumo energético', 'Eficiencia', 0, 100, 0, 130, 'Subestación', 'Servicios', 'Sobrecarga', 'Alerta si pico >30% promedio'),
        ]

        print("Seeding data...")
        for path, desc, role, n_min, n_max, c_min, c_max, loc, sys, impact, notes in metadata:
            cur.execute('SELECT id FROM tag_definition WHERE path = %s', (path,))
            res = cur.fetchone()
            if res:
                tag_id = res[0]
                cur.execute('''
                    INSERT INTO sensor_metadata (tag_id, description, process_role, normal_range_min, normal_range_max, critical_range_min, critical_range_max, physical_location, related_system, failure_impact, operating_notes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (tag_id) DO UPDATE SET
                        description = EXCLUDED.description,
                        process_role = EXCLUDED.process_role,
                        normal_range_min = EXCLUDED.normal_range_min,
                        normal_range_max = EXCLUDED.normal_range_max,
                        critical_range_min = EXCLUDED.critical_range_min,
                        critical_range_max = EXCLUDED.critical_range_max,
                        physical_location = EXCLUDED.physical_location,
                        related_system = EXCLUDED.related_system,
                        failure_impact = EXCLUDED.failure_impact,
                        operating_notes = EXCLUDED.operating_notes,
                        updated_at = NOW()
                ''', (tag_id, desc, role, n_min, n_max, c_min, c_max, loc, sys, impact, notes))
            else:
                print(f"Tag not found: {path}")

        conn.commit()
        print("Success!")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
