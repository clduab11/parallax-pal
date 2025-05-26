import { io, Socket } from 'socket.io-client';

interface WebSocketConfig {
  url: string;
  reconnection: boolean;
  reconnectionAttempts: number;
  reconnectionDelay: number;
}

class WebSocketService {
  private socket: Socket | null = null;
  private config: WebSocketConfig = {
    url: process.env.REACT_APP_WS_URL || 'ws://localhost:8000',
    reconnection: true,
    reconnectionAttempts: 5,
    reconnectionDelay: 1000
  };

  connect(token?: string): void {
    if (this.socket?.connected) {
      return;
    }

    this.socket = io(this.config.url, {
      reconnection: this.config.reconnection,
      reconnectionAttempts: this.config.reconnectionAttempts,
      reconnectionDelay: this.config.reconnectionDelay,
      auth: token ? { token } : undefined,
      transports: ['websocket']
    });

    this.setupEventListeners();
  }

  private setupEventListeners(): void {
    if (!this.socket) return;

    this.socket.on('connect', () => {
      console.log('WebSocket connected');
    });

    this.socket.on('disconnect', (reason) => {
      console.log('WebSocket disconnected:', reason);
    });

    this.socket.on('error', (error) => {
      console.error('WebSocket error:', error);
    });
  }

  emit(event: string, data: any): void {
    if (this.socket?.connected) {
      this.socket.emit(event, data);
    } else {
      console.warn('WebSocket not connected');
    }
  }

  on(event: string, callback: (data: any) => void): void {
    if (this.socket) {
      this.socket.on(event, callback);
    }
  }

  off(event: string, callback?: (data: any) => void): void {
    if (this.socket) {
      this.socket.off(event, callback);
    }
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  isConnected(): boolean {
    return this.socket?.connected || false;
  }
}

const websocketService = new WebSocketService();
export default websocketService;