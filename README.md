# Connect Four — Adversarial AI

A classic Connect Four game with a Minimax + Alpha-Beta Pruning AI, available in both a terminal (CLI) and a graphical (Pygame) interface.

---

## Features

- **Minimax with Alpha-Beta Pruning** — efficient adversarial search that prunes branches provably unable to affect the result.
- **Three difficulty levels** — Beginner (depth 2), Intermediate (depth 4), Advanced (depth 6).
- **Two interfaces** — a lightweight terminal UI and a full Pygame GUI with animations, a scoreboard, and a column-hover hint.
- **Modular architecture** — board logic, heuristics, search, and players are fully separated.

---

## Project Structure

```
Connect-Four/
├── board.py                # Board state, move validation, win detection
├── heuristic.py            # Board evaluation / utility function (3 difficulty levels)
├── minimax.py              # Minimax algorithm with Alpha-Beta pruning
├── players.py              # HumanPlayer and AIPlayer classes
├── main.py                 # CLI entry point
└── connect_four_pygame.py  # Pygame GUI entry point
```

---

## Requirements

```
pip install pygame   # only needed for the GUI version
```

---

## Running the Game

### Terminal (CLI)
```bash
python main.py
```

### Pygame GUI
```bash
python connect_four_pygame.py
```

---

## How It Works

### Board (`board.py`)
- 6 × 7 grid represented as a 2-D list.
- `drop_disc` returns a **new** board (immutable updates) to keep the search tree clean.
- `check_winner` scans all four directions and returns the winning cell coordinates (used for win highlighting in the GUI).

### Heuristic (`heuristic.py`)
| Difficulty   | Strategy |
|---|---|
| Beginner     | Centre-column occupancy only |
| Intermediate | All 4-cell windows (horizontal, vertical, diagonal) + centre bonus |
| Advanced     | Intermediate + near-centre column bonuses (cols 2–4) |

### Minimax (`minimax.py`)
- Alpha-Beta pruning cuts branches where `α ≥ β`.
- Terminal states return ±1,000,000 with a depth bonus to prefer **faster** wins and **slower** losses.
- `get_best_move` is the single public entry point.

---

## AI Difficulty Guide

| Level        | Search Depth | Character |
|---|---|---|
| Beginner     | 2 | Makes obvious mistakes; good for learning |
| Intermediate | 4 | Blocks threats and builds two-in-a-rows |
| Advanced     | 6 | Near-optimal; very hard to beat |