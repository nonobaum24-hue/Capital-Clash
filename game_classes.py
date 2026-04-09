import os
import pygame
from random import randint, uniform

# Bild-Cache und Helfer zum (einmaligen) Laden + Skalieren von Bildern
_IMAGE_CACHE = {}
def load_image(path, scale=0.25):
	key = (os.path.abspath(path), float(scale))
	if key in _IMAGE_CACHE:
		return _IMAGE_CACHE[key]
	img = pygame.image.load(path).convert_alpha()
	img = pygame.transform.scale(img,
		(int(img.get_width() * scale),
		 int(img.get_height() * scale)))
	_IMAGE_CACHE[key] = img
	return img


# ── Spieler ───────────────────────────────────────────────────────────────────

class marx:
	def __init__(self, x, y, idle_path, run_path, scale=0.25, health_points=100, screen_w=1250, screen_h=720):
		self.x = x
		self.y = y
		self.alive = True
		self.scale = scale
		self.health_points = health_points
		self.max_health = health_points          # FIX: max_health gespeichert (für Heal-Cap und Revive)
		self.damage = 30
		self.exception_radius = 150

		self.screen_w = screen_w
		self.screen_h = screen_h

		self.stand_bild = load_image(idle_path, scale=self.scale)
		self.lauf_bild  = load_image(run_path,  scale=self.scale)

		self.image = self.stand_bild
		self.rect  = self.image.get_rect(topleft=(self.x, self.y))

		self.framecount_skin  = 0
		self.is_first_skin    = True
		self.prev_is_moving   = False
		self.attack_cooldown  = 0

	def dead(self):
		self.alive = False

	def move(self, dx, dy):
		if 0 < self.x + dx < self.screen_w - self.rect.width:
			self.x += dx
		if 0 < self.y + dy < self.screen_h - self.rect.height:
			self.y += dy
		self.rect.topleft = (self.x, self.y)

	def draw(self, screen):
		if self.alive:
			screen.blit(self.image, (self.x, self.y))

	def get_rect(self):
		return self.rect

	def tick_animation(self, is_moving):
		if is_moving and not self.prev_is_moving:
			self.image = self.lauf_bild
			self.is_first_skin  = False
			self.framecount_skin = 0
			self.rect = self.image.get_rect(topleft=(self.x, self.y))
		elif is_moving:
			self.framecount_skin += 1
			if self.framecount_skin >= 15:
				self.image = self.stand_bild if not self.is_first_skin else self.lauf_bild
				self.is_first_skin = not self.is_first_skin
				self.rect = self.image.get_rect(topleft=(self.x, self.y))
				self.framecount_skin = 0
		else:
			self.image = self.stand_bild
			self.framecount_skin = 0
			self.is_first_skin   = True

		self.prev_is_moving = is_moving

	def update(self):
		return self.alive, (self.x, self.y)

	def input_monitoring(self, keys, area, opponents):
		if keys[pygame.K_LEFT]:  self.move(-5,  0)
		if keys[pygame.K_RIGHT]: self.move( 5,  0)
		if keys[pygame.K_UP]:    self.move( 0, -5)
		if keys[pygame.K_DOWN]:  self.move( 0,  5)

		if self.attack_cooldown > 0:
			self.attack_cooldown -= 1
			area.turnred()
		else:
			area.turnwhite()

		if keys[pygame.K_SPACE] and self.attack_cooldown == 0:
			in_range = [o for o in opponents if o.rect.colliderect(area.getrect())]
			if in_range:
				randint(0, len(in_range) - 1)
				in_range[randint(0, len(in_range) - 1)].getdamage(self.damage)
			self.attack_cooldown = 30

	def get_damage(self, damage, damage_screen=None):
		if self.alive:
			self.health_points -= damage
			if damage_screen:
				damage_screen.trigger()
			if self.health_points <= 0:
				self.dead()

	def heal(self, amount):                      # FIX: neue heal()-Methode, cappt auf max_health
		if self.alive:
			self.health_points = min(self.max_health, self.health_points + amount)

	def gethealth(self):
		return self.health_points

	def get_exception_area(self):
		x, y = self.get_rect().center
		return (x - self.exception_radius, x + self.exception_radius,
				y - self.exception_radius, y + self.exception_radius)


