# Quantum Chess: The Ruleset

## I. The Objective

The objective is identical to classical chess: **Checkmate the opponent's King.**

---

## II. The King: The Classical Anchor

The King is the only piece that is **always classical**.
* It can **never** be in a superposition.
* It must always occupy exactly one, known square.
* It cannot be entangled.

---

## III. The Turn: "Tempo Mode" vs. "Quantum Mode"

On your turn, you must choose **one** of two modes. You cannot do both.

---

## IV. 🌍 Tempo Mode (Make a Move)

You choose this mode to move a piece and affect the board. You make **one** of the following actions:

* **Classical Move:** A standard, non-quantum move (e.g., Pawn `e2-e4`).
* **Quantum Move (Split):** Move one classical piece into a superposition of **exactly two** legal squares.
    > **Example:** Knight on `c3` moves to $|\Psi\rangle = \frac{1}{\sqrt{2}}|d5\rangle + \frac{1}{\sqrt{2}}|e4\rangle$.
* **Interference Move:** Apply a `Quantum Move` to a piece *already* in superposition. (See VI. Core Interactions).
* **Entanglement Move (Attack):** Use a **classical move** to attack a square occupied by an opponent's superposition. This **does not** cause a collapse. (See VI. Core Interactions).

---

## V. ⚛️ Quantum Mode (Manipulate the Field)

You choose this mode to sacrifice your move (tempo) to manipulate the quantum state. **You do not move any pieces.** You may perform **one or both** of the following actions:

1.  **Measure a Square:**
    * You declare a measurement on one single square (e.g., "Measure `d5`").
    * All superpositions involving that square are instantly collapsed. (See VI. Core Interactions).
2.  **Apply a Phase Shift:**
    * You choose one of your pieces in superposition and apply a relative phase shift to one of its amplitudes (e.g., multiply the amplitude for $|d5\rangle$ by -1).
    * This "costs a turn" but sets up a future `Interference Move`.

---

## VI. 🔬 Core Quantum Interactions

These are the "physics" of the game, defining how pieces interact.

### Measurement

When a square is measured (via **Quantum Mode**), the game's logic "flips a coin" based on the probabilities.
> **Scenario:** An enemy Knight is at $|\Psi_N\rangle = \frac{1}{\sqrt{2}} |d5\rangle + \frac{1}{\sqrt{2}} |c6\rangle$.
> You **Measure `d5`**.
> * **Outcome A (50% Chance):** Measurement is "Occupied." The Knight's state collapses to $|d5\rangle$ (it is now classical on `d5`). The amplitude for `c6` vanishes.
> * **Outcome B (50% Chance):** Measurement is "Empty." The Knight's state collapses to $|c6\rangle$ (it is now classical on `c6`). The amplitude for `d5` vanishes.

### Entanglement (CNOT)

This happens when you use a **Tempo Mode** action to *attack* an enemy superposition.
> **Scenario:** White Knight is at $|\Psi_{wN}\rangle = \frac{1}{\sqrt{2}} |d5\rangle + \frac{1}{\sqrt{2}} |e4\rangle$. Black Pawn is on `c6`.
> **Black's Action:** Black plays the classical `Entanglement Move` `...c6-d5`.
> **Result:** The system becomes entangled. The new state is:
> $$|\Psi_{\text{System}}\rangle = \underbrace{\frac{1}{\sqrt{2}} |wN_{d5}, bP_{c6}\rangle}_{\text{50% chance: Knight was on d5, Pawn move failed}} + \underbrace{\frac{1}{\sqrt{2}} |wN_{e4}, bP_{d5}\rangle}_{\text{50% chance: Knight was on e4, Pawn move succeeded}}$$



### Interference

This happens when you use an `Interference Move` (a `Quantum Move` on a piece already in superposition).
> **Scenario:** Your Knight is at $|\Psi_N\rangle = \frac{1}{\sqrt{2}} |c3\rangle + \frac{1}{\sqrt{2}} |g3\rangle$. You have previously used **Quantum Mode** to apply a negative phase to the $|g3\rangle$ amplitude, making the state $|\Psi_N\rangle = \frac{1}{\sqrt{2}} |c3\rangle - \frac{1}{\sqrt{2}} |g3\rangle$.
> **Your Action:** You apply an `Interference Move` $U$ that splits both paths to `d5` and `e4`.
> **Result:** The amplitudes for the `d5` square cancel out.
> $$U |\Psi_{N}\rangle = \left( \frac{1}{2} |d5\rangle + \frac{1}{2} |e4\rangle \right) - \left( \frac{1}{2} |d5\rangle - \frac{1}{2} |e4\rangle \right)$$
> $$= (0 \cdot |d5\rangle) + (1 \cdot |e4\rangle) = |e4\rangle$$
> You have successfully created **destructive interference** on `d5` and **constructive interference** on `e4`, forcing your piece to `e4`.



[Image of destructive wave interference]


---

## VII. ⚠️ Key Constraints & Consequences

These are the crucial rules that create the game's strategy.

### No Double Occupancy

A `Quantum Move` is **illegal** if any of its target squares *already* have a non-zero amplitude from *any* other piece. This prevents unmanageable states and is the source of "Gridlock."

### Quantum Gridlock (The Risk of Entanglement)

This is the direct consequence of the `Entanglement Move`.
* In the CNOT example above, the Black Pawn's new state is $|\Psi_{bP}\rangle = \frac{1}{\sqrt{2}}|c6\rangle + \frac{1}{\sqrt{2}}|d5\rangle$.
* **The Gridlock:** This pawn now casts a "quantum shadow" on *both* `c6` and `d5`. Due to the **No Double Occupancy** rule, the Black player **cannot** move their *other* pieces to `c6` or `d5`.
* **Solution:** The Black player is now heavily incentivized to use their next turn in **Quantum Mode** to **Measure** `c6` or `d5` to "un-stick" their pawn.

### Moving an Entangled Piece (Advanced)

If a player tries to move a piece that is *already* entangled (like the White Knight in the CNOT example), the move is applied **conditionally** to the part of the wavefunction where it's "free."
> **Scenario:** The board is in the entangled state from the CNOT. It's White's turn.
> **White's Action:** White tries to move the Knight with a `Quantum Move` $U$ (e.g., from `e4` to `f6` and `g5`).
> **Result (New Entangled State):** The $U$ operation *only* applies to the branch of the wavefunction where the Knight *wasn't* captured (the $|wN_{e4}, bP_{d5}\rangle$ part).
> **New State:**
> $$|\Psi_{\text{NEW}}\rangle = \underbrace{\frac{1}{\sqrt{2}} |wN_{d5}, bP_{c6}\rangle}_{\text{50% Chance: Move failed}} + \underbrace{\frac{1}{2} |wN_{f6}, bP_{d5}\rangle}_{\text{25% Chance: Move succeeded}} + \underbrace{\frac{1}{2} |wN_{g5}, bP_{d5}\rangle}_{\text{25% Chance: Move succeeded}}$$
> This makes the game state exponentially more complex and highlights why using **Quantum Mode** to "clean up" (Measure) an entangled state is often the smarter, safer move.

### Quantum Check

A King is in "Quantum Check" if an opponent's piece has a non-zero amplitude on the King's square. The King *must* escape the check.
* **How to Escape:**
    1.  **Tempo Mode (Move):** Move the King to a safe square.
    2.  **Tempo Mode (Block):** Place a classical piece between the King and the threatening "ghost."
3.  **Quantum Mode (Measure):** Measure the threatening square and *hope* the collapse is "Empty." This is a high-risk gamble.