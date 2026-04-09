import os
import pygame
from random import randint, uniform

# Bild-Cache und Helfer zum (einmaligen) Laden + Skalieren von Bildern (KI)
_IMAGE_CACHE = {}
def load_image(path, scale=0.25):
	# key nach Pfad + Scale, damit verschiedene Skalierungen separat gecached werden
	key = (os.path.abspath(path), float(scale))
	if key in _IMAGE_CACHE:
		return _IMAGE_CACHE[key]
	img = pygame.image.load(path).convert_alpha()
	img = pygame.transform.scale(img,
		(int(img.get_width() * scale),
		 int(img.get_height() * scale)))
	_IMAGE_CACHE[key] = img
	return img

class marx:
	def __init__(self, x, y, idle_path, run_path, scale=0.25, health_points=100, screen_w=1250, screen_h=720):
		# Initialisiert den Spieler mit Position, Bildpfaden, Skalierung, Gesundheit und Bildschirmgröße
		self.x = x
		self.y = y
		self.alive = True
		self.scale = scale
		self.health_points = health_points
		self.damage = 30
		self.exception_radius = 150  # Radius um den Spieler, in dem Gegner nicht spawnen sollen

		# Bildschirmgröße speichern für Bewegungsbegrenzung
		self.screen_w = screen_w
		self.screen_h = screen_h

		# Lade beide Skins direkt
		self.stand_bild = load_image(idle_path, scale=self.scale)
		self.lauf_bild = load_image(run_path, scale=self.scale)

		# Starte mit Idle
		self.image = self.stand_bild
		self.rect = self.image.get_rect(topleft=(self.x, self.y))

		# Animation State
		self.framecount_skin = 0
		self.is_first_skin = True
		self.prev_is_moving = False

		# Attack Cooldown
		self.attack_cooldown = 0

	def dead(self):
		self.alive = False

	def move(self, dx, dy): # Bewegt den Spieler, prüft aber vorher, ob er sich noch im Bildschirm befindet
		if self.x + dx > 0 and self.x + dx < self.screen_w - self.rect.width:
			self.x += dx
		if self.y + dy > 0 and self.y + dy < self.screen_h - self.rect.height:
			self.y += dy
		self.rect.topleft = (self.x, self.y)

	def draw(self, screen):
		if self.alive:
			screen.blit(self.image, (self.x, self.y))

	def get_rect(self):
		return self.rect

	def tick_animation(self, is_moving):
		# Detect Start/Stop
		if is_moving and not self.prev_is_moving:
			# Bewegung gestartet: sofort Run-Skin zeigen
			self.image = self.lauf_bild
			self.is_first_skin = False
			self.framecount_skin = 0
			self.rect = self.image.get_rect(topleft=(self.x, self.y))
		elif is_moving:
			# Laufanimation
			self.framecount_skin += 1
			if self.framecount_skin >= 15:
				# toggle zwischen Idle und Run-Surface
				if self.is_first_skin == False:
					self.image = self.stand_bild
					self.is_first_skin = True
				else:
					self.image = self.lauf_bild
					self.is_first_skin = False
				self.rect = self.image.get_rect(topleft=(self.x, self.y))
				self.framecount_skin = 0
		else:
			# Nicht bewegend: zurück zu Idle
			self.image = self.stand_bild
			self.framecount_skin = 0
			self.is_first_skin = True

		self.prev_is_moving = is_moving

	def update(self):
		position = (self.x, self.y)
		return self.alive, position

	def input_monitoring(self, keys, area, opponents): # Verarbeitet Bewegung und Angriffe basierend auf Tasteneingaben
		if keys[pygame.K_LEFT]:
			self.move(-5, 0)
		if keys[pygame.K_RIGHT]:
			self.move(5, 0)
		if keys[pygame.K_UP]:
			self.move(0, -5)
		if keys[pygame.K_DOWN]:
			self.move(0, 5)

		# Attack Cooldown runterzählen
		if self.attack_cooldown > 0:
			self.attack_cooldown -= 1
			area.turnred()
		else:
			area.turnwhite()

		#Auswahl Liste bei mehrfachem Treffer
		self.opp_list = []

		if keys[pygame.K_SPACE] and self.attack_cooldown == 0:
			# Alle Gegner durchgehen und prüfen, ob sie im Angriffsbereich sind
			for opp in opponents:
				if opp.rect.colliderect(area.getrect()):
					self.opp_list.append(opp)
			# Wenn Gegner in Reichweite, zufällig einen auswählen und Schaden zufügen
			if self.opp_list:
				self.chosen_opp = self.opp_list[randint(0, len(self.opp_list) - 1)]
				self.chosen_opp.getdamage(self.damage)
			self.attack_cooldown = 30  # 0.5 Sekunden Cooldown bei 60 FPS


	def get_damage(self, damage, damage_screen=None):
		self.damage_screen = damage_screen
		if self.alive:
			self.health_points -= damage
			#Bildschirm rot einfärben, wenn Schaden genommen wird
			if self.damage_screen:
				self.damage_screen.trigger()
			# Überprüfen, ob Gesundheit auf 0 oder darunter gefallen ist
			if self.health_points <= 0:
				self.dead()
	
	def gethealth(self):
		return self.health_points
	
	def get_exception_area(self): # Berechnet den Bereich um den Spieler, in dem Gegner nicht spawnen sollen
		x, y = self.get_rect().center
		exception_x_start = x - self.exception_radius
		exception_x_end = x + self.exception_radius
		exception_y_start = y - self.exception_radius
		exception_y_end = y + self.exception_radius
		return exception_x_start, exception_x_end, exception_y_start, exception_y_end

