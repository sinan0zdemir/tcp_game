"""
Main Window for TCP Game GUI - Dual Window Version
Two separate windows for Player A and Player B
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


class SharedState:
    """Shared game state between both player windows"""
    def __init__(self):
        self.game_state = GameState()
        self.window_a = None
        self.window_b = None
        self.updating = False  # Prevent recursion


class PlayerWindow:
    """Window for one player"""
    
    def __init__(self, player: Player, shared: SharedState, root_or_toplevel):
        self.player = player
        self.shared = shared
        self.game_state = shared.game_state
        
        # Create window
        if player == Player.A:
            self.root = root_or_toplevel
            self.root.title("TCP Game - Player A")
        else:
            self.root = tk.Toplevel(root_or_toplevel)
            self.root.title("TCP Game - Player B")
        
        self.root.geometry("500x750")
        self.root.configure(bg="#0f0f1a")
        
        # Position windows side by side
        if player == Player.A:
            self.root.geometry("+50+50")
        else:
            self.root.geometry("+560+50")
        
        # Timer state
        self.timer_id = None
        self.rwnd_timer_id = None
        self.time_left = 45
        
        # Build UI
        self.setup_styles()
        self.create_widgets()
        self.update_display_local()
        
        # Start rwnd increase timer (every 15 seconds)
        self.start_rwnd_timer()
    
    def setup_styles(self):
        """Configure ttk styles for dark theme"""
        style = ttk.Style()
        style.theme_use('clam')
        
        player_color = "#00d4ff" if self.player == Player.A else "#ff6b6b"
        
        style.configure("Dark.TFrame", background="#0f0f1a")
        style.configure("Dark.TLabel", background="#0f0f1a", foreground="#e0e0e0", font=("Segoe UI", 11))
        style.configure("Title.TLabel", background="#0f0f1a", foreground=player_color, font=("Segoe UI", 16, "bold"))
        style.configure("Score.TLabel", background="#1a1a2e", foreground="#4ade80", font=("Consolas", 14, "bold"))
        style.configure("Turn.TLabel", background="#1a1a2e", foreground="#ffd93d", font=("Segoe UI", 14, "bold"))
        style.configure("Timer.TLabel", background="#1a1a2e", foreground="#ff6b6b", font=("Consolas", 18, "bold"))
        style.configure("Status.TLabel", background="#0f0f1a", foreground="#4ade80", font=("Consolas", 10))
        style.configure("Error.TLabel", background="#0f0f1a", foreground="#ff4444", font=("Consolas", 10))
        style.configure("RWND.TLabel", background="#1a1a2e", foreground="#a78bfa", font=("Consolas", 12, "bold"))
    
    def create_widgets(self):
        """Create all GUI widgets"""
        player_color = "#00d4ff" if self.player == Player.A else "#ff6b6b"
        
        # Main container
        main_frame = ttk.Frame(self.root, style="Dark.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_frame, text=f"Player {self.player.value}", style="Title.TLabel")
        title_label.pack(pady=(0, 5))
        
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
        self.turn_label = ttk.Label(info_frame, text="Your Turn!", style="Turn.TLabel")
        self.turn_label.pack(pady=5)
        
        # RWND display (not editable)
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
        
        # RWND (editable, auto-filled with calculated value)
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
            btn_frame,
            text="📤 Send",
            font=("Segoe UI", 11, "bold"),
            bg="#4ade80",
            fg="#0f0f1a",
            activebackground="#22c55e",
            command=self.send_packet,
            width=10,
            height=1
        )
        self.send_btn.pack(side=tk.LEFT, padx=5)
        
        self.error_btn = tk.Button(
            btn_frame,
            text="⚠️ ERROR",
            font=("Segoe UI", 11, "bold"),
            bg="#ff6b6b",
            fg="white",
            activebackground="#ef4444",
            command=self.send_error,
            width=10,
            height=1
        )
        self.error_btn.pack(side=tk.LEFT, padx=5)
        
        # Status
        self.status_label = ttk.Label(input_frame, text="Waiting...", style="Status.TLabel", wraplength=380)
        self.status_label.pack(pady=5)
        
        # Timeline diagram
        timeline_frame = tk.Frame(main_frame, bg="#1a1a2e", relief=tk.RIDGE, bd=2)
        timeline_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        ttk.Label(timeline_frame, text="Packet Timeline", style="Dark.TLabel").pack(pady=3)
        
        self.timeline = TimelineCanvas(timeline_frame, bg="#1a1a2e")
        self.timeline.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Packet log
        log_frame = tk.Frame(main_frame, bg="#1a1a2e", relief=tk.RIDGE, bd=2)
        log_frame.pack(fill=tk.X, pady=5)
        
        self.log_text = tk.Text(
            log_frame,
            height=4,
            bg="#0f0f1a",
            fg="#e0e0e0",
            font=("Consolas", 9),
            state=tk.DISABLED
        )
        self.log_text.pack(fill=tk.X, padx=5, pady=5)
        
        # Reset button
        reset_btn = tk.Button(
            main_frame,
            text="🔄 Reset Game",
            font=("Segoe UI", 10),
            bg="#6366f1",
            fg="white",
            command=self.reset_game,
            width=12
        )
        reset_btn.pack(pady=5)
    
    def get_my_state(self):
        """Get this player's state"""
        return self.game_state.player_a if self.player == Player.A else self.game_state.player_b
    
    def get_opponent_state(self):
        """Get opponent's state"""
        return self.game_state.player_b if self.player == Player.A else self.game_state.player_a
    
    def update_display_local(self):
        """Update only this window's display (no recursion)"""
        # Scores
        self.score_a_label.configure(text=f"A: {self.game_state.score_a}")
        self.score_b_label.configure(text=f"B: {self.game_state.score_b}")
        
        # Turn indicator
        is_my_turn = self.game_state.current_turn == self.player
        if is_my_turn:
            self.turn_label.configure(text="✨ YOUR TURN!", foreground="#4ade80")
            self.send_btn.configure(state=tk.NORMAL)
            self.error_btn.configure(state=tk.NORMAL)
        else:
            self.turn_label.configure(text="Waiting for opponent...", foreground="#888888")
            self.send_btn.configure(state=tk.DISABLED)
            self.error_btn.configure(state=tk.DISABLED)
        
        # RWND displays
        my_state = self.get_my_state()
        opp_state = self.get_opponent_state()
        self.my_rwnd_label.configure(text=f"My RWND: {my_state.rwnd}")
        self.opp_rwnd_label.configure(text=f"Opp RWND: {opp_state.rwnd}")
        # Update rwnd entry with auto-calculated value
        self.rwnd_entry.delete(0, tk.END)
        self.rwnd_entry.insert(0, str(my_state.rwnd))
    
    def update_all_displays(self):
        """Update both windows (prevents recursion)"""
        if self.shared.updating:
            return
        self.shared.updating = True
        
        try:
            self.update_display_local()
        except Exception:
            pass
        
        # Update other window safely
        other = self.shared.window_b if self.player == Player.A else self.shared.window_a
        if other:
            try:
                other.update_display_local()
            except Exception:
                pass
        
        self.shared.updating = False
    
    def start_timer(self):
        """Start the 45-second countdown timer only if it's my turn"""
        if self.timer_id is not None:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None
        
        self.time_left = 45
        self.update_timer()
    
    def stop_timer(self):
        """Stop the timer"""
        if self.timer_id is not None:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None
    
    def update_timer(self):
        """Update timer display - only counts down if it's my turn"""
        is_my_turn = self.game_state.current_turn == self.player
        
        self.timer_label.configure(text=f"{self.time_left}s")
        
        if is_my_turn:
            if self.time_left <= 10:
                self.timer_label.configure(foreground="#ff4444")
            elif self.time_left <= 20:
                self.timer_label.configure(foreground="#ffd93d")
            else:
                self.timer_label.configure(foreground="#4ade80")
            
            if self.time_left <= 0:
                self.handle_timeout()
                return
            
            self.time_left -= 1
        else:
            self.timer_label.configure(foreground="#888888")
        
        self.timer_id = self.root.after(1000, self.update_timer)
    
    def start_rwnd_timer(self):
        """Start the rwnd increase timer (every 15 seconds, +20)"""
        # Only Player A starts the timer to avoid duplicates
        if self.player == Player.A:
            self.schedule_rwnd_increase()
    
    def schedule_rwnd_increase(self):
        """Schedule the next rwnd increase"""
        self.rwnd_timer_id = self.root.after(15000, self.increase_rwnd)
    
    def increase_rwnd(self):
        """Increase rwnd by 20 every 15 seconds for BOTH players"""
        try:
            # Increase for both players
            old_a = self.game_state.player_a.rwnd
            old_b = self.game_state.player_b.rwnd
            
            #RWND INCREASE 
            self.game_state.player_a.rwnd =  old_a + 20
            self.game_state.player_b.rwnd =  old_b + 20
            
            # Update displays
            self.update_all_displays()
            
            if self.game_state.player_a.rwnd != old_a:
                self.log_message(f"📈 Both RWND +20 (A:{self.game_state.player_a.rwnd}, B:{self.game_state.player_b.rwnd})")
                if self.shared.window_b:
                    try:
                        self.shared.window_b.log_message(f"📈 Both RWND +20 (A:{self.game_state.player_a.rwnd}, B:{self.game_state.player_b.rwnd})")
                    except Exception:
                        pass
        except Exception:
            pass
        
        # Schedule next increase
        self.schedule_rwnd_increase()
    
    def handle_timeout(self):
        """Handle 45-second timeout"""
        if self.game_state.current_turn == self.player:
            message = self.game_state.apply_timeout_penalty()
            self.log_message(f"⏰ {message}", is_error=True)
            self.update_all_displays()
        self.start_timer()
    
    def send_packet(self):
        """Send a packet"""
        if self.game_state.current_turn != self.player:
            self.status_label.configure(text="Not your turn!", style="Error.TLabel")
            return
        
        try:
            seq = int(self.seq_entry.get())
            ack = int(self.ack_entry.get())
            length = int(self.len_entry.get())
            # Use entered rwnd if valid, otherwise use auto-calculated
            rwnd_str = self.rwnd_entry.get().strip()
            if rwnd_str:
                rwnd = int(rwnd_str)
            else:
                rwnd = self.get_my_state().rwnd
        except ValueError:
            self.status_label.configure(text="Invalid input - use integers", style="Error.TLabel")
            return
        
        # Process packet
        is_valid, message, _, _ = self.game_state.process_packet(seq, ack, length, rwnd, is_error=False)
        
        # Add to timeline for both windows
        packet_info = self.game_state.packet_history[-1]
        self.timeline.add_packet(packet_info)
        other = self.shared.window_b if self.player == Player.A else self.shared.window_a
        if other:
            other.timeline.add_packet(packet_info)
        
        # Log
        packet_str = f"seq={seq} ack={ack} len={length} rwnd={rwnd}"
        if is_valid:
            self.log_message(f"📤 {packet_str}: ✓ VALID")
            self.status_label.configure(text=message, style="Status.TLabel")
        else:
            self.log_message(f"📤 {packet_str}: ✗ {message}", is_error=True)
            self.status_label.configure(text=message, style="Error.TLabel")
        
        # Update rwnd - decrease by length received
        if is_valid:
            opp_state = self.get_opponent_state()
            opp_state.rwnd = max(0, opp_state.rwnd - length)
        
        self.update_all_displays()
        self.start_timer()
        self.update_suggested_values()
        
        # Start timer for other player too
        if other:
            other.start_timer()
    
    def send_error(self):
        """Send ERROR packet"""
        if self.game_state.current_turn != self.player:
            self.status_label.configure(text="Not your turn!", style="Error.TLabel")
            return
        
        is_valid, message, _, _ = self.game_state.process_packet(0, 0, 0, 0, is_error=True)
        
        # Add to timeline for both windows
        packet_info = self.game_state.packet_history[-1]
        self.timeline.add_packet(packet_info)
        other = self.shared.window_b if self.player == Player.A else self.shared.window_a
        if other:
            other.timeline.add_packet(packet_info)
        
        if is_valid:
            self.log_message(f"⚠️ ERROR: {message}")
            self.status_label.configure(text=message, style="Status.TLabel")
        else:
            self.log_message(f"⚠️ ERROR: {message}", is_error=True)
            self.status_label.configure(text=message, style="Error.TLabel")
        
        self.update_all_displays()
        self.start_timer()
        
        if other:
            other.start_timer()
    
    def update_suggested_values(self):
        """Update entry fields with suggested next values"""
        my_state = self.get_my_state()
        
        self.seq_entry.delete(0, tk.END)
        self.seq_entry.insert(0, str(my_state.next_seq))
        
        self.ack_entry.delete(0, tk.END)
        self.ack_entry.insert(0, str(my_state.last_ack_received))
        
        self.len_entry.delete(0, tk.END)
        self.len_entry.insert(0, "10")
    
    def log_message(self, message: str, is_error: bool = False):
        """Add message to log"""
        self.log_text.configure(state=tk.NORMAL)
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)
    
    def reset_game(self):
        """Reset the game for both players"""
        if messagebox.askyesno("Reset", "Reset the game for BOTH players?"):
            self.do_reset()
            
            other = self.shared.window_b if self.player == Player.A else self.shared.window_a
            if other:
                other.do_reset()
    
    def do_reset(self):
        """Actually perform the reset"""
        self.game_state.reset()
        
        # Reset rwnd to 50
        self.game_state.player_a.rwnd = 50
        self.game_state.player_b.rwnd = 50
        
        # Clear log
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state=tk.DISABLED)
        
        # Clear timeline
        self.timeline.clear()
        
        # Reset entries
        self.seq_entry.delete(0, tk.END)
        self.seq_entry.insert(0, "0")
        self.ack_entry.delete(0, tk.END)
        self.ack_entry.insert(0, "0")
        self.len_entry.delete(0, tk.END)
        self.len_entry.insert(0, "10")
        
        self.update_display_local()
        self.start_timer()
        self.log_message("🔄 Game Reset")


def main():
    """Entry point - creates both player windows"""
    root = tk.Tk()
    
    # Create shared state
    shared = SharedState()
    
    # Initialize rwnd to 50
    shared.game_state.player_a.rwnd = 50
    shared.game_state.player_b.rwnd = 50
    
    # Create Player A window (main window)
    window_a = PlayerWindow(Player.A, shared, root)
    shared.window_a = window_a
    
    # Create Player B window (toplevel)
    window_b = PlayerWindow(Player.B, shared, root)
    shared.window_b = window_b
    
    # Start timer for player A (who goes first)
    window_a.start_timer()
    window_b.start_timer()
    
    root.mainloop()


if __name__ == "__main__":
    main()