# ── Kampf-Hilfsobjekte ────────────────────────────────────────────────────────

class damage_area:
	def __init__(self, origin):
		self.widthmulti  = 1
		self.damagemulti = 1
		self.origin      = origin
		self.normal_width = 150
		self.color = (255, 255, 255, 125)

	def getparentposition(self):
		return self.origin.get_rect().center

	def drawrect(self, screen):
		radius = 200
		target_rect = pygame.Rect(self.getparentposition(), (0, 0)).inflate((radius * 2, radius * 2))
		shape_surf = pygame.Surface(target_rect.size, pygame.SRCALPHA)
		pygame.draw.circle(shape_surf, self.color, (radius, radius), radius)
		screen.blit(shape_surf, target_rect)

	def getrect(self):
		pos    = self.getparentposition()
		radius = self.normal_width * self.widthmulti
		return pygame.Rect(pos[0] - radius, pos[1] - radius, radius * 2, radius * 2)

	def turnred(self):   self.color = (255,   0, 0, 125)
	def turnwhite(self): self.color = (255, 255, 255, 125)


class damage_screen:
	def __init__(self):
		self.color    = (255, 0, 0, 0)
		self.duration = 20
		self.counter  = 0

	def trigger(self):
		self.color   = (255, 0, 0, 80)
		self.counter = self.duration

	def draw(self, screen):
		if self.counter > 0:
			self.counter -= 1
		else:
			self.color = (255, 0, 0, 0)
		surf = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
		surf.fill(self.color)
		screen.blit(surf, (0, 0))


class health_bar:
	def __init__(self, x, y, width, height, object, follow=False):
		self.x          = x
		self.y          = y
		self.width      = width
		self.height     = height
		self.max_health = object.gethealth()
		self.object     = object
		self.follow     = follow

	def draw(self, screen):
		hp = self.object.gethealth()
		if self.follow:
			self.x = self.object.rect.x - 10
			self.y = self.object.rect.y - 12
		pygame.draw.rect(screen, (255, 0, 0), (self.x, self.y, self.width, self.height))
		pct = max(0, hp / self.max_health)
		pygame.draw.rect(screen, (0, 255, 0), (self.x, self.y, self.width * pct, self.height))


# ── Gegner-Basisklasse ────────────────────────────────────────────────────────

class opponent:
	# FIX: coll_manager komplett entfernt — Drops werden jetzt vom collectible_manager erkannt
	def __init__(self, health_points):
		self.alive          = True
		self.isfirst_skin   = False
		self.health_points  = health_points
		self.is_moving      = True
		self.damagecooldown = 0
		self.tick           = 0
		self.offset_x       = uniform(-20, 20)
		self.offset_y       = uniform(-20, 20)
		self.vx = 0
		self.vy = 0

		# Wird in Unterklassen gesetzt:
		self.collectible        = None
		self.collectible_chance = 0

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

	def followplayer(self, player):
		target_x = player.x + self.offset_x
		target_y = player.y + self.offset_y
		dx = target_x - self.x
		dy = target_y - self.y
		dist = (dx**2 + dy**2) ** 0.5
		if dist < 5:
			self.vx = self.vy = 0
			return
		dx /= dist
		dy /= dist
		self.vx += (dx * self.speed - self.vx) * 0.1
		self.vy += (dy * self.speed - self.vy) * 0.1
		self.move(self.vx, self.vy)

	def checkcollision(self, player, damage_screen=None):
		if self.damagecooldown == 0 and self.rect.colliderect(player.get_rect()) and self.alive:
			player.get_damage(self.damage, damage_screen)
		self.damagecooldown += 1
		if self.damagecooldown >= 60:
			self.damagecooldown = 0

	def update(self):
		return self.alive

	def getplayerposition(self, player):
		return player.x, player.y

	def set_position_out_of_range_of_player(self, player):
		ex0, ex1, ey0, ey1 = player.get_exception_area()
		while True:
			self.x = randint(0, 1250 - self.rect.width)
			if self.x < ex0 or self.x > ex1:
				break
		while True:
			self.y = randint(0, 720 - self.rect.height)
			if self.y < ey0 or self.y > ey1:
				break
		self.rect.topleft = (self.x, self.y)

	def animation(self):
		self.tick += 1
		if self.tick >= 15 and self.is_moving and self.alive:
			if not self.isfirst_skin:
				self.skinchange(self.image1)
				self.isfirst_skin = True
			else:
				self.skinchange(self.image2)
				self.isfirst_skin = False
			self.tick = 0
		elif not self.is_moving and self.alive:
			self.skinchange(self.image1)
			self.isfirst_skin = True
			self.tick = 0


