"""
Connect Four — Premium Pygame UI  (v3 — IDDFS)
Dark theme, glossy discs, glow effects, particle burst on win,
animated drop with bounce, AI thinking indicator.

New in v3
  - IDDFS (Iterative-Deepening) replaces fixed-depth search in the GUI
  - Live depth counter updates as AI searches deeper each iteration
  - Time-budget label in controls bar (replaces fixed-depth label)
  - Keyboard shortcuts: R=new game  1/2/3=difficulty  Q=quit

Requirements:  pip install pygame
Run:           python connect_four_pygame_v3.py
"""

import sys
import math
import time
import random
import pygame

from board import (
    ROWS, COLS, EMPTY, PLAYER1, PLAYER2,
    create_board, get_valid_columns,
    drop_disc, check_winner, is_board_full,
)
from minimax import get_best_move, get_best_move_iddfs, IDDFS_TIME_LIMITS

# ─────────────────────────────────────────────────────────────────────────────
# Layout constants
# ─────────────────────────────────────────────────────────────────────────────
P1 = PLAYER1   # Human  — crimson red
P2 = PLAYER2   # AI     — golden yellow

CELL    = 84    # px per grid cell
RADIUS  = 34    # disc radius
PAD     = 12    # board outer padding
HINT_H  = 56    # column-hint strip height (hover preview)
SCORE_H = 110   # top score/status bar height
CTRL_H  = 56    # bottom controls bar height

W = COLS * CELL + PAD * 2
H = SCORE_H + HINT_H + ROWS * CELL + PAD * 2 + CTRL_H

BOARD_TOP = SCORE_H + HINT_H + PAD

# ─────────────────────────────────────────────────────────────────────────────
# Colour Palette  (dark premium theme)
# ─────────────────────────────────────────────────────────────────────────────
BG_TOP        = (10,  14,  26)   # deep midnight at the top
BG_BOT        = (18,  24,  48)   # slightly lighter navy at the bottom

BOARD_COL     = (15,  35,  75)   # board panel — deep ocean blue
BOARD_EDGE    = (22,  52, 110)   # board border highlight
HOLE_EMPTY    = (8,   18,  42)   # empty cell — near-black indigo
HOLE_SHADOW   = (4,    9,  22)   # inner shadow ring on empty cells

P1_COL        = (230,  55,  70)  # human — vibrant crimson
P1_LIGHT      = (255, 120, 130)  # highlight ring
P1_GLOW       = (230,  55,  70, 80)

P2_COL        = (245, 195,  25)  # AI — warm gold
P2_LIGHT      = (255, 230, 130)
P2_GLOW       = (245, 195,  25, 80)

WHITE         = (255, 255, 255)
TEXT_PRIMARY  = (220, 225, 240)
TEXT_DIM      = (120, 130, 155)

CARD_BG       = (22,  30,  60)
CARD_BORDER   = (38,  52,  95)

BTN_BG        = (28,  38,  75)
BTN_HV        = (38,  55, 105)
BTN_BORDER    = (55,  75, 140)
BTN_TEXT      = (200, 210, 235)

WIN_GLOW_A    = (255, 240,  60)
WIN_GLOW_B    = (255, 180,  20)

SEPARATOR     = (30,  42,  80)

DIFF_DEPTHS = {"Beginner": 2, "Intermediate": 4, "Advanced": 6}
DIFF_NAMES  = list(DIFF_DEPTHS.keys())
DIFF_TIMES  = {"Beginner": 1.0, "Intermediate": 3.0, "Advanced": 5.0}

# ─────────────────────────────────────────────────────────────────────────────
# Low-level drawing helpers
# ─────────────────────────────────────────────────────────────────────────────

def lerp_color(c1, c2, t):
    """Linearly interpolate between two RGB colours."""
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def draw_gradient_rect(surf, top_color, bot_color, rect):
    """Draw a vertical gradient over `rect` using horizontal lines."""
    x, y, w, h = rect
    for dy in range(h):
        t = dy / max(h - 1, 1)
        col = lerp_color(top_color, bot_color, t)
        pygame.draw.line(surf, col, (x, y + dy), (x + w - 1, y + dy))


def draw_rounded_rect(surf, color, rect, radius=10, border=0, border_color=None):
    pygame.draw.rect(surf, color, rect, border_radius=radius)
    if border and border_color:
        pygame.draw.rect(surf, border_color, rect, border, border_radius=radius)


def draw_text(surf, text, font, color, cx, cy, anchor="center"):
    img = font.render(text, True, color)
    r   = img.get_rect()
    if anchor == "center":
        r.center   = (cx, cy)
    elif anchor == "left":
        r.midleft  = (cx, cy)
    elif anchor == "right":
        r.midright = (cx, cy)
    surf.blit(img, r)


