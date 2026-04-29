"""
main.py - Game Entry Point (CLI)
Manages difficulty selection, turn order, the game loop, and match scoring.

Run:  python main.py
"""

import os

from board import (
    create_board, print_board,
    drop_disc, check_winner, is_board_full,
    PLAYER1, PLAYER2,
)
from players import HumanPlayer, AIPlayer


# ──────────────────────────────────────────────
# Display Helpers
# ──────────────────────────────────────────────

def clear_screen():
    """Clear the terminal for a cleaner display."""
    os.system("cls" if os.name == "nt" else "clear")


def print_banner():
    print("=" * 45)
    print("        CONNECT FOUR — Adversarial AI")
    print("         Minimax + Alpha-Beta Pruning")
    print("=" * 45)


def print_score(scores):
    print(
        f"\n  Score  →  You: {scores['human']}  |  "
        f"AI: {scores['ai']}  |  Draws: {scores['draw']}"
    )
    print()


# ──────────────────────────────────────────────
# Setup
# ──────────────────────────────────────────────

def choose_difficulty():
    """Ask the player to select an AI difficulty level."""
    options = {
        "1": "beginner",
        "2": "intermediate",
        "3": "advanced",
    }
    print("\n  Select AI difficulty:")
    print("    1. Beginner     (depth 2 — mostly random mistakes)")
    print("    2. Intermediate (depth 4 — understands threats)")
    print("    3. Advanced     (depth 6 — near-optimal play)")
    while True:
        choice = input("\n  Enter 1 / 2 / 3: ").strip()
        if choice in options:
            return options[choice]
        print("  Invalid choice. Enter 1, 2, or 3.")


def choose_who_goes_first():
    """Ask whether the human or AI plays first (PLAYER1)."""
    print("\n  Who goes first?")
    print("    1. You (X)")
    print("    2. AI  (O)")
    while True:
        choice = input("\n  Enter 1 or 2: ").strip()
        if choice == "1":
            return "human"
        if choice == "2":
            return "ai"
        print("  Please enter 1 or 2.")


# ──────────────────────────────────────────────
# Single Round
# ──────────────────────────────────────────────

def play_round(human_player, ai_player, human_goes_first):
    """
    Run a single game round.
    Returns 'human', 'ai', or 'draw'.
    """
    board = create_board()
    turn_order = (
        [human_player, ai_player] if human_goes_first
        else [ai_player, human_player]
    )
    turn_index = 0

    while True:
        clear_screen()
        print_banner()
        print_board(board)

        current = turn_order[turn_index % 2]
        col = current.get_move(board)

        new_board, _ = drop_disc(board, col, current.player_id)
        if new_board is None:
            print("  Invalid move — column is full!")
            continue
        board = new_board

        win_cells = check_winner(board, current.player_id)
        if win_cells:
            clear_screen()
            print_banner()
            print_board(board)
            if current is human_player:
                print("\n  *** YOU WIN! Congratulations! ***\n")
                return "human"
            else:
                print("\n  *** AI WINS! Better luck next time. ***\n")
                return "ai"

        if is_board_full(board):
            clear_screen()
            print_banner()
            print_board(board)
            print("\n  *** IT'S A DRAW! ***\n")
            return "draw"

        turn_index += 1


# ──────────────────────────────────────────────
# Main Loop
# ──────────────────────────────────────────────

def main():
    clear_screen()
    print_banner()

    difficulty = choose_difficulty()
    first = choose_who_goes_first()

    human_id = PLAYER1 if first == "human" else PLAYER2
    ai_id    = PLAYER2 if first == "human" else PLAYER1

    human_player = HumanPlayer(human_id, name="You")
    ai_player    = AIPlayer(ai_id, difficulty=difficulty, name="AI")

    scores = {"human": 0, "ai": 0, "draw": 0}

    while True:
        result = play_round(
            human_player, ai_player,
            human_goes_first=(first == "human"),
        )
        scores[result] += 1
        print_score(scores)

        again = input("  Play again? (y/n): ").strip().lower()
        if again != "y":
            print("\n  Thanks for playing! Final scores:")
            print_score(scores)
            break

        switch = input("  Switch who goes first? (y/n): ").strip().lower()
        if switch == "y":
            first = "ai" if first == "human" else "human"
            human_id = PLAYER1 if first == "human" else PLAYER2
            ai_id    = PLAYER2 if first == "human" else PLAYER1
            human_player = HumanPlayer(human_id, name="You")
            ai_player    = AIPlayer(ai_id, difficulty=difficulty, name="AI")


if __name__ == "__main__":
    main()
