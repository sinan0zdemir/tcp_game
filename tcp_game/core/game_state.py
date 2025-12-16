"""
Game State management for TCP Game
Handles turn tracking, scoring, and packet validation
Based on test_cases.csv requirements
"""
from dataclasses import dataclass, field
from typing import Optional, Tuple, List
from enum import Enum


class Player(Enum):
    A = "A"
    B = "B"


class ValidationResult(Enum):
    VALID = "VALID"
    ERROR_SEQ = "ERROR_SEQ"
    ERROR_ACK = "ERROR_ACK"
    ERROR_LEN = "ERROR_LEN"
    ERROR_RWND = "ERROR_RWND"
    ERROR_WRONG_ERROR = "ERROR_WRONG_ERROR"
    ERROR_RETRANSMIT_TOO_EARLY = "ERROR_RETRANSMIT_TOO_EARLY"


@dataclass
class PlayerState:
    """State for one player"""
    next_seq: int = 0  # Next sequence number this player should send
    last_seq_sent: int = 0  # Last seq this player sent
    last_len_sent: int = 0  # Last length this player sent
    last_ack_received: int = 0  # Last ACK this player received
    rwnd: int = 50  # This player's advertised receive window
    dup_ack_count: int = 0  # Count of duplicate ACKs received from opponent
    bytes_sent_total: int = 0  # Total bytes sent by this player


