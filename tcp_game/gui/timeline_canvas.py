"""
Timeline Canvas for TCP Game
Displays packet flow visualization between Player A and Player B
With scrollbar support
"""
import tkinter as tk
from tkinter import Canvas
from typing import List, Dict


class TimelineCanvas(tk.Frame):
    """Canvas showing packet flow between two clients like TCP diagrams - with scrolling"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        # Create canvas with scrollbar
        self.canvas = Canvas(
            self, 
            bg="#1a1a2e", 
            highlightthickness=0,
            width=450,
            height=250
        )
        
        # Scrollbar
        self.scrollbar = tk.Scrollbar(self, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Pack scrollbar and canvas
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Layout constants
        self.left_x = 60  # Player A line
        self.right_x = 390  # Player B line
        self.start_y = 50
        self.packet_spacing = 45
        self.current_y = self.start_y
        
        # Draw initial state
        self.draw_headers()
        self.draw_vertical_lines()
        
        # Initial scroll region
        self.canvas.configure(scrollregion=(0, 0, 450, 300))
        
        # Scrolling support
        self.packet_count = 0
        
        # Bind mousewheel scrolling
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Enter>", lambda e: self.canvas.focus_set())
    
    def _on_mousewheel(self, event):
        """Handle mousewheel scrolling"""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def draw_headers(self):
        """Draw Player A and Player B headers"""
        self.canvas.create_text(
            self.left_x, 20,
            text="A",
            fill="#00d4ff",
            font=("Consolas", 12, "bold")
        )
        self.canvas.create_text(
            self.right_x, 20,
            text="B", 
            fill="#ff6b6b",
            font=("Consolas", 12, "bold")
        )
    
    def draw_vertical_lines(self):
        """Draw timeline vertical lines for both players"""
        self.line_a = self.canvas.create_line(
            self.left_x, 35, self.left_x, 5000,
            fill="#00d4ff", width=2, dash=(4, 2)
        )
        self.line_b = self.canvas.create_line(
            self.right_x, 35, self.right_x, 5000,
            fill="#ff6b6b", width=2, dash=(4, 2)
        )
    
    def add_packet(self, packet_info: Dict):
        """Add a packet arrow to the timeline"""
        sender = packet_info.get("sender", "A")
        is_valid = packet_info.get("valid", True)
        is_error = packet_info.get("type") == "ERROR"
        
        # Determine arrow direction
        if sender == "A":
            x1, x2 = self.left_x, self.right_x
        else:
            x1, x2 = self.right_x, self.left_x
        
        # Arrow color based on validity
        if is_error:
            color = "#ffd93d" if is_valid else "#ff4444"
        else:
            color = "#4ade80" if is_valid else "#ff4444"
        
        # Draw arrow line
        self.canvas.create_line(
            x1, self.current_y, x2, self.current_y + 15,
            fill=color, width=2, arrow=tk.LAST
        )
        
        # Build packet label
        if is_error:
            label = "ERROR"
        else:
            label = f"s={packet_info.get('seq', 0)} a={packet_info.get('ack', 0)} l={packet_info.get('len', 0)} r={packet_info.get('rwnd', 0)}"
        
        # Draw packet label on arrow
        mid_x = (x1 + x2) // 2
        mid_y = self.current_y + 7
        
        self.canvas.create_text(
            mid_x, mid_y - 10,
            text=label,
            fill=color,
            font=("Consolas", 8),
            anchor=tk.CENTER
        )
        
        # Draw validity indicator
        if not is_valid:
            self.canvas.create_text(
                mid_x, mid_y + 12,
                text="✗",
                fill="#ff4444",
                font=("Consolas", 8, "bold")
            )
        
        # Update position for next packet
        self.current_y += self.packet_spacing
        self.packet_count += 1
        
        # Update scroll region
        self.canvas.configure(scrollregion=(0, 0, 450, self.current_y + 50))
        
        # Auto-scroll to bottom
        self.canvas.yview_moveto(1.0)
    
    def clear(self):
        """Clear all packets and reset timeline"""
        self.canvas.delete("all")
        self.current_y = self.start_y
        self.packet_count = 0
        self.draw_headers()
        self.draw_vertical_lines()
        self.canvas.configure(scrollregion=(0, 0, 450, 300))
