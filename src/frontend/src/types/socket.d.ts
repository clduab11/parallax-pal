import { Socket } from 'socket.io-client';
import { SocketEvents } from './terminal';

export interface SocketClient extends Socket {
  on: <T extends keyof SocketEvents>(event: T, listener: SocketEvents[T]) => void;
  emit: <T extends keyof SocketEvents>(event: T, ...args: Parameters<SocketEvents[T]>) => void;
}