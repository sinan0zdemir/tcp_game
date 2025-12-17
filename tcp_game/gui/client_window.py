"""
Client Window for TCP Game - Player B (Client)
Connects to host and receives game state updates
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import time
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tcp_game.core.game_state import Player
from tcp_game.gui.timeline_canvas import TimelineCanvas
from tcp_game.networking.client import SocketClient


class ClientWindow:
    """Window for Player B (Client) - connects to host"""
    
    def __init__(self, root: tk.Tk, host: str = "127.0.0.1", port: int = 5555):
        self.root = root
        self.root.title("TCP Game - Player B (Client)")
        self.root.geometry("550x800")
        self.root.configure(bg="#0f0f1a")
        
        self.host = host
        self.port = port
        
        # Local state (mirrors server state)
        self.current_turn = "A"
        self.score_a = 0
        self.score_b = 0
        self.my_rwnd = 50
        self.opp_rwnd = 50
        self.my_next_seq = 0
        self.opponent_sent_invalid = False
        self.last_displayed_packet_count = 0
        
        # Socket client
        self.client = SocketClient()
        self.client.on_connected = self.on_connected
        self.client.on_state_update = self.on_state_update
        self.client.on_disconnected = self.on_disconnected
        self.client.on_error = self.on_network_error
        
        # Timer state
        self.timer_id = None
        self.time_left = 45
        
        # Build UI
        self.setup_styles()
        self.create_widgets()
        self.update_display()
        
        # Connect to host
        self.connect_to_host()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def setup_styles(self):
        """Configure ttk styles for dark theme"""
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure("Dark.TFrame", background="#0f0f1a")
        style.configure("Dark.TLabel", background="#0f0f1a", foreground="#e0e0e0", font=("Segoe UI", 11))
        style.configure("Title.TLabel", background="#0f0f1a", foreground="#ff6b6b", font=("Segoe UI", 16, "bold"))
        style.configure("Score.TLabel", background="#1a1a2e", foreground="#4ade80", font=("Consolas", 14, "bold"))
        style.configure("Turn.TLabel", background="#1a1a2e", foreground="#ffd93d", font=("Segoe UI", 14, "bold"))
        style.configure("Timer.TLabel", background="#1a1a2e", foreground="#ff6b6b", font=("Consolas", 18, "bold"))
        style.configure("Status.TLabel", background="#0f0f1a", foreground="#4ade80", font=("Consolas", 10))
        style.configure("Error.TLabel", background="#0f0f1a", foreground="#ff4444", font=("Consolas", 10))
        style.configure("RWND.TLabel", background="#1a1a2e", foreground="#a78bfa", font=("Consolas", 12, "bold"))
        style.configure("Network.TLabel", background="#1a1a2e", foreground="#fbbf24", font=("Consolas", 10))
    
    def create_widgets(self):
        """Create all GUI widgets"""
        # Main container
        main_frame = ttk.Frame(self.root, style="Dark.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_frame, text="Player B (Client)", style="Title.TLabel")
        title_label.pack(pady=(0, 5))
        
        # Network status panel
        net_frame = tk.Frame(main_frame, bg="#1a1a2e", relief=tk.RIDGE, bd=2)
        net_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.network_label = ttk.Label(net_frame, text="Connecting...", style="Network.TLabel")
        self.network_label.pack(pady=5, padx=10)
        
        # Info panel
        info_frame = tk.Frame(main_frame, bg="#1a1a2e", relief=tk.RIDGE, bd=2)
        info_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Scores row
        score_row = tk.Frame(info_frame, bg="#1a1a2e")
        score_row.pack(fill=tk.X, padx=10, pady=5)
        
        self.score_a_label = ttk.Label(score_row, text="A: 0", style="Score.TLabel")
        self.score_a_label.pack(side=tk.LEFT, padx=5)
        
        self.score_b_label = ttk.Label(score_row, text="B: 0", style="Score.TLabel")
        self.score_b_label.pack(side=tk.LEFT, padx=5)
        
        # Timer
        self.timer_label = ttk.Label(score_row, text="45s", style="Timer.TLabel")
        self.timer_label.pack(side=tk.RIGHT, padx=5)
        
        # Turn indicator
        self.turn_label = ttk.Label(info_frame, text="Waiting...", style="Turn.TLabel")
        self.turn_label.pack(pady=5)
        
        # RWND display
        rwnd_frame = tk.Frame(info_frame, bg="#1a1a2e")
        rwnd_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.my_rwnd_label = ttk.Label(rwnd_frame, text="My RWND: 50", style="RWND.TLabel")
        self.my_rwnd_label.pack(side=tk.LEFT, padx=5)
        
        self.opp_rwnd_label = ttk.Label(rwnd_frame, text="Opp RWND: 50", style="RWND.TLabel")
        self.opp_rwnd_label.pack(side=tk.RIGHT, padx=5)
        
        # Input panel
        input_frame = tk.Frame(main_frame, bg="#1a1a2e", relief=tk.RIDGE, bd=2)
        input_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(input_frame, text="Send Packet", style="Title.TLabel").pack(pady=5)
        
        # Input fields
        fields_frame = tk.Frame(input_frame, bg="#1a1a2e")
        fields_frame.pack(padx=15, pady=5)
        
        # SEQ
        seq_frame = tk.Frame(fields_frame, bg="#1a1a2e")
        seq_frame.pack(fill=tk.X, pady=2)
        ttk.Label(seq_frame, text="SEQ:", style="Dark.TLabel", width=8).pack(side=tk.LEFT)
        self.seq_entry = tk.Entry(seq_frame, font=("Consolas", 12), width=12, bg="#2a2a3e", fg="white", insertbackground="white")
        self.seq_entry.pack(side=tk.LEFT, padx=5)
        self.seq_entry.insert(0, "0")
        
        # ACK
        ack_frame = tk.Frame(fields_frame, bg="#1a1a2e")
        ack_frame.pack(fill=tk.X, pady=2)
        ttk.Label(ack_frame, text="ACK:", style="Dark.TLabel", width=8).pack(side=tk.LEFT)
        self.ack_entry = tk.Entry(ack_frame, font=("Consolas", 12), width=12, bg="#2a2a3e", fg="white", insertbackground="white")
        self.ack_entry.pack(side=tk.LEFT, padx=5)
        self.ack_entry.insert(0, "0")
        
        # LEN
        len_frame = tk.Frame(fields_frame, bg="#1a1a2e")
        len_frame.pack(fill=tk.X, pady=2)
        ttk.Label(len_frame, text="LEN:", style="Dark.TLabel", width=8).pack(side=tk.LEFT)
        self.len_entry = tk.Entry(len_frame, font=("Consolas", 12), width=12, bg="#2a2a3e", fg="white", insertbackground="white")
        self.len_entry.pack(side=tk.LEFT, padx=5)
        self.len_entry.insert(0, "10")
        
        # RWND
        rwnd_input_frame = tk.Frame(fields_frame, bg="#1a1a2e")
        rwnd_input_frame.pack(fill=tk.X, pady=2)
        ttk.Label(rwnd_input_frame, text="RWND:", style="Dark.TLabel", width=8).pack(side=tk.LEFT)
        self.rwnd_entry = tk.Entry(rwnd_input_frame, font=("Consolas", 12), width=12, bg="#2a2a3e", fg="white", insertbackground="white")
        self.rwnd_entry.pack(side=tk.LEFT, padx=5)
        self.rwnd_entry.insert(0, "50")
        
        # Buttons
        btn_frame = tk.Frame(input_frame, bg="#1a1a2e")
        btn_frame.pack(pady=5)
        
        self.send_btn = tk.Button(
            btn_frame, text="📤 Send", font=("Segoe UI", 11, "bold"),
            bg="#4ade80", fg="#0f0f1a", activebackground="#22c55e",
            command=self.send_packet, width=10, height=1, state=tk.DISABLED
        )
        self.send_btn.pack(side=tk.LEFT, padx=5)
        
        self.error_btn = tk.Button(
            btn_frame, text="⚠️ ERROR", font=("Segoe UI", 11, "bold"),
            bg="#ff6b6b", fg="white", activebackground="#ef4444",
            command=self.send_error, width=10, height=1, state=tk.DISABLED
        )
        self.error_btn.pack(side=tk.LEFT, padx=5)
        
        # Status
        self.status_label = ttk.Label(input_frame, text="Connecting to host...", style="Status.TLabel", wraplength=400)
        self.status_label.pack(pady=5)
        
        # Timeline
        timeline_frame = tk.Frame(main_frame, bg="#1a1a2e", relief=tk.RIDGE, bd=2)
        timeline_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        ttk.Label(timeline_frame, text="Packet Timeline", style="Dark.TLabel").pack(pady=3)
        
        self.timeline = TimelineCanvas(timeline_frame, bg="#1a1a2e")
        self.timeline.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Packet log
        log_frame = tk.Frame(main_frame, bg="#1a1a2e", relief=tk.RIDGE, bd=2)
        log_frame.pack(fill=tk.X, pady=5)
        
        self.log_text = tk.Text(
            log_frame, height=4, bg="#0f0f1a", fg="#e0e0e0",
            font=("Consolas", 9), state=tk.DISABLED
        )
        self.log_text.pack(fill=tk.X, padx=5, pady=5)
        
        # Reconnect button
        reconnect_btn = tk.Button(
            main_frame, text="🔄 Reconnect", font=("Segoe UI", 10),
            bg="#6366f1", fg="white", command=self.reconnect, width=12
        )
        reconnect_btn.pack(pady=5)
    
    def connect_to_host(self):
        """Connect to the host server"""
        self.network_label.configure(text=f"🔌 Connecting to {self.host}:{self.port}...")
        
        if self.client.connect(self.host, self.port):
            self.log_message(f"Connecting to {self.host}:{self.port}...")
        else:
            self.network_label.configure(text="❌ Connection failed")
            self.log_message("Connection failed", is_error=True)
    
    def on_connected(self):
        """Called when connected to host"""
        self.root.after(0, self._handle_connected)
    
    def _handle_connected(self):
        """Handle connection on main thread"""
        self.network_label.configure(text=f"✅ Connected to {self.host}:{self.port}")
        self.log_message("Connected to host!")
        self.status_label.configure(text="Connected! Waiting for your turn...", style="Status.TLabel")
        self.start_timer()
    
    def on_state_update(self, state: dict):
        """Called when state update received from host"""
        self.root.after(0, lambda: self._handle_state_update(state))
    
    def _handle_state_update(self, state: dict):
        """Handle state update on main thread"""
        # Update local state
        self.current_turn = state.get("current_turn", "A")
        self.score_a = state.get("score_a", 0)
        self.score_b = state.get("score_b", 0)
        self.my_rwnd = state.get("player_b_rwnd", 50)
        self.opp_rwnd = state.get("player_a_rwnd", 50)
        self.my_next_seq = state.get("player_b_next_seq", 0)
        self.opponent_sent_invalid = state.get("opponent_sent_invalid", False)
        
        last_message = state.get("last_message", "")
        last_valid = state.get("last_valid", True)
        
        # Update timeline with new packets
        packet_history = state.get("packet_history", [])
        for i in range(self.last_displayed_packet_count, len(packet_history)):
            self.timeline.add_packet(packet_history[i])
        self.last_displayed_packet_count = len(packet_history)
        
        # Log the message
        if last_message:
            self.status_label.configure(
                text=last_message,
                style="Status.TLabel" if last_valid else "Error.TLabel"
            )
        
        # Update display
        self.update_display()
        
        # Only reset timer if server says to (not on RWND updates)
        if state.get("reset_timer", True):
            self.start_timer()
    
    def on_disconnected(self):
        """Called when disconnected from host"""
        self.root.after(0, self._handle_disconnected)
    
    def _handle_disconnected(self):
        """Handle disconnect on main thread"""
        self.network_label.configure(text="❌ Disconnected from host")
        self.log_message("Disconnected from host", is_error=True)
        self.send_btn.configure(state=tk.DISABLED)
        self.error_btn.configure(state=tk.DISABLED)
        self.stop_timer()
    
    def on_network_error(self, error: str):
        """Called on network error"""
        self.root.after(0, lambda: self.log_message(f"Network error: {error}", is_error=True))
    
    def send_packet(self):
        """Send a packet to host"""
        if self.current_turn != "B":
            self.status_label.configure(text="Not your turn!", style="Error.TLabel")
            return
        
        if not self.client.connected:
            self.status_label.configure(text="Not connected to host!", style="Error.TLabel")
            return
        
        try:
            seq = int(self.seq_entry.get())
            ack = int(self.ack_entry.get())
            length = int(self.len_entry.get())
            rwnd = int(self.rwnd_entry.get()) if self.rwnd_entry.get().strip() else self.my_rwnd
        except ValueError:
            self.status_label.configure(text="Invalid input - use integers", style="Error.TLabel")
            return
        
        # Send to host
        self.client.send_packet(seq, ack, length, rwnd, is_error=False)
        
        # Log locally (actual result comes from server)
        packet_str = f"seq={seq} ack={ack} len={length} rwnd={rwnd}"
        self.log_message(f"📤 Sending: {packet_str}")
        self.status_label.configure(text="Packet sent, waiting for validation...", style="Status.TLabel")
    
    def send_error(self):
        """Send ERROR packet to host"""
        if self.current_turn != "B":
            self.status_label.configure(text="Not your turn!", style="Error.TLabel")
            return
        
        if not self.client.connected:
            self.status_label.configure(text="Not connected to host!", style="Error.TLabel")
            return
        
        # Send to host
        self.client.send_packet(0, 0, 0, 0, is_error=True)
        
        self.log_message("⚠️ Sending ERROR")
        self.status_label.configure(text="ERROR sent, waiting for validation...", style="Status.TLabel")
    
    def update_display(self):
        """Update all display elements"""
        # Scores
        self.score_a_label.configure(text=f"A: {self.score_a}")
        self.score_b_label.configure(text=f"B: {self.score_b}")
        
        # Turn indicator
        is_my_turn = self.current_turn == "B"
        if is_my_turn:
            self.turn_label.configure(text="✨ YOUR TURN!", foreground="#4ade80")
            if self.client.connected:
                self.send_btn.configure(state=tk.NORMAL)
                self.error_btn.configure(state=tk.NORMAL)
        else:
            self.turn_label.configure(text="Waiting for Player A...", foreground="#888888")
            self.send_btn.configure(state=tk.DISABLED)
            self.error_btn.configure(state=tk.DISABLED)
        
        # RWND displays (B's perspective: my = B, opp = A)
        self.my_rwnd_label.configure(text=f"My RWND: {self.my_rwnd}")
        self.opp_rwnd_label.configure(text=f"Opp RWND: {self.opp_rwnd}")
        self.rwnd_entry.delete(0, tk.END)
        self.rwnd_entry.insert(0, str(self.my_rwnd))
        
        # Update suggested values when it's my turn
        if is_my_turn:
            self.seq_entry.delete(0, tk.END)
            self.seq_entry.insert(0, str(self.my_next_seq))
    
    def start_timer(self):
        """Start the 45-second countdown timer"""
        self.stop_timer()
        self.time_left = 45
        self.update_timer()
    
    def stop_timer(self):
        """Stop the timer"""
        if self.timer_id is not None:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None
    
    def update_timer(self):
        """Update timer display"""
        is_my_turn = self.current_turn == "B"
        
        self.timer_label.configure(text=f"{self.time_left}s")
        
        if is_my_turn:
            if self.time_left <= 10:
                self.timer_label.configure(foreground="#ff4444")
            elif self.time_left <= 20:
                self.timer_label.configure(foreground="#ffd93d")
            else:
                self.timer_label.configure(foreground="#4ade80")
            
            if self.time_left <= 0:
                # Timeout - server handles penalty
                self.log_message("⏰ TIMEOUT!", is_error=True)
                self.start_timer()
                return
            
            self.time_left -= 1
        else:
            self.timer_label.configure(foreground="#888888")
        
        self.timer_id = self.root.after(1000, self.update_timer)
    
    def log_message(self, message: str, is_error: bool = False):
        """Add message to log"""
        self.log_text.configure(state=tk.NORMAL)
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)
    
    def reconnect(self):
        """Reconnect to host"""
        # Disconnect old connection (non-blocking)
        self.client.disconnect()
        
        # Reset UI state
        self.timeline.clear()
        self.last_displayed_packet_count = 0
        self.current_turn = "A"
        self.score_a = 0
        self.score_b = 0
        self.my_rwnd = 50
        self.opp_rwnd = 50
        self.my_next_seq = 0
        
        # Clear log
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state=tk.DISABLED)
        
        # Reset entries
        self.seq_entry.delete(0, tk.END)
        self.seq_entry.insert(0, "0")
        self.ack_entry.delete(0, tk.END)
        self.ack_entry.insert(0, "0")
        self.len_entry.delete(0, tk.END)
        self.len_entry.insert(0, "10")
        self.rwnd_entry.delete(0, tk.END)
        self.rwnd_entry.insert(0, "50")
        
        self.update_display()
        
        # Create a new client instance to avoid socket reuse issues
        self.client = SocketClient()
        self.client.on_connected = self.on_connected
        self.client.on_state_update = self.on_state_update
        self.client.on_disconnected = self.on_disconnected
        self.client.on_error = self.on_network_error
        
        # Connect using async method (non-blocking)
        self.network_label.configure(text=f"🔌 Reconnecting to {self.host}:{self.port}...")
        self.log_message(f"Reconnecting to {self.host}:{self.port}...")
        self.client.connect_async(self.host, self.port)
    
    def on_close(self):
        """Handle window close"""
        self.stop_timer()
        self.client.disconnect()
        self.root.destroy()


def main(host: str = "127.0.0.1", port: int = 5555):
    """Entry point for client window"""
    root = tk.Tk()
    app = ClientWindow(root, host=host, port=port)
    root.mainloop()


if __name__ == "__main__":
    main()
