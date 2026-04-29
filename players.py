"""
players.py - Player Classes
HumanPlayer: reads input from the console.
AIPlayer: uses Minimax to choose moves.
"""

from board import is_valid_column, get_valid_columns, PLAYER1, PLAYER2
from minimax import get_best_move


class HumanPlayer:
    """
    Represents a human player.
    Prompts the user to enter a column number and validates the input.
    """

    def __init__(self, player_id, name="Human"):
        self.player_id = player_id   # PLAYER1 or PLAYER2
        self.name = name
        self.symbol = "X" if player_id == PLAYER1 else "O"

    def get_move(self, board):
        """
        Ask the human to enter a column (0–6) and validate it.
        Repeats until a valid column is provided.
        """
        valid = get_valid_columns(board)
        while True:
            try:
                col = int(input(f"{self.name} ({self.symbol}), choose a column {valid}: "))
                if is_valid_column(board, col):
                    return col
                else:
                    print(f"  Column {col} is full or invalid. Try again.")
            except ValueError:
                print("  Please enter a number between 0 and 6.")


class AIPlayer:
    """
    Represents the AI opponent.
    Uses Minimax with Alpha-Beta pruning to choose the optimal move.

    Difficulty levels control search depth and heuristic complexity:
      beginner     — depth 2, basic center heuristic
      intermediate — depth 4, full window scoring
      advanced     — depth 6, extended positional awareness
    """

    DIFFICULTY_LABELS = {
        "beginner":     "Beginner     (depth 2)",
        "intermediate": "Intermediate (depth 4)",
        "advanced":     "Advanced     (depth 6)",
    }

    def __init__(self, player_id, difficulty="intermediate", name="AI"):
        self.player_id = player_id
        self.difficulty = difficulty
        self.name = name
        self.symbol = "X" if player_id == PLAYER1 else "O"

    def get_move(self, board):
        """Use Minimax to find and return the best column."""
        print(f"\n  {self.name} ({self.symbol}) is thinking "
              f"[{self.DIFFICULTY_LABELS[self.difficulty]}]...")
        col = get_best_move(board, self.player_id, self.difficulty)
        print(f"  {self.name} plays column {col}.")
        return col
