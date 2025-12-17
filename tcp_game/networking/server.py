"""
Socket Server for TCP Game
Handles incoming connections and packet processing from remote client
"""
import socket
import threading
import time
from typing import Callable, Optional

from tcp_game.networking.protocol import (
    decode_message, create_state_update, create_ready_message,
    MSG_PACKET, MSG_DISCONNECT, MSG_READY
)


class SocketServer:
    """
    TCP Socket server for hosting the game.
    Runs in background thread, calls callbacks on main thread.
    """
    
    def __init__(self, host: str = "0.0.0.0", port: int = 5555):
        self.host = host
        self.port = port
        self.socket: Optional[socket.socket] = None
        self.client_socket: Optional[socket.socket] = None
        self.running = False
        self.connected = False
        
        # Callbacks (set by host window)
        self.on_client_connected: Optional[Callable] = None
        self.on_packet_received: Optional[Callable] = None
        self.on_client_disconnected: Optional[Callable] = None
        self.on_error: Optional[Callable] = None
        
        # Buffer for incomplete messages
        self.recv_buffer = ""
    
    def start(self) -> bool:
        """Start the server and begin listening"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(1)
            self.running = True
            
            # Start accept thread
            accept_thread = threading.Thread(target=self._accept_loop, daemon=True)
            accept_thread.start()
            
            return True
        except Exception as e:
            if self.on_error:
                self.on_error(f"Failed to start server: {e}")
            return False
    
    def _accept_loop(self):
        """Wait for client connections - keeps listening after disconnect"""
        try:
            self.socket.settimeout(1.0)  # Allow periodic check for shutdown
            while self.running:
                try:
                    client, addr = self.socket.accept()
                    
                    # Close old client if exists
                    if self.client_socket:
                        try:
                            self.client_socket.close()
                        except:
                            pass
                    
                    self.client_socket = client
                    self.connected = True
                    self.recv_buffer = ""  # Clear buffer for new connection
                    
                    if self.on_client_connected:
                        self.on_client_connected(addr)
                    
                    # Send ready message
                    self.client_socket.sendall(create_ready_message())
                    
                    # Start receive loop (blocks until disconnect)
                    self._receive_loop()
                    
                    # After receive loop ends, continue accepting new connections
                    # (don't break - keep listening)
                    
                except socket.timeout:
                    continue
        except Exception as e:
            if self.running and self.on_error:
                self.on_error(f"Accept error: {e}")
    
    def _receive_loop(self):
        """Receive packets from client"""
        try:
            while self.running and self.connected:
                try:
                    self.client_socket.settimeout(0.5)
                    data = self.client_socket.recv(4096)
                    
                    if not data:
                        self.connected = False
                        if self.on_client_disconnected:
                            self.on_client_disconnected()
                        break
                    
                    # Add to buffer and process complete messages
                    self.recv_buffer += data.decode("utf-8")
                    self._process_buffer()
                    
                except socket.timeout:
                    continue
        except Exception as e:
            self.connected = False
            if self.on_client_disconnected:
                self.on_client_disconnected()
    
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
        
        if msg_type == MSG_PACKET:
            if self.on_packet_received:
                self.on_packet_received(
                    msg.get("seq", 0),
                    msg.get("ack", 0),
                    msg.get("length", 0),
                    msg.get("rwnd", 0),
                    msg.get("is_error", False)
                )
        elif msg_type == MSG_DISCONNECT:
            self.connected = False
            if self.on_client_disconnected:
                self.on_client_disconnected()
    
    def send_state_update(self, game_state, last_message: str, last_valid: bool, reset_timer: bool = True, game_time_left: int = 300, game_over: bool = False):
        """Send game state update to client"""
        if self.connected and self.client_socket:
            try:
                data = create_state_update(game_state, last_message, last_valid, reset_timer, game_time_left, game_over)
                self.client_socket.sendall(data)
            except Exception as e:
                if self.on_error:
                    self.on_error(f"Send error: {e}")
                self.connected = False
    
    def stop(self):
        """Stop the server"""
        self.running = False
        self.connected = False
        
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
    
    def get_local_ip(self) -> str:
        """Get local IP address for display"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