# ── Gegner-Unterklassen ───────────────────────────────────────────────────────

class normal_opp(opponent):
	def __init__(self, x, y):
		super().__init__(health_points=150)
		self.x = x
		self.y = y
		self.speed  = 3 + uniform(-0.5, 0.5)
		self.damage = 15

		script_dir = os.path.dirname(os.path.abspath(__file__))
		self.image1 = load_image(os.path.join(script_dir, "normal_opp1.png"), scale=0.28)
		self.image2 = load_image(os.path.join(script_dir, "normal_opp2.png"), scale=0.28)
		self.image  = self.image1
		self.rect   = self.image.get_rect(topleft=(self.x, self.y))

		self.collectible        = "aoe"
		self.collectible_chance = 70


class super_opp(opponent):
	def __init__(self, x, y):
		super().__init__(health_points=300)
		self.x = x
		self.y = y
		self.speed  = 2 + uniform(-0.5, 0.5)
		self.damage = 25

		script_dir = os.path.dirname(os.path.abspath(__file__))
		self.image1 = load_image(os.path.join(script_dir, "super_opp1.png"), scale=1)
		self.image2 = load_image(os.path.join(script_dir, "super_opp2.png"), scale=1)
		self.image  = self.image1
		self.rect   = self.image.get_rect(topleft=(self.x, self.y))

		self.collectible        = "revive"
		self.collectible_chance = 90


class mini_opp(opponent):
	def __init__(self, x, y):
		super().__init__(health_points=60)
		self.x = x
		self.y = y
		self.speed  = 4 + uniform(-0.5, 0.5)
		self.damage = 5

		script_dir = os.path.dirname(os.path.abspath(__file__))
		self.image1 = load_image(os.path.join(script_dir, "mini_opp1.png"), scale=0.09)
		self.image2 = load_image(os.path.join(script_dir, "mini_opp2.png"), scale=0.09)
		self.image  = self.image1
		self.rect   = self.image.get_rect(topleft=(self.x, self.y))

		self.collectible        = "heal"
		self.collectible_chance = 30


# ── SpawnManager ──────────────────────────────────────────────────────────────

