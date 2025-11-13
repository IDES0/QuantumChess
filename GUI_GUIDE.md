# Quantum Chess GUI Guide

## Getting Started

Launch the GUI:
```bash
python quantum_chess_gui.py
```

## Interface Overview

The GUI is divided into two main sections:

### Left Panel: Chess Board
- Visual 8x8 chess board with pieces
- Click squares to select and make moves
- Yellow highlight shows selected square
- Blue circles indicate pieces in superposition (with probability)

### Right Panel: Controls and Information

#### Game Status
- **Turn**: Shows current player (White/Black)
- **Branches**: Number of quantum branches in the state
- **Quantum Check**: Warning when king is in quantum check

#### Quantum State
- Shows occupancy probability for selected square
- Updates in real-time as you select different squares

#### Turn Mode Selection
Choose between:
- **Tempo Mode**: Make moves (Classical, Quantum Split, Entanglement)
- **Quantum Mode**: Manipulate quantum state (Measure, Phase Shift)

## How to Play

### Tempo Mode - Making Moves

#### 1. Move (Classical/Entanglement)
1. Select "Move" button
2. Click the piece you want to move
3. Click the destination square
4. Move is executed:
   - If target square is empty or fully occupied: regular classical move
   - If target square has superposition: automatically uses entanglement

**Note:** Entanglement happens automatically when you move to a square with superposition. No separate button needed!

#### 2. Quantum Split
1. Select "Quantum Split" button
2. Click the piece you want to split (yellow highlight)
3. Click the first destination square (blue highlight)
4. Click the second destination square
5. Piece enters superposition between the two squares

**Requirements:**
- Both destination squares must be empty (No Double Occupancy)
- Both moves must be legal for the piece
- You can see your selections highlighted on the board

### Quantum Mode - Manipulating State

#### 1. Measure Square
1. Select "Quantum Mode" radio button
2. Click "Measure Square" button
3. Click any square on the board
4. All superpositions involving that square collapse probabilistically
5. Result (Occupied/Empty) is shown in a popup

#### 2. Apply Phase Shift
1. Select "Quantum Mode" radio button
2. Click "Apply Phase Shift" button
3. Click a square with a piece in superposition
4. Phase of amplitudes on that square is flipped (multiplied by -1)
5. Sets up for interference moves

## Visual Indicators

- **Yellow Highlight**: Selected square
- **Blue Circle**: Piece in superposition (probability shown above)
- **Red Text**: Quantum check warning
- **Move History**: All moves logged in the history panel

## Tips

1. **Quantum Split**: Use to create tactical advantages by threatening multiple squares
2. **Measurement**: Use to collapse opponent's superpositions, but it's probabilistic
3. **Phase Shift**: Prepare for interference moves to force pieces to specific squares
4. **Entanglement**: Can create "quantum gridlock" - be careful as it affects your own pieces too
5. **Branch Count**: Watch the branch count - too many branches can slow down the game

## Keyboard Shortcuts

- Click "Reset Game" to start over
- Move history scrolls automatically
- Click squares to interact (no keyboard needed)

## Troubleshooting

**Move fails?**
- Check if it's your turn
- Verify the move type is correct
- For quantum split: ensure both targets are empty (NDO rule)
- For entanglement: ensure the move is legal

**GUI not responding?**
- Check console for error messages
- Ensure python-chess is installed
- Try restarting the application

## Example Game Flow

1. **White**: Classical move `e2e4`
2. **Black**: Classical move `e7e5`
3. **White**: Quantum split knight from `g1` to `f3` and `h3`
4. **Black**: Measure `f3` (50% chance knight collapses there)
5. **White**: If knight on `f3`, make classical move `f3g5`
6. Continue with quantum tactics!

Enjoy playing Quantum Chess!

