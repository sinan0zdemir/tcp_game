"""
Timeline Canvas for TCP Game
Displays packet flow visualization between Player A and Player B
With scrollbar support and centered layout
"""
import tkinter as tk
from tkinter import Canvas
from typing import List, Dict


class TimelineCanvas(tk.Frame):
    """Canvas showing packet flow between two clients like TCP diagrams - with scrolling"""
    
    def __init__(self, parent, **kwargs):
        # Extract height if provided
        canvas_height = kwargs.pop('height', 250)
        super().__init__(parent, **kwargs)
        
        # Create canvas with scrollbar
        self.canvas = Canvas(
            self, 
            bg="#1a1a2e", 
            highlightthickness=0,
            height=canvas_height
        )
        
        # Scrollbar
        self.scrollbar = tk.Scrollbar(self, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Pack scrollbar and canvas
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Layout constants - will be recalculated on resize
        self.diagram_width = 330  # Width of the diagram (space between A and B lines)
        self.margin = 60  # Minimum margin from edges
        self.start_y = 50
        self.packet_spacing = 45
        self.current_y = self.start_y
        
        # Packet history for redraw
        self.packets: List[Dict] = []
        
        # Scrolling support
        self.packet_count = 0
        
        # Bind mousewheel scrolling
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Enter>", lambda e: self.canvas.focus_set())
        
        # Bind resize to recenter
        self.canvas.bind("<Configure>", self._on_resize)
        
        # Initial draw will happen on first resize
        self._last_width = 0
    
    def _get_centered_positions(self):
        """Calculate centered x positions for A and B lines"""
        canvas_width = self.canvas.winfo_width()
        if canvas_width < 100:
            canvas_width = 450  # Default fallback
        
        # Center the diagram
        center_x = canvas_width // 2
        half_diagram = self.diagram_width // 2
        
        left_x = center_x - half_diagram
        right_x = center_x + half_diagram
        
        return left_x, right_x
    
    def _on_resize(self, event):
        """Handle canvas resize - recenter content"""
        if event.width != self._last_width and event.width > 50:
            self._last_width = event.width
            self._redraw_all()
    
    def _on_mousewheel(self, event):
        """Handle mousewheel scrolling"""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def _redraw_all(self):
        """Redraw everything centered"""
        self.canvas.delete("all")
        self.current_y = self.start_y
        
        self.draw_headers()
        self.draw_vertical_lines()
        
        # Redraw all packets
        for packet_info in self.packets:
            self._draw_packet(packet_info)
        
        # Update scroll region
        self._update_scroll_region()
    
    def draw_headers(self):
        """Draw Player A and Player B headers"""
        left_x, right_x = self._get_centered_positions()
        
        self.canvas.create_text(
            left_x, 20,
            text="A",
            fill="#00d4ff",
            font=("Consolas", 12, "bold")
        )
        self.canvas.create_text(
            right_x, 20,
            text="B", 
            fill="#ff6b6b",
            font=("Consolas", 12, "bold")
        )
    
    def draw_vertical_lines(self):
        """Draw timeline vertical lines for both players"""
        left_x, right_x = self._get_centered_positions()
        
        self.line_a = self.canvas.create_line(
            left_x, 35, left_x, 5000,
            fill="#00d4ff", width=2, dash=(4, 2)
        )
        self.line_b = self.canvas.create_line(
            right_x, 35, right_x, 5000,
            fill="#ff6b6b", width=2, dash=(4, 2)
        )
    
    def add_packet(self, packet_info: Dict):
        """Add a packet arrow to the timeline"""
        # Store packet for redraw
        self.packets.append(packet_info)
        self.packet_count += 1
        
        # Draw the packet
        self._draw_packet(packet_info)
        
        # Update scroll region and auto-scroll
        self._update_scroll_region()
        self.canvas.yview_moveto(1.0)
    
    def _draw_packet(self, packet_info: Dict):
        """Draw a single packet arrow"""
        left_x, right_x = self._get_centered_positions()
        
        sender = packet_info.get("sender", "A")
        is_valid = packet_info.get("valid", True)
        is_error = packet_info.get("type") == "ERROR"
        
        # Determine arrow direction
        if sender == "A":
            x1, x2 = left_x, right_x
        else:
            x1, x2 = right_x, left_x
        
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
    
    def _update_scroll_region(self):
        """Update the scroll region based on content"""
        canvas_width = max(self.canvas.winfo_width(), 450)
        self.canvas.configure(scrollregion=(0, 0, canvas_width, self.current_y + 50))
    
    def clear(self):
        """Clear all packets and reset timeline"""
        self.packets = []
        self.packet_count = 0
        self.current_y = self.start_y
        self._redraw_all()