class SpawnManager:
	"""
	Verwaltet das Spawnen von Gegnern anhand eines Plans (SCHEDULE).

	Jeder Eintrag im Schedule ist ein dict mit:
	  - "type"     : Klasse des Gegners (normal_opp, mini_opp, super_opp …)
	  - "count"    : Anzahl der Gegner pro Spawn (Standard: 1)
	  - "tick"     : (optional) einmaliger Spawn bei genau diesem Tick
	  - "interval" : (optional) periodischer Spawn alle N Ticks
	  - "start"    : (optional, nur mit interval) ab welchem Tick gestartet wird
	  - "end"      : (optional, nur mit interval) bis zu welchem Tick gespawnt wird (Standard: 0)
	"""
	def __init__(self, schedule):
		self.schedule      = schedule
		self.all_opponents = []
		self.opp_bars      = []

	def tick(self, current_tick, player):
		newly_spawned = []
		for entry in self.schedule:
			opp_type     = entry["type"]
			count        = entry.get("count", 1)
			should_spawn = False

			if "tick" in entry and entry["tick"] == current_tick:
				should_spawn = True
			elif "interval" in entry:
				start = entry.get("start", current_tick)
				end   = entry.get("end", 0)
				# Tick zählt runter: start (hoch) >= current_tick >= end (niedrig)
				if end <= current_tick <= start:
					if (current_tick - start) % entry["interval"] == 0:
						should_spawn = True

			if should_spawn:
				for _ in range(count):
					new_opp = opp_type(0, 0)
					new_opp.set_position_out_of_range_of_player(player)
					newly_spawned.append(new_opp)
					self.opp_bars.append(health_bar(-40, 0, 60, 7, new_opp, follow=True))

		self.all_opponents.extend(newly_spawned)
		return newly_spawned

	def cleanup(self):
		self.all_opponents = [o for o in self.all_opponents if o.alive]
		self.opp_bars      = [b for b in self.opp_bars      if b.object.alive]


# ── Collectibles ──────────────────────────────────────────────────────────────

class collectible:
	def __init__(self, x, y, image_path, effect, player):
		self.x         = x
		self.y         = y
		self.image     = load_image(image_path, scale=0.25)
		self.rect      = self.image.get_rect(topleft=(self.x, self.y))
		self.collected = False
		self.effect    = effect
		self.player    = player

	def spawn(self, screen):
		if not self.collected:
			screen.blit(self.image, (self.x, self.y))

	def collectcheck(self, opponents):
		if not self.collected and self.rect.colliderect(self.player.get_rect()):
			self.collected = True
			self.trigger_effect(opponents)

	def trigger_effect(self, opponents):
		if self.effect == "health":
			self.player.heal(25)
		elif self.effect == "aoe":
			for opp in opponents:
				opp.getdamage(10)
		elif self.effect == "revive":
			self.player.max_health += 10
			self.player.health_points = self.player.max_health


class heal(collectible):
	def __init__(self, x, y, player):
		script_dir = os.path.dirname(os.path.abspath(__file__))
		super().__init__(x, y, os.path.join(script_dir, "heal.png"), "health", player)

class aoe(collectible):
	def __init__(self, x, y, player):
		script_dir = os.path.dirname(os.path.abspath(__file__))
		super().__init__(x, y, os.path.join(script_dir, "aoe.png"), "aoe", player)

class revive(collectible):
	def __init__(self, x, y, player):
		script_dir = os.path.dirname(os.path.abspath(__file__))
		super().__init__(x, y, os.path.join(script_dir, "revive.png"), "revive", player)

# Mapping: collectible-String → Klasse
_COLLECTIBLE_MAP = {
	"heal":   heal,
	"aoe":    aoe,
	"revive": revive,
}


# ── collectible_manager ───────────────────────────────────────────────────────

class collectible_manager:
	def __init__(self, player):
		self.player       = player
		self.collectibles = []
		self._dropped     = set()   # IDs von Gegnern, die schon einen Drop hatten

	def collectible_tick(self, screen, opponents):
		#Dran denken: vor dem Cleanup wegen tote-Gegner-Bug
		for opp in opponents:
			if not opp.alive and id(opp) not in self._dropped:
				self._dropped.add(id(opp))
				if opp.collectible and randint(1, 100) <= opp.collectible_chance:
					cls = _COLLECTIBLE_MAP.get(opp.collectible)
					if cls:
						self.collectibles.append(cls(opp.x, opp.y, self.player))

		active = []
		for c in self.collectibles:
			c.collectcheck(opponents)
			if not c.collected:
				c.spawn(screen)
				active.append(c)
		self.collectibles = active
