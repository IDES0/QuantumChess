"""
Quantum Chess GUI
A graphical interface for playing Quantum Chess.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import chess
import math
from quantum_chess import QuantumChessGame


class ChessBoardGUI:
    """Main GUI class for Quantum Chess."""
    
    SQUARE_SIZE = 60
    BOARD_SIZE = 8 * SQUARE_SIZE
    
    # Piece Unicode symbols
    # Note: Uppercase = White, Lowercase = Black in python-chess
    # Unicode symbols: ♔♕♖♗♘♙ (uppercase) appear lighter/white
    #                  ♚♛♜♝♞♟ (lowercase) appear darker/black
    # If colors appear reversed, we swap the symbols
    PIECES = {
        'K': '♚', 'Q': '♛', 'R': '♜', 'B': '♝', 'N': '♞', 'P': '♟',  # White pieces use dark symbols
        'k': '♔', 'q': '♕', 'r': '♖', 'b': '♗', 'n': '♘', 'p': '♙'   # Black pieces use light symbols
    }
    
    def __init__(self, root):
        self.root = root
        self.root.title("Quantum Chess")
        self.root.geometry("1000x800")
        
        self.game = QuantumChessGame()
        self.selected_square = None
        self.quantum_mode = False
        self.move_type = "classical"  # classical, quantum_split
        self._quantum_target1 = None  # For quantum split: first target square
        self._view_mode = False  # For view mode
        
        # Create UI
        self.create_widgets()
        self.update_display()
    
    def create_widgets(self):
        """Create all GUI widgets."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=0)  # Board row - fixed
        main_frame.rowconfigure(1, weight=0)  # Quantum state row - fixed
        
        # Top section: Board and Controls side by side
        top_section = ttk.Frame(main_frame)
        top_section.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        top_section.columnconfigure(0, weight=0)  # Board - fixed width
        top_section.columnconfigure(1, weight=1)  # Controls - can expand
        
        # Left panel: Board (fixed position)
        board_frame = ttk.Frame(top_section)
        board_frame.grid(row=0, column=0, padx=10, pady=10, sticky=(tk.N))
        
        # Create canvas for chess board
        self.canvas = tk.Canvas(
            board_frame,
            width=self.BOARD_SIZE,
            height=self.BOARD_SIZE,
            borderwidth=0,
            highlightthickness=0
        )
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.on_square_click)
        
        # Right panel: Controls and Info
        control_frame = ttk.Frame(top_section)
        control_frame.grid(row=0, column=1, padx=10, pady=10, sticky=(tk.N, tk.W))
        
        # Game status
        status_frame = ttk.LabelFrame(control_frame, text="Game Status", padding="10")
        status_frame.pack(fill=tk.X, pady=5)
        
        self.turn_label = ttk.Label(status_frame, text="Turn: White", font=("Arial", 12, "bold"))
        self.turn_label.pack()
        
        self.branch_label = ttk.Label(status_frame, text="Branches: 1", font=("Arial", 10))
        self.branch_label.pack()
        
        self.check_label = ttk.Label(status_frame, text="", font=("Arial", 10), foreground="red")
        self.check_label.pack()
        
        # Mode selection
        mode_frame = ttk.LabelFrame(control_frame, text="Mode", padding="10")
        mode_frame.pack(fill=tk.X, pady=5)
        
        self.mode_var = tk.StringVar(value="view")
        ttk.Radiobutton(mode_frame, text="View Mode (Inspect)", variable=self.mode_var,
                       value="view", command=self.on_mode_change).pack(anchor=tk.W)
        ttk.Radiobutton(mode_frame, text="Tempo Mode (Move)", variable=self.mode_var,
                       value="tempo", command=self.on_mode_change).pack(anchor=tk.W)
        ttk.Radiobutton(mode_frame, text="Quantum Mode (Manipulate)", variable=self.mode_var,
                       value="quantum", command=self.on_mode_change).pack(anchor=tk.W)
        
        # Tempo Mode controls
        self.tempo_frame = ttk.LabelFrame(control_frame, text="Tempo Mode Actions", padding="10")
        self.tempo_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(self.tempo_frame, text="Move", 
                  command=lambda: self.set_move_type("classical")).pack(fill=tk.X, pady=2)
        ttk.Button(self.tempo_frame, text="Quantum Split", 
                  command=lambda: self.set_move_type("quantum_split")).pack(fill=tk.X, pady=2)
        
        self.move_type_label = ttk.Label(self.tempo_frame, text="Selected: Move", 
                                        font=("Arial", 9, "italic"))
        self.move_type_label.pack(pady=5)
        
        # Quantum Mode controls
        self.quantum_frame = ttk.LabelFrame(control_frame, text="Quantum Mode Actions", padding="10")
        self.quantum_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(self.quantum_frame, text="Measure Square", 
                  command=self.start_measurement).pack(fill=tk.X, pady=2)
        ttk.Button(self.quantum_frame, text="Apply Phase Shift", 
                  command=self.start_phase_shift).pack(fill=tk.X, pady=2)
        
        # Selected square info
        self.selected_label = ttk.Label(control_frame, text="Click a square to select", 
                                      font=("Arial", 9))
        self.selected_label.pack(pady=10)
        
        # Reset button
        ttk.Button(control_frame, text="Reset Game", command=self.reset_game).pack(pady=10)
        
        # Bottom section: Quantum State and Move History side by side
        bottom_section = ttk.Frame(main_frame)
        bottom_section.grid(row=1, column=0, padx=10, pady=10, sticky=(tk.W, tk.E, tk.S))
        main_frame.columnconfigure(0, weight=1)
        bottom_section.columnconfigure(0, weight=1)
        bottom_section.columnconfigure(1, weight=1)
        
        # Quantum state info - left half of bottom
        quantum_frame = ttk.LabelFrame(bottom_section, text="Quantum State", padding="10")
        quantum_frame.grid(row=0, column=0, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
        bottom_section.rowconfigure(0, weight=1)
        
        quantum_text_frame = ttk.Frame(quantum_frame)
        quantum_text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.prob_label = tk.Text(quantum_text_frame, height=6, wrap=tk.WORD, font=("Courier", 9))
        quantum_scrollbar = ttk.Scrollbar(quantum_text_frame, orient=tk.VERTICAL, command=self.prob_label.yview)
        self.prob_label.configure(yscrollcommand=quantum_scrollbar.set)
        self.prob_label.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        quantum_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Move history - right half of bottom
        history_frame = ttk.LabelFrame(bottom_section, text="Move History", padding="10")
        history_frame.grid(row=0, column=1, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.history_text = tk.Text(history_frame, height=6, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, command=self.history_text.yview)
        self.history_text.configure(yscrollcommand=scrollbar.set)
        self.history_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def draw_board(self):
        """Draw the chess board."""
        self.canvas.delete("all")
        
        # Draw squares
        for row in range(8):
            for col in range(8):
                x1 = col * self.SQUARE_SIZE
                y1 = row * self.SQUARE_SIZE
                x2 = x1 + self.SQUARE_SIZE
                y2 = y1 + self.SQUARE_SIZE
                
                # Alternate colors
                color = "#f0d9b5" if (row + col) % 2 == 0 else "#b58863"
                
                # Highlight selected squares
                sq = chess.square(col, 7 - row)
                if self.selected_square is not None and sq == self.selected_square:
                    color = "#ffeb3b"  # Yellow highlight for selected piece
                elif hasattr(self, '_quantum_target1') and self._quantum_target1 is not None and sq == self._quantum_target1:
                    color = "#90caf9"  # Light blue for first quantum target
                
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="black")
        
        # Draw pieces - show all pieces with amplitude on each square
        # Collect pieces from all branches
        square_pieces = {}  # square -> list of (piece, probability)
        
        for branch in self.game.state_manager.branches.values():
            if abs(branch.amplitude) < 1e-10:  # Skip zero-amplitude branches
                continue
            
            prob = branch.get_probability()
            board = branch.board
            
            for square in chess.SQUARES:
                piece = board.piece_at(square)
                if piece:
                    if square not in square_pieces:
                        square_pieces[square] = []
                    # Check if this piece type/color already exists for this square
                    found = False
                    for existing_piece, existing_prob in square_pieces[square]:
                        if existing_piece.symbol() == piece.symbol():
                            # Same piece, add probability
                            square_pieces[square].remove((existing_piece, existing_prob))
                            square_pieces[square].append((piece, existing_prob + prob))
                            found = True
                            break
                    if not found:
                        square_pieces[square].append((piece, prob))
        
        # Draw pieces on all squares where they have amplitude
        for square, pieces_list in square_pieces.items():
            row, col = chess.square_rank(square), chess.square_file(square)
            x = col * self.SQUARE_SIZE + self.SQUARE_SIZE // 2
            y = (7 - row) * self.SQUARE_SIZE + self.SQUARE_SIZE // 2
            
            # If multiple pieces on same square, offset them slightly
            num_pieces = len(pieces_list)
            offset_step = 8 if num_pieces > 1 else 0
            
            for idx, (piece, prob) in enumerate(pieces_list):
                piece_symbol = self.PIECES.get(piece.symbol(), '?')
                
                # Calculate offset for multiple pieces
                offset_x = (idx - (num_pieces - 1) / 2) * offset_step if num_pieces > 1 else 0
                offset_y = 0
                
                # Only show probability indicators for pieces in superposition (prob < 1.0)
                # Use tolerance to handle floating point precision
                if prob < 0.999:  # Classical pieces have prob = 1.0 (within tolerance)
                    # Piece in superposition - use lighter/grayed colors
                    if piece.color == chess.WHITE:
                        text_color = "#666666"  # Gray for white pieces in superposition
                    else:
                        text_color = "#999999"  # Light gray for black pieces in superposition
                    
                    # Draw piece
                    self.canvas.create_text(x + offset_x, y + offset_y, text=piece_symbol, 
                                           font=("Arial", 32), fill=text_color, tags="piece")
                    
                    # Determine if it's current player's piece or opponent's
                    current_turn = self.game.get_current_turn()
                    is_own_piece = (piece.color == chess.WHITE) == current_turn
                    
                    # Color code: green for own pieces, red for enemy pieces
                    circle_color = "#90EE90" if is_own_piece else "#FFB6C1"  # Light green or light pink
                    outline_color = "green" if is_own_piece else "red"
                    text_color_indicator = "darkgreen" if is_own_piece else "darkred"
                    
                    # Draw smaller probability indicator (4px radius instead of 8px)
                    self.canvas.create_oval(x + offset_x - 4, y + offset_y - 4, 
                                           x + offset_x + 4, y + offset_y + 4, 
                                           fill=circle_color, outline=outline_color, width=1)
                    self.canvas.create_text(x + offset_x, y + offset_y - 15, text=f"{prob:.2f}", 
                                           font=("Arial", 7, "bold"), fill=text_color_indicator)
                else:
                    # Classical piece (prob = 1.0) - draw normally with full color, NO indicator
                    # Determine square color for proper contrast
                    row, col = chess.square_rank(square), chess.square_file(square)
                    is_light_square = (row + col) % 2 == 0
                    
                    # White pieces: use dark color on light squares, light color on dark squares
                    # Black pieces: use light color on light squares, dark color on dark squares
                    # But actually, Unicode chess symbols may have their own appearance
                    # So we use colors that provide good contrast
                    if piece.color == chess.WHITE:
                        # White pieces: dark color for visibility
                        text_color = "#000000"  # Black text for white pieces
                    else:
                        # Black pieces: light color for visibility  
                        text_color = "#FFFFFF"  # White text for black pieces
                    
                    self.canvas.create_text(x + offset_x, y + offset_y, text=piece_symbol, 
                                           font=("Arial", 32), fill=text_color, tags="piece")
        
        # Draw file and rank labels
        for i in range(8):
            # Files (a-h) at bottom
            file_label = chr(97 + i)
            x = i * self.SQUARE_SIZE + self.SQUARE_SIZE // 2
            self.canvas.create_text(x, self.BOARD_SIZE + 15, text=file_label, 
                                   font=("Arial", 10, "bold"))
            # Ranks (1-8) on left
            rank_label = str(8 - i)
            y = i * self.SQUARE_SIZE + self.SQUARE_SIZE // 2
            self.canvas.create_text(15, y, text=rank_label, font=("Arial", 10, "bold"))
    
    def on_square_click(self, event):
        """Handle square click events."""
        col = event.x // self.SQUARE_SIZE
        row = event.y // self.SQUARE_SIZE
        
        if 0 <= col < 8 and 0 <= row < 8:
            square = chess.square(col, 7 - row)
            square_name = chess.square_name(square)
            
            if self.mode_var.get() == "view":
                # View mode: just show probabilities
                self.view_square(square)
            elif self.mode_var.get() == "quantum":
                # Quantum mode: measure or phase shift
                if hasattr(self, '_measuring'):
                    self.measure_square(square)
                elif hasattr(self, '_phase_shifting'):
                    self.apply_phase_shift_to_square(square)
            else:
                # Tempo mode: make moves
                if self.move_type == "quantum_split":
                    # Quantum split: need piece + two targets
                    if self.selected_square is None:
                        # First click: select piece to split
                        self.selected_square = square
                        self._quantum_target1 = None
                        self.selected_label.config(text=f"Quantum Split: Selected piece on {square_name}\nClick first destination square")
                        self.draw_board()
                    elif self._quantum_target1 is None:
                        # Second click: first target square
                        self._quantum_target1 = square
                        self.selected_label.config(
                            text=f"Quantum Split: {chess.square_name(self.selected_square)} -> {square_name}\nClick second destination square")
                        self.draw_board()
                    else:
                        # Third click: second target square - execute split
                        self.make_quantum_split(self.selected_square, 
                                               self._quantum_target1, square)
                        self.selected_square = None
                        self._quantum_target1 = None
                        self.draw_board()
                else:
                    # Regular move (automatically handles entanglement)
                    if self.selected_square is None:
                        # First click: select square
                        self.selected_square = square
                        self.selected_label.config(text=f"Selected: {square_name}\nClick destination square")
                        self.draw_board()
                    else:
                        # Second click: make move
                        self.make_classical_move(self.selected_square, square)
                        self.selected_square = None
                        self.draw_board()
    
    def make_classical_move(self, from_square, to_square):
        """Make a move (automatically uses entanglement if target has superposition)."""
        move_uci = f"{chess.square_name(from_square)}{chess.square_name(to_square)}"
        
        # Check if it's the correct player's turn
        first_branch = next(iter(self.game.state_manager.branches.values()))
        board = first_branch.board
        piece = board.piece_at(from_square)
        
        if piece is None:
            messagebox.showerror("Illegal Move", f"No piece on {chess.square_name(from_square)}!")
            return
        
        # Check if piece belongs to current player
        current_turn = board.turn  # True = White, False = Black
        if piece.color != (chess.WHITE if current_turn else chess.BLACK):
            turn_name = "White" if current_turn else "Black"
            messagebox.showerror("Wrong Turn", f"It's {turn_name}'s turn! You can't move {piece.symbol()}.")
            return
        
        # Check if this will be an entanglement move
        target_prob = self.game.state_manager.get_occupancy_probability(to_square)
        is_entanglement = 0 < target_prob < 1
        
        success = self.game.classical_move(move_uci)
        
        if success:
            if is_entanglement:
                self.add_history(f"Move (Entanglement): {move_uci}")
            else:
                self.add_history(f"Move: {move_uci}")
            self.update_display()
        else:
            messagebox.showerror("Illegal Move", f"Move {move_uci} is illegal!")
    
    def make_quantum_split(self, from_square, to_square1, to_square2):
        """Make a quantum split move."""
        # Check if it's the correct player's turn
        first_branch = next(iter(self.game.state_manager.branches.values()))
        board = first_branch.board
        piece = board.piece_at(from_square)
        
        if piece is None:
            messagebox.showerror("Illegal Move", f"No piece on {chess.square_name(from_square)}!")
            return
        
        # Check if piece belongs to current player
        current_turn = board.turn  # True = White, False = Black
        if piece.color != (chess.WHITE if current_turn else chess.BLACK):
            turn_name = "White" if current_turn else "Black"
            messagebox.showerror("Wrong Turn", f"It's {turn_name}'s turn! You can't move {piece.symbol()}.")
            return
        
        success = self.game.quantum_move_split(from_square, to_square1, to_square2)
        
        if success:
            sq1_name = chess.square_name(to_square1)
            sq2_name = chess.square_name(to_square2)
            self.add_history(f"Quantum Split: {chess.square_name(from_square)} -> {sq1_name} + {sq2_name}")
            self.update_display()
        else:
            messagebox.showerror("Illegal Move", 
                               f"Quantum split failed! Check:\n- Both targets are empty (NDO)\n- Moves are legal")
    
    def start_measurement(self):
        """Start measurement mode."""
        self._measuring = True
        self.selected_label.config(text="Click a square to measure")
        messagebox.showinfo("Measurement", "Click a square to measure and collapse superpositions.")
    
    def measure_square(self, square):
        """Measure a square."""
        success, outcome = self.game.measure_square(square)
        
        if success:
            square_name = chess.square_name(square)
            self.add_history(f"Measured {square_name}: {outcome}")
            messagebox.showinfo("Measurement Result", f"Square {square_name}: {outcome}")
            self.update_display()
        else:
            messagebox.showerror("Error", "Measurement failed!")
        
        delattr(self, '_measuring')
        self.selected_label.config(text="Click a square to select")
    
    def start_phase_shift(self):
        """Start phase shift mode."""
        self._phase_shifting = True
        self.selected_label.config(text="Click a square to apply phase shift")
        messagebox.showinfo("Phase Shift", "Click a square to flip the phase of amplitudes on that square.")
    
    def apply_phase_shift_to_square(self, square):
        """Apply phase shift to a square."""
        success = self.game.apply_phase_shift(square, -1)
        
        if success:
            square_name = chess.square_name(square)
            self.add_history(f"Phase shift on {square_name}")
            messagebox.showinfo("Phase Shift", f"Phase flipped on {square_name}")
            self.update_display()
        else:
            messagebox.showerror("Error", "Phase shift failed! No amplitude on that square.")
        
        delattr(self, '_phase_shifting')
        self.selected_label.config(text="Click a square to select")
    
    def set_move_type(self, move_type):
        """Set the move type for tempo mode."""
        self.move_type = move_type
        type_names = {
            "classical": "Move",
            "quantum_split": "Quantum Split"
        }
        self.move_type_label.config(text=f"Selected: {type_names[move_type]}")
        
        # Clear selection state
        self.selected_square = None
        self._quantum_target1 = None
        self.selected_label.config(text="Click a square to select")
    
    def _format_amplitude(self, amp):
        """Format amplitude in LaTeX-style notation with square roots."""
        if abs(amp) < 1e-10:
            return "0"
        
        # Check if it's a common quantum amplitude
        sqrt2 = 1.0 / math.sqrt(2)
        sqrt2_half = 0.5
        
        # Check for 1/√2
        if abs(abs(amp) - sqrt2) < 1e-6:
            sign = "-" if amp < 0 else ""
            return f"{sign}1/√2"
        # Check for -1/√2
        elif abs(abs(amp) + sqrt2) < 1e-6:
            return "-1/√2"
        # Check for 1/2
        elif abs(abs(amp) - 0.5) < 1e-6:
            sign = "-" if amp < 0 else ""
            return f"{sign}1/2"
        # Check for 1
        elif abs(abs(amp) - 1.0) < 1e-6:
            sign = "-" if amp < 0 else ""
            return sign + "1"
        # Otherwise format as decimal
        else:
            if isinstance(amp, complex) and amp.imag != 0:
                return f"{amp.real:.4f} + {amp.imag:.4f}i"
            return f"{amp:.6f}"
    
    def view_square(self, square):
        """View mode: show detailed probability and amplitude information in LaTeX notation."""
        square_name = chess.square_name(square)
        prob = self.game.state_manager.get_occupancy_probability(square)
        amplitude = self.game.state_manager.get_occupancy_amplitude(square)
        
        # Get all pieces that have amplitude on this square with branch details
        pieces_info = []
        if square in self.game.state_manager.occupancy_cache:
            for branch_id in self.game.state_manager.occupancy_cache[square]:
                if branch_id in self.game.state_manager.branches:
                    branch = self.game.state_manager.branches[branch_id]
                    piece = branch.board.piece_at(square)
                    if piece and abs(branch.amplitude) > 1e-10:
                        branch_prob = branch.get_probability()
                        branch_amp = branch.amplitude
                        pieces_info.append((piece, branch_prob, branch_amp, branch_id))
        
        # Build info text with LaTeX-style notation
        self.prob_label.delete(1.0, tk.END)
        info_text = f"Square {square_name}:\n"
        info_text += f"|ψ⟩ = {self._format_amplitude(amplitude)}|{square_name}⟩\n"
        info_text += f"P({square_name}) = {prob:.6f}\n"
        info_text += "="*50 + "\n\n"
        
        if pieces_info:
            # Group by piece type/color
            piece_states = {}
            for piece, branch_prob, branch_amp, branch_id in pieces_info:
                piece_key = (piece.color, piece.symbol())
                if piece_key not in piece_states:
                    piece_states[piece_key] = []
                piece_states[piece_key].append((branch_amp, branch_prob, branch_id))
            
            info_text += "Quantum State (Dirac Notation):\n"
            info_text += "-"*50 + "\n"
            
            for (color, piece_symbol), states in piece_states.items():
                color_name = "White" if color else "Black"
                piece_name = piece_symbol
                
                # Build ket notation
                if len(states) == 1:
                    amp, prob, bid = states[0]
                    amp_str = self._format_amplitude(amp)
                    info_text += f"{color_name} {piece_name}:\n"
                    info_text += f"  |ψ⟩ = {amp_str}|{square_name}⟩\n"
                    info_text += f"  P = |{amp_str}|² = {prob:.6f}\n"
                else:
                    # Multiple branches - show superposition
                    info_text += f"{color_name} {piece_name}:\n"
                    ket_parts = []
                    for amp, prob, bid in states:
                        amp_str = self._format_amplitude(amp)
                        ket_parts.append(f"{amp_str}|{square_name}⟩")
                    info_text += f"  |ψ⟩ = " + " + ".join(ket_parts) + "\n"
                    total_prob = sum(p for _, p, _ in states)
                    info_text += f"  P = {total_prob:.6f}\n"
                info_text += "-"*50 + "\n"
        else:
            info_text += f"|ψ⟩ = 0|{square_name}⟩ (empty square)\n"
        
        self.prob_label.insert(1.0, info_text)
        self.selected_label.config(text=f"Viewing: {square_name}")
    
    def on_mode_change(self):
        """Handle mode change."""
        mode = self.mode_var.get()
        if mode == "view":
            self.tempo_frame.pack_forget()
            self.quantum_frame.pack_forget()
            self.selected_label.config(text="Click a square to view probabilities")
        elif mode == "tempo":
            self.tempo_frame.pack(fill=tk.X, pady=5)
            self.quantum_frame.pack_forget()
            self.selected_label.config(text="Click a square to select")
        else:  # quantum
            self.tempo_frame.pack_forget()
            self.quantum_frame.pack(fill=tk.X, pady=5)
            self.selected_label.config(text="Click a square to select")
        
        self.selected_square = None
        self._quantum_target1 = None
    
    def update_display(self):
        """Update all display elements."""
        # Update board
        self.draw_board()
        
        # Update status - fix: show whose turn it is to play
        # get_current_turn() returns True for White, False for Black
        # But we need to check the actual board turn
        first_branch = next(iter(self.game.state_manager.branches.values()))
        board_turn = first_branch.board.turn  # True = White, False = Black
        turn = "White" if board_turn else "Black"
        self.turn_label.config(text=f"Turn: {turn}")
        
        branch_count = self.game.get_branch_count()
        self.branch_label.config(text=f"Branches: {branch_count}")
        
        # Update check status
        if self.game.is_quantum_check():
            self.check_label.config(text="⚠️ QUANTUM CHECK!")
        else:
            self.check_label.config(text="")
        
        # Update probability info - only if in view mode or if square is selected
        if self.mode_var.get() == "view":
            # In view mode, keep the current view info (don't clear it)
            pass
        elif self.selected_square is not None:
            prob = self.game.state_manager.get_occupancy_probability(self.selected_square)
            amplitude = self.game.state_manager.get_occupancy_amplitude(self.selected_square)
            square_name = chess.square_name(self.selected_square)
            piece = self.game.get_expected_board().piece_at(self.selected_square)
            piece_info = f" ({piece.symbol()})" if piece else ""
            amp_str = self._format_amplitude(amplitude)
            info_text = f"{square_name}{piece_info}:\n"
            info_text += f"|ψ⟩ = {amp_str}|{square_name}⟩\n"
            info_text += f"P = {prob:.6f}"
            self.prob_label.delete(1.0, tk.END)
            self.prob_label.insert(1.0, info_text)
        else:
            self.prob_label.delete(1.0, tk.END)
            self.prob_label.insert(1.0, "Select a square to see quantum state")
    
    def add_history(self, move_text):
        """Add a move to history."""
        self.history_text.insert(tk.END, f"{move_text}\n")
        self.history_text.see(tk.END)
    
    def reset_game(self):
        """Reset the game."""
        if messagebox.askyesno("Reset Game", "Are you sure you want to reset the game?"):
            self.game = QuantumChessGame()
            self.selected_square = None
            self._quantum_target1 = None
            self.move_type = "classical"
            self.history_text.delete(1.0, tk.END)
            self.update_display()


def main():
    """Launch the GUI."""
    root = tk.Tk()
    app = ChessBoardGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

