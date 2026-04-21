# =============================================================================
# startmenu.py  –  Start Screen for Capital Clash
# =============================================================================
# Shows the initial game window before the main game starts.
# Currently it skips immediately (running = False after one iteration), but
# it is designed to be expanded with buttons for settings, skin selection, etc.
#
# Returns the pygame screen surface so the same window can be reused by
# mainloop() and boss_fight() without reopening a new window.
# =============================================================================

def startmenu():
    import os
    import pygame

    # Window dimensions – must match the values used in mainloop() and boss_fight()
    # so the screen surface stays compatible across all phases.
    width  = 1250   # window width in pixels
    height = 720    # window height in pixels

    # Initialise pygame and create the display window
    pygame.init()
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Capital Crush")   # title bar text

    running = True

    while running:
        # TODO: This is where the start menu UI would be drawn.
        # Possible future additions:
        #   - "Start Game" button
        #   - Settings (volume, key bindings)
        #   - Skin / character selection
        # For now the menu is skipped immediately by setting running = False.
        running = False

    # Return the screen surface so the caller (game.py) can pass it on to
    # mainloop() and boss_fight() – avoids reopening the window.
    return screen
