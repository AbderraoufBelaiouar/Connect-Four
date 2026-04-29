"""
minimax.py — Adversarial Search with Alpha-Beta Pruning + IDDFS
================================================================
Two public entry-points:

  get_best_move(board, ai_player, difficulty)
      Fixed-depth search (Beginner d2 / Intermediate d4 / Advanced d6).
      Used by the CLI and as a guaranteed fallback.

  get_best_move_iddfs(board, ai_player, difficulty,
                      time_limit=None, callback=None)
      Iterative-Deepening Depth-First Search with a wall-clock timer.
      Starts at depth 1 and searches deeper and deeper until the timer
      expires, then returns the best complete result found so far.
      A move is ALWAYS returned (depth-1 is the fallback).

      callback(depth, col, score, elapsed) is called after every completed
      iteration — the pygame UI uses this to update the live depth label.

IDDFS advantages over plain fixed-depth
  - Never exceeds the time budget regardless of board position.
  - Shallower results seed move-ordering for deeper iterations,
    making Alpha-Beta pruning significantly more effective.
  - Automatically deepens on simple positions and shallows on complex ones.
"""

import math
import time
from board import (
    PLAYER1, PLAYER2,
    get_valid_columns, drop_disc,
    check_winner, is_board_full,
)
from heuristic import evaluate_board


# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

FIXED_DEPTHS = {
    "beginner":     2,
    "intermediate": 4,
    "advanced":     6,
}

IDDFS_TIME_LIMITS = {
    "beginner":     1.0,   # 1 s  — shallow, feels snappy
    "intermediate": 3.0,   # 3 s  — meaningful lookahead
    "advanced":     5.0,   # 5 s  — near-optimal, as per assignment spec
}

IDDFS_MAX_DEPTH = 20   # hard cap so we never spin forever on an empty board


# ─────────────────────────────────────────────────────────────────────────────
# Internal — time-aware Minimax
# ─────────────────────────────────────────────────────────────────────────────

class _TimeUp(Exception):
    """Thrown inside the search tree the instant the deadline is breached."""


