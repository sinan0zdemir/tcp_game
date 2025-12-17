#!/usr/bin/env python3
"""
TCP Game - Host Launcher (Player A)
Run this to host a game and wait for Player B to connect.
"""
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from tcp_game.gui.host_window import main

if __name__ == "__main__":
    port = 5555
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port: {sys.argv[1]}, using default 5555")
    
    print(f"Starting TCP Game Host on port {port}...")
    print("Share your IP address with Player B to connect.")
    main(port=port)
