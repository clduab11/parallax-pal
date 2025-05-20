import { Socket } from 'socket.io-client';
import { SocketEvents } from './terminal';

/**
 * Extended Socket interface with strongly-typed events
 */
export interface SocketClient extends Socket {
  on: <T extends keyof SocketEvents>(event: T, listener: SocketEvents[T]) => void;
  emit: <T extends keyof SocketEvents>(event: T, ...args: Parameters<SocketEvents[T]>) => void;
  
  /**
   * Connect to the Socket.IO server
   */
  connect: () => void;
  
  /**
   * Whether the socket is currently connected
   */
  connected: boolean;
}