def draw_glow_circle(surf, color, center, radius, glow_radius, alpha=80):
    """Draw a soft radial glow behind a disc using a temporary surface."""
    glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
    for r in range(glow_radius, 0, -1):
        a = int(alpha * (1 - r / glow_radius) ** 1.5)
        pygame.draw.circle(glow_surf, (*color[:3], a), (glow_radius, glow_radius), r)
    surf.blit(glow_surf, (center[0] - glow_radius, center[1] - glow_radius))


def draw_glossy_disc(surf, color, light_color, center, radius):
    """Draw a filled disc with a highlight ring and inner shine spot."""
    cx, cy = center

    # Base disc
    pygame.draw.circle(surf, color, (cx, cy), radius)

    # Outer thin highlight ring
    pygame.draw.circle(surf, light_color, (cx, cy), radius, 2)

    # Inner shine — small bright ellipse offset up-left
    shine_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    shine_r = max(6, radius // 3)
    shine_x = radius - radius // 4
    shine_y = radius - radius // 4
    pygame.draw.ellipse(
        shine_surf,
        (255, 255, 255, 55),
        (shine_x - shine_r, shine_y - shine_r, shine_r * 2, shine_r),
    )
    surf.blit(shine_surf, (cx - radius, cy - radius))


# ─────────────────────────────────────────────────────────────────────────────
# Drop animation  (bounce easing)
# ─────────────────────────────────────────────────────────────────────────────

class DropAnim:
    DURATION = 0.35  # seconds for base travel
    BOUNCE   = 0.08  # fraction that bounces back

    def __init__(self, col, target_row, player):
        self.col        = col
        self.target_row = target_row
        self.player     = player
        self.start_t    = time.time()
        self.done       = False

    def y_pos(self):
        elapsed = time.time() - self.start_t
        t = min(1.0, elapsed / self.DURATION)
        # Bounce easing: ease-out with a small overshoot
        if t < 0.85:
            ease = 1 - (1 - t / 0.85) ** 3
        else:
            # tiny bounce back
            sub = (t - 0.85) / 0.15
            ease = 1.0 + math.sin(sub * math.pi) * self.BOUNCE

        start_y = BOARD_TOP - RADIUS * 2
        end_y   = cell_center(self.target_row, self.col)[1]
        y = start_y + (end_y - start_y) * ease
        if t >= 1.0:
            self.done = True
        return y


# ─────────────────────────────────────────────────────────────────────────────
# Particle system  (confetti burst on win)
# ─────────────────────────────────────────────────────────────────────────────

class Particle:
    def __init__(self, x, y, color):
        angle   = random.uniform(0, 2 * math.pi)
        speed   = random.uniform(3, 9)
        self.x  = float(x)
        self.y  = float(y)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed - random.uniform(2, 5)
        self.life   = 1.0
        self.decay  = random.uniform(0.012, 0.028)
        self.size   = random.randint(4, 9)
        self.color  = color
        self.gravity = 0.25

    def update(self):
        self.vy   += self.gravity
        self.x    += self.vx
        self.y    += self.vy
        self.life -= self.decay
        self.vx   *= 0.98

    def draw(self, surf):
        if self.life <= 0:
            return
        alpha = int(255 * max(0, self.life))
        s = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        col = (*self.color[:3], alpha)
        pygame.draw.rect(s, col, (0, 0, self.size, self.size), border_radius=2)
        surf.blit(s, (int(self.x), int(self.y)))

    @property
    def alive(self):
        return self.life > 0


# ─────────────────────────────────────────────────────────────────────────────
# Button widget
# ─────────────────────────────────────────────────────────────────────────────

class Button:
    def __init__(self, rect, label, font):
        self.rect  = pygame.Rect(rect)
        self.label = label
        self.font  = font

    def draw(self, surf, mouse_pos):
        hovered = self.rect.collidepoint(mouse_pos)
        bg = BTN_HV if hovered else BTN_BG
        draw_rounded_rect(surf, bg, self.rect, 10, 1, BTN_BORDER)
        if hovered:
            # subtle inner highlight line at top
            hi = pygame.Rect(self.rect.x + 2, self.rect.y + 1, self.rect.width - 4, 2)
            pygame.draw.rect(surf, (80, 110, 180), hi, border_radius=2)
        draw_text(surf, self.label, self.font, BTN_TEXT, self.rect.centerx, self.rect.centery)

    def is_clicked(self, event):
        return (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        )


# ─────────────────────────────────────────────────────────────────────────────
# Coordinate helpers
# ─────────────────────────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────────────────────────
# Main Game class
# ─────────────────────────────────────────────────────────────────────────────

class ConnectFour:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Connect Four  ·  Minimax AI")
        self.screen = pygame.display.set_mode((W, H))
        self.clock  = pygame.time.Clock()

        # Background surface (pre-rendered gradient to avoid per-frame cost)
        self._bg = pygame.Surface((W, H))
        draw_gradient_rect(self._bg, BG_TOP, BG_BOT, (0, 0, W, H))

        # Fonts
        self.font_xl = pygame.font.SysFont("segoeui,helvetica,arial", 26, bold=True)
        self.font_lg = pygame.font.SysFont("segoeui,helvetica,arial", 20, bold=True)
        self.font_md = pygame.font.SysFont("segoeui,helvetica,arial", 15)
        self.font_sm = pygame.font.SysFont("segoeui,helvetica,arial", 13)

        # Persistent state
        self.scores  = {P1: 0, P2: 0, "draw": 0}
        self.diff_idx = 1   # default: Intermediate
        self.pulse_t  = 0
        self.frame    = 0

        # Particles
        self.particles: list[Particle] = []

        # Controls — placed in bottom bar
        btn_y = H - CTRL_H + 13
        self.btn_new  = Button((PAD + 4,  btn_y, 140, 32), "⟳  New Game",  self.font_sm)
        self.btn_diff = Button((W - PAD - 160, btn_y, 156, 32),
                               self._diff_label(), self.font_sm)

        self.new_game()

    # ── Helpers ───────────────────────────────────

    def _diff_label(self):
        return f"⚙  {DIFF_NAMES[self.diff_idx]}"

    def new_game(self):
        self.board      = create_board()
        self.current    = P1
        self.game_over  = False
        self.win_cells  = None
        self.anim       = None
        self.status_msg = ""
        self.hover_col  = None
        self.particles.clear()
        self.ai_thinking   = False
        # IDDFS live state
        self.iddfs_depth   = 0      # deepest completed iteration
        self.iddfs_score   = 0
        self.iddfs_elapsed = 0.0
        self.iddfs_col     = None

    # ── Update ────────────────────────────────────

    def update(self):
        self.frame += 1

        # Advance drop animation
        if self.anim:
            self.anim.y_pos()   # side-effects: sets .done
            if self.anim.done:
                self._finish_move(self.anim.col, self.anim.target_row, self.anim.player)
                self.anim = None

        # AI turn
        if not self.game_over and not self.anim and self.current == P2:
            self.ai_thinking = True
            self._do_ai_move()
            self.ai_thinking = False

        # Pulse / animation counters
        self.pulse_t = (self.pulse_t + 1) % 60

        # Update particles
        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.alive]

    def _drop_with_anim(self, col, player):
        nb, row = drop_disc(self.board, col, player)
        if nb is None:
            return
        self.board = nb
        self.anim  = DropAnim(col, row, player)

    def _finish_move(self, col, row, player):
        win = check_winner(self.board, player)
        if win:
            self.win_cells  = win
            self.game_over  = True
            if player == P1:
                self.scores[P1] += 1
                self.status_msg  = "You win!  🎉"
            else:
                self.scores[P2] += 1
                self.status_msg  = "AI wins!"
            self._spawn_particles(win, player)
            return
        if is_board_full(self.board):
            self.scores["draw"] += 1
            self.status_msg = "It's a draw!"
            self.game_over  = True
            return
        self.current = P2 if player == P1 else P1

    def _do_ai_move(self):
        diff = DIFF_NAMES[self.diff_idx].lower()
        tl   = IDDFS_TIME_LIMITS.get(diff, 5.0)

        def _cb(depth, col, score, elapsed):
            """Called by IDDFS after each completed depth iteration."""
            self.iddfs_depth   = depth
            self.iddfs_score   = score
            self.iddfs_elapsed = elapsed
            self.iddfs_col     = col
            # Redraw so the depth counter updates live
            self.draw()
            pygame.event.pump()   # keep OS from thinking the window froze

        col, stats = get_best_move_iddfs(
            self.board, P2, diff,
            time_limit=tl,
            callback=_cb,
        )
        self.iddfs_depth   = stats["depth_reached"]
        self.iddfs_score   = stats["score"]
        self.iddfs_elapsed = stats["elapsed"]
        self._drop_with_anim(col, P2)

    def _spawn_particles(self, win_cells, player):
        color = P1_COL if player == P1 else P2_COL
        colors = [color, P1_LIGHT if player == P1 else P2_LIGHT, WIN_GLOW_A]
        for (r, c) in win_cells:
            cx, cy = cell_center(r, c)
            for _ in range(20):
                self.particles.append(Particle(cx, cy, random.choice(colors)))

    # ── Events ────────────────────────────────────

    def handle_event(self, event):
        if self.btn_new.is_clicked(event):
            self.new_game()
            return

        if self.btn_diff.is_clicked(event):
            self.diff_idx       = (self.diff_idx + 1) % len(DIFF_NAMES)
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

    # ── Drawing ───────────────────────────────────

    def draw(self):
        self.screen.blit(self._bg, (0, 0))
        self._draw_title()
        self._draw_score_bar()
        self._draw_hint_row()
        self._draw_board()
        self._draw_particles()
        self._draw_controls()
        pygame.display.flip()

    # -- Title strip --

    def _draw_title(self):
        # Tiny decorative dots flanking the title
        title = "CONNECT  FOUR"
        tx = W // 2
        ty = 22
        draw_text(self.screen, title, self.font_xl, TEXT_PRIMARY, tx, ty)
        # decorative separator line
        pygame.draw.line(self.screen, SEPARATOR, (PAD + 4, 38), (W - PAD - 4, 38), 1)

    # -- Score cards --

    def _draw_score_bar(self):
        card_w, card_h = 116, 58
        gap  = 16
        total = card_w * 3 + gap * 2
        sx   = (W - total) // 2
        cy   = 46 + card_h // 2

        entries = [
            ("YOU",   P1_COL, P1_LIGHT, self.scores[P1]),
            ("DRAWS", TEXT_DIM, TEXT_DIM, self.scores["draw"]),
            ("AI",    P2_COL, P2_LIGHT,  self.scores[P2]),
        ]

        for i, (lbl, accent, light, val) in enumerate(entries):
            x = sx + i * (card_w + gap)
            rect = pygame.Rect(x, cy - card_h // 2, card_w, card_h)
            draw_rounded_rect(self.screen, CARD_BG, rect, 12, 1, CARD_BORDER)

            # Coloured top accent bar
            top_bar = pygame.Rect(x + 10, cy - card_h // 2, card_w - 20, 3)
            pygame.draw.rect(self.screen, accent, top_bar, border_radius=2)

            draw_text(self.screen, lbl,      self.font_sm, TEXT_DIM,   x + card_w // 2, cy - 10)
            draw_text(self.screen, str(val), self.font_lg, light,      x + card_w // 2, cy + 14)

        # Status indicator below cards
        self._draw_status()

    def _draw_status(self):
        y = SCORE_H - 14
        if self.status_msg:
            msg   = self.status_msg
            color = P1_LIGHT if "You" in msg else (P2_LIGHT if "AI" in msg else TEXT_DIM)
            draw_text(self.screen, msg, self.font_md, color, W // 2, y)
        elif self.current == P1 and not self.game_over:
            draw_text(self.screen, "▸  Your turn", self.font_md, P1_LIGHT, W // 2, y)
        elif self.current == P2 and not self.game_over:
            if self.iddfs_depth > 0:
                # Show live IDDFS progress: depth reached + elapsed
                tl   = IDDFS_TIME_LIMITS.get(DIFF_NAMES[self.diff_idx].lower(), 5.0)
                pct  = min(1.0, self.iddfs_elapsed / tl)
                bar_w = 120
                filled = int(bar_w * pct)
                bx = W // 2 - bar_w // 2
                pygame.draw.rect(self.screen, (30, 45, 90),
                                 (bx, y - 6, bar_w, 8), border_radius=4)
                pygame.draw.rect(self.screen, P2_COL,
                                 (bx, y - 6, filled, 8), border_radius=4)
                label = (f"depth {self.iddfs_depth}  "
                         f"score {self.iddfs_score:+d}  "
                         f"{self.iddfs_elapsed:.1f}s / {tl:.0f}s")
                draw_text(self.screen, label, self.font_sm, P2_LIGHT, W // 2, y + 10)
            else:
                dots = "." * (1 + (self.frame // 15) % 3)
                draw_text(self.screen, f"AI thinking{dots}", self.font_md, P2_LIGHT, W // 2, y)

    # -- Column hover hint --

    def _draw_hint_row(self):
        if self.game_over or self.current != P1 or self.anim:
            return
        c = self.hover_col
        if c is None or c not in get_valid_columns(self.board):
            return

        x, _  = cell_center(0, c)
        cy    = SCORE_H + HINT_H // 2

        # Ghost disc preview with glow
        draw_glow_circle(self.screen, P1_COL, (x, cy + 6), RADIUS, RADIUS + 18, alpha=60)
        # Small translucent disc
        ghost = pygame.Surface((RADIUS * 2, RADIUS * 2), pygame.SRCALPHA)
        pygame.draw.circle(ghost, (*P1_COL, 110), (RADIUS, RADIUS), RADIUS)
        pygame.draw.circle(ghost, (*P1_LIGHT, 60), (RADIUS, RADIUS), RADIUS, 2)
        self.screen.blit(ghost, (x - RADIUS, cy + 6 - RADIUS))

        # Down-arrow below ghost
        tip_y  = cy + 6 + RADIUS + 6
        arr_pts = [(x, tip_y + 8), (x - 7, tip_y - 2), (x + 7, tip_y - 2)]
        pygame.draw.polygon(self.screen, P1_LIGHT, arr_pts)

    # -- Board and discs --

    def _draw_board(self):
        board_rect = pygame.Rect(0, SCORE_H + HINT_H, W, ROWS * CELL + PAD * 2)

        # Draw board panel with gradient (dark at bottom)
        grad_surf = pygame.Surface((board_rect.width, board_rect.height))
        draw_gradient_rect(
            grad_surf,
            (18, 42, 90),   # lighter top
            (10, 24, 58),   # darker bottom
            (0, 0, board_rect.width, board_rect.height),
        )
        pygame.draw.rect(grad_surf, (0, 0, 0, 0), (0, 0, board_rect.width, board_rect.height),
                         border_radius=16)
        self.screen.blit(grad_surf, (board_rect.x, board_rect.y))

        # Board border
        pygame.draw.rect(self.screen, BOARD_EDGE, board_rect, 2, border_radius=16)

        # Win cells set for fast lookup
        win_set   = set(map(tuple, self.win_cells)) if self.win_cells else set()
        pulse_val = self.pulse_t / 60.0  # 0→1 each second

        for r in range(ROWS):
            for c in range(COLS):
                cx, cy = cell_center(r, c)
                val    = self.board[r][c]
                is_win = (r, c) in win_set

                if val == EMPTY:
                    # Empty hole — dark indigo with shadow ring
                    pygame.draw.circle(self.screen, HOLE_SHADOW, (cx, cy), RADIUS + 3)
                    pygame.draw.circle(self.screen, HOLE_EMPTY,  (cx, cy), RADIUS)
                else:
                    color = P1_COL if val == P1 else P2_COL
                    light = P1_LIGHT if val == P1 else P2_LIGHT

                    if is_win:
                        # Animated glow pulse
                        glow_r = int(RADIUS * 1.6 + 8 * math.sin(pulse_val * 2 * math.pi))
                        glow_c = lerp_color(WIN_GLOW_A, WIN_GLOW_B,
                                            0.5 + 0.5 * math.sin(pulse_val * 2 * math.pi))
                        draw_glow_circle(self.screen, glow_c, (cx, cy), RADIUS, glow_r, alpha=120)
                        # Win disc — brighter
                        draw_glossy_disc(self.screen, glow_c, (255, 255, 200), (cx, cy), RADIUS)
                    else:
                        draw_glossy_disc(self.screen, color, light, (cx, cy), RADIUS)

        # Animated falling disc (drawn on top)
        if self.anim:
            acx  = cell_center(0, self.anim.col)[0]
            acy  = int(self.anim.y_pos())
            col  = P1_COL   if self.anim.player == P1 else P2_COL
            lite = P1_LIGHT if self.anim.player == P1 else P2_LIGHT
            draw_glow_circle(self.screen, col, (acx, acy), RADIUS, RADIUS + 14, alpha=70)
            draw_glossy_disc(self.screen, col, lite, (acx, acy), RADIUS)

    # -- Particles --

    def _draw_particles(self):
        for p in self.particles:
            p.draw(self.screen)

    # -- Bottom controls bar --

    def _draw_controls(self):
        y0 = H - CTRL_H
        # Separator line
        pygame.draw.line(self.screen, SEPARATOR, (0, y0), (W, y0), 1)

        mp = pygame.mouse.get_pos()
        self.btn_new.draw(self.screen, mp)
        self.btn_diff.draw(self.screen, mp)

        # Centre label — IDDFS budget
        diff  = DIFF_NAMES[self.diff_idx]
        tl    = DIFF_TIMES[diff]
        label = f"Minimax  α-β  +  IDDFS  ·  {tl:.0f}s budget  ·  1/2/3 difficulty  R=new"
        draw_text(self.screen, label, self.font_sm, TEXT_DIM, W // 2, y0 + CTRL_H // 2)

    # ── Main loop ─────────────────────────────────

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


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    ConnectFour().run()
