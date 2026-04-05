import os
import pygame
from game_classes import load_image, marx, normal_opp

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
marx1_img = load_image(marx_path, scale=0.25)
marx2_img = load_image(marx_path2, scale=0.25)

try:
    floor_img = pygame.image.load(floor_path).convert_alpha()
    floor_img = pygame.transform.scale(floor_img, (width, height))
except Exception as e:
    print(f"Floor nicht gefunden: {e}")
    floor_img = None

# Marx mit beiden Skin-Pfaden initialisieren
marx_char = marx(width // 2, height // 2, marx_path, marx_path2)

running = True

clock = pygame.time.Clock()

opp1 = normal_opp(0, 0)

while running:
	screen.fill((0,0,0))
	
	if floor_img:
		screen.blit(floor_img, (0, 0))
	
	# Steuerung
	keys = pygame.key.get_pressed()
	is_moving = keys[pygame.K_LEFT] or keys[pygame.K_RIGHT] or keys[pygame.K_UP] or keys[pygame.K_DOWN]
	
	# Bewegung verwaltet marx intern
	marx_char.input_monitoring(keys)

	# Animation intern verwaltet, nur is_moving übergeben
	marx_char.tick_animation(is_moving)

	# Update & Draw
	alive, position = marx_char.update()
	marx_char.draw(screen)

	opp1.followplayer(marx_char)
	opp1.animation()
	opp1.draw(screen)

	if not alive:
		print("Marx ist tot!")
		running = False
	
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			running = False
	
	pygame.display.flip()
	clock.tick(60)

pygame.quit()