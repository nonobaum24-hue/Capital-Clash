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

    scrn_surf = pygame.Surface((width, height), pygame.SRCALPHA)  # surface for drawing the menu
    scrn_surf.fill((30, 30, 30, 100))  # fill with dark gray background
    screen.blit(scrn_surf, (0, 0))  # draw the menu surface onto the main screen

    strt_btn = start_button()  # create an instance of the start button

    running = True

    while running:
        strt = strt_btn.draw(screen)  # draw the start button on the screen
        if strt:
            running = False  # Exit the loop if the start button is clicked

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False  # Exit the loop if the window is closed
        running = False
        pygame.display.flip()  # update the display to show the button

    # Return the screen surface so the caller (game.py) can pass it on to
    # mainloop() and boss_fight() – avoids reopening the window.
    del scrn_surf  # clean up the menu surface as it's no longer needed
    return screen