class damage_area:
	def __init__(self, origin):
		self.widthmulti = 1
		self.damagemulti = 1
		self.origin = origin
		self.normal_width = 150
		self.color = (255, 255, 255, 125)  # Weiß mit Transparenz
	
	def getparentposition(self):
		position = self.origin.get_rect().center
		return position
	
	def drawrect(self, screen):
		radius = 200
		target_rect = pygame.Rect(self.getparentposition(), (0, 0)).inflate((radius * 2, radius * 2))
		shape_surf = pygame.Surface(target_rect.size, pygame.SRCALPHA)
		pygame.draw.circle(shape_surf, self.color, (radius, radius), radius)
		screen.blit(shape_surf, target_rect)

	def getrect(self):
		pos = self.getparentposition()
		radius = self.normal_width * self.widthmulti
		return pygame.Rect(pos[0] - radius, pos[1] - radius, radius * 2, radius * 2)
	
	def turnred(self):
		self.color = (255, 0, 0, 125)  # Rot mit Transparenz
	
	def turnwhite(self):
		self.color = (255, 255, 255, 125)  # Weiß mit Transparenz

class damage_screen:
	def __init__(self):
		self.color = (255, 0, 0, 0)  # Rot mit Transparenz
		self.duration = 20  # Dauer des Effekts in Frames
		self.counter = 0

	def trigger(self):
		self.color = (255, 0, 0, 80)  # Effekt starten
		self.counter = self.duration

	def draw(self, screen):
		if self.counter > 0:
			self.counter -= 1
		else:
			self.color = (255, 0, 0, 0)  # Effekt beenden
		effect_surf = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
		effect_surf.fill(self.color)
		screen.blit(effect_surf, (0, 0))

class health_bar:
	def __init__(self, x, y, width, height, object, follow=False):
		self.x = x
		self.y = y
		self.width = width
		self.height = height
		self.max_health = object.gethealth()
		self.health_points = self.max_health
		self.object = object
		self.follow = follow  # Wenn True: Bar folgt dem Objekt automatisch

	def draw(self, screen):
		self.health_points = self.object.gethealth()

		# Position dynamisch aus dem Rect des Objekts berechnen
		if self.follow:
			self.x = self.object.rect.x - 10
			self.y = self.object.rect.y - 12  # 12px über dem Kopf

		pygame.draw.rect(screen, (255, 0, 0), (self.x, self.y, self.width, self.height))
		health_percentage = self.health_points / self.max_health
		pygame.draw.rect(screen, (0, 255, 0), (self.x, self.y, self.width * health_percentage, self.height))

