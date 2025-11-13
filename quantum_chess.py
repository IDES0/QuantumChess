"""
Quantum Chess Implementation
Based on the architecture with GameStateManager and NDO Cache optimization.
"""

import chess
import math
import random
import uuid
from typing import Dict, Set, List, Optional, Tuple
from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class QuantumBranch:
    """Represents a single branch in the quantum state vector."""
    branch_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    amplitude: complex = 1.0  # Complex amplitude (real part for now, can extend to complex)
    board: chess.Board = field(default_factory=chess.Board)
    
    def copy(self) -> 'QuantumBranch':
        """Create a deep copy of this branch."""
        new_branch = QuantumBranch(
            branch_id=str(uuid.uuid4()),
            amplitude=self.amplitude,
            board=self.board.copy()
        )
        return new_branch
    
    def get_probability(self) -> float:
        """Get the probability of this branch (|amplitude|^2)."""
        if isinstance(self.amplitude, complex):
            return abs(self.amplitude) ** 2
        return abs(self.amplitude) ** 2


class GameStateManager:
    """
    Manages the quantum game state with multiple branches.
    Implements the NDO Cache optimization for fast occupancy checks.
    """
    
    def __init__(self, fen: Optional[str] = None):
        # Sparse state vector: Map of branch IDs to quantum branches
        self.branches: Dict[str, QuantumBranch] = {}
        
        # NDO Cache: Maps square to set of branch IDs that have amplitude on that square
        self.occupancy_cache: Dict[chess.Square, Set[str]] = defaultdict(set)
        
        # Reverse lookup: Maps branch ID to set of squares it occupies (for cache cleanup)
        self.branch_occupancy: Dict[str, Set[chess.Square]] = defaultdict(set)
        
        # Initialize with a single classical branch
        initial_branch = QuantumBranch()
        if fen:
            initial_branch.board = chess.Board(fen)
        self.branches[initial_branch.branch_id] = initial_branch
        self._update_cache_for_branch(initial_branch.branch_id)
    
    def _update_cache_for_branch(self, branch_id: str) -> None:
        """Update the NDO cache for a specific branch."""
        if branch_id not in self.branches:
            return
        
        branch = self.branches[branch_id]
        board = branch.board
        
        # Clear old cache entries for this branch
        if branch_id in self.branch_occupancy:
            for square in self.branch_occupancy[branch_id]:
                self.occupancy_cache[square].discard(branch_id)
        
        # Update cache with current board state
        # Only cache squares with non-zero amplitude
        occupied_squares = set()
        if abs(branch.amplitude) > 1e-10:  # Only cache if amplitude is non-zero
            for square in chess.SQUARES:
                piece = board.piece_at(square)
                if piece is not None:
                    occupied_squares.add(square)
                    self.occupancy_cache[square].add(branch_id)
        
        self.branch_occupancy[branch_id] = occupied_squares
    
    def no_double_occupancy_check(self, square: chess.Square) -> bool:
        """
        O(1) check if a square has any amplitude (No Double Occupancy rule).
        Returns True if square is safe (no amplitude), False if occupied.
        """
        if square not in self.occupancy_cache:
            return True
        
        occupied_branches = self.occupancy_cache[square]
        # Check if any branch has non-zero amplitude on this square
        for branch_id in occupied_branches:
            if branch_id in self.branches:
                branch = self.branches[branch_id]
                if abs(branch.amplitude) > 1e-10:  # Non-zero amplitude
                    return False
        
        return True
    
    def no_double_occupancy_check_for_capture(self, square: chess.Square, capturing_piece_color: bool) -> bool:
        """
        NDO check that allows captures of opponent pieces.
        Returns True if square is safe for quantum split (no own pieces or superpositions).
        Allows captures of classical opponent pieces.
        """
        # First check if square has any superposition (probability between 0 and 1)
        prob = self.get_occupancy_probability(square)
        
        # If there's superposition (0 < prob < 1), it's an NDO violation
        if 0 < prob < 1:
            return False
        
        # If prob == 1.0, there's a classical piece - check if it's opponent's (capture allowed)
        # If prob == 0.0, square is empty - allowed
        if prob == 0.0:
            return True
        
        # prob == 1.0, check piece color
        if square in self.occupancy_cache:
            for branch_id in self.occupancy_cache[square]:
                if branch_id in self.branches:
                    branch = self.branches[branch_id]
                    piece = branch.board.piece_at(square)
                    if piece is not None:
                        # If it's the same color, it's an NDO violation
                        if piece.color == capturing_piece_color:
                            return False
                        # If it's opponent's piece, capture is allowed
                        return True
        
        return True
    
    def get_occupancy_amplitude(self, square: chess.Square) -> complex:
        """Get the total amplitude on a square (sum across all branches)."""
        total_amplitude = 0.0
        if square in self.occupancy_cache:
            for branch_id in self.occupancy_cache[square]:
                if branch_id in self.branches:
                    branch = self.branches[branch_id]
                    total_amplitude += branch.amplitude
        return total_amplitude
    
    def get_occupancy_probability(self, square: chess.Square) -> float:
        """Get the probability that a square is occupied."""
        total_prob = 0.0
        if square in self.occupancy_cache:
            for branch_id in self.occupancy_cache[square]:
                if branch_id in self.branches:
                    branch = self.branches[branch_id]
                    total_prob += branch.get_probability()
        return total_prob
    
    def _clean_cache_for_branches(self, deleted_branch_ids: Set[str]) -> None:
        """Remove cache entries for deleted branches (garbage collection)."""
        for branch_id in deleted_branch_ids:
            if branch_id in self.branch_occupancy:
                for square in self.branch_occupancy[branch_id]:
                    self.occupancy_cache[square].discard(branch_id)
                del self.branch_occupancy[branch_id]
    
    def _normalize_amplitudes(self) -> None:
        """Renormalize amplitudes so total probability is 1."""
        total_prob = sum(branch.get_probability() for branch in self.branches.values())
        if total_prob > 1e-10:
            normalization_factor = 1.0 / math.sqrt(total_prob)
            for branch in self.branches.values():
                branch.amplitude *= normalization_factor


