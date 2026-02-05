import React, { createContext, useContext, useState } from 'react';
import { fetchHistory, fetchHistoryStats } from '../services/historyService';

const HistoryContext = createContext();

export const HistoryProvider = ({ children }) => {
    const [histories, setHistories] = useState({}); // { [path]: data }
    const [tagStats, setTagStats] = useState({}); // { [path]: stats }
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);

    const loadHistories = async (tagPaths, options = { hours: 1 }) => {
        setIsLoading(true);
        setError(null);
        try {
            const results = await Promise.all(
                tagPaths.map(path => fetchHistory(path, options))
            );
            const newHistories = {};
            results.forEach(res => {
                newHistories[res.path] = res.data;
            });
            setHistories(newHistories);
        } catch (err) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    const loadTagStats = async (tagPath, options = { hours: 1 }) => {
        try {
            const res = await fetchHistoryStats(tagPath, options);
            setTagStats(prev => ({ ...prev, [tagPath]: res.stats }));
        } catch (err) {
            console.error("Error loading stats:", err);
        }
    };

    const clearHistory = () => {
        setHistories({});
        setTagStats({});
    };

    return (
        <HistoryContext.Provider value={{
            histories,
            tagStats,
            isLoading,
            error,
            loadHistories,
            loadTagStats,
            clearHistory
        }}>
            {children}
        </HistoryContext.Provider>
    );
};

export const useHistory = () => {
    const context = useContext(HistoryContext);
    if (!context) {
        throw new Error('useHistory must be used within a HistoryProvider');
    }
    return context;
};
