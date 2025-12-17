"""
Protocol for TCP Game network communication
JSON-based message serialization/deserialization
"""
import json
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List

# Message types
MSG_PACKET = "PACKET"
MSG_STATE_UPDATE = "STATE_UPDATE"
MSG_DISCONNECT = "DISCONNECT"
MSG_READY = "READY"


@dataclass
class PacketMessage:
    """Message containing packet data from a player"""
    seq: int
    ack: int
    length: int
    rwnd: int
    is_error: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": MSG_PACKET,
            "seq": self.seq,
            "ack": self.ack,
            "length": self.length,
            "rwnd": self.rwnd,
            "is_error": self.is_error
        }


@dataclass  
class StateUpdate:
    """
    Full game state update sent from host to client.
    Contains everything client needs to update their display.
    """
    current_turn: str  # "A" or "B"
    score_a: int
    score_b: int
    player_a_rwnd: int
    player_b_rwnd: int
    player_a_next_seq: int
    player_b_next_seq: int
    player_a_bytes_sent: int
    player_b_bytes_sent: int
    last_message: str
    last_valid: bool
    packet_history: List[Dict]
    opponent_sent_invalid: bool = False
    reset_timer: bool = True  # Whether client should reset their timer
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": MSG_STATE_UPDATE,
            **asdict(self)
        }


def encode_message(msg: Dict[str, Any]) -> bytes:
    """Encode a message dict to bytes for sending over socket"""
    json_str = json.dumps(msg) + "\n"  # Newline as message delimiter
    return json_str.encode("utf-8")


def decode_message(data: bytes) -> Optional[Dict[str, Any]]:
    """Decode bytes received from socket to message dict"""
    try:
        json_str = data.decode("utf-8").strip()
        if not json_str:
            return None
        return json.loads(json_str)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


def create_packet_message(seq: int, ack: int, length: int, rwnd: int, is_error: bool = False) -> bytes:
    """Create and encode a packet message"""
    msg = PacketMessage(seq, ack, length, rwnd, is_error)
    return encode_message(msg.to_dict())


def create_state_update(game_state, last_message: str, last_valid: bool, reset_timer: bool = True) -> bytes:
    """Create and encode a state update from GameState object"""
    update = StateUpdate(
        current_turn=game_state.current_turn.value,
        score_a=game_state.score_a,
        score_b=game_state.score_b,
        player_a_rwnd=game_state.player_a.rwnd,
        player_b_rwnd=game_state.player_b.rwnd,
        player_a_next_seq=game_state.player_a.next_seq,
        player_b_next_seq=game_state.player_b.next_seq,
        player_a_bytes_sent=game_state.player_a.bytes_sent_total,
        player_b_bytes_sent=game_state.player_b.bytes_sent_total,
        last_message=last_message,
        last_valid=last_valid,
        packet_history=game_state.packet_history,
        opponent_sent_invalid=game_state.opponent_sent_invalid,
        reset_timer=reset_timer
    )
    return encode_message(update.to_dict())


def create_disconnect_message() -> bytes:
    """Create a disconnect notification message"""
    return encode_message({"type": MSG_DISCONNECT})


def create_ready_message() -> bytes:
    """Create a ready notification message"""
    return encode_message({"type": MSG_READY})
