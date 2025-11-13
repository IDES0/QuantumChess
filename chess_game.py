"""
Basic chess game implementation using python-chess.
This serves as a starting point for implementing Quantum Chess rules.
"""

import chess
import chess.engine


class ChessGame:
    """Basic chess game wrapper around python-chess."""
    
    def __init__(self):
        self.board = chess.Board()
    
    def make_move(self, move_uci: str) -> bool:
        """
        Make a move in UCI format (e.g., 'e2e4').
        Returns True if move is legal, False otherwise.
        """
        try:
            move = chess.Move.from_uci(move_uci)
            if move in self.board.legal_moves:
                self.board.push(move)
                return True
            return False
        except ValueError:
            return False
    
    def get_legal_moves(self) -> list:
        """Get all legal moves in UCI format."""
        return [move.uci() for move in self.board.legal_moves]
    
    def is_game_over(self) -> bool:
        """Check if the game is over."""
        return self.board.is_game_over()
    
    def get_result(self) -> str:
        """Get game result: '1-0', '0-1', '1/2-1/2', or None if ongoing."""
        return self.board.result() if self.is_game_over() else None
    
    def get_fen(self) -> str:
        """Get current board position in FEN notation."""
        return self.board.fen()
    
    def display(self):
        """Display the current board position."""
        print(self.board)
        print(f"\nFEN: {self.get_fen()}")
        print(f"Turn: {'White' if self.board.turn else 'Black'}")
        if self.is_game_over():
            print(f"Game Over: {self.get_result()}")
        else:
            print(f"Legal moves: {len(self.get_legal_moves())}")


def main():
    """Example usage of the chess game."""
    game = ChessGame()
    
    print("=== Chess Game ===")
    print("\nInitial position:")
    game.display()
    
    # Example moves
    print("\n--- Making moves ---")
    moves = ["e2e4", "e7e5", "g1f3", "b8c6"]
    
    for move in moves:
        print(f"\nMove: {move}")
        if game.make_move(move):
            game.display()
        else:
            print("Illegal move!")
            break
        
        if game.is_game_over():
            print(f"\nGame Over! Result: {game.get_result()}")
            break


if __name__ == "__main__":
    main()

