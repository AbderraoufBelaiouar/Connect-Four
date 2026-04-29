"""
board.py - Game Board Representation and Core Logic
Handles the 2D array, move validation, and win-checking logic.
"""

ROWS = 6
COLS = 7
EMPTY = 0
PLAYER1 = 1
PLAYER2 = 2


def create_board():
    """Initialize a 6x7 board filled with EMPTY (0)."""
    return [[EMPTY for _ in range(COLS)] for _ in range(ROWS)]


def print_board(board):
    """Print the board in a human-readable format."""
    print("\n  " + "   ".join(str(c) for c in range(COLS)))
    print("  " + "---" * COLS)
    for row in board:
        print("| " + " | ".join(_cell_char(cell) for cell in row) + " |")
    print("  " + "---" * COLS)
    print()


def _cell_char(cell):
    """Return display character for a cell value."""
    if cell == PLAYER1:
        return "X"
    elif cell == PLAYER2:
        return "O"
    return "."


def get_valid_columns(board):
    """Return list of columns that are not full."""
    return [c for c in range(COLS) if board[0][c] == EMPTY]


def is_valid_column(board, col):
    """Check if a column index is valid and not full."""
    if col < 0 or col >= COLS:
        return False
    return board[0][col] == EMPTY


def drop_disc(board, col, player):
    """
    Drop a disc into the given column for the given player.
    Returns (new_board, row) or (None, None) if invalid.
    The disc falls to the lowest available row.
    """
    if not is_valid_column(board, col):
        return None, None
    # Deep copy the board so the original is unchanged
    new_board = [row[:] for row in board]
    for r in range(ROWS - 1, -1, -1):
        if new_board[r][col] == EMPTY:
            new_board[r][col] = player
            return new_board, r
    return None, None


def check_winner(board, player):
    """
    Check if the given player has four in a row.
    Returns list of winning cell coordinates [(r,c), ...] or None.
    Checks horizontal, vertical, and both diagonals.
    """
    # Horizontal
    for r in range(ROWS):
        for c in range(COLS - 3):
            if all(board[r][c + i] == player for i in range(4)):
                return [(r, c + i) for i in range(4)]

    # Vertical
    for r in range(ROWS - 3):
        for c in range(COLS):
            if all(board[r + i][c] == player for i in range(4)):
                return [(r + i, c) for i in range(4)]

    # Diagonal down-right (\)
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            if all(board[r + i][c + i] == player for i in range(4)):
                return [(r + i, c + i) for i in range(4)]

    # Diagonal up-right (/)
    for r in range(3, ROWS):
        for c in range(COLS - 3):
            if all(board[r - i][c + i] == player for i in range(4)):
                return [(r - i, c + i) for i in range(4)]

    return None


def is_board_full(board):
    """Return True if no empty cells remain (draw condition)."""
    return all(board[0][c] != EMPTY for c in range(COLS))


def is_terminal(board):
    """Return True if the game is over (win or draw)."""
    return (
        check_winner(board, PLAYER1) is not None
        or check_winner(board, PLAYER2) is not None
        or is_board_full(board)
    )
