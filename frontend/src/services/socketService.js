import config from '../config';

class SocketService {
    constructor() {
        this.socket = null;
        this.listeners = new Set();
        this.statusListeners = new Set();
        this.reconnectTimeout = null;
    }

    connect() {
        if (this.socket && (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)) {
            return;
        }

        this.socket = new WebSocket(config.WS_URL);

        this.socket.onopen = () => {
            console.log('🟢 [SocketService] Connected');
            this._notifyStatus(true);
        };

        this.socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this._notifyListeners(data);
            } catch (err) {
                console.error('⚠️ [SocketService] Message parse error:', err);
            }
        };

        this.socket.onclose = () => {
            console.warn('🔴 [SocketService] Disconnected. Scheduling reconnect...');
            this._notifyStatus(false);
            this._reconnect();
        };

        this.socket.onerror = (error) => {
            console.error('❌ [SocketService] WebSocket Error:', error);
            this.socket.close();
        };
    }

    _reconnect() {
        if (this.reconnectTimeout) clearTimeout(this.reconnectTimeout);
        this.reconnectTimeout = setTimeout(() => this.connect(), 3000);
    }

    subscribe(callback) {
        this.listeners.add(callback);
        return () => this.listeners.delete(callback);
    }

    subscribeStatus(callback) {
        this.statusListeners.add(callback);
        return () => this.statusListeners.delete(callback);
    }

    _notifyListeners(data) {
        this.listeners.forEach(cb => cb(data));
    }

    _notifyStatus(isConnected) {
        this.statusListeners.forEach(cb => cb(isConnected));
    }

    disconnect() {
        if (this.reconnectTimeout) clearTimeout(this.reconnectTimeout);
        if (this.socket) {
            this.socket.onclose = null; // Evitar reconexión automática al cerrar manual
            this.socket.close();
        }
    }
}

// Singleton para toda la app
const socketService = new SocketService();
export default socketService;
