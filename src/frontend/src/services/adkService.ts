import { AxiosResponse } from 'axios';
import api from './api';
import WebSocket from 'isomorphic-ws';

/**
 * ADK Service for interacting with Agent Development Kit backend
 */
class ADKService {
  private socket: WebSocket | null = null;
  private sessionId: string | null = null;
  private messageHandlers: Map<string, Function[]> = new Map();
  private connectionStatus: 'disconnected' | 'connecting' | 'connected' = 'disconnected';
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectTimeout: any = null;

  /**
   * Start a new research task
   * @param query Research query
   * @param continuousMode Whether to research all focus areas (true) or just the first one (false)
   * @param forceRefresh Whether to ignore cache and force a fresh research
   * @returns Response with request ID
   */
  public async startResearch(
    query: string,
    continuousMode: boolean = false,
    forceRefresh: boolean = false
  ): Promise<AxiosResponse<any>> {
    return api.post('/api/adk/research', {
      query,
      continuous_mode: continuousMode,
      force_refresh: forceRefresh
    });
  }

  /**
   * Get research status
   * @param requestId Research request ID
   * @returns Response with research status
   */
  public async getResearchStatus(requestId: string): Promise<AxiosResponse<any>> {
    return api.get(`/api/adk/research/${requestId}`);
  }

  /**
   * Cancel research
   * @param requestId Research request ID
   * @returns Response with cancellation status
   */
  public async cancelResearch(requestId: string): Promise<AxiosResponse<any>> {
    return api.post(`/api/adk/research/${requestId}/cancel`);
  }

  /**
   * Generate follow-up questions for research
   * @param requestId Research request ID
   * @returns Response with follow-up questions
   */
  public async getFollowupQuestions(requestId: string): Promise<AxiosResponse<any>> {
    return api.post(`/api/adk/research/${requestId}/followup`);
  }

  /**
   * Get knowledge graph for research
   * @param requestId Research request ID
   * @returns Response with knowledge graph
   */
  public async getKnowledgeGraph(requestId: string): Promise<AxiosResponse<any>> {
    return api.get(`/api/adk/graph/${requestId}`);
  }

  /**
   * Get citations for research
   * @param requestId Research request ID
   * @param style Citation style (default: 'apa')
   * @returns Response with citations
   */
  public async getCitations(requestId: string, style: string = 'apa'): Promise<AxiosResponse<any>> {
    return api.get(`/api/adk/citations/${requestId}?style=${style}`);
  }

  /**
   * Check ADK system health
   * @returns Response with health status
   */
  public async checkHealth(): Promise<AxiosResponse<any>> {
    return api.get('/api/adk/health');
  }

  /**
   * Initialize WebSocket connection for real-time updates
   * @param token Authentication token
   * @returns Promise resolving when connection is established
   */
  public async initializeWebSocket(token: string): Promise<void> {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected');
      return Promise.resolve();
    }

    this.connectionStatus = 'connecting';
    
