"""
Quantum Chess GUI
A graphical interface for playing Quantum Chess.

Pick an action in the toolbar (or press its key), then click the board.
The inspector on the right shows the selected piece, the selected square,
the whole quantum state, every piece at risk, and the rules.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import chess
import math
from collections import defaultdict
from quantum_chess import QuantumChessGame, piece_id_name

# Matplotlib for LaTeX-style quantum state rendering.
# Falls back gracefully to plain text if not installed.
try:
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    _MATPLOTLIB = True
except ImportError:
    _MATPLOTLIB = False


# ── Look & feel ──────────────────────────────────────────────────────────────
BG = "#f4f4f8"
PANEL = "#ffffff"
INK = "#1d1d2c"
MUTED = "#6b6b80"
ACCENT = "#5b4bd6"
LIGHT_SQ = "#ede3d2"
DARK_SQ = "#b48a66"
SELECT_1 = "#f6d860"
SELECT_2 = "#8ec5f7"
SELECT_3 = "#a8e6a3"
TRACK = "#7c4dff"
CHECK_TINT = "#e57373"
ERROR = "#c62828"
NOTE = "#1e5fa8"
GOOD = "#2e7d32"

ACTIONS = [
    # key, label, shortcut, hint for each click
    ("inspect", "Inspect", "i", ["Click any square to inspect it and the piece on it."]),
    ("move", "Move", "m", ["Click one of your pieces.", "Click where it should go."]),
    ("split", "Split", "s", ["Click one of your pieces.", "Click the first destination.",
                             "Click the second destination."]),
    ("merge", "Merge", "g", ["Click the first half of a split piece (a failed merge lands here).",
                             "Click the second half.", "Click the empty target square."]),
    ("measure", "Measure", "x", ["Click a square whose contents are uncertain to measure it "
                                 "(uses your turn)."]),
    ("phase", "Phase ×−1", "p", ["Click one of your superposed pieces to flip its phase "
                                 "(free, once per turn)."]),
]
ACTION_HINTS = {key: hints for key, _, _, hints in ACTIONS}

RULES = """\
TURN
Each turn is ONE main action — Move, Split, Merge or Measure — plus an optional \
free Phase shift beforehand.

