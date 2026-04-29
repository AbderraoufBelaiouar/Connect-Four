"""
heuristic.py - Board Evaluation / Utility Function
Scores non-terminal board states to guide the Minimax search.
Supports three difficulty levels with increasing heuristic sophistication.
"""

from board import ROWS, COLS, EMPTY, PLAYER1, PLAYER2


def score_window(window, player):
    """
    Score a 4-cell window for the given player.
    Rewards threats and penalises opponent threats.
    """
    opponent = PLAYER2 if player == PLAYER1 else PLAYER1

    player_count = window.count(player)
    empty_count  = window.count(EMPTY)
    opp_count    = window.count(opponent)

    if player_count == 4:
        return 100
    elif player_count == 3 and empty_count == 1:
        return 5        # One away from winning
    elif player_count == 2 and empty_count == 2:
        return 2        # Two away from winning
    elif opp_count == 3 and empty_count == 1:
        return -4       # Opponent is one away — must block
    elif opp_count == 4:
        return -100     # Opponent has won (shouldn't occur in normal flow)
    return 0


def _scan_all_windows(board, player):
    """
    Iterate over every possible 4-cell window on the board
    (horizontal, vertical, both diagonals) and return their total score.
    """
    score = 0

    # Horizontal
    for r in range(ROWS):
        for c in range(COLS - 3):
            window = [board[r][c + i] for i in range(4)]
            score += score_window(window, player)

    # Vertical
    for c in range(COLS):
        for r in range(ROWS - 3):
            window = [board[r + i][c] for i in range(4)]
            score += score_window(window, player)

    # Diagonal down-right (\)
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            window = [board[r + i][c + i] for i in range(4)]
            score += score_window(window, player)

    # Diagonal up-right (/)
    for r in range(3, ROWS):
        for c in range(COLS - 3):
            window = [board[r - i][c + i] for i in range(4)]
            score += score_window(window, player)

    return score


def _center_column_bonus(board, player, weight=3):
    """Return a bonus for occupying the center column."""
    center_col = [board[r][COLS // 2] for r in range(ROWS)]
    return center_col.count(player) * weight


def evaluate_board_beginner(board, player):
    """
    Beginner heuristic: only rewards center column control.
    Makes the AI look for immediate wins/blocks but misses
    longer-term strategy — behaves somewhat randomly.
    """
    return _center_column_bonus(board, player)


def evaluate_board_intermediate(board, player):
    """
    Intermediate heuristic: evaluates all 4-cell windows across
    the board. Understands runs of 2 or 3 and centre control.
    """
    score = _center_column_bonus(board, player)
    score += _scan_all_windows(board, player)
    return score


def evaluate_board_advanced(board, player):
    """
    Advanced heuristic: all windows + adjacent-column bonuses.
    Rewards controlling columns near the centre for maximum
    connectivity potential.
    """
    score = evaluate_board_intermediate(board, player)

    # Extra bonus for near-centre columns (cols 2, 3, 4)
    for col in [2, 3, 4]:
        col_vals = [board[r][col] for r in range(ROWS)]
        score += col_vals.count(player)

    return score


# ──────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────

_EVALUATORS = {
    "beginner":     evaluate_board_beginner,
    "intermediate": evaluate_board_intermediate,
    "advanced":     evaluate_board_advanced,
}


def evaluate_board(board, player, difficulty):
    """
    Dispatch to the appropriate heuristic based on difficulty level.

    Parameters:
        board      : current 2D board state
        player     : which player to evaluate for (PLAYER1 or PLAYER2)
        difficulty : 'beginner', 'intermediate', or 'advanced'

    Returns:
        Score (int) for the given board state.
    """
    evaluator = _EVALUATORS.get(difficulty, evaluate_board_intermediate)
    return evaluator(board, player)
