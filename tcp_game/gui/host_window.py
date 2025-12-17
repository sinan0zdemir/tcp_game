"""
Host Window for TCP Game - Player A (Server)
Runs the game server and accepts incoming connection from Player B
"""
import tkinter as tk
from tkinter import ttk, messagebox
import time
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tcp_game.core.game_state import GameState, Player
from tcp_game.gui.timeline_canvas import TimelineCanvas
from tcp_game.networking.server import SocketServer


class HostWindow:
    """Window for Player A (Host) - runs the game server"""
    
    def __init__(self, root: tk.Tk, port: int = 5555):
        self.root = root
        self.root.title("TCP Game - Player A (Host)")
        self.root.geometry("520x650")
        self.root.minsize(450, 500)
        self.root.configure(bg="#0f0f1a")
        
        # Game state (host owns the authoritative state)
        self.game_state = GameState()
        self.game_state.player_a.rwnd = 50
        self.game_state.player_b.rwnd = 50
        
        # Socket server
        self.server = SocketServer(port=port)
        self.server.on_client_connected = self.on_client_connected
        self.server.on_packet_received = self.on_remote_packet
        self.server.on_client_disconnected = self.on_client_disconnected
        self.server.on_error = self.on_network_error
        
        # Timer state
        self.timer_id = None
        self.rwnd_timer_id = None
        self.game_timer_id = None
        self.time_left = 45  # Turn timer (45 seconds)
        self.game_time_left = 300  # Game timer (5 minutes = 300 seconds)
        self.game_over = False
        
        # Build UI
        self.setup_styles()
        self.create_widgets()
        self.update_display()
        
        # Start server
        self.start_server()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def setup_styles(self):
        """Configure ttk styles for dark theme"""
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure("Dark.TFrame", background="#0f0f1a")
        style.configure("Dark.TLabel", background="#0f0f1a", foreground="#e0e0e0", font=("Segoe UI", 11))
        style.configure("Title.TLabel", background="#0f0f1a", foreground="#00d4ff", font=("Segoe UI", 16, "bold"))
        style.configure("Score.TLabel", background="#1a1a2e", foreground="#4ade80", font=("Consolas", 14, "bold"))
        style.configure("Turn.TLabel", background="#1a1a2e", foreground="#ffd93d", font=("Segoe UI", 14, "bold"))
        style.configure("Timer.TLabel", background="#1a1a2e", foreground="#ff6b6b", font=("Consolas", 18, "bold"))
        style.configure("Status.TLabel", background="#0f0f1a", foreground="#4ade80", font=("Consolas", 10))
        style.configure("Error.TLabel", background="#0f0f1a", foreground="#ff4444", font=("Consolas", 10))
        style.configure("RWND.TLabel", background="#1a1a2e", foreground="#a78bfa", font=("Consolas", 12, "bold"))
        style.configure("Network.TLabel", background="#1a1a2e", foreground="#fbbf24", font=("Consolas", 10))
    
    def create_widgets(self):
        """Create all GUI widgets"""
        # Main container - simple pack layout
        main_frame = ttk.Frame(self.root, style="Dark.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        
        # Title
        title_label = ttk.Label(main_frame, text="Player A (Host)", style="Title.TLabel")
        title_label.pack(pady=(0, 3))
        
        # Network status panel
        net_frame = tk.Frame(main_frame, bg="#1a1a2e", relief=tk.RIDGE, bd=1)
        net_frame.pack(fill=tk.X, pady=(0, 3))
        
        self.network_label = ttk.Label(net_frame, text="Starting server...", style="Network.TLabel")
        self.network_label.pack(pady=3, padx=8)
        
        # Info panel
        info_frame = tk.Frame(main_frame, bg="#1a1a2e", relief=tk.RIDGE, bd=1)
        info_frame.pack(fill=tk.X, pady=(0, 3))
        
        # Scores row
        score_row = tk.Frame(info_frame, bg="#1a1a2e")
        score_row.pack(fill=tk.X, padx=8, pady=3)
        
        self.score_a_label = ttk.Label(score_row, text="A: 0", style="Score.TLabel")
        self.score_a_label.pack(side=tk.LEFT, padx=3)
        
        self.score_b_label = ttk.Label(score_row, text="B: 0", style="Score.TLabel")
        self.score_b_label.pack(side=tk.LEFT, padx=3)
        
        # Turn timer (45s countdown)
        self.timer_label = ttk.Label(score_row, text="45s", style="Timer.TLabel")
        self.timer_label.pack(side=tk.RIGHT, padx=3)
        
        # Game timer (5:00 countdown)
        self.game_timer_label = ttk.Label(score_row, text="5:00", style="Dark.TLabel")
        self.game_timer_label.pack(side=tk.RIGHT, padx=8)
        
        # Turn indicator
        self.turn_label = ttk.Label(info_frame, text="Your Turn!", style="Turn.TLabel")
        self.turn_label.pack(pady=3)
        
        # RWND display
        rwnd_frame = tk.Frame(info_frame, bg="#1a1a2e")
        rwnd_frame.pack(fill=tk.X, padx=8, pady=3)
        
        self.my_rwnd_label = ttk.Label(rwnd_frame, text="My RWND: 50", style="RWND.TLabel")
        self.my_rwnd_label.pack(side=tk.LEFT, padx=3)
        
        self.opp_rwnd_label = ttk.Label(rwnd_frame, text="Opp RWND: 50", style="RWND.TLabel")
        self.opp_rwnd_label.pack(side=tk.RIGHT, padx=3)
        
        # Input panel
        input_frame = tk.Frame(main_frame, bg="#1a1a2e", relief=tk.RIDGE, bd=1)
        input_frame.pack(fill=tk.X, pady=3)
        
        ttk.Label(input_frame, text="Send Packet", style="Title.TLabel").pack(pady=3)
        
        # Input fields - use grid for more compact layout
        fields_frame = tk.Frame(input_frame, bg="#1a1a2e")
        fields_frame.pack(padx=10, pady=3)
        
        # Row 1: SEQ and ACK
        row1 = tk.Frame(fields_frame, bg="#1a1a2e")
        row1.pack(fill=tk.X, pady=1)
        
        ttk.Label(row1, text="SEQ:", style="Dark.TLabel", width=5).pack(side=tk.LEFT)
        self.seq_entry = tk.Entry(row1, font=("Consolas", 10), width=8, bg="#2a2a3e", fg="white", insertbackground="white")
        self.seq_entry.pack(side=tk.LEFT, padx=2)
        self.seq_entry.insert(0, "0")
        
        ttk.Label(row1, text="ACK:", style="Dark.TLabel", width=5).pack(side=tk.LEFT, padx=(8, 0))
        self.ack_entry = tk.Entry(row1, font=("Consolas", 10), width=8, bg="#2a2a3e", fg="white", insertbackground="white")
        self.ack_entry.pack(side=tk.LEFT, padx=2)
        self.ack_entry.insert(0, "0")
        
        # Row 2: LEN and RWND
        row2 = tk.Frame(fields_frame, bg="#1a1a2e")
        row2.pack(fill=tk.X, pady=1)
        
        ttk.Label(row2, text="LEN:", style="Dark.TLabel", width=5).pack(side=tk.LEFT)
        self.len_entry = tk.Entry(row2, font=("Consolas", 10), width=8, bg="#2a2a3e", fg="white", insertbackground="white")
        self.len_entry.pack(side=tk.LEFT, padx=2)
        self.len_entry.insert(0, "10")
        
        ttk.Label(row2, text="RWND:", style="Dark.TLabel", width=6).pack(side=tk.LEFT, padx=(8, 0))
        self.rwnd_entry = tk.Entry(row2, font=("Consolas", 10), width=8, bg="#2a2a3e", fg="white", insertbackground="white")
        self.rwnd_entry.pack(side=tk.LEFT, padx=2)
        self.rwnd_entry.insert(0, "50")
        
        # Buttons
        btn_frame = tk.Frame(input_frame, bg="#1a1a2e")
        btn_frame.pack(pady=3)
        
        self.send_btn = tk.Button(
            btn_frame, text="📤 Send", font=("Segoe UI", 10, "bold"),
            bg="#4ade80", fg="#0f0f1a", activebackground="#22c55e",
            command=self.send_packet, width=8, state=tk.DISABLED
        )
        self.send_btn.pack(side=tk.LEFT, padx=3)
        
        self.error_btn = tk.Button(
            btn_frame, text="⚠️ ERROR", font=("Segoe UI", 10, "bold"),
            bg="#ff6b6b", fg="white", activebackground="#ef4444",
            command=self.send_error, width=8, state=tk.DISABLED
        )
        self.error_btn.pack(side=tk.LEFT, padx=3)
        
        # Status
        self.status_label = ttk.Label(input_frame, text="Waiting for Player B to connect...", style="Status.TLabel", wraplength=350)
        self.status_label.pack(pady=3)
        
        # Timeline - larger area for packet visualization
        timeline_frame = tk.Frame(main_frame, bg="#1a1a2e", relief=tk.RIDGE, bd=1)
        timeline_frame.pack(fill=tk.BOTH, expand=True, pady=3)
        
        ttk.Label(timeline_frame, text="Packet Timeline", style="Dark.TLabel").pack(pady=2)
        
        self.timeline = TimelineCanvas(timeline_frame, bg="#1a1a2e", height=180)
        self.timeline.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)
        
        # Packet log
        log_frame = tk.Frame(main_frame, bg="#1a1a2e", relief=tk.RIDGE, bd=1)
        log_frame.pack(fill=tk.X, pady=3)
        
        self.log_text = tk.Text(
            log_frame, height=3, bg="#0f0f1a", fg="#e0e0e0",
            font=("Consolas", 8), state=tk.DISABLED
        )
        self.log_text.pack(fill=tk.X, padx=3, pady=3)
        
        # Reset button
        reset_btn = tk.Button(
            main_frame, text="🔄 Reset Game", font=("Segoe UI", 9),
            bg="#6366f1", fg="white", command=self.reset_game, width=10
        )
        reset_btn.pack(pady=3)
    
    def start_server(self):
        """Start the socket server"""
        if self.server.start():
            ip = self.server.get_local_ip()
            self.network_label.configure(text=f"Listening on {ip}:{self.server.port}")
            self.log_message(f"Server started on {ip}:{self.server.port}")
        else:
            self.network_label.configure(text="Failed to start server")
    
    def send_update(self, message: str, is_valid: bool, reset_timer: bool = True):
        """Send state update to client including game timer info"""
        if self.server.connected:
            self.server.send_state_update(
                self.game_state, message, is_valid, reset_timer,
                game_time_left=self.game_time_left,
                game_over=self.game_over
            )
    
    def on_client_connected(self, addr):
        """Called when client connects"""
        self.root.after(0, lambda: self._handle_client_connected(addr))
    
    def _handle_client_connected(self, addr):
        """Handle client connection on main thread - resets game state"""
        self.network_label.configure(text=f"✅ Player B connected from {addr[0]}")
        self.log_message(f"Player B connected from {addr}")
        
        # Reset game state for new game
        self.game_state.reset()
        self.game_state.player_a.rwnd = 50
        self.game_state.player_b.rwnd = 50
        
        # Clear timeline
        self.timeline.clear()
        
        # Reset input fields
        self.seq_entry.delete(0, tk.END)
        self.seq_entry.insert(0, "0")
        self.ack_entry.delete(0, tk.END)
        self.ack_entry.insert(0, "0")
        self.len_entry.delete(0, tk.END)
        self.len_entry.insert(0, "10")
        self.rwnd_entry.delete(0, tk.END)
        self.rwnd_entry.insert(0, "50")
        
        self.status_label.configure(text="Game started! (State reset)", style="Status.TLabel")
        
        # Enable buttons for Player A's turn
        self.send_btn.configure(state=tk.NORMAL)
        self.error_btn.configure(state=tk.NORMAL)
        
        # Cancel old timers if exists
        if self.rwnd_timer_id:
            self.root.after_cancel(self.rwnd_timer_id)
            self.rwnd_timer_id = None
        if self.game_timer_id:
            self.root.after_cancel(self.game_timer_id)
            self.game_timer_id = None
        
        # Reset game state
        self.game_over = False
        self.game_time_left = 300  # 5 minutes
        
        # Start timers
        self.start_timer()
        self.start_rwnd_timer()
        self.start_game_timer()
        
        # Update display
        self.update_display()
        
        # Send initial state
        self.send_update("Game started!", True)
        self.log_message("Game state reset for new connection")
    
    def on_remote_packet(self, seq: int, ack: int, length: int, rwnd: int, is_error: bool):
        """Called when packet received from Player B"""
        self.root.after(0, lambda: self._handle_remote_packet(seq, ack, length, rwnd, is_error))
    
    def _handle_remote_packet(self, seq: int, ack: int, length: int, rwnd: int, is_error: bool):
        """Handle remote packet on main thread"""
        if self.game_state.current_turn != Player.B:
            self.log_message("⚠️ Received packet but not B's turn", is_error=True)
            return
        
        # Process packet through game state
        is_valid, message, _, _ = self.game_state.process_packet(seq, ack, length, rwnd, is_error=is_error)
        
        # Add to timeline
        if self.game_state.packet_history:
            packet_info = self.game_state.packet_history[-1]
            self.timeline.add_packet(packet_info)
        
        # Update RWND if valid
        if is_valid and not is_error:
            self.game_state.player_a.rwnd = max(0, self.game_state.player_a.rwnd - length)
        
        # Log
        if is_error:
            self.log_message(f"📥 B sent ERROR: {message}")
        else:
            packet_str = f"seq={seq} ack={ack} len={length} rwnd={rwnd}"
            if is_valid:
                self.log_message(f"📥 B: {packet_str}: ✓ VALID")
            else:
                self.log_message(f"📥 B: {packet_str}: ✗ {message}", is_error=True)
        
        # Update display
        self.update_display()
        self.start_timer()
        
        # Send state update to client
        self.send_update(message, is_valid)
    
    def on_client_disconnected(self):
        """Called when client disconnects"""
        self.root.after(0, self._handle_client_disconnected)
    
    def _handle_client_disconnected(self):
        """Handle client disconnect on main thread"""
        self.network_label.configure(text="❌ Player B disconnected")
        self.log_message("Player B disconnected", is_error=True)
        self.send_btn.configure(state=tk.DISABLED)
        self.error_btn.configure(state=tk.DISABLED)
        self.stop_timer()
    
    def on_network_error(self, error: str):
        """Called on network error"""
        self.root.after(0, lambda: self.log_message(f"Network error: {error}", is_error=True))
    
    def send_packet(self):
        """Send a packet (local Player A)"""
        if self.game_state.current_turn != Player.A:
            self.status_label.configure(text="Not your turn!", style="Error.TLabel")
            return
        
        if not self.server.connected:
            self.status_label.configure(text="Player B not connected!", style="Error.TLabel")
            return
        
        try:
            seq = int(self.seq_entry.get())
            ack = int(self.ack_entry.get())
            length = int(self.len_entry.get())
            rwnd = int(self.rwnd_entry.get()) if self.rwnd_entry.get().strip() else self.game_state.player_a.rwnd
        except ValueError:
            self.status_label.configure(text="Invalid input - use integers", style="Error.TLabel")
            return
        
        # Process packet
        is_valid, message, _, _ = self.game_state.process_packet(seq, ack, length, rwnd, is_error=False)
        
        # Add to timeline
        if self.game_state.packet_history:
            packet_info = self.game_state.packet_history[-1]
            self.timeline.add_packet(packet_info)
        
        # Log
        packet_str = f"seq={seq} ack={ack} len={length} rwnd={rwnd}"
        if is_valid:
            self.log_message(f"📤 {packet_str}: ✓ VALID")
            self.status_label.configure(text=message, style="Status.TLabel")
            # Update opponent's rwnd
            self.game_state.player_b.rwnd = max(0, self.game_state.player_b.rwnd - length)
        else:
            self.log_message(f"📤 {packet_str}: ✗ {message}", is_error=True)
            self.status_label.configure(text=message, style="Error.TLabel")
        
        self.update_display()
        self.start_timer()
        self.update_suggested_values()
        
        # Send state update to client
        self.send_update(message, is_valid)
    
    def send_error(self):
        """Send ERROR packet"""
        if self.game_state.current_turn != Player.A:
            self.status_label.configure(text="Not your turn!", style="Error.TLabel")
            return
        
        if not self.server.connected:
            self.status_label.configure(text="Player B not connected!", style="Error.TLabel")
            return
        
        is_valid, message, _, _ = self.game_state.process_packet(0, 0, 0, 0, is_error=True)
        
        # Add to timeline
        if self.game_state.packet_history:
            packet_info = self.game_state.packet_history[-1]
            self.timeline.add_packet(packet_info)
        
        if is_valid:
            self.log_message(f"⚠️ ERROR: {message}")
            self.status_label.configure(text=message, style="Status.TLabel")
        else:
            self.log_message(f"⚠️ ERROR: {message}", is_error=True)
            self.status_label.configure(text=message, style="Error.TLabel")
        
        self.update_display()
        self.start_timer()
        
        # Send state update to client
        self.send_update(message, is_valid)
    
    def update_display(self):
        """Update all display elements"""
        # Scores
        self.score_a_label.configure(text=f"A: {self.game_state.score_a}")
        self.score_b_label.configure(text=f"B: {self.game_state.score_b}")
        
        # Turn indicator
        is_my_turn = self.game_state.current_turn == Player.A
        if is_my_turn:
            self.turn_label.configure(text="YOUR TURN!", foreground="#4ade80")
            if self.server.connected:
                self.send_btn.configure(state=tk.NORMAL)
                self.error_btn.configure(state=tk.NORMAL)
        else:
            self.turn_label.configure(text="Waiting for Player B...", foreground="#888888")
            self.send_btn.configure(state=tk.DISABLED)
            self.error_btn.configure(state=tk.DISABLED)
        
        # RWND displays
        self.my_rwnd_label.configure(text=f"My RWND: {self.game_state.player_a.rwnd}")
        self.opp_rwnd_label.configure(text=f"Opp RWND: {self.game_state.player_b.rwnd}")
        self.rwnd_entry.delete(0, tk.END)
        self.rwnd_entry.insert(0, str(self.game_state.player_a.rwnd))
    
    def update_suggested_values(self):
        """Update entry fields with suggested next values"""
        self.seq_entry.delete(0, tk.END)
        self.seq_entry.insert(0, str(self.game_state.player_a.next_seq))
        
        self.ack_entry.delete(0, tk.END)
        self.ack_entry.insert(0, str(self.game_state.player_a.last_ack_received))
        
        self.len_entry.delete(0, tk.END)
        self.len_entry.insert(0, "10")
    
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
        """Update timer display - counts down for BOTH players"""
        is_my_turn = self.game_state.current_turn == Player.A
        
        self.timer_label.configure(text=f"{self.time_left}s")
        
        # Timer always counts down (host tracks both players' timeouts)
        if self.time_left <= 10:
            self.timer_label.configure(foreground="#ff4444")
        elif self.time_left <= 20:
            self.timer_label.configure(foreground="#ffd93d")
        else:
            if is_my_turn:
                self.timer_label.configure(foreground="#4ade80")
            else:
                self.timer_label.configure(foreground="#888888")
        
        if self.time_left <= 0:
            self.handle_timeout()
            return
        
        self.time_left -= 1
        self.timer_id = self.root.after(1000, self.update_timer)
    
    def handle_timeout(self):
        """Handle 45-second timeout for current player"""
        # Apply penalty to whoever's turn it is
        message = self.game_state.apply_timeout_penalty()
        self.log_message(f"⏰ {message}", is_error=True)
        self.update_display()
        if self.server.connected:
            self.send_update(message, False)
        self.start_timer()
    
    def start_rwnd_timer(self):
        """Start the rwnd increase timer"""
        self.schedule_rwnd_increase()
    
    def schedule_rwnd_increase(self):
        """Schedule the next rwnd increase"""
        self.rwnd_timer_id = self.root.after(15000, self.increase_rwnd)
    
    def increase_rwnd(self):
        """Increase rwnd by 20 every 15 seconds"""
        if self.game_over:
            return
            
        old_a = self.game_state.player_a.rwnd
        old_b = self.game_state.player_b.rwnd
        
        self.game_state.player_a.rwnd = old_a + 20
        self.game_state.player_b.rwnd = old_b + 20
        
        self.update_display()
        self.log_message(f"Both RWND +20 (A:{self.game_state.player_a.rwnd}, B:{self.game_state.player_b.rwnd})")
        
        # Send update to client (don't reset their timer - RWND update is not a packet exchange)
        self.send_update("RWND increased +20", True, reset_timer=False)
        
        self.schedule_rwnd_increase()
    
    def start_game_timer(self):
        """Start the 5-minute game timer"""
        self.update_game_timer()
    
    def update_game_timer(self):
        """Update game timer display every second"""
        if self.game_over:
            return
        
        # Update display (MM:SS format)
        minutes = self.game_time_left // 60
        seconds = self.game_time_left % 60
        self.game_timer_label.configure(text=f"{minutes}:{seconds:02d}")
        
        # Color based on time left
        if self.game_time_left <= 30:
            self.game_timer_label.configure(foreground="#ff4444")
        elif self.game_time_left <= 60:
            self.game_timer_label.configure(foreground="#ffd93d")
        else:
            self.game_timer_label.configure(foreground="#e0e0e0")
        
        if self.game_time_left <= 0:
            self.end_game()
            return
        
        self.game_time_left -= 1
        self.game_timer_id = self.root.after(1000, self.update_game_timer)
    
    def end_game(self):
        """End the game after 5 minutes and determine winner"""
        self.game_over = True
        self.game_state.game_over = True
        
        # Stop all timers
        self.stop_timer()
        if self.rwnd_timer_id:
            self.root.after_cancel(self.rwnd_timer_id)
            self.rwnd_timer_id = None
        
        # Disable buttons
        self.send_btn.configure(state=tk.DISABLED)
        self.error_btn.configure(state=tk.DISABLED)
        
        # Determine winner
        score_a = self.game_state.score_a
        score_b = self.game_state.score_b
        
        if score_a > score_b:
            winner_msg = f"GAME OVER! Player A WINS! (A: {score_a}, B: {score_b})"
            self.turn_label.configure(text="YOU WIN!", foreground="#4ade80")
        elif score_b > score_a:
            winner_msg = f"GAME OVER! Player B WINS! (A: {score_a}, B: {score_b})"
            self.turn_label.configure(text="YOU LOSE!", foreground="#ff4444")
        else:
            winner_msg = f"GAME OVER! IT'S A TIE! (A: {score_a}, B: {score_b})"
            self.turn_label.configure(text="TIE GAME!", foreground="#ffd93d")
        
        self.log_message(f"GAME OVER - Final Score: A={score_a}, B={score_b}")
        self.status_label.configure(text=winner_msg, style="Status.TLabel")
        self.game_timer_label.configure(text="0:00", foreground="#ff4444")
        
        # Notify client
        self.send_update(winner_msg, True)
    
    def log_message(self, message: str, is_error: bool = False):
        """Add message to log"""
        self.log_text.configure(state=tk.NORMAL)
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)
    
    def reset_game(self):
        """Reset the game"""
        if messagebox.askyesno("Reset", "Reset the game?"):
            self.game_state.reset()
            self.game_state.player_a.rwnd = 50
            self.game_state.player_b.rwnd = 50
            
            self.log_text.configure(state=tk.NORMAL)
            self.log_text.delete(1.0, tk.END)
            self.log_text.configure(state=tk.DISABLED)
            
            self.timeline.clear()
            
            self.seq_entry.delete(0, tk.END)
            self.seq_entry.insert(0, "0")
            self.ack_entry.delete(0, tk.END)
            self.ack_entry.insert(0, "0")
            self.len_entry.delete(0, tk.END)
            self.len_entry.insert(0, "10")
            
            self.update_display()
            self.start_timer()
            self.log_message("🔄 Game Reset")
            
            self.send_update("Game Reset", True)
    
    def on_close(self):
        """Handle window close"""
        self.stop_timer()
        if self.rwnd_timer_id:
            self.root.after_cancel(self.rwnd_timer_id)
        self.server.stop()
        self.root.destroy()


def main(port: int = 5555):
    """Entry point for host window"""
    root = tk.Tk()
    app = HostWindow(root, port=port)
    root.mainloop()


if __name__ == "__main__":
    main()
