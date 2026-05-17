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

def startmenu(game_settings):
    import os
    import pygame
    from start_classes import start_button, settings_button

    # Load settings
    # game_settings = settings

    # Window dimensions from settings
    width  = game_settings.width
    height = game_settings.height

    # Initialise pygame and create the display window
    pygame.init()
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Capital Clash")   # title bar text

    script_dir  = os.path.dirname(os.path.abspath(__file__))
    floor_path  = os.path.join(script_dir, "assets", "environment", "floor.png")   # background image
    try:
        floor_img = pygame.image.load(floor_path).convert_alpha()
        floor_img = pygame.transform.scale(floor_img, (width, height))   # fit to window
    except Exception as e:
        print(f"Floor nicht gefunden: {e}")
        floor_img = None   # None → screen.fill((0,0,0)) serves as fallback

    scrn_surf = pygame.Surface((width, height), pygame.SRCALPHA)  # surface for drawing the menu
    scrn_surf.fill((*game_settings.get_background_color(), game_settings.get_background_opacity()))  # fill with dark gray background
    screen.blit(scrn_surf, (0, 0))  # draw the menu surface onto the main screen

    strt_btn = start_button(width, height)  # create an instance of the start button, passing window dimensions
    stngs_btn = settings_button(width, height, game_settings, screen)  # create an instance of the settings button

    running = True

    while running:
        screen.fill((0, 0, 0))            # black fill prevents ghost frames
        if floor_img:
            screen.blit(floor_img, (0, 0))
        scrn_surf = pygame.Surface((width, height), pygame.SRCALPHA)  # surface for drawing the menu
        scrn_surf.fill((*game_settings.get_background_color(), game_settings.get_background_opacity()))  # fill with dark gray background
        screen.blit(scrn_surf, (0, 0))  # draw the menu surface onto the main screen

        stngs_btn.draw(screen)  # draw the settings button on the screen

        strt = strt_btn.draw(screen)  # draw the start button on the screen
        if strt:
            running = False  # Exit the loop if the start button is clicked

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False  # Exit the loop if the window is closed
        
        pygame.display.flip()  # update the display to show the button

    # Return the screen surface so the caller (game.py) can pass it on to
    # mainloop() and boss_fight() – avoids reopening the window.
    del scrn_surf  # clean up the menu surface as it's no longer needed
    return screen
    return screen
