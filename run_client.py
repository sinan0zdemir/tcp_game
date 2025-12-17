#!/usr/bin/env python3
"""
TCP Game - Client Launcher (Player B)
Run this to connect to a host and play as Player B.
"""
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from tcp_game.gui.client_window import main

if __name__ == "__main__":
    host = "127.0.0.1"  # Default to localhost
    port = 5555
    
    if len(sys.argv) > 1:
        host = sys.argv[1]
    if len(sys.argv) > 2:
        try:
            port = int(sys.argv[2])
        except ValueError:
            print(f"Invalid port: {sys.argv[2]}, using default 5555")
    
    print(f"Connecting to TCP Game Host at {host}:{port}...")
    main(host=host, port=port)