BRANCHES
The board is a superposition of ordinary chess positions. Every action is played \
in each branch separately. Where it is impossible (the piece isn't there, the path \
is blocked by a superposed piece, your king is in check…) that branch simply passes. \
The message bar tells you when that happened.

MOVE
An ordinary move. Capturing a half-present piece captures it only in the branches \
where it is there. Pawns promote to queens automatically.

SPLIT
Move a piece to two squares at once, 50/50. Each leg must be a legal move \
(captures allowed).

MERGE
Recombine two halves of the same piece onto an empty square both halves can reach. \
Halves with the same phase interfere constructively and the piece lands on the \
target. If one half's phase was flipped they interfere destructively there, and \
the whole piece lands on the FIRST half you clicked instead. Probability is never \
renormalized — it is moved by interference.

PHASE (free, once per turn)
Multiply one of your superposed pieces' amplitude by −1 (shown as “−” on the \
board). Phase is invisible to measurement; it only matters when you merge.

MEASURE (uses your turn)
Ask “what is on this square?” — which kind of piece, or empty. The state collapses \
to the branches that agree, and the rest are renormalized (this is the one place \
renormalization happens).

CHECK & CHECKMATE
Check can be partial (“Quantum check 50%”). Ignore it and your king can be captured \
in those branches. Whenever the side to move is checkmated (or its king is gone) \
in some branches, the game measures just that question: either it is mate and the \
game ends, or those branches vanish and play continues.

INSPECTOR
Piece — where a piece may be, and which pieces it is entangled with (knowing where \
one is tells you about the other).
Square — the state of one square as a ket.
State — every branch with its amplitude.
Pieces — every piece in superposition or at risk of having been captured.
"""


def pct(p: float) -> str:
    return f"{p * 100:.0f}%"


def loc_name(loc) -> str:
    return "captured" if loc is None else chess.square_name(loc)


class ChessBoardGUI:
    """Main GUI class for Quantum Chess."""

    MARGIN = 22

    GLYPH = {
        chess.KING: "♚", chess.QUEEN: "♛", chess.ROOK: "♜",
        chess.BISHOP: "♝", chess.KNIGHT: "♞", chess.PAWN: "♟",
    }
    OUTLINE = {
        chess.KING: "♔", chess.QUEEN: "♕", chess.ROOK: "♖",
        chess.BISHOP: "♗", chess.KNIGHT: "♘", chess.PAWN: "♙",
    }

    # Maps piece symbol → LaTeX \mathrm label used in the state formula
    _PIECE_LATEX = {
        'K': r'\mathrm{W\!K}', 'Q': r'\mathrm{W\!Q}', 'R': r'\mathrm{W\!R}',
        'B': r'\mathrm{W\!B}', 'N': r'\mathrm{W\!N}', 'P': r'\mathrm{W\!P}',
        'k': r'\mathrm{B\!K}', 'q': r'\mathrm{B\!Q}', 'r': r'\mathrm{B\!R}',
        'b': r'\mathrm{B\!B}', 'n': r'\mathrm{B\!N}', 'p': r'\mathrm{B\!P}',
    }

    def __init__(self, root):
        self.root = root
        self.root.title("Quantum Chess")
        self.root.geometry("1220x860")
        self.root.configure(bg=BG)

        self.game = QuantumChessGame()
        self.action = tk.StringVar(value="move")
        self._main_action = "move"        # restored after a free phase shift
        self.clicks = []                  # squares clicked for the current action
        self.inspected_pid = None         # piece shown in the Piece tab
        self.inspected_square = None      # square shown in the Square tab
        self.turn_number = 1
        self.SQUARE_SIZE = 64             # recomputed whenever the board is resized
        self._ox = 0                      # horizontal offset that centres the board

        self._setup_style()
        self.create_widgets()
        self._bind_keys()
        self.root.bind("<Configure>", self._relayout, add="+")
        self.root.update_idletasks()
        self._relayout()
        self.set_message("White to move. Pick an action above the board, or press "
                         "its key (M, S, G, X, P, I).", NOTE)
        self.update_display()

    # ── Widget construction ──────────────────────────────────────────────────

    def _setup_style(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(".", background=BG, foreground=INK, font=("Helvetica", 11))
        style.configure("Card.TFrame", background=PANEL)
        style.configure("Card.TLabel", background=PANEL, foreground=INK)
        style.configure("Muted.TLabel", background=PANEL, foreground=MUTED,
                        font=("Helvetica", 10))
        style.configure("Big.TLabel", background=PANEL, foreground=INK,
                        font=("Helvetica", 16, "bold"))
        style.configure("Check.TLabel", background=PANEL, foreground=ERROR,
                        font=("Helvetica", 11, "bold"))
        style.configure("Action.Toolbutton", padding=(10, 6), font=("Helvetica", 11))
        style.map("Action.Toolbutton",
                  background=[("selected", ACCENT), ("active", "#e4e1fb")],
                  foreground=[("selected", "#ffffff")])
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", padding=(12, 5))
        style.configure("Treeview", rowheight=24, font=("Helvetica", 11))
        style.configure("Treeview.Heading", font=("Helvetica", 10, "bold"))

    def create_widgets(self):
        # Board and inspector sit side by side in a wide window and stacked
        # in a tall one (see _relayout).
        self.body = ttk.Frame(self.root, padding=10)
        self.body.pack(fill=tk.BOTH, expand=True)
        self._layout = None

        # ── Board side: toolbar, board, message bar ─────────────────────────
        left = self.left = ttk.Frame(self.body)

        toolbar = ttk.Frame(left)
        toolbar.pack(fill=tk.X, pady=(0, 6))
        for key, label, shortcut, _ in ACTIONS:
            ttk.Radiobutton(toolbar, text=label, value=key,
                            variable=self.action, style="Action.Toolbutton",
                            command=self.on_action_change).pack(side=tk.LEFT, padx=1)

        buttons = ttk.Frame(left)
        buttons.pack(side=tk.BOTTOM, fill=tk.X, pady=(6, 0))
        ttk.Button(buttons, text="Cancel (Esc)",
                   command=self.cancel_selection).pack(side=tk.LEFT)
        ttk.Button(buttons, text="New game", command=self.reset_game).pack(side=tk.RIGHT)
        self.message = tk.Label(left, text="", bg=BG, fg=NOTE, anchor="nw",
                                justify=tk.LEFT, font=("Helvetica", 11), height=4)
        self.message.pack(side=tk.BOTTOM, fill=tk.X)
        self.hint_label = tk.Label(left, text="", bg=BG, fg=INK, anchor="w",
                                   justify=tk.LEFT, font=("Helvetica", 12, "bold"))
        self.hint_label.pack(side=tk.BOTTOM, fill=tk.X, pady=(6, 2))

        self.canvas = tk.Canvas(left, width=560, height=560, bg=BG,
                                highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", self.on_square_click)
        self.canvas.bind("<Configure>", self._on_canvas_resize)

        # ── Inspector side: status card, inspector tabs, history ────────────
        right = self.right = ttk.Frame(self.body)
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)

        status = ttk.Frame(right, style="Card.TFrame", padding=12)
        status.grid(row=0, column=0, sticky="ew")
        status.columnconfigure(1, weight=1)
        self.turn_label = ttk.Label(status, text="", style="Big.TLabel")
        self.turn_label.grid(row=0, column=0, sticky="w")
        self.check_label = ttk.Label(status, text="", style="Check.TLabel")
        self.check_label.grid(row=0, column=1, sticky="e")
        self.info_label = ttk.Label(status, text="", style="Muted.TLabel",
                                    justify=tk.LEFT)
        self.info_label.grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 0))

        self.tabs = ttk.Notebook(right)
        self.tabs.grid(row=1, column=0, sticky="nsew", pady=10)

        self.piece_tab = self._text_tab("Piece")
        self.square_tab_frame, self.square_text, self._sq_fig = self._formula_tab("Square")
        self.state_tab_frame, self.state_text, self._st_fig = self._formula_tab("State")
        self._build_pieces_tab()
        rules = self._text_tab("Rules")
        rules.insert(tk.END, RULES)
        for heading in ("TURN", "BRANCHES", "MOVE", "SPLIT", "MERGE", "PHASE",
                        "MEASURE", "CHECK & CHECKMATE", "INSPECTOR"):
            start = rules.search(heading + "\n", "1.0", tk.END)
            if not start:
                start = rules.search(heading + " ", "1.0", tk.END)
            if start:
                rules.tag_add("h2", start, f"{start} lineend")
        rules.configure(state=tk.DISABLED)

        hist = ttk.Frame(right, style="Card.TFrame", padding=8)
        hist.grid(row=2, column=0, sticky="ew")
        ttk.Label(hist, text="History", style="Card.TLabel",
                  font=("Helvetica", 11, "bold")).pack(anchor="w")
        self.history_text = tk.Text(hist, height=6, wrap=tk.WORD, relief=tk.FLAT,
                                    bg=PANEL, fg=INK, font=("Menlo", 11),
                                    highlightthickness=0, borderwidth=0)
        self.history_text.pack(fill=tk.X)

    def _style_text(self, text: tk.Text):
        text.tag_configure("h1", font=("Helvetica", 15, "bold"), spacing1=4, spacing3=6)
        text.tag_configure("h2", font=("Helvetica", 12, "bold"), foreground=ACCENT,
                           spacing1=10, spacing3=4)
        text.tag_configure("muted", foreground=MUTED)
        text.tag_configure("mono", font=("Menlo", 11))
        text.tag_configure("bar", font=("Menlo", 11), foreground=TRACK)
        text.tag_configure("bad", foreground=ERROR)
        text.tag_configure("good", foreground=GOOD)
        text.tag_configure("link", foreground=ACCENT, underline=True)

    def _text_tab(self, title: str) -> tk.Text:
        frame = ttk.Frame(self.tabs, style="Card.TFrame", padding=10)
        self.tabs.add(frame, text=title)
        text = tk.Text(frame, wrap=tk.WORD, relief=tk.FLAT, bg=PANEL, fg=INK,
                       font=("Helvetica", 12), padx=4, pady=4, cursor="arrow",
                       highlightthickness=0, borderwidth=0)
        sb = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=text.yview)
        text.configure(yscrollcommand=sb.set)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self._style_text(text)
        return text

    def _formula_tab(self, title: str):
        """A tab with a LaTeX formula on top and a text area below."""
        frame = ttk.Frame(self.tabs, style="Card.TFrame", padding=10)
        self.tabs.add(frame, text=title)
        fig = None
        if _MATPLOTLIB:
            figure = Figure(figsize=(6.2, 1.7), facecolor=PANEL, dpi=90)
            ax = figure.add_axes([0, 0, 1, 1])
            ax.axis("off")
            canvas = FigureCanvasTkAgg(figure, master=frame)
            canvas.get_tk_widget().pack(fill=tk.X)
            fig = (figure, ax, canvas)
        text = tk.Text(frame, wrap=tk.WORD, relief=tk.FLAT, bg=PANEL, fg=INK,
                       font=("Helvetica", 12), padx=4, pady=4, height=12, cursor="arrow",
                       highlightthickness=0, borderwidth=0)
        text.pack(fill=tk.BOTH, expand=True)
        self._style_text(text)
        return frame, text, fig

    def _build_pieces_tab(self):
        frame = ttk.Frame(self.tabs, style="Card.TFrame", padding=10)
        self.tabs.add(frame, text="Pieces")
        ttk.Label(frame, text="Pieces in superposition or possibly captured. "
                              "Click a row to inspect it.",
                  style="Muted.TLabel").pack(anchor="w", pady=(0, 6))
        cols = ("alive", "where")
        self.pieces_tree = ttk.Treeview(frame, columns=cols, show="tree headings",
                                        selectmode="browse")
        self.pieces_tree.heading("#0", text="Piece")
        self.pieces_tree.heading("alive", text="On board")
        self.pieces_tree.heading("where", text="Where it may be")
        self.pieces_tree.column("#0", width=190)
        self.pieces_tree.column("alive", width=80, anchor="center")
        self.pieces_tree.column("where", width=280)
        self.pieces_tree.pack(fill=tk.BOTH, expand=True)
        self.pieces_tree.bind("<<TreeviewSelect>>", self._on_piece_row)

    def _relayout(self, event=None):
        """Side by side when the window is wide, stacked when it is tall."""
        if event is not None and event.widget is not self.root:
            return
        w, h = self.root.winfo_width(), self.root.winfo_height()
        layout = "wide" if w >= h * 1.05 else "tall"
        if layout == self._layout:
            return
        self._layout = layout
        body = self.body
        for i in range(2):
            body.columnconfigure(i, weight=0, minsize=0)
            body.rowconfigure(i, weight=0, minsize=0)
        if layout == "wide":
            self.left.grid(row=0, column=0, sticky="nsew")
            self.right.grid(row=0, column=1, sticky="nsew", padx=(12, 0))
            body.columnconfigure(0, weight=3)
            body.columnconfigure(1, weight=2, minsize=380)
            body.rowconfigure(0, weight=1)
        else:
            self.left.grid(row=0, column=0, sticky="nsew")
            self.right.grid(row=1, column=0, sticky="nsew", pady=(12, 0))
            body.columnconfigure(0, weight=1)
            body.rowconfigure(0, weight=3)
            body.rowconfigure(1, weight=2, minsize=300)

    def _bind_keys(self):
        for key, _, shortcut, _ in ACTIONS:
            self.root.bind(f"<KeyPress-{shortcut}>",
                           lambda e, k=key: (self.action.set(k), self.on_action_change()))
        self.root.bind("<Escape>", lambda e: self.cancel_selection())

    # ── Board drawing ────────────────────────────────────────────────────────

    def _on_canvas_resize(self, event):
        size = max(28, (min(event.width, event.height) - 2 * self.MARGIN) // 8)
        self.message.configure(wraplength=max(200, event.width - 10))
        self.hint_label.configure(wraplength=max(200, event.width - 10))
        ox = max(0, (event.width - 8 * size - 2 * self.MARGIN) // 2)
        if (size, ox) != (self.SQUARE_SIZE, self._ox):
            self.SQUARE_SIZE, self._ox = size, ox
            self.draw_board()

    def _square_xy(self, square):
        col, row = chess.square_file(square), 7 - chess.square_rank(square)
        x = self._ox + self.MARGIN + col * self.SQUARE_SIZE
        y = self.MARGIN + row * self.SQUARE_SIZE
        return x, y

    def _legal_targets(self, square):
        """Squares the current player's piece on `square` can reach in some branch."""
        color = self.game.get_current_turn()
        targets = set()
        for branch in self.game.branches.values():
            p = branch.board.piece_at(square)
            if p is not None and p.color == color:
                targets |= {m.to_square for m in branch.board.legal_moves
                            if m.from_square == square}
        return targets

    def draw_board(self):
        c = self.canvas
        c.delete("all")
        s = self.SQUARE_SIZE
        branches = list(self.game.branches.values())

        # Tint the king's square by the probability of check
        p_check = self.game.get_check_probability() if self.game.result is None else 0
        king_sq = branches[0].board.king(self.game.get_current_turn())

        for square in chess.SQUARES:
            x, y = self._square_xy(square)
            light = (chess.square_file(square) + chess.square_rank(square)) % 2 == 1
            color = LIGHT_SQ if light else DARK_SQ
            if square == king_sq and p_check > 1e-9:
                color = CHECK_TINT
            if square in self.clicks:
                color = [SELECT_1, SELECT_2, SELECT_3][self.clicks.index(square)]
            c.create_rectangle(x, y, x + s, y + s, fill=color, outline="")

        # Coordinates
        for i in range(8):
            c.create_text(self._ox + self.MARGIN + i * s + s / 2, self.MARGIN + 8 * s + 11,
                          text="abcdefgh"[i], fill=MUTED, font=("Helvetica", 11))
            c.create_text(self._ox + self.MARGIN / 2, self.MARGIN + i * s + s / 2,
                          text=str(8 - i), fill=MUTED, font=("Helvetica", 11))

        # Where the inspected piece may be
        if self.inspected_pid is not None:
            for loc, p in self.game.piece_distribution(self.inspected_pid).items():
                if loc is None:
                    continue
                x, y = self._square_xy(loc)
                c.create_rectangle(x + 2, y + 2, x + s - 2, y + s - 2,
                                   outline=TRACK, width=3)

        # Move hints for the piece being moved / split
        if self.action.get() in ("move", "split") and self.clicks:
            occupied = {sq for b in branches for sq in b.board.piece_map()}
            for t in self._legal_targets(self.clicks[0]):
                if t in self.clicks:
                    continue
                x, y = self._square_xy(t)
                if t in occupied:
                    c.create_oval(x + 4, y + 4, x + s - 4, y + s - 4,
                                  outline="#3a3a55", width=3)
                else:
                    r = max(4, s // 9)
                    c.create_oval(x + s / 2 - r, y + s / 2 - r, x + s / 2 + r,
                                  y + s / 2 + r, fill="#3a3a55", outline="")

        # Pieces: probability and phase per (square, symbol)
        occupants = defaultdict(lambda: defaultdict(lambda: [0.0, True]))
        for b in branches:
            p = b.get_probability()
            negative = complex(b.amplitude).real < 0
            for sq, piece in b.board.piece_map().items():
                entry = occupants[sq][piece.symbol()]
                entry[0] += p
                entry[1] = entry[1] and negative

        for sq, symbols in occupants.items():
            x, y = self._square_xy(sq)
            items = sorted(symbols.items(), key=lambda kv: -kv[1][0])
            n = len(items)
            size = int(s * (0.6 if n == 1 else 0.4))
            for idx, (sym, (prob, negative)) in enumerate(items):
                piece = chess.Piece.from_symbol(sym)
                cx = x + s / 2 + (idx - (n - 1) / 2) * (s / (n + 0.4))
                cy = y + s / 2 + 3
                certain = prob > 0.999
                self._draw_glyph(cx, cy, piece, size, certain)
                if not certain:
                    label = ("−" if negative else "") + pct(prob)
                    bx, by = cx, y + 9
                    fsize = 9 if n == 1 else 7
                    w = fsize * 0.62 * len(label) / 2 + 3
                    dark = piece.color == chess.BLACK
                    c.create_rectangle(bx - w, by - 7, bx + w, by + 7,
                                       fill="#26263a" if dark else "#ffffff",
                                       outline="#26263a")
                    c.create_text(bx, by, text=label, font=("Helvetica", fsize, "bold"),
                                  fill="#ffffff" if dark else "#26263a")

    def _draw_glyph(self, cx, cy, piece, size, certain):
        font = ("Arial", size)
        glyph = self.GLYPH[piece.piece_type]
        if piece.color == chess.WHITE:
            fill = "#ffffff" if certain else "#f3f0ff"
            line = "#1b1b1b" if certain else "#8a85a8"
            self.canvas.create_text(cx, cy, text=glyph, font=font, fill=fill)
            self.canvas.create_text(cx, cy, text=self.OUTLINE[piece.piece_type],
                                    font=font, fill=line)
        else:
            fill = "#151515" if certain else "#6e6a85"
            self.canvas.create_text(cx, cy, text=glyph, font=font, fill=fill)

    # ── Click handling ───────────────────────────────────────────────────────

    def _square_from_event(self, event):
        col = int((event.x - self._ox - self.MARGIN) // self.SQUARE_SIZE)
        row = int((event.y - self.MARGIN) // self.SQUARE_SIZE)
        if not (0 <= col < 8 and 0 <= row < 8):
            return None
        return chess.square(col, 7 - row)

    def on_square_click(self, event):
        square = self._square_from_event(event)
        if square is None:
            return
        action = self.action.get()

        # Clicking a square always inspects it.
        self.inspect_square(square, switch_tab=(action == "inspect"))
        if action == "inspect":
            self.update_display()
            return

        if square in self.clicks:           # clicking a chosen square again undoes it
            self.clicks = self.clicks[:self.clicks.index(square)]
            self.update_display()
            return

        self.clicks.append(square)
        needed = len(ACTION_HINTS[action])
        if len(self.clicks) < needed:
            self.update_display()
            return

        sq = self.clicks
        self.clicks = []
        if action == "move":
            self.do_move(sq[0], sq[1])
        elif action == "split":
            self.do_split(sq[0], sq[1], sq[2])
        elif action == "merge":
            self.do_merge(sq[0], sq[1], sq[2])
        elif action == "measure":
            self.do_measure(sq[0])
        elif action == "phase":
            self.do_phase(sq[0])
        self.update_display()

    def on_action_change(self):
        if self.action.get() != "phase":
            self._main_action = self.action.get()
        self.clicks = []
        self.update_display()

    def cancel_selection(self):
        self.clicks = []
        self.update_display()

    # ── Actions ──────────────────────────────────────────────────────────────

    def _player(self):
        return "White" if self.game.get_current_turn() == chess.WHITE else "Black"

    def _record(self, player, text):
        prefix = f"{self.turn_number}." if player == "White" else f"{self.turn_number}…"
        self.history_text.insert(tk.END, f"{prefix} {text}\n")
        self.history_text.see(tk.END)
        if player == "Black":
            self.turn_number += 1

    def _report(self, success, done_text):
        """Show the outcome of an action in the message bar."""
        if not success:
            self.set_message(self.game.last_error or "That action isn't possible.", ERROR)
            return
        lines = [done_text] + self.game.last_notes
        self.set_message("\n".join(lines), NOTE if self.game.last_notes else GOOD)
        self._report_mate()

    def _report_mate(self):
        m = self.game.last_mate_measurement
        if m is None:
            return
        p = pct(m['probability'])
        if m['mate']:
            winner = "White" if self.game.result['winner'] == chess.WHITE else "Black"
            self.history_text.insert(tk.END, f"   Mate measured ({p}) — {winner} wins\n")
            self.set_message(f"Checkmate! The king was lost in {p} of the branches and "
                             f"the measurement landed there. {winner} wins.", GOOD)
            messagebox.showinfo("Checkmate!",
                                f"The king was lost in {p} of the superposition.\n"
                                f"The measurement collapsed onto that outcome:\n\n"
                                f"{winner} wins!")
        else:
            self.history_text.insert(tk.END, f"   Mate measured ({p}) — escaped\n")
            self.set_message(f"Checkmate existed in {p} of the branches. The measurement "
                             "said NO — those branches vanished and play continues.", NOTE)

    def do_move(self, frm, to):
        player = self._player()
        name = f"{chess.square_name(frm)}→{chess.square_name(to)}"
        ok = self.game.classical_move(chess.square_name(frm) + chess.square_name(to))
        if ok:
            self._record(player, f"Move {name}")
        self._report(ok, f"{player} moved {name}.")

    def do_split(self, frm, t1, t2):
        player = self._player()
        name = (f"{chess.square_name(frm)}→{chess.square_name(t1)} | "
                f"{chess.square_name(t2)}")
        ok = self.game.quantum_move_split(frm, t1, t2)
        if ok:
            self._record(player, f"Split {name}")
        self._report(ok, f"{player} split {name}.")

    def do_merge(self, a, b, t):
        player = self._player()
        name = f"{chess.square_name(a)} + {chess.square_name(b)} → {chess.square_name(t)}"
        ok = self.game.quantum_merge(a, b, t)
        if ok:
            self._record(player, f"Merge {name}")
        self._report(ok, f"{player} merged {name}.")

    def do_measure(self, square):
        player = self._player()
        ok, outcome = self.game.measure_square(square)
        name = chess.square_name(square)
        if ok:
            self._record(player, f"Measure {name}: {outcome.lower()}")
        self._report(ok, f"Measured {name}: {outcome}. "
                         "Every branch that disagreed is gone.")

    def do_phase(self, square):
        player = self._player()
        ok = self.game.apply_phase_shift(square, -1)
        name = chess.square_name(square)
        if ok:
            self.history_text.insert(tk.END, f"   ({player} flips phase on {name})\n")
            self.action.set(self._main_action)
        names = {k: label for k, label, _, _ in ACTIONS}
        self._report(ok, f"Phase flipped on {name}. Now make your main action — "
                         f"{names[self.action.get()]} is selected.")

    # ── Inspector ────────────────────────────────────────────────────────────

    def inspect_square(self, square, switch_tab=True):
        self.inspected_square = square
        on_square = self.game.pieces_on_square(square)
        if on_square:
            self.inspected_pid = max(on_square, key=on_square.get)
            if switch_tab:
                self.tabs.select(0)
        elif switch_tab:
            self.tabs.select(1)

    def _on_piece_row(self, _event):
        sel = self.pieces_tree.selection()
        if sel and sel[0] != self.inspected_pid:
            self.inspected_pid = sel[0]
            self.tabs.select(0)
            self.update_display()

    def _write(self, text: tk.Text, chunks):
        text.configure(state=tk.NORMAL)
        text.delete("1.0", tk.END)
        for chunk in chunks:
            if isinstance(chunk, tuple):
                text.insert(tk.END, chunk[0], chunk[1])
            else:
                text.insert(tk.END, chunk)
        text.configure(state=tk.DISABLED)

    def _location_phase(self, pid, loc):
        """'+', '−' or 'mixed' for the branches where `pid` is at `loc`."""
        signs = set()
        for b in self.game.branches.values():
            if self.game._location(b, pid) == loc:
                signs.add(complex(b.amplitude).real < 0)
        if signs == {True}:
            return "−"
        if signs == {False}:
            return "+"
        return "±"

    def render_piece_tab(self):
        pid = self.inspected_pid
        if pid is None:
            self._write(self.piece_tab, [
                ("No piece selected\n", "h1"),
                ("Click a piece on the board (any action) to see where it may be and "
                 "which other pieces its fate is tied to.", "muted")])
            return
        dist = self.game.piece_distribution(pid)
        alive = 1 - dist.get(None, 0.0)
        chunks = [(piece_id_name(pid) + "\n", "h1")]
        if alive < 1e-9:
            chunks.append(("Captured.\n", "bad"))
            self._write(self.piece_tab, chunks)
            return
        state = "in superposition" if self.game.is_quantum_piece(pid) else "classical"
        chunks.append((f"On the board: {pct(alive)}   ·   {state}\n", "muted"))

        chunks.append(("Where it may be\n", "h2"))
        for loc, p in sorted(dist.items(), key=lambda kv: -kv[1]):
            bar = "█" * round(p * 10) + "·" * (10 - round(p * 10))
            name = loc_name(loc)
            chunks.append((f" {name:8} ", "mono"))
            chunks.append((bar, "bar" if loc is not None else "bad"))
            chunks.append((f" {pct(p):>4}", "mono"))
            if loc is not None and self.game.is_quantum_piece(pid):
                chunks.append((f"   phase {self._location_phase(pid, loc)}", "muted"))
            chunks.append("\n")

        corr = self.game.piece_correlations(pid)
        chunks.append(("Entangled with\n", "h2"))
        if not corr:
            chunks.append(("Nothing — this piece's position tells you nothing about "
                           "any other piece.\n", "muted"))
        for item in corr:
            other = item['piece']
            chunks.append((f"{piece_id_name(other)}", ""))
            chunks.append((f"   ({item['information']:.2f} bits shared)\n", "muted"))
            for loc, cond in sorted(item['conditional'].items(),
                                    key=lambda kv: -dist.get(kv[0], 0)):
                where = ", ".join(f"{loc_name(l)} {pct(p)}"
                                  for l, p in sorted(cond.items(), key=lambda kv: -kv[1]))
                me = "captured" if loc is None else f"on {chess.square_name(loc)}"
                chunks.append((f"   if this piece is {me}: ", "muted"))
                chunks.append((f"{where}\n", "mono"))
        self._write(self.piece_tab, chunks)

    def render_square_tab(self):
        square = self.inspected_square
        if square is None:
            self._render_formula(self._sq_fig, "Click a square",
                                 r"|\mathrm{square}\rangle\;=\;?", "")
            self._write(self.square_text, [("Click any square to see what may be on it.",
                                            "muted")])
            return
        title, formula, subtitle = self._build_square_latex(square)
        self._render_formula(self._sq_fig, title, formula, subtitle)
        chunks = [("Who may be here\n", "h2")]
        on = self.game.pieces_on_square(square)
        for pid, p in sorted(on.items(), key=lambda kv: -kv[1]):
            chunks.append((f"  {pct(p):>4}  ", "mono"))
            chunks.append((piece_id_name(pid) + "\n", ""))
        empty = 1 - sum(on.values())
        if empty > 1e-9:
            chunks.append((f"  {pct(empty):>4}  ", "mono"))
            chunks.append(("empty\n", "muted"))
        if not self._sq_fig:
            chunks.insert(0, (f"{title}\n{formula}\n{subtitle}\n", "mono"))
        self._write(self.square_text, chunks)

    def render_state_tab(self):
        rows = self.game.branch_summaries()
        qp = self.game.quantum_pieces()
        n = len(rows)
        if not qp:
            self._render_formula(self._st_fig, "Classical position",
                                 r"|\psi\rangle \;=\; 1\,|\mathrm{board}\rangle",
                                 "No superpositions active")
        elif n <= 4 and len(qp) <= 4:
            terms = []
            for amp, locs in rows:
                ket = r",\,".join(
                    rf"{self._piece_tex(pid)}\!:\!{self._loc_tex(locs[pid])}" for pid in qp)
                terms.append(rf"{self._amp_to_latex(amp)}\,|{ket}\rangle")
            formula = r"|\psi\rangle = " + r" + ".join(terms).replace("+ -", "- ")
            self._render_formula(self._st_fig, f"{n} branches", formula,
                                 "Only pieces in superposition are written in each ket")
        else:
            self._render_formula(self._st_fig, f"{n} branches",
                                 r"|\psi\rangle \;=\; \sum_{i}\,\alpha_i\,|b_i\rangle",
                                 "Too many terms to typeset — see the table below")

        chunks = [("Branches\n", "h2")]
        if qp:
            header = "  amplitude    prob   " + "  ".join(
                f"{self._short(pid):>6}" for pid in qp) + "\n"
            chunks.append((header, ("mono", "muted")))
            for amp, locs in rows[:40]:
                line = f"  {self._amp_plain(amp):>9}  {pct(abs(amp) ** 2):>5}   " + "  ".join(
                    f"{loc_name(locs[pid]) if locs[pid] is not None else '✝':>6}"
                    for pid in qp)
                chunks.append((line + "\n", "mono"))
            if n > 40:
                chunks.append((f"  … and {n - 40} more branches\n", "muted"))
            chunks.append(("\nColumns: ", "muted"))
            chunks.append((", ".join(f"{self._short(p)} = {piece_id_name(p)}" for p in qp),
                           "muted"))
            chunks.append(("\n✝ = captured", "muted"))
        else:
            chunks.append(("Just one ordinary chess position.", "muted"))
        self._write(self.state_text, chunks)

    def render_pieces_tab(self):
        tree = self.pieces_tree
        tree.delete(*tree.get_children())
        for pid in self.game.piece_ids():
            dist = self.game.piece_distribution(pid)
            dead = dist.get(None, 0.0)
            if not self.game.is_quantum_piece(pid) and dead < 1e-9:
                continue
            where = ", ".join(f"{loc_name(l)} {pct(p)}"
                              for l, p in sorted(dist.items(), key=lambda kv: -kv[1]))
            tree.insert("", tk.END, iid=pid, text=piece_id_name(pid),
                        values=(pct(1 - dead), where))
        if self.inspected_pid in tree.get_children():
            tree.selection_set(self.inspected_pid)

    # ── LaTeX helpers ────────────────────────────────────────────────────────

    def _short(self, pid):
        symbol, start = pid.split("@")
        return f"{symbol}{start}"

    def _piece_tex(self, pid):
        symbol, start = pid.split("@")
        return rf"\mathrm{{{symbol}}}_{{{start}}}"

    def _loc_tex(self, loc):
        return r"\times" if loc is None else rf"\mathrm{{{chess.square_name(loc)}}}"

    def _amp_plain(self, amp):
        r = complex(amp).real
        sign = "-" if r < -1e-10 else ""
        val = abs(amp)
        for target, text in ((1.0, "1"), (1 / math.sqrt(2), "1/√2"), (0.5, "1/2"),
                             (0.5 / math.sqrt(2), "1/(2√2)"), (0.25, "1/4")):
            if abs(val - target) < 1e-6:
                return sign + text
        return f"{sign}{val:.4f}"

    def _amp_to_latex(self, amp) -> str:
        """Convert an amplitude value to a LaTeX coefficient string."""
        r = amp.real if isinstance(amp, complex) else float(amp)
        i = amp.imag if isinstance(amp, complex) else 0.0
        sign = "" if r >= -1e-10 else "-"
        val = abs(complex(r, i))

        if val < 1e-10:
            return "0"

        # Return exact forms for the common Clifford-gate amplitudes
        sqrt2 = 1.0 / math.sqrt(2)
        if abs(i) < 1e-10:
            if abs(val - 1.0) < 1e-6:
                return sign + "1"
            if abs(val - sqrt2) < 1e-6:
                return sign + r"\frac{1}{\sqrt{2}}"
            if abs(val - 0.5) < 1e-6:
                return sign + r"\frac{1}{2}"
            if abs(val - 0.5 * sqrt2) < 1e-6:
                return sign + r"\frac{1}{2\sqrt{2}}"
            return f"{sign}{val:.4f}"
        # Complex amplitude (e.g. after phase shift by i)
        return f"({r:.3f}{'+' if i >= 0 else ''}{i:.3f}i)"

    def _build_square_latex(self, square: chess.Square):
        """
        Build (title, formula, subtitle) LaTeX strings describing the reduced
        quantum state of the square — which occupant (piece or empty) can be
        found there and with what Born-rule amplitude.

        Coefficients are √(probability) — the standard Born-rule amplitude for
        each outcome.  Because different branches are orthogonal histories we
        sum |α|² (probabilities), not amplitudes, per occupant.  A minus sign
        is shown when every branch with that occupant carries a −1 phase.
        """
        sq_name = chess.square_name(square).upper()

        piece_probs: dict = {}   # symbol -> float
        piece_neg: dict = {}     # symbol -> True if every branch has a −1 phase
        empty_prob: float = 0.0

        for branch in self.game.branches.values():
            p = branch.get_probability()
            piece = branch.board.piece_at(square)
            if piece is not None:
                sym = piece.symbol()
                piece_probs[sym] = piece_probs.get(sym, 0.0) + p
                negative = complex(branch.amplitude).real < 0
                piece_neg[sym] = piece_neg.get(sym, True) and negative
            else:
                empty_prob += p

        parts = []
        for sym, prob in piece_probs.items():
            if prob > 1e-10:
                coeff = self._amp_to_latex(
                    -math.sqrt(prob) if piece_neg[sym] else math.sqrt(prob))
                ket = self._PIECE_LATEX.get(sym, r"\mathrm{?}")
                parts.append(f"{coeff}\\,|{ket}\\rangle")

        if empty_prob > 1e-10:
            coeff = self._amp_to_latex(math.sqrt(empty_prob))
            parts.append(f"{coeff}\\,|\\emptyset\\rangle")

        if not parts:
            formula = rf"|\mathrm{{{sq_name}}}\rangle \;=\; |\emptyset\rangle"
        else:
            rhs = r"\;+\;".join(parts).replace(r"\;+\;-", r"\;-\;")
            formula = rf"|\mathrm{{{sq_name}}}\rangle \;=\; {rhs}"

        total_occ = sum(piece_probs.values())
        subtitle = (f"P(occupied) = {total_occ:.3f}   "
                    f"P(empty) = {max(0.0, 1.0 - total_occ):.3f}")
        return f"State of square {sq_name}", formula, subtitle

    def _render_formula(self, fig, title, formula, subtitle=""):
        if fig is None:
            return
        figure, ax, canvas = fig
        ax.clear()
        ax.axis("off")
        ax.text(0.5, 0.92, title, ha="center", va="top", fontsize=10,
                fontweight="bold", color=INK, transform=ax.transAxes)
        ax.text(0.5, 0.5, f"${formula}$", ha="center", va="center", fontsize=14,
                color=INK, transform=ax.transAxes)
        if subtitle:
            ax.text(0.5, 0.06, subtitle, ha="center", va="bottom", fontsize=8.5,
                    color=MUTED, transform=ax.transAxes)
        try:
            canvas.draw()
        except Exception:
            # A formula matplotlib can't typeset shouldn't break the game.
            ax.clear()
            ax.axis("off")
            ax.text(0.5, 0.5, title, ha="center", va="center", transform=ax.transAxes)
            canvas.draw()

    # ── Display update ───────────────────────────────────────────────────────

    def set_message(self, text, color=NOTE):
        self.message.configure(text=text, fg=color)

    def update_display(self):
        """Refresh board, status, hint and every inspector tab."""
        self.draw_board()

        game = self.game
        if game.result is not None:
            winner = "White" if game.result['winner'] == chess.WHITE else "Black"
            self.turn_label.config(text=f"{winner} wins")
            self.check_label.config(text="CHECKMATE")
            self.info_label.config(text="Start a new game to play again.")
        else:
            self.turn_label.config(text=f"{self._player()} to move")
            p_check = game.get_check_probability()
            if p_check > 0.999:
                self.check_label.config(text="CHECK")
            elif p_check > 1e-9:
                self.check_label.config(text=f"Quantum check {pct(p_check)}")
            else:
                self.check_label.config(text="")
            phase = "available" if game.can_phase_shift() else "used this turn"
            self.info_label.config(
                text=f"Branches: {game.get_branch_count()}  ·  "
                     f"in superposition: {len(game.quantum_pieces())} pieces\n"
                     f"Free phase shift: {phase}")

        hints = ACTION_HINTS[self.action.get()]
        step = min(len(self.clicks), len(hints) - 1)
        prefix = f"Step {step + 1}/{len(hints)}: " if len(hints) > 1 else ""
        if self.game.result is None:
            prefix = f"{self._player()} to move · " + prefix
        self.hint_label.config(text=prefix + hints[step])

        self.render_piece_tab()
        self.render_square_tab()
        self.render_state_tab()
        self.render_pieces_tab()

    def reset_game(self):
        if messagebox.askyesno("New game", "Start a new game?"):
            self.game = QuantumChessGame()
            self.clicks = []
            self.inspected_pid = None
            self.inspected_square = None
            self.turn_number = 1
            self.action.set("move")
            self.history_text.delete("1.0", tk.END)
            self.set_message("New game. White to move.", NOTE)
            self.update_display()


def main():
    root = tk.Tk()
    ChessBoardGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