class opponent:
	def __init__(self, health_points, coll_manager):
		self.alive = True
		self.isfirst_skin = False
		self.health_points = health_points
		self.is_moving = True
		self.damagecooldown = 0
		self.tick = 0

		self.offset_x = uniform(-20, 20)
		self.offset_y = uniform(-20, 20)
		self.vx = 0
		self.vy = 0

		self.manager = coll_manager




	def skinchange(self, new_image):
		if isinstance(new_image, str):
			self.image = load_image(new_image, scale=0.25)
		elif isinstance(new_image, pygame.Surface):
			self.image = new_image
		else:
			raise TypeError("skinchange erwartet Pfad (str) oder pygame.Surface")
		self.rect = self.image.get_rect(topleft=(self.x, self.y))

	def spawn_collectible(self):
		r = randint(1, 100)
		if r <= self.collectible_chance:
			if self.collectible == "heal":
				x = "nr"+str(uniform(1, 4))
				x = heal(self.x, self.y, self.player, self.manager)
			elif self.collectible == "aoe":
				x = "nr"+str(uniform(1, 4))
				x = aoe(self.x, self.y, self.player, self.manager)
			elif self.collectible == "revive":
				x = "nr"+str(uniform(1, 4))
				x = revive(self.x, self.y, self.player, self.manager)


	def getdamage(self, damage):
		self.health_points -= damage
		if self.health_points <= 0:
			self.alive = False
			self.spawn_collectible()

	def gethealth(self):
		return self.health_points

	def move(self, dx, dy):
		self.x += dx
		self.y += dy
		self.rect.topleft = (self.x, self.y)
		self.is_moving = True

	def draw(self, screen):
		if self.alive:
			screen.blit(self.image, (self.x, self.y))

	def followplayer(self, player):
		player_x, player_y = self.getplayerposition(player)

		# Ziel mit Offset
		target_x = player_x + self.offset_x
		target_y = player_y + self.offset_y

		dx = target_x - self.x
		dy = target_y - self.y

		dist = (dx**2 + dy**2) ** 0.5

		# STOP wenn nah genug am Ziel, um Flackern zu vermeiden
		if dist < 5:
			self.vx = 0
			self.vy = 0
			return

		# Normalisieren
		dx /= dist
		dy /= dist

		# Smooth Movement
		self.vx += (dx * self.speed - self.vx) * 0.1
		self.vy += (dy * self.speed - self.vy) * 0.1

		self.move(self.vx, self.vy)

	def checkcollision(self, player, damage_screen=None):
		if self.damagecooldown == 0:
			if self.rect.colliderect(player.get_rect()) and self.alive:
				self.damageplayer(player, damage_screen)
		self.damagecooldown += 1
		if self.damagecooldown >= 60:  # 1 Sekunde Cooldown bei
			self.damagecooldown = 0

	def update(self):
		return self.alive
	
	def getplayerposition(self, player):
		player_x = player.x
		player_y = player.y
		return player_x, player_y
	
	def damageplayer(self, player, damage_screen=None):
		player.get_damage(self.damage, damage_screen)
	
	def set_position_out_of_range_of_player(self, player):
		self.exception_x_start, self.exception_x_end, self.exception_y_start, self.exception_y_end = player.get_exception_area()
		while True:
			self.x = randint(0, 1250 - self.rect.width)
			if self.x <self.exception_x_start or self.x > self.exception_x_end:
				break
		while True:
			self.y = randint(0, 720 - self.rect.height)
			if self.y < self.exception_y_start or self.y > self.exception_y_end:
				break
		self.rect.topleft = (self.x, self.y)

	def animation(self):
		self.tick += 1
		if self.tick >= 15 and self.is_moving == True and self.alive == True:
			if self.isfirst_skin == False:
				self.skinchange(self.image1)
				self.isfirst_skin = True
			else:
				self.skinchange(self.image2)
				self.isfirst_skin = False
			self.tick = 0
		elif self.is_moving == False and self.alive == True:
			self.skinchange(self.image1)
			self.isfirst_skin = True
			self.tick = 0

class normal_opp(opponent):
	def __init__(self, x, y):
		opponent.__init__(self, health_points=150)
		self.x = x
		self.y = y
		self.speed = 3 + uniform(-0.5, 0.5)
		self.damage = 15

		# Bilder laden
		script_dir = os.path.dirname(os.path.abspath(__file__))
		normal_opp1_path = os.path.join(script_dir, "normal_opp1.png")
		normal_opp2_path = os.path.join(script_dir, "normal_opp2.png")
		self.image1 = load_image(normal_opp1_path, scale=0.28)
		self.image2 = load_image(normal_opp2_path, scale=0.28)
		self.image = self.image1
		self.rect = self.image.get_rect(topleft=(self.x, self.y))

		self.collectible = "aoe"
		self.collectible_chance = 40  # 40% Chance, ein AOE-Collectible zu droppen

class super_opp(opponent):
	def __init__(self, x, y):
		opponent.__init__(self, health_points=300)
		self.x = x
		self.y = y
		self.speed = 2 + uniform(-0.5, 0.5)
		self.damage = 25

		# Bilder laden
		script_dir = os.path.dirname(os.path.abspath(__file__))
		super_opp1_path = os.path.join(script_dir, "super_opp1.png")
		super_opp2_path = os.path.join(script_dir, "super_opp2.png")
		self.image1 = load_image(super_opp1_path, scale=1)
		self.image2 = load_image(super_opp2_path, scale=1)
		self.image = self.image1
		self.rect = self.image.get_rect(topleft=(self.x, self.y))

		self.collectible = "revive"
		self.collectible_chance = 70  # 70% Chance, ein Revive-Collectible zu droppen

