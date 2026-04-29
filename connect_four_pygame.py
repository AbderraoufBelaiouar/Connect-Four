"""
Connect Four — Pygame UI
Mirrors the web version: dark board, red vs yellow discs,
scoreboard, difficulty selector, animated drops, win highlight.

Requirements:  pip install pygame
Run:           python connect_four_pygame.py
"""

import sys
import math
import time
import pygame

# Import from existing modules
from board import (
    ROWS,
    COLS,
    EMPTY,
    PLAYER1,
    PLAYER2,
    create_board,
    get_valid_columns,
    drop_disc,
    check_winner,
    is_board_full,
)
from minimax import get_best_move

# ─────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────
# Map internal constants to module constants
P1 = PLAYER1  # Human (red)
P2 = PLAYER2  # AI (yellow)

CELL = 80  # px per grid cell
RADIUS = 32  # disc radius
PAD = 10  # board outer padding
HINT_H = 50  # column-hint arrow strip height
SCORE_H = 90  # top score / status bar height
CTRL_H = 50  # bottom controls bar height

W = COLS * CELL + PAD * 2
H = SCORE_H + HINT_H + ROWS * CELL + PAD * 2 + CTRL_H

# ── Colours ──────────────────────────────────
BG = (245, 244, 240)  # page background
BOARD_COL = (26, 58, 107)  # board blue
CELL_COL = (200, 216, 240)  # empty cell
P1_COL = (232, 64, 64)  # red  (human)
P2_COL = (245, 197, 24)  # yellow (AI)
P1_LIGHT = (255, 130, 130)
P2_LIGHT = (255, 224, 100)
WHITE = (255, 255, 255)
DARK_TEXT = (40, 40, 40)
MID_TEXT = (100, 98, 90)
BORDER_COL = (210, 208, 200)
BTN_BG = (230, 228, 220)
BTN_HV = (215, 213, 205)
WIN_PULSE = [(255, 255, 80), (255, 200, 40)]  # alternating pulse frames

DIFF_DEPTHS = {"Beginner": 2, "Intermediate": 4, "Advanced": 6}
DIFF_NAMES = list(DIFF_DEPTHS.keys())


# ─────────────────────────────────────────────
# Helpers: coordinate conversion
# ─────────────────────────────────────────────
BOARD_TOP = SCORE_H + HINT_H + PAD


def cell_center(row, col):
    x = PAD + col * CELL + CELL // 2
    y = BOARD_TOP + row * CELL + CELL // 2
    return x, y


def col_from_x(mx):
    x = mx - PAD
    if x < 0:
        return None
    c = x // CELL
    return c if 0 <= c < COLS else None


# ─────────────────────────────────────────────
# Drawing helpers
# ─────────────────────────────────────────────


def draw_rounded_rect(surf, color, rect, radius=10, border=0, border_color=None):
    pygame.draw.rect(surf, color, rect, border_radius=radius)
    if border and border_color:
        pygame.draw.rect(surf, border_color, rect, border, border_radius=radius)


def draw_text(surf, text, font, color, cx, cy, anchor="center"):
    img = font.render(text, True, color)
    r = img.get_rect()
    if anchor == "center":
        r.center = (cx, cy)
    elif anchor == "left":
        r.midleft = (cx, cy)
    elif anchor == "right":
        r.midright = (cx, cy)
    surf.blit(img, r)


# ─────────────────────────────────────────────
# Drop animation state
# ─────────────────────────────────────────────


class DropAnim:
    DURATION = 0.28  # seconds

    def __init__(self, col, target_row, player):
        self.col = col
        self.target_row = target_row
        self.player = player
        self.start_t = time.time()
        self.done = False

    def y_pos(self):
        t = min(1.0, (time.time() - self.start_t) / self.DURATION)
        # ease-out quad
        t = 1 - (1 - t) ** 2
        start_y = BOARD_TOP - RADIUS
        end_y = cell_center(self.target_row, self.col)[1]
        y = start_y + (end_y - start_y) * t
        if t >= 1.0:
            self.done = True
        return y


# ─────────────────────────────────────────────
# Button widget
# ─────────────────────────────────────────────