class QuantumChessGame:
    """
    Main game class implementing Quantum Chess rules.
    """
    
    def __init__(self, fen: Optional[str] = None):
        self.state_manager = GameStateManager(fen)
        self.turn_count = 0
    
    def get_current_turn(self) -> bool:
        """Get current turn (True = White, False = Black)."""
        # All branches should have the same turn, so check first branch
        if self.state_manager.branches:
            first_branch = next(iter(self.state_manager.branches.values()))
            return first_branch.board.turn
        return True  # Default to White (starting player)
    
    # ==================== TEMPO MODE OPERATIONS ====================
    
    def classical_move(self, move_uci: str) -> bool:
        """
        Execute a classical move on all branches.
        Automatically uses entanglement if target square has superposition.
        No branching occurs - all branches make the same move.
        """
        try:
            move = chess.Move.from_uci(move_uci)
        except ValueError:
            return False
        
        to_square = move.to_square
        
        # Check if target square has superposition (non-zero probability but not 1.0)
        target_prob = self.state_manager.get_occupancy_probability(to_square)
        
        # If target has superposition (0 < prob < 1), use entanglement
        if 0 < target_prob < 1:
            return self.entanglement_move(move_uci, to_square)
        
        # Otherwise, make a regular classical move
        # Validate move on at least one branch
        valid = False
        for branch in self.state_manager.branches.values():
            if move in branch.board.legal_moves:
                valid = True
                break
        
        if not valid:
            return False
        
        # Apply move to all branches
        for branch in self.state_manager.branches.values():
            if move in branch.board.legal_moves:
                branch.board.push(move)
        
        # Update cache for all branches
        for branch_id in list(self.state_manager.branches.keys()):
            self.state_manager._update_cache_for_branch(branch_id)
        
        return True
    
    def quantum_move_split(self, from_square: chess.Square, to_square1: chess.Square, 
                          to_square2: chess.Square) -> bool:
        """
        Quantum Move (Split): Move a piece into superposition of two squares.
        Creates new branches with amplitudes divided by sqrt(2).
        Allows captures of opponent pieces.
        """
        # Check that it's the right player's turn and piece belongs to them
        current_turn = self.get_current_turn()
        first_branch = next(iter(self.state_manager.branches.values()))
        piece = first_branch.board.piece_at(from_square)
        if piece is None or piece.color != (chess.WHITE if current_turn else chess.BLACK):
            return False
        
        piece_color = piece.color
        
        # Validate: both target squares must pass NDO check (allows captures)
        # Check if squares are safe for quantum split - can capture opponent pieces
        # but can't have own pieces or superpositions
        if not self.state_manager.no_double_occupancy_check_for_capture(to_square1, piece_color):
            return False
        if not self.state_manager.no_double_occupancy_check_for_capture(to_square2, piece_color):
            return False
        
        new_branches: Dict[str, QuantumBranch] = {}
        has_valid_split = False
        
        for old_branch in self.state_manager.branches.values():
            board = old_branch.board
            piece = board.piece_at(from_square)
            
            # Create moves
            move1 = chess.Move(from_square, to_square1)
            move2 = chess.Move(from_square, to_square2)
            
            # Check if piece exists and belongs to current player
            if (piece is not None and 
                piece.color == (chess.WHITE if board.turn else chess.BLACK)):
                
                # For quantum split, check if both moves are valid
                # They can be pseudo-legal moves OR valid captures (for quantum split)
                move1_valid = move1 in board.pseudo_legal_moves
                move2_valid = move2 in board.pseudo_legal_moves
                
                # If not pseudo-legal, check if they're valid captures for quantum split
                if not move1_valid:
                    target1_piece = board.piece_at(to_square1)
                    # Valid if target has opponent piece and move is a valid capture pattern
                    move1_valid = (target1_piece is not None and 
                                  target1_piece.color != piece.color and
                                  self._is_valid_capture_pattern(board, from_square, to_square1, piece))
                
                if not move2_valid:
                    target2_piece = board.piece_at(to_square2)
                    # Valid if target has opponent piece and move is a valid capture pattern
                    move2_valid = (target2_piece is not None and 
                                  target2_piece.color != piece.color and
                                  self._is_valid_capture_pattern(board, from_square, to_square2, piece))
                
                if move1_valid and move2_valid:
                    # Verify moves don't leave king in check (make a test board)
                    test_board1 = board.copy()
                    test_board2 = board.copy()
                    test_board1.push(move1)
                    test_board2.push(move2)
                    
                    # Check if moves are actually legal (don't leave in check)
                    if not test_board1.was_into_check() and not test_board2.was_into_check():
                        # Piece exists and both moves are legal - create split
                        has_valid_split = True
                        new_amplitude = old_branch.amplitude / math.sqrt(2)
                        
                        # Branch A: move to square1
                        branch_a = old_branch.copy()
                        branch_a.amplitude = new_amplitude
                        branch_a.board.push(move1)
                        new_branches[branch_a.branch_id] = branch_a
                        
                        # Branch B: move to square2
                        branch_b = old_branch.copy()
                        branch_b.amplitude = new_amplitude
                        branch_b.board.push(move2)
                        new_branches[branch_b.branch_id] = branch_b
                    else:
                        # Moves leave in check - keep branch unchanged
                        new_branches[old_branch.branch_id] = old_branch
                else:
                    # Moves not valid - keep branch unchanged
                    new_branches[old_branch.branch_id] = old_branch
            else:
                # Piece doesn't exist or moves aren't legal - keep branch unchanged
                new_branches[old_branch.branch_id] = old_branch
        
        if not has_valid_split:
            return False
        
        # Replace old branches with new branches
        old_branch_ids = set(self.state_manager.branches.keys())
        self.state_manager.branches = new_branches
        
        # Clean cache for old branches that were split
        deleted_ids = old_branch_ids - set(new_branches.keys())
        if deleted_ids:
            self.state_manager._clean_cache_for_branches(deleted_ids)
        
        # Update cache for all branches
        for branch_id in new_branches.keys():
            self.state_manager._update_cache_for_branch(branch_id)
        
        return True
    
    def entanglement_move(self, move_uci: str, target_square: chess.Square) -> bool:
        """
        Entanglement Move (CNOT): Attack a square with superposition.
        Creates entangled state where move succeeds/fails based on target occupancy.
        """
        try:
            move = chess.Move.from_uci(move_uci)
        except ValueError:
            return False
        
        from_square = move.from_square
        to_square = move.to_square
        
        # Validate: move must be a classical move (not quantum split)
        if from_square == to_square:
            return False
        
        new_branches: Dict[str, QuantumBranch] = {}
        
        for old_branch in self.state_manager.branches.values():
            board = old_branch.board
            
            # Check if move is legal in this branch
            if move not in board.legal_moves:
                continue
            
            # Check if target square is occupied in this branch
            target_piece = board.piece_at(target_square)
            
            if target_piece is not None:
                # Target is occupied: move fails (piece stays on from_square)
                new_branch = old_branch.copy()
                # Don't push the move - it fails
                new_branches[new_branch.branch_id] = new_branch
            else:
                # Target is empty: move succeeds
                new_branch = old_branch.copy()
                new_branch.board.push(move)
                new_branches[new_branch.branch_id] = new_branch
        
        if not new_branches:
            return False
        
        # Replace old branches
        old_branch_ids = set(self.state_manager.branches.keys())
        self.state_manager.branches = new_branches
        
        # Clean and update cache
        self.state_manager._clean_cache_for_branches(old_branch_ids)
        for branch_id in new_branches.keys():
            self.state_manager._update_cache_for_branch(branch_id)
        
        return True
    
    # ==================== QUANTUM MODE OPERATIONS ====================
    
    def apply_phase_shift(self, square: chess.Square, phase_multiplier: complex = -1) -> bool:
        """
        Apply a phase shift to amplitudes on a specific square.
        Typically used to flip phase (multiply by -1) for interference.
        """
        if square not in self.state_manager.occupancy_cache:
            return False
        
        # Apply phase shift to all branches with amplitude on this square
        for branch_id in self.state_manager.occupancy_cache[square]:
            if branch_id in self.state_manager.branches:
                branch = self.state_manager.branches[branch_id]
                branch.amplitude *= phase_multiplier
        
        return True
    
    def measure_square(self, square: chess.Square) -> Tuple[bool, str]:
        """
        Measure a square, collapsing all superpositions involving it.
        Returns (success, outcome) where outcome is "Occupied" or "Empty".
        """
        # Calculate probability of occupation
        prob_occupied = self.state_manager.get_occupancy_probability(square)
        
        # Roll the dice
        outcome_occupied = random.random() < prob_occupied
        outcome = "Occupied" if outcome_occupied else "Empty"
        
        # Filter branches based on outcome
        new_branches: Dict[str, QuantumBranch] = {}
        deleted_branch_ids: Set[str] = set()
        
        for branch_id, branch in self.state_manager.branches.items():
            board = branch.board
            piece = board.piece_at(square)
            
            is_occupied = (piece is not None)
            
            if (outcome_occupied and is_occupied) or (not outcome_occupied and not is_occupied):
                # Branch matches outcome - keep it
                new_branches[branch_id] = branch
            else:
                # Branch doesn't match - delete it
                deleted_branch_ids.add(branch_id)
        
        if not new_branches:
            # All branches deleted - this shouldn't happen, but handle it
            return False, outcome
        
        # Replace branches
        self.state_manager.branches = new_branches
        
        # Clean cache for deleted branches
        self.state_manager._clean_cache_for_branches(deleted_branch_ids)
        
        # Renormalize amplitudes
        self.state_manager._normalize_amplitudes()
        
        # Update cache for remaining branches
        for branch_id in new_branches.keys():
            self.state_manager._update_cache_for_branch(branch_id)
        
        return True, outcome
    
    def _is_valid_capture_pattern(self, board: chess.Board, from_square: chess.Square, 
                                   to_square: chess.Square, piece: chess.Piece) -> bool:
        """
        Check if a move is a valid capture pattern for the piece type.
        Used for quantum split validation when both targets have opponent pieces.
        """
        from_rank, from_file = chess.square_rank(from_square), chess.square_file(from_square)
        to_rank, to_file = chess.square_rank(to_square), chess.square_file(to_square)
        
        rank_diff = abs(to_rank - from_rank)
        file_diff = abs(to_file - from_file)
        
        if piece.piece_type == chess.PAWN:
            # Pawn: must be diagonal capture (1 rank forward, 1 file diagonal)
            direction = 1 if piece.color == chess.WHITE else -1
            return (to_rank == from_rank + direction and file_diff == 1)
        elif piece.piece_type == chess.KNIGHT:
            # Knight: L-shape
            return (rank_diff == 2 and file_diff == 1) or (rank_diff == 1 and file_diff == 2)
        elif piece.piece_type == chess.BISHOP:
            # Bishop: diagonal
            return rank_diff == file_diff and rank_diff > 0
        elif piece.piece_type == chess.ROOK:
            # Rook: horizontal or vertical
            return (rank_diff == 0 and file_diff > 0) or (file_diff == 0 and rank_diff > 0)
        elif piece.piece_type == chess.QUEEN:
            # Queen: diagonal, horizontal, or vertical
            return ((rank_diff == file_diff and rank_diff > 0) or
                   (rank_diff == 0 and file_diff > 0) or
                   (file_diff == 0 and rank_diff > 0))
        elif piece.piece_type == chess.KING:
            # King: one square in any direction
            return rank_diff <= 1 and file_diff <= 1 and (rank_diff + file_diff > 0)
        
        return False
    
    # ==================== UTILITY METHODS ====================
    
    def is_quantum_check(self) -> bool:
        """Check if the current player's king is in quantum check."""
        current_turn = self.get_current_turn()
        king_color = chess.WHITE if current_turn else chess.BLACK
        opponent_color = chess.BLACK if current_turn else chess.WHITE
        
        # Find king square (should be same in all branches since king is classical)
        if not self.state_manager.branches:
            return False
        
        first_branch = next(iter(self.state_manager.branches.values()))
        king_square = first_branch.board.king(king_color)
        
        if king_square is None:
            return False
        
        # Check if any opponent piece has amplitude on king square
        # We need to check branches where an opponent piece (not the king) is on king_square
        if king_square in self.state_manager.occupancy_cache:
            for branch_id in self.state_manager.occupancy_cache[king_square]:
                if branch_id in self.state_manager.branches:
                    branch = self.state_manager.branches[branch_id]
                    piece = branch.board.piece_at(king_square)
                    # Check if it's an opponent piece (not the king itself)
                    if piece is not None and piece.color == opponent_color:
                        if abs(branch.amplitude) > 1e-10:
                            return True
        
        return False
    
    def get_branch_count(self) -> int:
        """Get the number of active branches."""
        return len(self.state_manager.branches)
    
    def get_expected_board(self) -> chess.Board:
        """
        Get the 'expected' board state (most probable branch).
        For display purposes.
        """
        if not self.state_manager.branches:
            return chess.Board()
        
        # Return the branch with highest probability
        max_prob = -1
        best_branch = None
        
        for branch in self.state_manager.branches.values():
            prob = branch.get_probability()
            if prob > max_prob:
                max_prob = prob
                best_branch = branch
        
        return best_branch.board.copy() if best_branch else chess.Board()
    
    def display(self):
        """Display the current game state."""
        expected_board = self.get_expected_board()
        print(expected_board)
        print(f"\nBranches: {self.get_branch_count()}")
        print(f"Turn: {'White' if self.get_current_turn() else 'Black'}")
        
        if self.is_quantum_check():
            print("⚠️  QUANTUM CHECK!")
    
    def get_fen(self) -> str:
        """Get FEN of the expected board."""
        return self.get_expected_board().fen()