class mini_opp(opponent):
	def __init__(self, x, y):
		opponent.__init__(self, health_points=60)
		self.x = x
		self.y = y
		self.speed = 4 + uniform(-0.5, 0.5)
		self.damage = 5

		# Bilder laden
		script_dir = os.path.dirname(os.path.abspath(__file__))
		mini_opp1_path = os.path.join(script_dir, "mini_opp1.png")
		mini_opp2_path = os.path.join(script_dir, "mini_opp2.png")
		self.image1 = load_image(mini_opp1_path, scale=0.09)
		self.image2 = load_image(mini_opp2_path, scale=0.09)
		self.image = self.image1
		self.rect = self.image.get_rect(topleft=(self.x, self.y))

		self.collectible = "heal"
		self.collectible_chance = 30  # 30% Chance, ein Heal-Collectible zu droppen

class SpawnManager:
    """
    Verwaltet das Spawnen von Gegnern anhand eines Plans (SCHEDULE).

    Jeder Eintrag im Schedule ist ein dict mit:
      - "type"     : Klasse des Gegners (normal_opp, mini_opp, super_opp, BOSS_opp)
      - "count"    : Anzahl der Gegner pro Spawn
      - "tick"     : (optional) einmaliger Spawn bei genau diesem Tick
      - "interval" : (optional) periodischer Spawn alle N Ticks
      - "start"    : (optional, nur mit interval) ab welchem Tick gestartet wird (Standard: 0)
      - "end"      : (optional, nur mit interval) bis zu welchem Tick gespawnt wird
    """
    def __init__(self, schedule: list[dict]):
        self.schedule = schedule
        self.all_opponents = []   # alle je gespawnten Gegner
        self.opp_bars = []        # zugehörige Healthbars

    def tick(self, current_tick: int, player) -> list:
        """
        Gibt die neu gespawnten Gegner dieses Ticks zurück
        und fügt sie intern zur Gesamtliste hinzu.
        """
        newly_spawned = []

        for entry in self.schedule:
            opp_type  = entry["type"]
            count     = entry.get("count", 1)
            should_spawn = False

            if "tick" in entry and entry["tick"] == current_tick:
                should_spawn = True

            elif "interval" in entry:
                start = entry.get("start", 0)
                end   = entry.get("end", float("inf"))
                if start >= current_tick >= end:   # Tick zählt runter, daher >=
                    interval = entry["interval"]
                    if (current_tick - start) % interval == 0:
                        should_spawn = True

            if should_spawn:
                for _ in range(count):
                    new_opp = opp_type(0, 0)
                    new_opp.set_position_out_of_range_of_player(player)
                    newly_spawned.append(new_opp)
                    self.opp_bars.append(
                        health_bar(-40, 0, 60, 7, new_opp, follow=True)
                    )

        self.all_opponents.extend(newly_spawned)
        return newly_spawned

    def cleanup(self):
        """Tote Gegner und ihre Healthbars entfernen."""
        self.all_opponents = [o for o in self.all_opponents if o.alive]
        self.opp_bars      = [b for b in self.opp_bars      if b.object.alive]

class collectible:
	def __init__(self, x, y, image_path, effect, player, manager):
		self.x = x
		self.y = y
		self.image = load_image(image_path, scale=0.25)
		self.rect = self.image.get_rect(topleft=(self.x, self.y))
		self.collected = False
		self.effect = effect
		self.player = player
		manager.collectibles.append(self)


	def spawn(self, screen):
		if self.collected == False:
			screen.blit(self.image, (self.x, self.y))
	
	def collectcheck(self, opponents):
		if self.rect.colliderect(self.player.get_rect()):
			self.collected = True
			self.trigger_effect(opponents)

	def trigger_effect(self, opponents):
		if self.effect == "health":
			self.player.health_points += 5
		elif self.effect == "aoe":
			for opp in opponents:
				opp.getdamage(10)
		elif self.effect == "revive":
			self.player.health_points = self.player.max_health
			self.player.maxhealth += 20

class heal(collectible):
	def __init__(self, x, y, player, manager):
		script_dir = os.path.dirname(os.path.abspath(__file__))
		image_path = os.path.join(script_dir, "heal.png")
		super().__init__(x, y, image_path, effect="health", player=player, manager=manager)

class aoe(collectible):
	def __init__(self, x, y, player, manager):
		script_dir = os.path.dirname(os.path.abspath(__file__))
		image_path = os.path.join(script_dir, "aoe.png")
		super().__init__(x, y, image_path, effect="aoe", player=player, manager=manager)

class revive(collectible):
	def __init__(self, x, y, player, manager):
		script_dir = os.path.dirname(os.path.abspath(__file__))
		image_path = os.path.join(script_dir, "revive.png")
		super().__init__(x, y, image_path, effect="revive", player=player, manager=manager)

class collectible_manager():
	def __init__(self, player):
		self.collectibles = []
		self.player = player

	def collectible_tick(self, screen, opponents):
		for i in self.collectibles:
			i.collectcheck(opponents)
			if i.collected == False:
				i.spawn(screen)
			if i.collected == True:
				self.collectibles.remove(i)