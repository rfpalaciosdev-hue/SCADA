import React, { createContext, useContext, useState, useEffect } from 'react';
import { fetchTags } from '../services/scadaService';
import socketService from '../services/socketService';

const SCADAContext = createContext();

export const SCADAProvider = ({ children }) => {
    const [tags, setTags] = useState({});
    const [connected, setConnected] = useState(false);
    const [lastUpdate, setLastUpdate] = useState(null);

    const handleUpdate = (update) => {
        setTags(prev => ({
            ...prev,
            [update.topic]: {
                ...prev[update.topic],
                path: update.topic,
                v: update.val,
                t: update.ts,
                q: update.q !== undefined ? update.q : (prev[update.topic]?.q ?? 192)
            }
        }));
        setLastUpdate(new Date().toLocaleTimeString());
    };

    useEffect(() => {
        // 1. Carga inicial vía Service
        const loadInitialData = async () => {
            try {
                const data = await fetchTags();
                // Inyectar el path en cada objeto tag
                const enrichedData = {};
                Object.entries(data).forEach(([key, value]) => {
                    enrichedData[key] = { ...value, path: key };
                });
                setTags(enrichedData);
            } catch (err) {
                console.error("SCADA Context Init Error:", err);
            }
        };

        loadInitialData();

        // 2. Suscripción a datos en tiempo real vía SocketService
        const unsubscribeData = socketService.subscribe(handleUpdate);

        // 3. Suscripción al estado de conexión
        const unsubscribeStatus = socketService.subscribeStatus(setConnected);

        // Conectar el servicio
        socketService.connect();

        return () => {
            unsubscribeData();
            unsubscribeStatus();
            socketService.disconnect();
        };
    }, []);

    return (
        <SCADAContext.Provider value={{ tags, connected, lastUpdate }}>
            {children}
        </SCADAContext.Provider>
    );
};

export const useSCADA = () => {
    const context = useContext(SCADAContext);
    if (!context) {
        throw new Error('useSCADA must be used within a SCADAProvider');
    }
    return context;
};
