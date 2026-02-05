import React, { createContext, useContext, useState, useEffect } from 'react';
import { fetchActiveAlarms, fetchAlarmConfigs, saveAlarmConfig, acknowledgeAlarm, deleteAlarmConfig } from '../services/alarmService';
import socketService from '../services/socketService';

const AlarmContext = createContext();

export const AlarmProvider = ({ children }) => {
    const [activeAlarms, setActiveAlarms] = useState([]);
    const [alarmConfigs, setAlarmConfigs] = useState([]);
    const [unreadCount, setUnreadCount] = useState(0);

    const loadAlarms = async () => {
        try {
            console.log("🔄 Cargando alarmas y configuraciones...");
            const [active, configs] = await Promise.all([
                fetchActiveAlarms(),
                fetchAlarmConfigs()
            ]);
            setActiveAlarms(active);
            setAlarmConfigs(configs);
            console.log("✅ Datos de alarmas cargados:", { active: active.length, configs: configs.length });
        } catch (err) {
            console.error("❌ Alarm context load error:", err);
        }
    };

    useEffect(() => {
        loadAlarms();

        const handleSocketMessage = (msg) => {
            if (msg.type === 'ALARM_OPEN' || msg.type === 'ALARM_CLOSE' || msg.type === 'ALARM_ACK' || msg.type === 'ALARM_ACK_ALL') {
                loadAlarms();
                if (msg.type === 'ALARM_OPEN') setUnreadCount(prev => prev + 1);
            }
        };

        const unsubscribe = socketService.subscribe(handleSocketMessage);
        return () => unsubscribe();
    }, []);

    const updateConfig = async (config) => {
        try {
            console.log("📤 Guardando configuración en el backend...");
            const result = await saveAlarmConfig(config);
            console.log("📥 Resultado del guardado:", result);
            await loadAlarms();
            return result;
        } catch (err) {
            console.error("❌ Error en updateConfig:", err);
            throw err;
        }
    };

    const acknowledge = async (id, source) => {
        try {
            await acknowledgeAlarm(id, source);
            await loadAlarms();
        } catch (err) {
            console.error("Acknowledge error:", err);
        }
    };

    const deleteConfig = async (id) => {
        try {
            await deleteAlarmConfig(id);
            await loadAlarms();
        } catch (err) {
            console.error("❌ Error en deleteConfig:", err);
            throw err;
        }
    };

    return (
        <AlarmContext.Provider value={{
            activeAlarms,
            alarmConfigs,
            unreadCount,
            resetUnread: () => setUnreadCount(0),
            updateConfig,
            deleteConfig,
            acknowledge,
            loadAlarms
        }}>
            {children}
        </AlarmContext.Provider>
    );
};

export const useAlarms = () => useContext(AlarmContext);
