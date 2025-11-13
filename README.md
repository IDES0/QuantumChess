# Quantum Chess

A chess variant implementation built on top of python-chess framework, implementing quantum mechanics in chess with superposition, entanglement, and measurement.

## Setup

Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Chess Game
Run the basic chess game:
```bash
python chess_game.py
```

### Quantum Chess Demo
Run the quantum chess demo to see all features:
```bash
python quantum_chess_demo.py
```

### GUI Application
Launch the graphical user interface:
```bash
python quantum_chess_gui.py
```

The GUI provides:
- Visual chess board with piece rendering
- Click-to-move interface
- Tempo Mode controls (Classical, Quantum Split, Entanglement)
- Quantum Mode controls (Measurement, Phase Shift)
- Real-time quantum state display (branch count, probabilities)
- Move history tracking
- Visual indicators for quantum check and superposition

### Using Quantum Chess in Code

```python
from quantum_chess import QuantumChessGame
import chess

# Create a game
game = QuantumChessGame()

# Tempo Mode: Classical Move
game.classical_move("e2e4")

# Tempo Mode: Quantum Move (Split)
from_sq = chess.parse_square("f3")
to_sq1 = chess.parse_square("d4")
to_sq2 = chess.parse_square("g5")
game.quantum_move_split(from_sq, to_sq1, to_sq2)

# Quantum Mode: Measure a square
square = chess.parse_square("d4")
success, outcome = game.measure_square(square)
print(f"Measurement result: {outcome}")

# Quantum Mode: Phase Shift
game.apply_phase_shift(square, -1)  # Flip phase

# Display game state
game.display()
```

## Architecture

This implementation uses the **GameStateManager** architecture with **NDO Cache optimization**:

### Core Components

1. **QuantumBranch**: Represents a single branch in the quantum state vector
   - Contains a classical chess board and a complex amplitude
   - Each branch is a "ghost reality" in the superposition

2. **GameStateManager**: Manages the sparse state vector
   - Holds all quantum branches (Map<BranchID, QuantumBranch>)
   - Implements NDO Cache for O(1) occupancy checks
   - Tracks which branches occupy which squares

3. **QuantumChessGame**: Main game class
   - Implements Tempo Mode operations (Classical, Quantum Split, Entanglement)
   - Implements Quantum Mode operations (Measurement, Phase Shift)
   - Handles quantum check detection

### Key Features

- **No Double Occupancy (NDO)**: Prevents multiple pieces from having amplitude on the same square
- **Quantum Gridlock**: Entangled pieces block their own squares
- **Measurement Collapse**: Probabilistic collapse of superpositions
- **Phase Shifts**: Enable interference effects
- **Efficient Caching**: NDO Cache makes occupancy checks O(1) instead of O(N)

## Framework

This project uses [python-chess](https://github.com/niklasf/python-chess) as the base framework, which provides:
- Full chess rules implementation
- Move generation and validation
- Board representation
- Extensible architecture for custom rules

## Rules

See `Rules.md` for the complete quantum chess ruleset, including:
- King is always classical (never in superposition)
- Tempo Mode vs Quantum Mode
- Quantum mechanics: superposition, entanglement, interference
- No Double Occupancy constraint
- Quantum check and escape mechanisms

