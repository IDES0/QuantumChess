"""
Demo of Quantum Chess functionality.
Shows how to use Tempo Mode and Quantum Mode operations.
"""

from quantum_chess import QuantumChessGame
import chess


def demo_classical_move():
    """Demonstrate a classical move."""
    print("=== Classical Move Demo ===")
    game = QuantumChessGame()
    print("\nInitial position:")
    game.display()
    
    print("\nMaking classical move e2e4:")
    game.classical_move("e2e4")
    game.display()
    print()


def demo_quantum_split():
    """Demonstrate a quantum move (split)."""
    print("=== Quantum Move (Split) Demo ===")
    game = QuantumChessGame()
    
    # First make a classical move to get knight out (White's turn)
    game.classical_move("g1f3")
    print("\nAfter g1f3 (Black's turn now):")
    game.display()
    
    # Black makes a move to get back to White's turn
    game.classical_move("e7e6")
    print("\nAfter e7e6 (White's turn now):")
    game.display()
    
    # Now split the knight - use legal knight moves from f3
    from_square = chess.parse_square("f3")
    to_square1 = chess.parse_square("d4")  # Knight can move here
    to_square2 = chess.parse_square("g5")  # Knight can also move here
    
    print(f"\nSplitting knight from f3 to d4 and g5:")
    success = game.quantum_move_split(from_square, to_square1, to_square2)
    if success:
        game.display()
        print(f"Branches created: {game.get_branch_count()}")
    else:
        print("Move failed (likely NDO violation or illegal move)")
    print()


def demo_entanglement():
    """Demonstrate an entanglement move."""
    print("=== Entanglement Move Demo ===")
    game = QuantumChessGame()
    
    # Setup: White knight in superposition
    game.classical_move("g1f3")
    from_square = chess.parse_square("f3")
    game.quantum_move_split(from_square, 
                           chess.parse_square("d4"), 
                           chess.parse_square("g5"))
    
    print("\nWhite knight in superposition on d4/g5:")
    game.display()
    
    # Black pawn attacks one of the squares (need to move pawn first)
    game.classical_move("e7e6")  # Black's move
    print("\nAfter e7e6:")
    game.display()
    
    # Now black pawn can attack d4
    print("\nBlack pawn e6 attacks d5 (targeting d4 square):")
    # Note: We need to attack a square where the knight might be
    # For demo, let's use a different setup
    print("(Entanglement requires attacking a square with superposition)")
    print()


def demo_measurement():
    """Demonstrate measurement (quantum mode)."""
    print("=== Measurement Demo ===")
    game = QuantumChessGame()
    
    # Setup: Create superposition
    game.classical_move("g1f3")
    from_square = chess.parse_square("f3")
    game.quantum_move_split(from_square, 
                           chess.parse_square("d4"), 
                           chess.parse_square("e5"))
    
    print("\nBefore measurement:")
    game.display()
    print(f"Probability d4 is occupied: {game.state_manager.get_occupancy_probability(chess.parse_square('d4')):.2f}")
    
    # Measure d4
    square = chess.parse_square("d4")
    success, outcome = game.measure_square(square)
    
    print(f"\nMeasuring d4... Outcome: {outcome}")
    game.display()
    print(f"Branches after measurement: {game.get_branch_count()}")
    print()


def demo_phase_shift():
    """Demonstrate phase shift."""
    print("=== Phase Shift Demo ===")
    game = QuantumChessGame()
    
    # Setup: Create superposition
    game.classical_move("g1f3")
    from_square = chess.parse_square("f3")
    game.quantum_move_split(from_square, 
                           chess.parse_square("d4"), 
                           chess.parse_square("e5"))
    
    print("\nBefore phase shift:")
    game.display()
    
    # Apply phase shift to d4
    square = chess.parse_square("d4")
    game.apply_phase_shift(square, -1)
    
    print("\nAfter phase shift on d4:")
    game.display()
    print("(Phase shift sets up for interference move)")
    print()


def main():
    """Run all demos."""
    print("=" * 50)
    print("QUANTUM CHESS DEMO")
    print("=" * 50)
    print()
    
    demo_classical_move()
    demo_quantum_split()
    demo_entanglement()
    demo_measurement()
    demo_phase_shift()
    
    print("=" * 50)
    print("Demo complete!")
    print("=" * 50)


if __name__ == "__main__":
    main()

