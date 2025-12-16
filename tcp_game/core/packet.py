"""
Packet model for TCP Game
Contains only seq, ack, len, rwnd fields (no data payload)
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Packet:
    """Represents a TCP-like packet with seq, ack, len, rwnd"""
    seq: int
    ack: int
    length: int
    rwnd: int
    is_error: bool = False
    
    def __str__(self):
        if self.is_error:
            return "ERROR"
        return f"seq={self.seq}, ack={self.ack}, len={self.length}, rwnd={self.rwnd}"
    
    def to_dict(self):
        """Convert to dictionary for display"""
        if self.is_error:
            return {"type": "ERROR"}
        return {
            "seq": self.seq,
            "ack": self.ack,
            "len": self.length,
            "rwnd": self.rwnd
        }


def create_error_packet() -> Packet:
    """Create an ERROR packet (no seq, ack, len, rwnd)"""
    return Packet(seq=0, ack=0, length=0, rwnd=0, is_error=True)


def create_packet(seq: int, ack: int, length: int, rwnd: int) -> Packet:
    """Create a regular packet with given parameters"""
    return Packet(seq=seq, ack=ack, length=length, rwnd=rwnd, is_error=False)