@dataclass
class GameState:
    """Main game state tracking both players"""
    current_turn: Player = Player.A
    score_a: int = 0
    score_b: int = 0
    
    # Player states
    player_a: PlayerState = field(default_factory=PlayerState)
    player_b: PlayerState = field(default_factory=PlayerState)
    
    # Track last packets for validation
    last_packet_from_a: Optional[dict] = None
    last_packet_from_b: Optional[dict] = None
    
    # Track if last opponent packet was invalid (for ERROR validation)
    opponent_sent_invalid: bool = False
    last_validation_error: Optional[str] = None
    who_sent_invalid: Optional[Player] = None  # Track who sent the invalid packet
    
    # History of all packets for timeline
    packet_history: List[dict] = field(default_factory=list)
    
    # Track what each player has received (for ACK validation)
    a_received_bytes: int = 0  # Total bytes A has received from B
    b_received_bytes: int = 0  # Total bytes B has received from A
    
    # Track last ACK sent by each player for duplicate detection
    last_ack_from_a: int = 0
    last_ack_from_b: int = 0
    
    # Game status
    game_over: bool = False
    
    def reset(self):
        """Reset game to initial state"""
        self.current_turn = Player.A
        self.score_a = 0
        self.score_b = 0
        self.player_a = PlayerState()
        self.player_b = PlayerState()
        self.last_packet_from_a = None
        self.last_packet_from_b = None
        self.opponent_sent_invalid = False
        self.last_validation_error = None
        self.who_sent_invalid = None
        self.packet_history = []
        self.a_received_bytes = 0
        self.b_received_bytes = 0
        self.last_ack_from_a = 0
        self.last_ack_from_b = 0
        self.game_over = False
    
    def get_current_player_state(self) -> PlayerState:
        """Get current player's state"""
        return self.player_a if self.current_turn == Player.A else self.player_b
    
    def get_opponent_player_state(self) -> PlayerState:
        """Get opponent's state"""
        return self.player_b if self.current_turn == Player.A else self.player_a
    
    def switch_turn(self):
        """Switch to other player's turn"""
        self.current_turn = Player.B if self.current_turn == Player.A else Player.A
    
    def validate_packet(self, seq: int, ack: int, length: int, rwnd: int) -> Tuple[bool, str]:
        """
        Validate an incoming packet from current player.
        Returns (is_valid, error_message)
        
        Validation rules based on test_cases.csv:
        - rwnd must be >= 0 (TC6 catches -5)
        - length must not exceed opponent's rwnd
        - seq must be expected OR valid retransmit after 3 dup ACKs
        - ack must be valid (not acking data not yet received)
        """
        current = self.get_current_player_state()
        opponent = self.get_opponent_player_state()
        
        # Rule 1: rwnd must be non-negative (TC6)
        if rwnd < 0:
            return False, f"INVALID RWND: {rwnd} is negative"
        
        # Rule 2: length must be non-negative
        if length < 0:
            return False, f"INVALID LENGTH: {length} is negative"
        
        # Rule 3: length must not exceed opponent's rwnd (flow control)
        if length > opponent.rwnd:
            return False, f"LENGTH {length} EXCEEDS OPPONENT RWND {opponent.rwnd}"
        
        # Rule 4: Check for valid retransmit or normal sequence
        expected_seq = current.next_seq
        
        if seq != expected_seq:
            # Could be a retransmit
            if seq < expected_seq:
                # Retransmit is only allowed after 3 duplicate ACKs (TC3, TC5)
                if current.dup_ack_count < 3:
                    return False, f"RETRANSMIT BEFORE 3 DUP ACKS: seq={seq}, expected={expected_seq}, dup_acks={current.dup_ack_count}"
                # Valid retransmit after 3 dup ACKs - allowed
            else:
                # seq jumped ahead - invalid
                return False, f"INVALID SEQ: expected {expected_seq}, got {seq}"
        
        # Rule 5: ACK validation - can't ack more than what was sent
        # A can only ACK bytes that B has sent, and vice versa
        if self.current_turn == Player.A:
            # A is sending - A's ack should not exceed what B has sent
            max_valid_ack = self.player_b.bytes_sent_total
        else:
            # B is sending - B's ack should not exceed what A has sent
            max_valid_ack = self.player_a.bytes_sent_total
        
        if ack > max_valid_ack:
            return False, f"INVALID ACK: {ack} exceeds max valid {max_valid_ack}"
        
        return True, "PACKET IS VALID"
    
    def validate_error_packet(self) -> Tuple[bool, str]:
        """
        Validate if sending ERROR packet is correct.
        ERROR is only valid if opponent's last packet was actually invalid.
        Returns (is_valid, reason)
        """
        if self.opponent_sent_invalid:
            return True, f"CORRECT ERROR: {self.last_validation_error}"
        return False, "WRONG ERROR: Opponent's packet was valid"
    
    def process_packet(self, seq: int, ack: int, length: int, rwnd: int, is_error: bool = False) -> Tuple[bool, str, int, int]:
        """
        Process a packet from current player.
        Returns (is_valid, message, score_a, score_b)
        """
        sender = self.current_turn
        
        # Handle ERROR packet
        if is_error:
            is_valid, message = self.validate_error_packet()
            if is_valid:
                # Correct error detection - sender (who detected) gets +1
                if sender == Player.A:
                    self.score_a += 1
                    message = f"Player A correctly detected error (+1)"
                else:
                    self.score_b += 1
                    message = f"Player B correctly detected error (+1)"
            else:
                # Wrong error - sender gets -1
                if sender == Player.A:
                    self.score_a -= 1
                    message = f"Player A sent wrong ERROR (-1)"
                else:
                    self.score_b -= 1
                    message = f"Player B sent wrong ERROR (-1)"
            
            # Record in history
            self.packet_history.append({
                "sender": sender.value,
                "type": "ERROR",
                "valid": is_valid
            })
            
            self.opponent_sent_invalid = False
            # Don't switch turn after ERROR - sender continues
            return is_valid, message, self.score_a, self.score_b
        
        # Regular packet validation
        is_valid, error_msg = self.validate_packet(seq, ack, length, rwnd)
        
        # Record packet info
        packet_info = {
            "sender": sender.value,
            "seq": seq,
            "ack": ack,
            "len": length,
            "rwnd": rwnd,
            "valid": is_valid
        }
        self.packet_history.append(packet_info)
        
        # Update last packet tracking
        if sender == Player.A:
            self.last_packet_from_a = packet_info
        else:
            self.last_packet_from_b = packet_info
        
        current = self.get_current_player_state()
        opponent = self.get_opponent_player_state()
        
        if is_valid:
            # Check if opponent sent an invalid packet that we didn't catch with ERROR
            # If so, the opponent (who sent invalid) gets +1 for undetected error
            if self.opponent_sent_invalid and self.who_sent_invalid:
                if self.who_sent_invalid == Player.A:
                    self.score_a += 1
                    message = "PACKET IS VALID (WARNING: A's previous error went undetected, A +1)"
                else:
                    self.score_b += 1
                    message = "PACKET IS VALID (WARNING: B's previous error went undetected, B +1)"
                self.opponent_sent_invalid = False
                self.who_sent_invalid = None
            else:
                message = "PACKET IS VALID"
            
            # Update sender's state
            current.last_seq_sent = seq
            current.last_len_sent = length
            current.next_seq = seq + length
            current.last_ack_received = ack
            current.rwnd = rwnd
            
            # Track total bytes sent for ACK validation
            if seq + length > current.bytes_sent_total:
                current.bytes_sent_total = seq + length
            
            # Track duplicate ACKs for fast retransmit (TC3, TC5)
            # Count when opponent sends the same ACK multiple times
            if sender == Player.A:
                if ack == self.last_ack_from_a and length == 0:
                    # This is A receiving duplicate ACK pattern - but A is sending
                    pass
                self.last_ack_from_a = ack
            else:
                # B is sending ack - check if it's duplicate of B's previous ack
                if ack == self.last_ack_from_b:
                    # B sent same ack again - this is a duplicate ACK for A
                    self.player_a.dup_ack_count += 1
                else:
                    self.player_a.dup_ack_count = 0
                self.last_ack_from_b = ack
            
            # Also track when A sends duplicate acks
            if sender == Player.A:
                if ack == self.last_ack_from_a:
                    self.player_b.dup_ack_count += 1
                else:
                    self.player_b.dup_ack_count = 0
            
            # Check if rwnd is 0 - don't switch turn, sender must send rwnd update
            if rwnd == 0:
                message = "PACKET IS VALID (rwnd=0, waiting for update)"
                # Don't switch turn - same player must send rwnd > 0 next
                return is_valid, message, self.score_a, self.score_b
        else:
            # Invalid packet - set flag so opponent can send ERROR
            self.opponent_sent_invalid = True
            self.who_sent_invalid = sender  # Remember who sent the invalid packet
            self.last_validation_error = error_msg
            message = f"PACKET ERROR: {error_msg}"
        
        self.switch_turn()
        return is_valid, message, self.score_a, self.score_b
    
    def apply_timeout_penalty(self) -> str:
        """Apply -1 penalty to current player for timeout"""
        if self.current_turn == Player.A:
            self.score_a -= 1
            return "TIMEOUT: Player A -1"
        else:
            self.score_b -= 1
            return "TIMEOUT: Player B -1"
    
    def check_zero_rwnd_timeout(self) -> Optional[str]:
        """Check if zero rwnd situation requires timeout penalty"""
        # Get the player whose rwnd is zero
        if self.player_a.rwnd == 0 or self.player_b.rwnd == 0:
            # The player who advertised zero rwnd loses if timeout occurs
            if self.player_b.rwnd == 0:
                self.score_b -= 1
                return "TIMEOUT: Player B advertised rwnd=0 and didn't update (-1)"
            else:
                self.score_a -= 1
                return "TIMEOUT: Player A advertised rwnd=0 and didn't update (-1)"
        return None


