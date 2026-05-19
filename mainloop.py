# =============================================================================
# mainloop.py  –  Main Game Loop
# =============================================================================
# Runs the main round of Capital Clash.
#
# What happens here:
#   - Spawns waves of normal, super, and mini enemies over 60 seconds
#   - The player (Marx) moves with arrow keys and attacks with SPACE
#   - Enemies follow Marx, deal contact damage and can be killed
#   - Killed enemies may drop collectibles (health, aoe, revive)
#   - The round ends when:
#       • the 60-second timer (roundtick) hits 0 AND no enemies remain, OR
#       • Marx's HP drops to 0
#
# The function receives the pygame screen surface from game.py so the same
# window is reused across all game phases.
# =============================================================================

def mainloop(screen, settings_obj):
    import os
    import pygame
    from game_classes import marx, damage_area, damage_screen, health_bar
    from opp_classes import normal_opp, super_opp, mini_opp, SpawnManager
    from collectible_classes import collectible_manager

    # Load settings
    game_settings = settings_obj.get_settings()
    
    # =========================================================================
    # Setup: Window / Display
    # =========================================================================

    width  = game_settings["width"]
    height = game_settings["height"]

    # =========================================================================
    # Setup: Asset Paths
    # =========================================================================

    # os.path.dirname(__file__) gives the folder that contains this script.
    # os.path.join() appends the filename – works on all operating systems
    # regardless of the current working directory.
    script_dir  = os.path.dirname(os.path.abspath(__file__))
    marx_path   = os.path.join(script_dir, "assets", "player", "marx1.png")   # Marx idle sprite
    marx_path2  = os.path.join(script_dir, "assets", "player", "marx2.png")   # Marx run sprite
    floor_path  = os.path.join(script_dir, "assets", "environment", "floor.png")   # background image

    # =========================================================================
    # Setup: Background Image
    # =========================================================================

    # try/except: the game still runs without floor.png (black background fallback)
    try:
        floor_img = pygame.image.load(floor_path).convert_alpha()
        floor_img = pygame.transform.scale(floor_img, (width, height))   # fit to window
    except Exception as e:
        print(f"Floor nicht gefunden: {e}")
        floor_img = None   # None → screen.fill((0,0,0)) serves as fallback

    # =========================================================================
    # Setup: Game Objects
    # =========================================================================

    # Player character placed at the centre of the screen
    marx_char = marx(width // 2, height // 2, marx_path, marx_path2, 
                     scale=game_settings["player_scale"], 
                     health_points=game_settings["player_health"],
                     screen_w=width, screen_h=height)

    # Marx's HP bar: centred at top of screen, 200 px wide, 20 px tall
    marx_bar  = health_bar(width//2 - 100, height - 40, 200, 20, marx_char)

    # Attack circle drawn around Marx (visual + collision for attacks)
    marx_area = damage_area(marx_char)

    # Red full-screen flash triggered whenever Marx takes damage
    dmg_scr   = damage_screen()

    #music
    music_path = os.path.join(script_dir, "assets", "music", "Arbeiterfront_8-Bit.mp3")
    pygame.mixer.music.load(music_path)
    pygame.mixer.music.set_volume(game_settings.music_volume*0.3)
    pygame.mixer.music.play(-1, 0)  # Loop the music indefinitely, starting at 0 seconds

    # =========================================================================
    # Setup: Enemy Spawn Schedule (SCHEDULE)
    # =========================================================================
    # roundtick counts DOWN from 3600 to 0.  3600 ticks = 60 seconds at 60 FPS.
    #
    # Each entry in SCHEDULE is a dict with:
    #   "type"     – enemy class to spawn (normal_opp, super_opp, mini_opp)
    #   "count"    – how many to spawn at once
    #   "tick"     – (one-shot) spawn when roundtick == this value
    #   "interval" – (periodic) spawn every N ticks
    #   "start"    – (periodic) only spawn while roundtick >= start
    #   "end"      – (periodic) only spawn while roundtick > end (0 = forever)
    #
    # To add a new wave, append another dict to this list.

    SCHEDULE = [
        # ── One-shot waves ──────────────────────────────────────────────────
        {"type": normal_opp, "count": 2, "tick": 3600},   # second   0: 2× Normal
        {"type": normal_opp, "count": 1, "tick": 1800},   # second  30: +1 Normal
        {"type": normal_opp, "count": 2, "tick": 1500},   # second  35: +2 Normal
        {"type": super_opp,  "count": 2, "tick":  900},   # second  45: 2× Super

        # ── Periodic waves ──────────────────────────────────────────────────
        # Every 5 seconds (300 ticks): 2 mini enemies, throughout the whole round
        {"type": mini_opp, "count": 2, "interval": 300, "start": 3600, "end": 0},

        # After the round timer ends (roundtick < 0): continue spawning 1 mini
        # every 5 seconds.  "start" is omitted → SpawnManager uses current tick.
        {"type": mini_opp, "count": 1, "interval": 300, "start": 0},
    ]

    # SpawnManager reads the schedule and handles all spawning automatically
    spawn_manager = SpawnManager(SCHEDULE)

    # collectible_manager watches for dead enemies and manages all drops
    coll_manager  = collectible_manager(marx_char)

    # List of currently alive enemies on the field
    opponents     = []

    # Round timer: decrements every frame
    roundtick     = game_settings["round_ticks"]
    endtick       = game_settings["end_tick_buffer"] * game_settings["fps"]

    clock   = pygame.time.Clock()
    running = True

    # =========================================================================
    # Main Game Loop
    # =========================================================================

    while running:

        # --- Step 1: Spawning ------------------------------------------------
        # SpawnManager checks whether any wave is due this tick and returns
        # the newly created enemy objects.
        newly_spawned = spawn_manager.tick(roundtick, marx_char)
        opponents.extend(newly_spawned)   # add fresh enemies to the active list
        roundtick -= 1                    # advance the round clock

        # --- Step 2: Draw Background -----------------------------------------
        screen.fill((0, 0, 0))            # black fill prevents ghost frames
        if floor_img:
            screen.blit(floor_img, (0, 0))

        # --- Step 3: Player Input & Update -----------------------------------
        keys = pygame.key.get_pressed()

        # is_moving: True if any arrow key is held (used to select animation frame)
        is_moving = any(keys[k] for k in (pygame.K_LEFT, pygame.K_RIGHT,
                                          pygame.K_UP,   pygame.K_DOWN))

        # Process movement and attack
        marx_char.input_monitoring(keys, marx_area, opponents)
        # Advance the animation (idle ↔ run sprite toggle)
        marx_char.tick_animation(is_moving)

        # Check whether Marx is still alive
        alive = marx_char.update()

        # --- Step 4: Draw Marx and His Attack Circle -------------------------
        marx_area.drawrect(screen)   # white/red circle around Marx
        marx_char.draw(screen)       # Marx sprite
        dmg_scr.draw(screen)         # red overlay if Marx was just hit

        # --- Step 5: Enemy Update and Draw -----------------------------------
        for opp in opponents:
            opp.followplayer(marx_char)            # move toward Marx
            opp.animation()                        # update run animation
            opp.checkcollision(marx_char, dmg_scr) # deal contact damage if touching
            opp.draw(screen)                       # draw the enemy sprite

        # Draw enemy HP bars (only for enemies that are alive and still on the field)
        for bar in spawn_manager.opp_bars:
            if bar.object.alive and bar.object in opponents:
                bar.draw(screen)

        # --- Step 6: Collectibles --------------------------------------------
        # MUST happen before the cleanup step (Step 7) so dead enemies are still
        # in the list and their drop positions can be read.
        coll_manager.collectible_tick(screen, opponents)

        # --- Step 7: Cleanup -------------------------------------------------
        # Remove dead enemies from the active list
        opponents = [o for o in opponents if o.alive]
        # Remove dead enemies and their HP bars from the SpawnManager's records
        spawn_manager.cleanup()

        # --- Step 8: Draw Marx's HP Bar --------------------------------------
        # Drawn last so it always appears on top of all other elements
        marx_bar.draw(screen)

        # --- Step 9: Death Check ---------------------------------------------
        if not alive:
            print("Marx ist tot!")
            running = False   # exit the loop on the next iteration
            return False, marx_char.health_points

        # --- Step 10: Event Handling -----------------------------------------
        # Handle the window close button
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                return False, marx_char.health_points

        # --- Step 11: Frame Cap and Display ----------------------------------
        pygame.display.flip()   # push the finished frame to the monitor
        clock.tick(60)          # cap at 60 FPS to keep game speed consistent

        # End condition: timer expired AND no enemies remain on the field
        if roundtick <= 0 and not opponents:
            if endtick > 0:
                endtick -= 1
            elif endtick == 0:
                running = False
                return True, marx_char.health_points
    #music stop
    pygame.mixer.music.stop()