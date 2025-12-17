"""
Socket Client for TCP Game
Connects to host and sends/receives game messages
"""
import socket
import threading
from typing import Callable, Optional

from tcp_game.networking.protocol import (
    decode_message, create_packet_message, create_disconnect_message,
    MSG_STATE_UPDATE, MSG_READY, MSG_DISCONNECT
)


class SocketClient:
    """
    TCP Socket client for connecting to game host.
    Runs receive loop in background thread.
    """
    
    def __init__(self):
        self.socket: Optional[socket.socket] = None
        self.running = False
        self.connected = False
        
        # Callbacks (set by client window)
        self.on_connected: Optional[Callable] = None
        self.on_state_update: Optional[Callable] = None
        self.on_disconnected: Optional[Callable] = None
        self.on_error: Optional[Callable] = None
        
        # Buffer for incomplete messages
        self.recv_buffer = ""
    
    def connect(self, host: str = "127.0.0.1", port: int = 5555) -> bool:
        """Connect to host server (blocking)"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10.0)  # Connection timeout
            self.socket.connect((host, port))
            self.socket.settimeout(None)
            self.running = True
            self.connected = True
            self.recv_buffer = ""  # Clear buffer on reconnect
            
            # Start receive thread
            recv_thread = threading.Thread(target=self._receive_loop, daemon=True)
            recv_thread.start()
            
            return True
        except Exception as e:
            if self.on_error:
                self.on_error(f"Connection failed: {e}")
            return False
    
    def connect_async(self, host: str = "127.0.0.1", port: int = 5555):
        """Connect to host server in background thread (non-blocking)"""
        def _connect():
            self.connect(host, port)
        
        connect_thread = threading.Thread(target=_connect, daemon=True)
        connect_thread.start()
    
    def _receive_loop(self):
        """Receive state updates from server"""
        try:
            while self.running and self.connected:
                try:
                    self.socket.settimeout(0.5)
                    data = self.socket.recv(4096)
                    
                    if not data:
                        self.connected = False
                        if self.on_disconnected:
                            self.on_disconnected()
                        break
                    
                    # Add to buffer and process complete messages
                    self.recv_buffer += data.decode("utf-8")
                    self._process_buffer()
                    
                except socket.timeout:
                    continue
        except Exception as e:
            self.connected = False
            if self.on_disconnected:
                self.on_disconnected()
    
    def _process_buffer(self):
        """Process complete messages from buffer"""
        while "\n" in self.recv_buffer:
            line, self.recv_buffer = self.recv_buffer.split("\n", 1)
            if line.strip():
                msg = decode_message(line.encode("utf-8"))
                if msg:
                    self._handle_message(msg)
    
    def _handle_message(self, msg: dict):
        """Handle received message"""
        msg_type = msg.get("type")
        
        if msg_type == MSG_READY:
            if self.on_connected:
                self.on_connected()
        elif msg_type == MSG_STATE_UPDATE:
            if self.on_state_update:
                self.on_state_update(msg)
        elif msg_type == MSG_DISCONNECT:
            self.connected = False
            if self.on_disconnected:
                self.on_disconnected()
    
    def send_packet(self, seq: int, ack: int, length: int, rwnd: int, is_error: bool = False):
        """Send a packet to the host"""
        if self.connected and self.socket:
            try:
                data = create_packet_message(seq, ack, length, rwnd, is_error)
                self.socket.sendall(data)
            except Exception as e:
                if self.on_error:
                    self.on_error(f"Send error: {e}")
                self.connected = False
    
    def disconnect(self):
        """Disconnect from server (non-blocking)"""
        self.running = False
        self.connected = False
        
        sock = self.socket
        self.socket = None
        
        if sock:
            def _close_socket():
                try:
                    sock.sendall(create_disconnect_message())
                except:
                    pass
                try:
                    sock.shutdown(socket.SHUT_RDWR)
                except:
                    pass
                try:
                    sock.close()
                except:
                    pass
            
            # Close socket in background to not block GUI
            close_thread = threading.Thread(target=_close_socket, daemon=True)
            close_thread.start()
