#!/usr/bin/env python3
"""
TCP Game - Launch Script
Run this to start the TCP Game GUI
"""
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from tcp_game.gui.main_window import main

if __name__ == "__main__":
    main()
