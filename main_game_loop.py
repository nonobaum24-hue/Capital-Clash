import os
import pygame
from game_classes import marx, health_bar, damage_area, damage_screen, SpawnManager, collectible_manager, normal_opp, super_opp, mini_opp

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

# ─────────────────────────────────────────────────────────────────────────────
# Spawn-Zeitplan (SCHEDULE)
# ─────────────────────────────────────────────────────────────────────────────
# roundtick zählt von 3600 auf 0 → 3600 Ticks = 60 Sekunden bei 60 FPS.
# Jeder Eintrag spawnt entweder einmalig ("tick") oder wiederholt ("interval").
# Neue Wellen einfach als weiteres dict hinzufügen.

SCHEDULE = [
	# ── Einmalige Wellen ────────────────────────────────────────────────────
	{"type": normal_opp, "count": 2, "tick": 3600},   # Sekunde  0: 2× Normal
	{"type": normal_opp, "count": 1, "tick": 1800},   # Sekunde 30: +1 Normal
	{"type": normal_opp, "count": 2, "tick": 1500},   # Sekunde 35: +2 Normal
	{"type": super_opp,  "count": 2, "tick":  900},   # Sekunde 45: 2× Super

	# ── Periodische Wellen ──────────────────────────────────────────────────
	# alle 5 Sekunden (300 Ticks) 2 Mini-Gegner, die gesamte Runde über
	{"type": mini_opp, "count": 2, "interval": 300, "start": 3600, "end": 0},

	# nach Rundenende (roundtick < 0) weiter 1 Mini alle 5 Sekunden spawnen
	# start fehlt → SpawnManager nutzt current_tick als Startpunkt
	{"type": mini_opp, "count": 1, "interval": 300, "start": 0},
]

# SpawnManager bekommt den Zeitplan und kümmert sich ab jetzt automatisch ums Spawnen
spawn_manager = SpawnManager(SCHEDULE)

# collectible_manager überwacht Gegnertode und verwaltet alle Drops
coll_manager  = collectible_manager(marx_char)

# Aktive Gegner-Liste: nur lebende Gegner die gerade auf dem Feld sind
opponents     = []

# Runduhr: 3600 Frames = 60 Sekunden; wird jeden Frame um 1 reduziert
roundtick     = 3600

clock   = pygame.time.Clock()
running = True

# ─────────────────────────────────────────────────────────────────────────────
# Haupt-Game-Loop
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

	# ── 9. Tod-Check ──────────────────────────────────────────────────────────
	if not alive:
		print("Marx ist tot!")
		running = False   # Loop beim nächsten Durchlauf beenden

	# ── 10. Events ────────────────────────────────────────────────────────────
	# Fenster-Schließen abfangen
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			running = False

	# ── 11. Frame begrenzen & anzeigen ────────────────────────────────────────
	pygame.display.flip()   # fertigen Frame auf den Bildschirm bringen
	clock.tick(60)          # maximal 60 FPS (hält Spielgeschwindigkeit konstant)

	if roundtick >= 0 and not opponents:
		running = False

# ─────────────────────────────────────────────────────────────────────────────
# Aufräumen
# ─────────────────────────────────────────────────────────────────────────────
pygame.quit()
