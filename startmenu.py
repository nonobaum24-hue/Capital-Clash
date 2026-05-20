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
    from ui_components import StartButton, SettingsButton

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

    # Hole die Settings als dict
    settings_dict = game_settings.get_settings()
    bg_color = settings_dict["background_color"]
    bg_opacity = settings_dict["background_opacity"]

    scrn_surf = pygame.Surface((width, height), pygame.SRCALPHA)
    scrn_surf.fill((*bg_color, bg_opacity))
    screen.blit(scrn_surf, (0, 0))

    strt_btn = StartButton(width // 2 - 100, height // 2 - 50 - 40, 200, 80)
    stngs_btn = SettingsButton(width // 2 - 100, height // 2 + 40, 200, 80, game_settings, screen)

    running = True
    resolution_changed = False

    while running:
        screen.fill((0, 0, 0))            # black fill prevents ghost frames
        if floor_img:
            screen.blit(floor_img, (0, 0))
        scrn_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        scrn_surf.fill((*bg_color, bg_opacity))
        screen.blit(scrn_surf, (0, 0))

        font = pygame.font.SysFont(None, 36)
        strt = strt_btn.is_clicked(pygame.event.get())
        if strt:
            running = False

        strt_btn.update(pygame.mouse.get_pos())
        strt_btn.draw(screen, font)
        
        stngs_btn.update(pygame.mouse.get_pos())
        stngs_btn.draw(screen, font)
        
        if stngs_btn.check_click():
            # Save old resolution
            old_width = game_settings.width
            old_height = game_settings.height
            
            # Check if resolution has changed
            if game_settings.width != old_width or game_settings.height != old_height:
                resolution_changed = True
                running = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False  # Exit the loop if the window is closed
        
        pygame.display.flip()  # update the display to show the button

    # Return the screen surface so the caller (game.py) can pass it on to
    # mainloop() and boss_fight() – avoids reopening the window.
    del scrn_surf  # clean up the menu surface as it's no longer needed
    
    # If resolution changed, restart the window
    if resolution_changed:
        pygame.quit()
        return startmenu(game_settings)  # Restart recursively
    
    return screen