def _minimax_timed(board, depth, alpha, beta, maximizing,
                   ai_player, difficulty, deadline):
    """
    Minimax with Alpha-Beta pruning + hard deadline.
    Raises _TimeUp when wall-clock >= deadline so the IDDFS loop can
    discard the incomplete result and keep the previous finished one.
    """
    if time.time() >= deadline:
        raise _TimeUp

    human = PLAYER2 if ai_player == PLAYER1 else PLAYER1
    valid = get_valid_columns(board)

    # Terminal / leaf
    if check_winner(board, ai_player):  return  1_000_000 + depth, None
    if check_winner(board, human):      return -1_000_000 - depth, None
    if is_board_full(board):            return  0, None
    if depth == 0:
        return evaluate_board(board, ai_player, difficulty), None

    if maximizing:
        best_score, best_col = -math.inf, valid[len(valid) // 2]
        for col in valid:
            nb, _ = drop_disc(board, col, ai_player)
            score, _ = _minimax_timed(nb, depth-1, alpha, beta,
                                      False, ai_player, difficulty, deadline)
            if score > best_score:
                best_score, best_col = score, col
            alpha = max(alpha, best_score)
            if alpha >= beta:
                break
        return best_score, best_col
    else:
        best_score, best_col = math.inf, valid[len(valid) // 2]
        for col in valid:
            nb, _ = drop_disc(board, col, human)
            score, _ = _minimax_timed(nb, depth-1, alpha, beta,
                                      True, ai_player, difficulty, deadline)
            if score < best_score:
                best_score, best_col = score, col
            beta = min(beta, best_score)
            if alpha >= beta:
                break
        return best_score, best_col


# ─────────────────────────────────────────────────────────────────────────────
# Public API 1 — Fixed-depth (backward-compatible, used by CLI)
# ─────────────────────────────────────────────────────────────────────────────

def minimax(board, depth, alpha, beta, maximizing_player,
            ai_player, difficulty):
    """
    Classic Minimax with Alpha-Beta pruning, no time limit.
    Kept for full backward-compatibility with players.py and main.py.
    """
    human = PLAYER2 if ai_player == PLAYER1 else PLAYER1
    valid = get_valid_columns(board)

    if check_winner(board, ai_player):  return  1_000_000 + depth, None
    if check_winner(board, human):      return -1_000_000 - depth, None
    if is_board_full(board):            return  0, None
    if depth == 0:
        return evaluate_board(board, ai_player, difficulty), None

    if maximizing_player:
        best_score, best_col = -math.inf, valid[len(valid) // 2]
        for col in valid:
            nb, _ = drop_disc(board, col, ai_player)
            score, _ = minimax(nb, depth-1, alpha, beta,
                               False, ai_player, difficulty)
            if score > best_score:
                best_score, best_col = score, col
            alpha = max(alpha, best_score)
            if alpha >= beta:
                break
        return best_score, best_col
    else:
        best_score, best_col = math.inf, valid[len(valid) // 2]
        for col in valid:
            nb, _ = drop_disc(board, col, human)
            score, _ = minimax(nb, depth-1, alpha, beta,
                               True, ai_player, difficulty)
            if score < best_score:
                best_score, best_col = score, col
            beta = min(beta, best_score)
            if alpha >= beta:
                break
        return best_score, best_col


def get_best_move(board, ai_player, difficulty):
    """Fixed-depth entry point used by the CLI / players.py."""
    depth = FIXED_DEPTHS.get(difficulty, 4)
    _, col = minimax(board, depth, -math.inf, math.inf,
                     True, ai_player, difficulty)
    return col


# ─────────────────────────────────────────────────────────────────────────────
# Public API 2 — IDDFS with time budget  (GUI uses this)
# ─────────────────────────────────────────────────────────────────────────────

def get_best_move_iddfs(board, ai_player, difficulty,
                        time_limit=None, callback=None):
    """
    Iterative-Deepening search bounded by a wall-clock timer.

    Parameters
    ----------
    board       : current 2-D board state
    ai_player   : PLAYER1 or PLAYER2
    difficulty  : 'beginner' | 'intermediate' | 'advanced'
    time_limit  : seconds allowed; None => use IDDFS_TIME_LIMITS table
    callback    : optional callable(depth, col, score, elapsed)
                  called after each COMPLETED depth iteration so the UI
                  can show live progress.

    Returns
    -------
    best_col : int        — column index of the best move found
    stats    : dict       — depth_reached, score, elapsed
    """
    if time_limit is None:
        time_limit = IDDFS_TIME_LIMITS.get(difficulty, 5.0)

    start    = time.time()
    deadline = start + time_limit

    # Safe fallback: centre column (or first valid)
    valid         = get_valid_columns(board)
    best_col      = valid[len(valid) // 2]
    best_score    = -math.inf
    depth_reached = 0

    for depth in range(1, IDDFS_MAX_DEPTH + 1):
        try:
            score, col = _minimax_timed(
                board, depth,
                -math.inf, math.inf,
                True, ai_player, difficulty,
                deadline,
            )
        except _TimeUp:
            # Depth not finished — discard partial result, keep previous
            break

        # Full depth completed — promote result
        best_col      = col
        best_score    = score
        depth_reached = depth
        elapsed       = time.time() - start

        if callback:
            try:
                callback(depth, col, score, elapsed)
            except Exception:
                pass   # never let a UI callback crash the search

        # Definitive win found — no need to search deeper
        if best_score >= 1_000_000:
            break

        # Budget nearly exhausted — stop before starting a depth that will
        # almost certainly be interrupted (saves wasted work)
        if time.time() >= deadline - 0.05:
            break

    elapsed = time.time() - start
    return best_col, {
        "depth_reached": depth_reached,
        "score":         best_score,
        "elapsed":       round(elapsed, 3),
    }
