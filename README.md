# TCP Game

A turn-based TCP protocol simulation game for two players. Players exchange packets (seq, ack, len, rwnd) and score points by following TCP rules correctly or catching opponent's mistakes.

## Features

- **Two-player GUI**: Separate windows for Player A and Player B
- **Packet validation**: Validates seq, ack, len, rwnd following TCP rules
- **Scoring system**:
  - +1 for correctly detecting opponent's error with ERROR packet
  - +1 for sending invalid packet that opponent fails to detect
  - -1 for sending wrong ERROR packet
  - -1 for timeout (45 seconds without response)
- **Visual timeline**: Packet flow diagram showing all exchanges
- **Auto RWND**: Increases by 20 every 15 seconds (simulating buffer processing)

## How to Run

```bash
python run_game.py
```

## Game Rules

1. **Turn-based**: Player A goes first, then turns alternate
2. **Packet format**: seq, ack, len, rwnd (no data payload)
3. **Error detection**: Send ERROR packet if opponent's packet is invalid
4. **Fast retransmit**: Retransmit only after 3 duplicate ACKs
5. **Flow control**: Length cannot exceed opponent's rwnd
6. **Timeout**: 45 seconds to respond or lose 1 point

## Project Structure

```
tcp_game_new/
├── run_game.py           # Entry point
├── tcp_game/
│   ├── core/
│   │   ├── packet.py     # Packet dataclass
│   │   └── game_state.py # Game logic & validation
│   └── gui/
│       ├── main_window.py     # Player windows
│       └── timeline_canvas.py # Packet diagram
└── Project Document tcp.md    # Original requirements
```

## Requirements

- Python 3.x
- Tkinter (included with Python)
