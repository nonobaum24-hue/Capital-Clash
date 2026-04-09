import os
import pygame
from game_classes import *

width = 1250
height = 720

pygame.init()
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Capital Crush")

#KI Anfang -------------------------------------------------------------------
script_dir = os.path.dirname(os.path.abspath(__file__))
marx_path = os.path.join(script_dir, "marx1.png")
marx_path2 = os.path.join(script_dir, "marx2.png")
floor_path = os.path.join(script_dir, "floor.png")
#KI Ende -------------------------------------------------------------------

# Bilder vorher laden (verwende load_image aus game_classes)
marx1_img = load_image(marx_path, scale=0.20)
marx2_img = load_image(marx_path2, scale=0.20)

try:
    floor_img = pygame.image.load(floor_path).convert_alpha()
    floor_img = pygame.transform.scale(floor_img, (width, height))
except Exception as e:
    print(f"Floor nicht gefunden: {e}")
    floor_img = None

# Marx mit beiden Skin-Pfaden initialisieren
marx_char = marx(width // 2, height // 2, marx_path, marx_path2)
marx_bar = health_bar(1250 - 220, 20, 200, 20, marx_char)
marx_area = damage_area(marx_char)
dmg_scr = damage_screen()

running = True

clock = pygame.time.Clock()

SCHEDULE = [
    # Einmalige Waves (tick = exakter Zeitpunkt)
    {"type": normal_opp, "count": 2, "tick": 3600},          # Start: 2 Normal
    {"type": normal_opp, "count": 1, "tick": 1800},          # 30 s: +1 Normal
    {"type": normal_opp, "count": 2, "tick": 1500},          # 35 s: +2 Normal
    {"type": super_opp,  "count": 2, "tick": 900},           # 45 s: 2 Super

    # Periodische Waves (interval = alle N Ticks)
    {"type": mini_opp, "count": 2, "interval": 300,          # alle 5 s ein Mini
     "start": 3600, "end": 0},
]

spawn_manager = SpawnManager(SCHEDULE)
collectible_manager = collectible_manager(marx_char)
opponents = []

roundtick = 3600 # 60 Sekunden bei 60 FPS


while running:
	# ── Spawning ──────────────────────────────────────────────────────
	newly_spawned = spawn_manager.tick(roundtick, marx_char)
	opponents.extend(newly_spawned)

	roundtick -= 1

	# ── Rendering & Logic ─────────────────────────────────────────────
	screen.fill((0, 0, 0))
	if floor_img:
		screen.blit(floor_img, (0, 0))

	keys      = pygame.key.get_pressed()
	is_moving = any(keys[k] for k in (pygame.K_LEFT, pygame.K_RIGHT,
								pygame.K_UP,   pygame.K_DOWN))

	marx_char.input_monitoring(keys, marx_area, opponents)
	marx_char.tick_animation(is_moving)

	alive, _ = marx_char.update()
	marx_area.drawrect(screen)
	marx_char.draw(screen)
	dmg_scr.draw(screen)

	for opp in opponents:
		opp.followplayer(marx_char)
		opp.animation()
		opp.checkcollision(marx_char, dmg_scr)
		opp.draw(screen)

	for bar in spawn_manager.opp_bars:
		if bar.object.alive and bar.object in opponents:
			bar.draw(screen)

	# ── Cleanup ───────────────────────────────────────────────────────
	opponents = [o for o in opponents if o.alive]
	spawn_manager.cleanup()
	collectible_manager.collectible_tick(opponents)

	marx_bar.draw(screen)
	
	if not alive:
		print("Marx ist tot!")
		running = False
		exit()

	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			running = False
			exit()
	
	pygame.display.flip()
	clock.tick(60)

pygame.quit()