def boss_fight(screen):
    import pygame
    import os
    from game_classes import marx, damage_area, damage_screen, health_bar
    from opp_classes import normal_opp, super_opp, mini_opp, SpawnManager
    from collectible_classes import collectible_manager

    print('bossfight')

    import os
    import pygame
    from game_classes import marx, damage_area, damage_screen, health_bar
    from opp_classes import normal_opp, super_opp, mini_opp, SpawnManager
    from collectible_classes import collectible_manager
    from boss_classes import boss_opp, punch_area, boss_projectile
    
    # ─────────────────────────────────────────────────────────────────────────────
    # Grundeinstellungen
    # ─────────────────────────────────────────────────────────────────────────────

    width  = 1250   # Fensterbreite in Pixeln
    height = 720    # Fensterhöhe in Pixeln

    pygame.init()
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Capital Crush")

    # ─────────────────────────────────────────────────────────────────────────────
    # Pfade zu Bild-Dateien
    # ─────────────────────────────────────────────────────────────────────────────

    # os.path.dirname(__file__) gibt den Ordner dieser Datei zurück;
    # join() hängt den Dateinamen dran → funktioniert unabhängig vom Arbeitsverzeichnis
    script_dir  = os.path.dirname(os.path.abspath(__file__))
    marx_path   = os.path.join(script_dir, "marx1.png")   # Marx Idle-Sprite
    marx_path2  = os.path.join(script_dir, "marx2.png")   # Marx Lauf-Sprite
    floor_path  = os.path.join(script_dir, "floor.png")   # Hintergrundbild

    # ─────────────────────────────────────────────────────────────────────────────
    # Hintergrundbild laden
    # ─────────────────────────────────────────────────────────────────────────────

    # try/except damit das Spiel auch ohne floor.png startet (schwarzer Hintergrund als Fallback)
    try:
        floor_img = pygame.image.load(floor_path).convert_alpha()
        floor_img = pygame.transform.scale(floor_img, (width, height))  # auf Fenstergröße skalieren
    except Exception as e:
        print(f"Floor nicht gefunden: {e}")
        floor_img = None   # kein Boden → screen.fill((0,0,0)) reicht als Hintergrund

    # ─────────────────────────────────────────────────────────────────────────────
    # Spielobjekte erstellen
    # ─────────────────────────────────────────────────────────────────────────────

    # Spielercharakter in der Mitte des Bildschirms
    marx_char = marx(width // 2, height // 2, marx_path, marx_path2)

    # Lebensanzeige von Marx: rechts oben, 200px breit, 20px hoch
    marx_bar  = health_bar(width//2 - 100, 20, 200, 20, marx_char)

    # Angriffsbereich-Visualisierung (Kreis um Marx)
    marx_area = damage_area(marx_char)

    # Roter Overlay-Effekt wenn Marx Schaden nimmt
    dmg_scr   = damage_screen()

    SCHEDULE = {}

    spawn_manager = SpawnManager(SCHEDULE)

    
    coll_manager  = collectible_manager(marx_char)

    # Aktive Gegner-Liste: nur lebende Gegner die gerade auf dem Feld sind
    opponents     = []

    # Runduhr: 3600 Frames = 60 Sekunden; wird jeden Frame um 1 reduziert
    roundtick     = 3600

    clock   = pygame.time.Clock()
    running = True

    # ── Boss & Punch-Area initialisieren ────────────────────────────────────────
    BOSS  = boss_opp()
    punch = punch_area(BOSS)

    # Boss-Healthbar: links oben, 400px breit, 30px hoch
    boss_bar = health_bar(width//2 - 200, 60, 400, 30, BOSS)

    # Projektile-Liste für Phase 2 des Bosses
    projectiles = []

    # ─────────────────────────────────────────────────────────────────────────────
    # Boss-Loop
    # ─────────────────────────────────────────────────────────────────────────────

    while running:

        # ── 1. Spawning ───────────────────────────────────────────────────────────
        # SpawnManager prüft ob bei diesem Tick eine Welle fällig ist
        # und gibt neu gespawnte Gegner zurück
        newly_spawned = spawn_manager.tick(roundtick, marx_char)
        opponents.extend(newly_spawned)   # sofort zur aktiven Liste hinzufügen
        roundtick -= 1                    # Uhr einen Tick weiterschalten

        # ── 2. Hintergrund zeichnen ───────────────────────────────────────────────
        screen.fill((0, 0, 0))            # erst alles schwarz (verhindert Geister-Frames)
        if floor_img:
            screen.blit(floor_img, (0, 0))

        # ── 3. Eingabe & Spieler-Update ───────────────────────────────────────────
        keys      = pygame.key.get_pressed()
        # is_moving: True wenn irgendeine Pfeiltaste gedrückt ist (für Animation)
        is_moving = any(keys[k] for k in (pygame.K_LEFT, pygame.K_RIGHT,
                                        pygame.K_UP,   pygame.K_DOWN))

        # Bewegung + Angriff verarbeiten
        marx_char.input_monitoring(keys, marx_area, opponents)
        # Animationssprite wechseln
        marx_char.tick_animation(is_moving)

        # alive = ob Marx noch lebt; _ = Position (hier nicht gebraucht)
        alive, _ = marx_char.update()

        # ── 4. Marx und Angriffsbereich zeichnen ──────────────────────────────────
        marx_area.drawrect(screen)   # Kreis (weiß/rot) um Marx
        marx_char.draw(screen)       # Marx selbst
        dmg_scr.draw(screen)         # roter Overlay wenn gerade Schaden

        # ── 5. Gegner updaten und zeichnen ────────────────────────────────────────

        # -- Boss-Bereich --------
        # Boss ticken (Bewegung, Angriffe, Animation, Phasen)
        BOSS.tick(marx_char, projectiles, punch)
        
        # Boss zeichnen
        BOSS.draw(screen)
        
        # Punch-Area zeichnen (weißer/roter Kreis um Boss)
        punch.draw(screen)

        # Projektile ticken und zeichnen (Phase 2)
        for proj in projectiles:
            proj.tick(marx_char)
            proj.draw(screen)
        
        # Tote Projektile entfernen
        projectiles = [p for p in projectiles if p.alive]

        for opp in opponents:
            opp.followplayer(marx_char)          # auf Marx zubewegen
            opp.animation()                      # Lauf-Animation
            opp.checkcollision(marx_char, dmg_scr) # Berührungsschaden prüfen
            opp.draw(screen)                     # Sprite zeichnen

        # Healthbars der Gegner zeichnen (nur wenn lebendig und aktiv)
        for bar in spawn_manager.opp_bars:
            if bar.object.alive and bar.object in opponents:
                bar.draw(screen)

        # ── 6. Collectibles ───────────────────────────────────────────────────────
        # MUSS vor dem Cleanup passieren: tote Gegner sind hier noch in der Liste
        # → Drop-Erkennung, Zeichnen und Aufsammel-Prüfung in einem Schritt
        coll_manager.collectible_tick(screen, opponents)

        # ── 7. Cleanup ────────────────────────────────────────────────────────────
        # Tote Gegner aus der aktiven Liste entfernen
        opponents = [o for o in opponents if o.alive]
        # Tote Gegner + ihre Healthbars aus dem SpawnManager entfernen
        spawn_manager.cleanup()

        # ── 8. Marx Lebensanzeige ─────────────────────────────────────────────────
        # Ganz zum Schluss damit sie über allem anderen liegt
        marx_bar.draw(screen)
        
        # Boss Lebensanzeige
        if BOSS.alive:
            boss_bar.draw(screen)

        # ── 9. Tod-Check ──────────────────────────────────────────────────────────
        if not alive:
            print("Marx ist tot!")
            running = False   # Loop beim nächsten Durchlauf beenden
        
        # Boss-Tod-Check (Spieler hat gewonnen!)
        if not BOSS.alive:
            print("Boss besiegt! Gewonnen!")
            running = False

        # ── 10. Events ────────────────────────────────────────────────────────────
        # Fenster-Schließen abfangen
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # ── 11. Frame begrenzen & anzeigen ────────────────────────────────────────
        pygame.display.flip()   # fertigen Frame auf den Bildschirm bringen
        clock.tick(60)          # maximal 60 FPS (hält Spielgeschwindigkeit konstant)