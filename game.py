# =============================================================================
# game.py  –  Entry Point of Capital Clash
# =============================================================================
# This file is the single entry point; run it with:  python3 game.py
#
# The game is divided into three sequential phases:
#   1. startmenu()  – Displays the start screen. Player can adjust settings or
#                     start the game. Returns the pygame screen surface for reuse.
#   2. mainloop()   – Main game: Marx fights waves of normal/super/mini enemies
#                     over 60 seconds, collecting power-ups from fallen foes.
#   3. boss_fight() – Finale: Marx fights the boss Olaf (two phases, 1000 HP).
#
# All three phases share the same pygame window (screen surface) so the window
# does not flicker or reopen between phases.
# =============================================================================

import pygame
from mainloop import mainloop
from boss_fight import boss_fight
from startmenu import startmenu
from settings import settings

game_settings = settings()  # Load settings from file or use defaults

# --- Phase 1: Start Menu ---
# startmenu() initialises pygame, opens the game window and waits until the
# player decides to start or adjust settings. It returns the Screen surface
# so we can hand the same window to the following phases.

screen = startmenu(game_settings)

print('Game started successfully')   # Debug output – start menu finished

# --- Phase 2: Main Game Loop ---
# Runs until either the 60-second round ends with no enemies left (player
# wins the round) or Marx's HP drops to 0 (player dies).

alive, health = mainloop(screen, game_settings)

# --- Phase 3: Boss Fight ---
# Same screen is reused. The loop ends when BOSS.alive becomes False (player
# wins) or marx.alive becomes False (player loses).
if alive:
    boss_fight(screen, health, game_settings)

# --- Shutdown ---
# pygame.quit() must be called exactly once after all game phases are done.
# It uninitialises all pygame modules and closes the window cleanly.
pygame.quit()
