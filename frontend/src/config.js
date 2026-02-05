const config = {
    API_URL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
    WS_URL: import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/live',
};

export default config;
