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

running = True

clock = pygame.time.Clock()

opp1 = normal_opp(0, 0)
opp2 = normal_opp(100, 300)
opp3 = normal_opp(300, 100)
opp4 = normal_opp(400, 400)
opp5 = normal_opp(500, 200)
opponents = []

# Für jeden Gegner eine Healthbar erstellen (follow=True hält sie über dem Kopf)
opp_bars = [health_bar(-40, 0, 60, 7, opp, follow=True) for opp in opponents]

roundtick = 7200 # zwei Minuten Spielzeit bei 60 FPS


while running and roundtick > 0:

	# Gegner spawnen zu bestimmten Zeiten
	if roundtick == 7200: # Gegner 1 spawnt nach 0 Sekunden
		opponents = opponents + [opp1]
	elif roundtick == 5400: # Gegner 2 spawnt nach 30 Sekunden
		opponents = opponents + [opp2]
	elif roundtick == 3600: # Gegner 3 spawnt nach 60 Sekunden
		opponents = opponents + [opp3]
	elif roundtick == 1800: # Gegner 4 und 5 spawnen nach 90 Sekunden
		opponents = opponents + [opp4, opp5]
	
	roundtick -= 1
	screen.fill((0,0,0))
	
	screen.blit(floor_img, (0, 0))
	
	# Steuerung
	keys = pygame.key.get_pressed()
	is_moving = keys[pygame.K_LEFT] or keys[pygame.K_RIGHT] or keys[pygame.K_UP] or keys[pygame.K_DOWN]
	
	# Bewegung verwaltet marx intern
	marx_char.input_monitoring(keys, marx_area, opponents)
	marx_char.tick_animation(is_moving)

	# Update & Draw
	alive, position = marx_char.update()
	marx_area.drawrect(screen)
	marx_char.draw(screen)

	for opp in opponents:
		opp.followplayer(marx_char)
		opp.animation()
		opp.checkcollision(marx_char)
		opp.draw(screen)

	# Healthbars der lebenden Gegner zeichnen
	for bar in opp_bars:
		if bar.object.alive:
			bar.draw(screen)

	
	alive_opponents = [opp for opp in opponents if opp.update()]
	opp_bars = [bar for bar in opp_bars if bar.object.alive]
	opponents = alive_opponents
	if not opponents:
		print("Alle Gegner besiegt!")

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