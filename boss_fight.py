# =============================================================================
# boss_fight.py  –  Boss Fight Game Loop
# =============================================================================
# Runs the final boss encounter of Capital Clash: Marx vs. Olaf.
#
# Differences from mainloop.py:
#   - No timed enemy waves (SCHEDULE is empty)
#   - The boss (BOSS) is a boss_opp instance with 1000 HP and two attack phases
#   - A punch_area around the boss visualises and applies melee damage
#   - In Phase 2 (HP ≤ 500) the boss also creates impact areas
#   - A separate boss HP bar is shown at the top of the screen
#
# Win condition:  BOSS.alive becomes False  →  player wins
# Lose condition: marx.alive becomes False  →  player loses
# =============================================================================

def boss_fight(screen, marxhealth):
    import pygame
    import os
    from game_classes import marx, damage_area, damage_screen, health_bar
    from opp_classes import normal_opp, super_opp, mini_opp, SpawnManager
    from collectible_classes import collectible_manager
    from boss_classes import boss_opp, punch_area, impact_area, boss_projectile

    print('bossfight')   # debug output to confirm the function was called

    # =========================================================================
    # Setup: Window / Display (same dimensions as mainloop.py)
    # =========================================================================

    width  = 1250   # window width in pixels
    height = 720    # window height in pixels

    pygame.init()
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Capital Crush")

    # Music
    #music
    pygame.mixer.music.load("music/the_red_army_is_the_strongest.mp3")
    pygame.mixer.music.play(-1, 0)  # Loop the music indefinitely, starting at 0 seconds

    # =========================================================================
    # Setup: Asset Paths
    # =========================================================================

    # Build absolute paths relative to this file so the game works regardless
    # of the current working directory.
    script_dir  = os.path.dirname(os.path.abspath(__file__))
    marx_path   = os.path.join(script_dir, "marx1.png")   # Marx idle sprite
    marx_path2  = os.path.join(script_dir, "marx2.png")   # Marx run sprite
    floor_path  = os.path.join(script_dir, "floor.png")   # background image

    # =========================================================================
    # Setup: Background Image
    # =========================================================================

    # Gracefully fall back to a black background if floor.png is missing
    try:
        floor_img = pygame.image.load(floor_path).convert_alpha()
        floor_img = pygame.transform.scale(floor_img, (width, height))   # fit to window
    except Exception as e:
        print(f"Floor nicht gefunden: {e}")
        floor_img = None

    # =========================================================================
    # Setup: Player Objects
    # =========================================================================

    # Player character centred on screen
    marx_char = marx(width // 2, height // 2, marx_path, marx_path2)
    marx_char.health_points = marxhealth

    # Marx HP bar: centred at top, 200 px wide, 20 px tall
    marx_bar  = health_bar(width//2 - 100, 20, 200, 20, marx_char)

    # Attack circle around Marx (visual indicator + hit detection)
    marx_area = damage_area(marx_char)

    # Red full-screen flash when Marx takes damage
    dmg_scr   = damage_screen()


    # Round timer (kept for API compatibility with SpawnManager)
    roundtick     = 3600

    clock   = pygame.time.Clock()
    running = True

    # =========================================================================
    # Setup: Boss and Associated Objects
    # =========================================================================

    # Create the boss (Olaf) and the melee attack area around him
    aoi = impact_area(marx_char)
    BOSS  = boss_opp(marx_char, aoi)
    punch = punch_area(BOSS)

    # Boss HP bar: wider than Marx's bar (400 px) and slightly lower (y=60)
    boss_bar = health_bar(width//2 - 200, 60, 400, 30, BOSS)

    # List for boss projectiles (populated during Phase 2)
    projectiles = []

    # =========================================================================
    # Boss Game Loop
    # =========================================================================

    while running:

        # --- Step 1: Spawning (no-op for boss fight) -------------------------
        roundtick -= 1

        # --- Step 2: Draw Background -----------------------------------------
        screen.fill((0, 0, 0))      # black fill prevents ghost frames
        if floor_img:
            screen.blit(floor_img, (0, 0))

        # --- Step 3: Player Input & Update -----------------------------------
        keys      = pygame.key.get_pressed()

        # is_moving: True if any arrow key is pressed (drives animation selection)
        is_moving = any(keys[k] for k in (pygame.K_LEFT, pygame.K_RIGHT,
                                          pygame.K_UP,   pygame.K_DOWN))

        # Apply movement and attack input
        marx_char.input_monitoring(keys, marx_area, BOSS)
        # Advance the animation sprite (idle ↔ run)
        marx_char.tick_animation(is_moving)

        # Check whether Marx is still alive
        alive = marx_char.update()

        # --- Step 4: Draw Marx and His Attack Circle -------------------------
        marx_area.drawrect(screen)   # white/red circle around Marx
        marx_char.draw(screen)       # Marx sprite
        dmg_scr.draw(screen)         # red overlay if Marx just took damage

        # --- Step 5: Boss Update and Draw ------------------------------------

        # tick() handles: phase transitions, movement toward Marx, punch system,
        # impact area system (Phase 2), and animation updates.
        BOSS.tick(marx_char, projectiles, punch)

        # Draw Olaf's sprite
        BOSS.draw(screen)

        # Draw the melee attack circle around the boss (fades white → red as delay counts down)
        punch.draw(screen)

        # Draw the impact area (red circle that fades in when activated, Phase 2 only)
        aoi.draw(screen)

        # Update and draw all active projectiles (Phase 2 only)
        for proj in projectiles:
            proj.tick()   # move projectile toward impact area
            proj.draw(screen)     # draw if past the delay phase

        # Remove projectiles that have arrived (alive = False)
        projectiles = [p for p in projectiles if p.alive]

        # --- Step 8: Draw HP Bars (drawn last to stay on top) ----------------
        marx_bar.draw(screen)      # Marx's HP bar (always shown)
        if BOSS.alive:
            boss_bar.draw(screen)  # Boss HP bar (hide when boss is dead)

        # --- Step 9: Death and Win Checks ------------------------------------
        if not alive:
            print("Marx ist tot!")
            running = False   # player lost → exit loop

        # Boss defeated → player wins
        if not BOSS.alive:
            print("Boss besiegt! Gewonnen!")
            running = False

        # --- Step 10: Event Handling -----------------------------------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # --- Step 11: Frame Cap and Display ----------------------------------
        pygame.display.flip()   # push finished frame to the monitor
        clock.tick(60)          # cap at 60 FPS
    #music stop
    pygame.mixer.music.stop()
