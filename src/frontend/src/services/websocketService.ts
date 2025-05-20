import { io, Socket } from 'socket.io-client';
import { SocketEvents, ResearchQueryData, ResearchUpdateData } from '../types/terminal';

class WebSocketService {
  private socket: Socket | null = null;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private reconnectAttempts = 0;
  private readonly maxReconnectAttempts = 5;
  private readonly reconnectDelay = 2000; // 2 seconds
  private eventHandlers: Partial<Record<keyof SocketEvents, Function[]>> = {};

  /**
   * Initialize the WebSocket connection with authentication
   */
  initialize(accessToken: string): Promise<void> {
    return new Promise((resolve, reject) => {
      const wsUrl = process.env.REACT_APP_WS_URL || 'http://localhost:8000';
      
      // Clean up any existing connection
      this.cleanup();
      
      try {
        // Create a new connection with auth token
        this.socket = io(wsUrl, {
          auth: {
            token: accessToken
          },
          transports: ['websocket'],
          reconnection: false // We'll handle reconnection manually
        });
        
        // Setup event listeners
        this.socket.on('connect', () => {
          console.log('WebSocket connected');
          this.reconnectAttempts = 0;
          resolve();
        });
        
        this.socket.on('connect_error', (err) => {
          console.error('WebSocket connection error:', err);
          this.handleReconnect();
          if (this.reconnectAttempts === 1) {
            reject(err);
          }
        });
        
        this.socket.on('disconnect', (reason) => {
          console.log('WebSocket disconnected:', reason);
          this.handleReconnect();
        });
        
        // Setup custom event forwarding
        this.setupEventForwarding();
      } catch (error) {
        console.error('Failed to initialize WebSocket:', error);
        reject(error);
      }
    });
  }
  
  /**
   * Clean up WebSocket connection and timers
   */
  cleanup(): void {
    if (this.socket) {
      this.socket.off();
      this.socket.disconnect();
      this.socket = null;
    }
    
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    
    this.reconnectAttempts = 0;
  }
  
  /**
   * Handle reconnection attempts
   */
  private handleReconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
    }
    
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      
      this.reconnectTimer = setTimeout(() => {
        console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
        this.updateToken();
      }, this.reconnectDelay * this.reconnectAttempts);
    } else {
      console.error('Max reconnection attempts reached');
      this.triggerEvent('error', { 
        message: 'Connection lost. Please refresh the page.' 
      });
    }
  }
  
  /**
   * Update the auth token (useful for reconnection after token refresh)
   */
  updateToken(newToken?: string): void {
    if (!this.socket) {
      const token = newToken || localStorage.getItem('accessToken');
      if (token) {
        this.initialize(token).catch(console.error);
      }
      return;
    }
    
    if (newToken) {
      this.socket.auth = { token: newToken };
      this.socket.disconnect().connect();
    }
  }
  
  /**
   * Setup forwarding of Socket.IO events to registered handlers
   */
  private setupEventForwarding(): void {
    if (!this.socket) return;
    
    // Forward research updates
    this.socket.on('research_update', (data: ResearchUpdateData) => {
      this.triggerEvent('research_update', data);
    });
    
    // Forward errors
    this.socket.on('error', (data: any) => {
      this.triggerEvent('error', data);
    });
    
    // Forward auth status updates
    this.socket.on('auth_status', (data: any) => {
      this.triggerEvent('auth_status', data);
    });
    
    // Handle keepalive
    this.socket.on('ping', (data: any) => {
      this.triggerEvent('ping', data);
      if (this.socket && this.socket.connected) {
        this.socket.emit('pong', { timestamp: new Date().toISOString() });
      }
    });
  }
  
  /**
   * Register an event handler
   */
  on<T extends keyof SocketEvents>(
    event: T, 
    handler: SocketEvents[T]
  ): () => void {
    if (!this.eventHandlers[event]) {
      this.eventHandlers[event] = [];
    }
    
    this.eventHandlers[event]!.push(handler as Function);
    
    // Return a function to remove this handler
    return () => {
      if (this.eventHandlers[event]) {
        this.eventHandlers[event] = this.eventHandlers[event]!.filter(h => h !== handler);
      }
    };
  }
  
  /**
   * Trigger an event for all registered handlers
   */
  private triggerEvent<T extends keyof SocketEvents>(
    event: T, 
    data: Parameters<SocketEvents[T]>[0]
  ): void {
    if (this.eventHandlers[event]) {
      this.eventHandlers[event]!.forEach(handler => {
        try {
          handler(data);
        } catch (error) {
          console.error(`Error in ${event} handler:`, error);
        }
      });
    }
  }
  
  /**
   * Send a research query
   */
  sendResearchQuery(query: ResearchQueryData): boolean {
    if (!this.socket || !this.socket.connected) {
      console.error('WebSocket not connected');
      return false;
    }
    
    this.socket.emit('research_query', query);
    return true;
  }
  
  /**
   * Check if WebSocket is connected
   */
  isConnected(): boolean {
    return !!this.socket && this.socket.connected;
  }
}

// Create a singleton instance
const websocketService = new WebSocketService();
export default websocketService;