class Button:
    def __init__(self, rect, label, font):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.font = font

    def draw(self, surf, mouse_pos):
        hovered = self.rect.collidepoint(mouse_pos)
        bg = BTN_HV if hovered else BTN_BG
        draw_rounded_rect(surf, bg, self.rect, 8, 1, BORDER_COL)
        draw_text(
            surf, self.label, self.font, DARK_TEXT, self.rect.centerx, self.rect.centery
        )

    def is_clicked(self, event):
        return (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        )


# ─────────────────────────────────────────────
# Main Game class
# ─────────────────────────────────────────────


class ConnectFour:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Connect Four — Minimax AI")
        self.screen = pygame.display.set_mode((W, H))
        self.clock = pygame.time.Clock()

        # Fonts
        self.font_lg = pygame.font.SysFont("segoeui,helvetica,arial", 22, bold=True)
        self.font_md = pygame.font.SysFont("segoeui,helvetica,arial", 16)
        self.font_sm = pygame.font.SysFont("segoeui,helvetica,arial", 13)

        # State
        self.scores = {P1: 0, P2: 0, "draw": 0}
        self.diff_idx = 1  # default: Intermediate
        self.anim = None
        self.win_cells = None
        self.pulse_t = 0

        # Controls
        btn_y = H - CTRL_H + 10
        self.btn_new = Button((PAD, btn_y, 130, 30), "New Game", self.font_sm)
        self.btn_diff = Button(
            (W - PAD - 140, btn_y, 140, 30), self._diff_label(), self.font_sm
        )

        self.new_game()

    def _diff_label(self):
        return f"Difficulty: {DIFF_NAMES[self.diff_idx]}"

    def new_game(self):
        self.board = create_board()
        self.current = P1  # human always first
        self.game_over = False
        self.win_cells = None
        self.anim = None
        self.status_msg = ""
        self.hover_col = None

    # ── Update ──────────────────────────────

    def update(self):
        if self.anim:
            _ = self.anim.y_pos()  # advance animation
            if self.anim.done:
                self._finish_move(self.anim.col, self.anim.target_row, self.anim.player)
                self.anim = None

        # AI turn (triggered after human drop anim finishes)
        if not self.game_over and not self.anim and self.current == P2:
            self._do_ai_move()

        # Pulse timer
        self.pulse_t = (self.pulse_t + 1) % 40

    def _drop_with_anim(self, col, player):
        nb, row = drop_disc(self.board, col, player)
        if nb is None:
            return
        self.board = nb
        self.anim = DropAnim(col, row, player)

    def _finish_move(self, col, row, player):
        win = check_winner(self.board, player)
        if win:
            self.win_cells = win
            self.game_over = True
            if player == P1:
                self.scores[P1] += 1
                self.status_msg = "You win!  🎉"
            else:
                self.scores[P2] += 1
                self.status_msg = "AI wins!"
            return
        if is_board_full(self.board):
            self.scores["draw"] += 1
            self.status_msg = "It's a draw!"
            self.game_over = True
            return
        # Switch turn
        self.current = P2 if player == P1 else P1

    def _do_ai_move(self):
        diff = DIFF_NAMES[self.diff_idx].lower()
        col = get_best_move(self.board, P2, diff)
        self._drop_with_anim(col, P2)

    def handle_event(self, event):
        if self.btn_new.is_clicked(event):
            self.new_game()
            return

        if self.btn_diff.is_clicked(event):
            self.diff_idx = (self.diff_idx + 1) % len(DIFF_NAMES)
            self.btn_diff.label = self._diff_label()
            return

        if event.type == pygame.MOUSEMOTION:
            self.hover_col = col_from_x(event.pos[0])

        if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and not self.game_over
            and self.current == P1
            and self.anim is None
        ):
            c = col_from_x(event.pos[0])
            if c is not None and c in get_valid_columns(self.board):
                self._drop_with_anim(c, P1)

    # ── Drawing ─────────────────────────────

    def draw(self):
        self.screen.fill(BG)
        self._draw_score_bar()
        self._draw_hint_row()
        self._draw_board()
        self._draw_controls()
        pygame.display.flip()

    def _draw_score_bar(self):
        card_w, card_h = 110, 64
        gap = 18
        total = card_w * 3 + gap * 2
        sx = (W - total) // 2
        cy = SCORE_H // 2

        labels = [
            ("You  ●", P1_COL, self.scores[P1]),
            ("Draws", MID_TEXT, self.scores["draw"]),
            ("AI   ●", P2_COL, self.scores[P2]),
        ]

        for i, (lbl, col, val) in enumerate(labels):
            x = sx + i * (card_w + gap)
            r = pygame.Rect(x, cy - card_h // 2, card_w, card_h)
            draw_rounded_rect(self.screen, WHITE, r, 10, 1, BORDER_COL)
            # coloured left accent bar
            accent = pygame.Rect(x, cy - card_h // 2 + 8, 3, card_h - 16)
            pygame.draw.rect(self.screen, col, accent, border_radius=2)
            draw_text(
                self.screen, lbl, self.font_sm, MID_TEXT, x + card_w // 2, cy - 14
            )
            draw_text(
                self.screen, str(val), self.font_lg, DARK_TEXT, x + card_w // 2, cy + 14
            )

        # Status / turn indicator
        if self.status_msg:
            msg = self.status_msg
            color = P1_COL if "You" in msg else (P2_COL if "AI" in msg else DARK_TEXT)
        elif self.game_over:
            msg, color = "", DARK_TEXT
        elif self.current == P1:
            msg, color = "Your turn", P1_COL
        else:
            msg, color = "AI thinking...", P2_COL

        draw_text(self.screen, msg, self.font_md, color, W // 2, SCORE_H - 14)

    def _draw_hint_row(self):
        if self.game_over or self.current != P1 or self.anim:
            return
        c = self.hover_col
        if c is not None and c in get_valid_columns(self.board):
            x, _ = cell_center(0, c)
            cy = SCORE_H + HINT_H // 2
            # draw down-triangle
            pts = [(x, cy + 10), (x - 10, cy - 8), (x + 10, cy - 8)]
            pygame.draw.polygon(self.screen, P1_COL, pts)

    def _draw_board(self):
        board_rect = pygame.Rect(0, SCORE_H + HINT_H, W, ROWS * CELL + PAD * 2)
        draw_rounded_rect(self.screen, BOARD_COL, board_rect, 14)

        win_set = set(map(tuple, self.win_cells)) if self.win_cells else set()
        pulse = self.pulse_t < 20  # toggle every 20 frames ≈ 3 Hz

        for r in range(ROWS):
            for c in range(COLS):
                cx, cy = cell_center(r, c)
                val = self.board[r][c]

                if (r, c) in win_set:
                    col = WIN_PULSE[0] if pulse else WIN_PULSE[1]
                elif val == P1:
                    col = P1_COL
                elif val == P2:
                    col = P2_COL
                else:
                    col = CELL_COL

                pygame.draw.circle(self.screen, col, (cx, cy), RADIUS)

        # Draw animated disc on top
        if self.anim:
            cx = cell_center(0, self.anim.col)[0]
            cy = int(self.anim.y_pos())
            col = P1_COL if self.anim.player == P1 else P2_COL
            pygame.draw.circle(self.screen, col, (cx, cy), RADIUS)

    def _draw_controls(self):
        y0 = H - CTRL_H
        pygame.draw.line(self.screen, BORDER_COL, (0, y0), (W, y0), 1)
        mp = pygame.mouse.get_pos()
        self.btn_new.draw(self.screen, mp)
        self.btn_diff.draw(self.screen, mp)

        # Difficulty label in centre
        diff = DIFF_NAMES[self.diff_idx]
        depth = DIFF_DEPTHS[diff]
        draw_text(
            self.screen,
            f"Minimax  ·  depth {depth}",
            self.font_sm,
            MID_TEXT,
            W // 2,
            y0 + CTRL_H // 2,
        )

    # ── Main loop ───────────────────────────

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                self.handle_event(event)

            self.update()
            self.draw()
            self.clock.tick(60)


# ─────────────────────────────────────────────
if __name__ == "__main__":
    ConnectFour().run()
