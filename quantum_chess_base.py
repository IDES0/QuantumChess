"""
Base classes for Quantum Chess rule modifications.
Extend these classes to implement custom quantum chess rules.
"""

import chess
from typing import Optional, List


class QuantumChessBoard(chess.Board):
    """
    Extended chess board for quantum chess rules.
    Inherits from python-chess Board and allows rule modifications.
    """
    
    def __init__(self, fen: Optional[str] = None, chess960: bool = False):
        super().__init__(fen, chess960)
        # Add quantum-specific state here
        self.quantum_state = {}
    
    def is_legal(self, move: chess.Move) -> bool:
        """
        Override to add custom move validation.
        Call super() to use standard chess rules, then add quantum rules.
        """
        # Standard chess validation
        if not super().is_legal(move):
            return False
        
        # Add quantum-specific validation here
        return self._validate_quantum_move(move)
    
    def _validate_quantum_move(self, move: chess.Move) -> bool:
        """
        Validate move according to quantum chess rules.
        Override this method to implement quantum-specific rules.
        """
        # Placeholder for quantum move validation
        return True
    
    def push(self, move: chess.Move) -> None:
        """
        Override to add custom move execution logic.
        This is called when a move is made.
        """
        # Add pre-move quantum logic here if needed
        super().push(move)
        # Add post-move quantum logic here if needed
        self._apply_quantum_effects(move)
    
    def _apply_quantum_effects(self, move: chess.Move) -> None:
        """
        Apply quantum effects after a move.
        Override this method to implement quantum mechanics.
        """
        pass
    
    def legal_moves(self) -> chess.LegalMoveGenerator:
        """
        Override to filter or modify legal moves based on quantum rules.
        """
        # Get standard legal moves
        moves = super().legal_moves
        
        # Filter or modify based on quantum rules
        # For now, return standard moves
        return moves


class QuantumChessGame:
    """
    Game wrapper for Quantum Chess.
    Use this as a base for implementing quantum chess variants.
    """
    
    def __init__(self, fen: Optional[str] = None):
        self.board = QuantumChessBoard(fen)
    
    def make_move(self, move_uci: str) -> bool:
        """Make a move in UCI format."""
        try:
            move = chess.Move.from_uci(move_uci)
            if move in self.board.legal_moves:
                self.board.push(move)
                return True
            return False
        except ValueError:
            return False
    
    def get_legal_moves(self) -> List[str]:
        """Get all legal moves in UCI format."""
        return [move.uci() for move in self.board.legal_moves]
    
    def is_game_over(self) -> bool:
        """Check if the game is over."""
        return self.board.is_game_over()
    
    def get_result(self) -> Optional[str]:
        """Get game result."""
        return self.board.result() if self.is_game_over() else None
    
    def display(self):
        """Display the current board position."""
        print(self.board)
        print(f"\nFEN: {self.get_fen()}")
        print(f"Turn: {'White' if self.board.turn else 'Black'}")
    
    def get_fen(self) -> str:
        """Get current board position in FEN notation."""
        return self.board.fen()