    // Close existing socket if any
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }

    return new Promise((resolve, reject) => {
      try {
        // Determine websocket URL (support both http and https)
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        const wsUrl = `${protocol}//${host}/api/adk/ws`;
        
        // Create new socket
        this.socket = new WebSocket(wsUrl);
        
        // Set up event handlers
        this.socket.onopen = () => {
          console.log('WebSocket connection established');
          this.connectionStatus = 'connected';
          this.reconnectAttempts = 0;
          resolve();
        };
        
        this.socket.onmessage = (event) => {
          try {
            const data = typeof event.data === 'string' ? event.data : event.data.toString();
            const message = JSON.parse(data);
            
            // Handle connection established message
            if (message.type === 'connection_established') {
              this.sessionId = message.session_id;
              console.log(`Connection established with session ID: ${this.sessionId}`);
            }
            
            // Dispatch message to handlers
            this._dispatchMessage(message);
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };
        
        this.socket.onclose = (event) => {
          console.log('WebSocket connection closed:', event.code, event.reason);
          this.connectionStatus = 'disconnected';
          
          // Attempt reconnection if not intentionally closed
          if (event.code !== 1000) {
            this._attemptReconnect(token);
          }
        };
        
        this.socket.onerror = (error) => {
          console.error('WebSocket error:', error);
          this.connectionStatus = 'disconnected';
          reject(error);
        };
      } catch (error) {
        console.error('Error initializing WebSocket:', error);
        this.connectionStatus = 'disconnected';
        reject(error);
      }
    });
  }

  /**
   * Cleanup WebSocket connection
   */
  public cleanup(): void {
    if (this.socket) {
      this.socket.close(1000, 'Client disconnecting');
      this.socket = null;
    }
    
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    
    this.sessionId = null;
    this.connectionStatus = 'disconnected';
    this.messageHandlers.clear();
  }

  /**
   * Start research via WebSocket
   * @param query Research query
   * @param continuousMode Whether to research all focus areas
   * @param forceRefresh Whether to ignore cache
   */
  public startResearchViaWebSocket(
    query: string,
    continuousMode: boolean = false,
    forceRefresh: boolean = false
  ): void {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN || !this.sessionId) {
      throw new Error('WebSocket not connected');
    }
    
    const message = {
      type: 'start_research',
      session_id: this.sessionId,
      query,
      continuous_mode: continuousMode,
      force_refresh: forceRefresh
    };
    
    this.socket.send(JSON.stringify(message));
  }

  /**
   * Cancel research via WebSocket
   * @param requestId Research request ID
   */
  public cancelResearchViaWebSocket(requestId: string): void {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN || !this.sessionId) {
      throw new Error('WebSocket not connected');
    }
    
    const message = {
      type: 'cancel_research',
      session_id: this.sessionId,
      request_id: requestId
    };
    
    this.socket.send(JSON.stringify(message));
  }

  /**
   * Add event listener for WebSocket messages
   * @param eventType Event type to listen for
   * @param handler Handler function
   */
  public addEventListener(eventType: string, handler: Function): void {
    if (!this.messageHandlers.has(eventType)) {
      this.messageHandlers.set(eventType, []);
    }
    
    this.messageHandlers.get(eventType)!.push(handler);
  }

  /**
   * Remove event listener
   * @param eventType Event type
   * @param handler Handler function to remove
   */
  public removeEventListener(eventType: string, handler: Function): void {
    if (!this.messageHandlers.has(eventType)) {
      return;
    }
    
    const handlers = this.messageHandlers.get(eventType)!;
    const index = handlers.indexOf(handler);
    
    if (index !== -1) {
      handlers.splice(index, 1);
    }
    
    if (handlers.length === 0) {
      this.messageHandlers.delete(eventType);
    }
  }

  /**
   * Get WebSocket connection status
   * @returns Connection status
   */
  public getConnectionStatus(): 'disconnected' | 'connecting' | 'connected' {
    return this.connectionStatus;
  }

  /**
   * Attempt to reconnect WebSocket
   * @param token Authentication token
   */
  private _attemptReconnect(token: string): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log('Maximum reconnect attempts reached');
      return;
    }
    
    this.reconnectAttempts++;
    const delay = Math.pow(2, this.reconnectAttempts) * 1000; // Exponential backoff
    
    console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`);
    
    this.reconnectTimeout = setTimeout(() => {
      console.log(`Reconnecting... (attempt ${this.reconnectAttempts})`);
      this.initializeWebSocket(token).catch(error => {
        console.error('Reconnection failed:', error);
      });
    }, delay);
  }

  /**
   * Dispatch WebSocket message to handlers
   * @param message WebSocket message
   */
  private _dispatchMessage(message: any): void {
    const eventType = message.type;
    
    if (!eventType) {
      console.warn('Received message without type:', message);
      return;
    }
    
    if (!this.messageHandlers.has(eventType)) {
      console.debug(`No handlers for message type: ${eventType}`);
      return;
    }
    
    const handlers = this.messageHandlers.get(eventType)!;
    
    for (const handler of handlers) {
      try {
        handler(message);
      } catch (error) {
        console.error(`Error in handler for ${eventType}:`, error);
      }
    }
  }
}

// Create singleton instance
const adkService = new ADKService();
export default adkService;