# Helper for testing
def test_validator():
    """Test the validator with some scenarios"""
    state = GameState()
    
    # TC1: Normal valid exchange
    # A sends: seq=0, ack=0, len=10, rwnd=50
    is_valid, msg, _, _ = state.process_packet(0, 0, 10, 50)
    print(f"TC1 A->B: {msg}")
    assert is_valid, f"TC1 A packet should be valid: {msg}"
    
    # B responds: seq=0, ack=10, len=10, rwnd=40
    is_valid, msg, _, _ = state.process_packet(0, 10, 10, 40)
    print(f"TC1 B->A: {msg}")
    assert is_valid, f"TC1 B packet should be valid: {msg}"
    
    # Test ACK validation
    state2 = GameState()
    # A sends: seq=0, ack=0, len=10, rwnd=50
    is_valid, msg, _, _ = state2.process_packet(0, 0, 10, 50)
    print(f"ACK Test A->B: {msg}")
    
    # B sends invalid ack=20 (should be max 10)
    is_valid, msg, _, _ = state2.process_packet(0, 20, 10, 40)
    print(f"ACK Test B->A (ack=20, should be invalid): valid={is_valid}, {msg}")
    assert not is_valid, f"B's ack=20 should be invalid, A only sent 10 bytes"
    
    print("Validator OK.")


if __name__ == "__main__":
    test_validator()
