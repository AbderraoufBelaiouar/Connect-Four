"""
minimax.py - Adversarial Search with Alpha-Beta Pruning
Implements the Minimax algorithm that powers the AI opponent.
Alpha-Beta pruning eliminates branches that cannot affect the result,
dramatically reducing the number of nodes evaluated.
"""

import math
from board import (
    ROWS, COLS, PLAYER1, PLAYER2,
    get_valid_columns, drop_disc,
    check_winner, is_board_full
)
from heuristic import evaluate_board


def minimax(board, depth, alpha, beta, maximizing_player, ai_player, difficulty):
    """
    Minimax algorithm with Alpha-Beta pruning.

    Parameters:
        board            : current 2D board state
        depth            : remaining search depth
        alpha            : best score the maximizer can guarantee (starts -inf)
        beta             : best score the minimizer can guarantee (starts +inf)
        maximizing_player: True if it's the AI's turn
        ai_player        : which player the AI controls (PLAYER1 or PLAYER2)
        difficulty       : 'beginner' | 'intermediate' | 'advanced'

    Returns:
        (score, best_column) — score of the best move, and which column it is.
        At depth > 0 internal calls, column is None (not needed).
    """
    human_player = PLAYER2 if ai_player == PLAYER1 else PLAYER1
    valid_cols = get_valid_columns(board)

    # --- Terminal / base cases ---
    ai_win = check_winner(board, ai_player)
    if ai_win:
        # Very large score; depth bonus rewards faster wins
        return (1_000_000 + depth, None)

    human_win = check_winner(board, human_player)
    if human_win:
        return (-1_000_000 - depth, None)

    if is_board_full(board):
        return (0, None)

    if depth == 0:
        return (evaluate_board(board, ai_player, difficulty), None)

    # --- Recursive Minimax ---
    if maximizing_player:
        best_score = -math.inf
        best_col = valid_cols[len(valid_cols) // 2]  # default: center
        for col in valid_cols:
            new_board, _ = drop_disc(board, col, ai_player)
            score, _ = minimax(new_board, depth - 1, alpha, beta, False, ai_player, difficulty)
            if score > best_score:
                best_score = score
                best_col = col
            alpha = max(alpha, best_score)
            if alpha >= beta:   # Beta cutoff — prune remaining branches
                break
        return (best_score, best_col)

    else:  # Minimizing player (human's perspective)
        best_score = math.inf
        best_col = valid_cols[len(valid_cols) // 2]
        for col in valid_cols:
            new_board, _ = drop_disc(board, col, human_player)
            score, _ = minimax(new_board, depth - 1, alpha, beta, True, ai_player, difficulty)
            if score < best_score:
                best_score = score
                best_col = col
            beta = min(beta, best_score)
            if alpha >= beta:   # Alpha cutoff — prune remaining branches
                break
        return (best_score, best_col)


def get_best_move(board, ai_player, difficulty):
    """
    Entry point for the AI: returns the best column to play.
    Searches to the depth defined by the difficulty level.
    """
    depth_map = {
        "beginner":     2,
        "intermediate": 4,
        "advanced":     6,
    }
    depth = depth_map[difficulty]
    _, best_col = minimax(board, depth, -math.inf, math.inf, True, ai_player, difficulty)
    return best_col
