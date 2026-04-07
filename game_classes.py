import os
import pygame

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
	def __init__(self, x, y, idle_path, run_path, scale=0.25, health_points=100):
		self.x = x
		self.y = y
		self.alive = True
		self.scale = scale
		self.health_points = health_points

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

	def move(self, dx, dy):
		from game import height, width
		if self.x + dx > 0 and self.x + dx < width - self.rect.width:
			self.x += dx
		if self.y + dy > 0 and self.y + dy < height - self.rect.height:
			self.y += dy
		self.rect.topleft = (self.x, self.y)

	def draw(self, screen):
		if self.alive:
			screen.blit(self.image, (self.x, self.y))

	def get_rect(self):
		return self.rect

	def tick_animation(self, is_moving):
		"""Pro Frame aufrufen. Verwaltet Animation intern basierend auf is_moving."""
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

	def input_monitoring(self, keys, area, opponents):
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

		if keys[pygame.K_SPACE] and self.attack_cooldown == 0:
			for opp in opponents:
				if opp.rect.colliderect(area.getrect()):
					opp.getdamage(50)
			self.attack_cooldown = 30  # 0.5 Sekunden Cooldown bei 60 FPS


	def get_damage(self, damage):
		if self.alive:
			self.health_points -= damage
			if self.health_points <= 0:
				self.dead()
	
	def gethealth(self):
		return self.health_points

class damage_area:
	def __init__(self, origin):
		self.widthmulti = 1
		self.damagemulti = 1
		self.origin = origin
		self.normal_width = 150

	def getparentposition(self):
		position = self.origin.get_rect().center
		return position

	def draw(self, screen):
		pygame.draw.circle(screen, (0,0,0,500), self.getparentposition(), self.normal_width * self.widthmulti, 5)
		pass

	def getrect(self):
		pos = self.getparentposition()
		radius = self.normal_width * self.widthmulti
		return pygame.Rect(pos[0] - radius, pos[1] - radius, radius * 2, radius * 2)


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
	def __init__(self, health_points):
		self.alive = True
		self.isfirst_skin = False
		self.health_points = health_points
		self.is_moving = True
		self.damagecooldown = 0

	def skinchange(self, new_image):
		if isinstance(new_image, str):
			self.image = load_image(new_image, scale=0.25)
		elif isinstance(new_image, pygame.Surface):
			self.image = new_image
		else:
			raise TypeError("skinchange erwartet Pfad (str) oder pygame.Surface")
		self.rect = self.image.get_rect(topleft=(self.x, self.y))

	def getdamage(self, damage):
		self.health_points -= damage
		if self.health_points <= 0:
			self.alive = False

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

	def follow(self, player, speed):
		player_x, player_y = self.getplayerposition(player)
		if self.alive:
			if player_x < self.x:
				self.move(-speed, 0)
			elif player_x > self.x:
				self.move(speed, 0)
			if player_y < self.y:
				self.move(0, -speed)
			elif player_y > self.y:
				self.move(0, speed)
			if self.x == player_x and self.y == player_y:
				self.is_moving = False

	def checkcollision(self, player):
		if self.damagecooldown == 0:
			if self.rect.colliderect(player.get_rect()) and self.alive:
				self.damageplayer(player)
		self.damagecooldown += 1
		if self.damagecooldown >= 60:  # 1 Sekunde Cooldown bei
			self.damagecooldown = 0

	def update(self):
		return self.alive

class normal_opp(opponent):
	def __init__(self, x, y):
		opponent.__init__(self, health_points=100)
		self.x = x
		self.y = y
		self.tick = 0
		self.script_dir = os.path.dirname(os.path.abspath(__file__))
		self.normal_opp1_path = os.path.join(self.script_dir, "normal_opp1.png")
		self.normal_opp2_path = os.path.join(self.script_dir, "normal_opp2.png")

		self.normal_opp1_image = load_image(self.normal_opp1_path, scale=0.25)
		self.normal_opp2_image = load_image(self.normal_opp2_path, scale=0.25)

		self.image = self.normal_opp1_image
		self.rect = self.image.get_rect(topleft=(self.x, self.y))

	def animation(self,):
		self.tick += 1
		if self.tick >= 15 and self.is_moving == True and self.alive == True:
			if self.isfirst_skin == False:
				self.skinchange(self.normal_opp1_image)
				self.isfirst_skin = True
			else:
				self.skinchange(self.normal_opp2_image)
				self.isfirst_skin = False
			self.tick = 0
		elif self.is_moving == False and self.alive == True:
			self.skinchange(self.normal_opp1_image)
			self.isfirst_skin = True
			self.tick = 0

	def getplayerposition(self, player):
		player_x = player.x
		player_y = player.y
		return player_x, player_y

	def update(self):
		return self.alive
	
	def followplayer(self, player):
		self.follow(player, speed=2.5)
	
	def damageplayer(self, player):
		player.get_damage(20)