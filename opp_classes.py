from game_classes import health_bar, load_image, SCRIPT_DIR
from resource_path import get_resource_path
from random import randint, uniform
import pygame
import os


class opponent:
	"""
	Abstrakte Basisklasse für alle Gegnertypen.
	Enthält gemeinsame Logik: Bewegung, Schadennahme, Kollision, Animation.
	Konkrete Typen (NormalOpp, SuperOpp, MiniOpp) erben von hier
	und setzen typspezifische Werte (HP, Speed, Sprites, Drop-Typ).
	"""

	def __init__(self, health_points):
		self.alive          = True
		self.isfirst_skin   = False          # Welcher der zwei Animationsframes aktiv ist
		self.health_points  = health_points
		self.damagecooldown = 0              # Verhindert dass Berührungsschaden jedes Frame auslöst
		self.tick           = 0             # Frame-Zähler für Animation

		# Kleiner zufälliger Versatz damit Gegner nicht alle exakt auf dieselbe Stelle laufen
		self.offset_x = uniform(-20, 20)
		self.offset_y = uniform(-20, 20)

		# Aktuelle Geschwindigkeit (wird durch smooth movement verändert)
		self.vx = 0
		self.vy = 0

		# Werden in den Unterklassen gesetzt:
		# collectible        – Welchen Drop-Typ dieser Gegner hinterlässt ("heal", "aoe", "revive")
		# collectible_chance – Prozentuale Dropchance (0–100)
		self.collectible        = None
		self.collectible_chance = 0

	def skinchange(self, new_image):
		"""
		Wechselt das aktuelle Sprite.
		Akzeptiert entweder einen Dateipfad (str) oder eine fertige pygame.Surface.
		"""
		if isinstance(new_image, str):
			self.image = load_image(new_image, scale=0.25)
		elif isinstance(new_image, pygame.Surface):
			self.image = new_image
		else:
			raise TypeError("skinchange erwartet Pfad (str) oder pygame.Surface")
		self.rect = self.image.get_rect(topleft=(self.x, self.y))

	def getdamage(self, damage):
		"""
		Zieht Schaden ab. Fällt HP auf 0 oder darunter → alive = False.
		Der Drop-Spawn passiert extern im CollectibleManager (nicht hier).
		"""
		self.health_points -= damage
		if self.health_points <= 0:
			self.alive = False

	def gethealth(self):
		"""Gibt aktuelle HP zurück (wird von HealthBar genutzt)."""
		return self.health_points

	def move(self, dx, dy):
		"""Verschiebt den Gegner und aktualisiert das Kollisionsrechteck."""
		self.x += dx
		self.y += dy
		self.rect.topleft = (self.x, self.y)

	def draw(self, screen):
		"""Zeichnet den Gegner (nur wenn lebendig)."""
		if self.alive:
			screen.blit(self.image, (self.x, self.y))

	def followplayer(self, player):
		"""
		Bewegt den Gegner mit sanftem Smooth-Movement auf Marx zu.
		Der individuelle Offset sorgt dafür dass nicht alle Gegner
		auf exakt denselben Punkt laufen → natürlicheres Aussehen.
		Unter 5 Pixel Distanz zum Ziel: Stopp (verhindert Flackern).
		"""
		target_x = player.x + self.offset_x
		target_y = player.y + self.offset_y

		dx = target_x - self.x
		dy = target_y - self.y
		dist = (dx**2 + dy**2) ** 0.5

		if dist < 5:
			self.vx = self.vy = 0   # nah genug → nicht weiter bewegen
			return

		# Richtungsvektor normalisieren (Länge = 1)
		dx /= dist
		dy /= dist

		# Geschwindigkeit sanft in Richtung Zielgeschwindigkeit schieben (10% pro Frame)
		self.vx += (dx * self.speed - self.vx) * 0.1
		self.vy += (dy * self.speed - self.vy) * 0.1

		self.move(self.vx, self.vy)

	def checkcollision(self, player, damage_screen=None):
		"""
		Prüft ob der Gegner Marx berührt und fügt ggf. Berührungsschaden zu.
		Cooldown von 60 Frames (1 Sek) verhindert Dauerschaden bei Kontakt.
		"""
		if self.damagecooldown == 0 and self.rect.colliderect(player.get_rect()) and self.alive:
			player.get_damage(self.damage, damage_screen)
		self.damagecooldown += 1
		if self.damagecooldown >= 60:
			self.damagecooldown = 0

	def update(self):
		"""Gibt zurück ob der Gegner noch am Leben ist."""
		return self.alive

	def set_position_out_of_range_of_player(self, player):
		"""
		Setzt die Spawn-Position zufällig, aber außerhalb des exception_radius
		von Marx. Verhindert Spawn direkt neben dem Spieler.
		X und Y werden unabhängig voneinander per while-Schleife gewürfelt.
		Nutzt die Bildschirmgröße des Spielers statt hardcodierter Werte.
		"""
		ex0, ex1, ey0, ey1 = player.get_exception_area()
		screen_w = player.screen_w
		screen_h = player.screen_h

		for _ in range(1000):  # Sicherheitslimit gegen theoretische Endlosschleife
			self.x = randint(0, screen_w - self.rect.width)
			if self.x < ex0 or self.x > ex1:
				break
		for _ in range(1000):
			self.y = randint(0, screen_h - self.rect.height)
			if self.y < ey0 or self.y > ey1:
				break
		self.rect.topleft = (self.x, self.y)

	def animation(self):
		"""
		Schaltet alle 15 Frames zwischen image1 und image2 um (Lauf-Animation).
		Steht der Gegner still (vx und vy nahe 0), bleibt image1 (Idle) aktiv.
		"""
		is_moving = abs(self.vx) > 0.1 or abs(self.vy) > 0.1

		self.tick += 1
		if self.tick >= 15 and is_moving and self.alive:
			if not self.isfirst_skin:
				self.skinchange(self.image1)
				self.isfirst_skin = True
			else:
				self.skinchange(self.image2)
				self.isfirst_skin = False
			self.tick = 0
		elif not is_moving and self.alive:
			self.skinchange(self.image1)
			self.isfirst_skin = True
			self.tick = 0


# ─────────────────────────────────────────────────────────────────────────────
# Gegner-Unterklassen
# ─────────────────────────────────────────────────────────────────────────────

class normal_opp(opponent):
	"""
	Standardgegner. Mittlere HP, mittlere Geschwindigkeit.
	Droppt beim Tod mit 70% Chance ein AOE-Collectible.
	"""
	def __init__(self, x, y):
		super().__init__(health_points=150)
		self.x = x
		self.y = y
		self.speed  = 3 + uniform(-0.5, 0.5)  # leichte Zufallsvariation
		self.damage = 15

		self.image1 = load_image(get_resource_path("normal_opp1.png"), scale=0.28)
		self.image2 = load_image(get_resource_path("normal_opp2.png"), scale=0.28)
		self.image  = self.image1
		self.rect   = self.image.get_rect(topleft=(self.x, self.y))

		self.collectible        = "aoe"   # Drop-Typ
		self.collectible_chance = 70      # 70% Dropchance


class super_opp(opponent):
	"""
	Starker Gegner. Hohe HP, langsam, hoher Schaden.
	Droppt beim Tod mit 90% Chance ein Revive-Collectible (heilt auf Max + erhöht Max-HP).
	Letzter Gegner vor BOSS (in Progress) → Belohnung entsprechend wertvoll.
	"""
	def __init__(self, x, y):
		super().__init__(health_points=300)
		self.x = x
		self.y = y
		self.speed  = 2 + uniform(-0.5, 0.5)
		self.damage = 25

		self.image1 = load_image(get_resource_path("super_opp1.png"), scale=1)
		self.image2 = load_image(get_resource_path("super_opp2.png"), scale=1)
		self.image  = self.image1
		self.rect   = self.image.get_rect(topleft=(self.x, self.y))

		self.collectible        = "revive"
		self.collectible_chance = 90


class mini_opp(opponent):
	"""
	Kleiner, schneller Gegner mit wenig HP und geringem Schaden.
	Spawnt periodisch in Wellen. Droppt mit 30% Chance ein Heal-Collectible.
	"""
	def __init__(self, x, y):
		super().__init__(health_points=60)
		self.x = x
		self.y = y
		self.speed  = 4 + uniform(-0.5, 0.5)
		self.damage = 5

		self.image1 = load_image(get_resource_path("mini_opp1.png"), scale=0.09)
		self.image2 = load_image(get_resource_path("mini_opp2.png"), scale=0.09)
		self.image  = self.image1
		self.rect   = self.image.get_rect(topleft=(self.x, self.y))

		self.collectible        = "heal"
		self.collectible_chance = 30


# ─────────────────────────────────────────────────────────────────────────────
# SpawnManager
# ─────────────────────────────────────────────────────────────────────────────

class SpawnManager:
	"""
	Steuert das Spawnen aller Gegner anhand eines deklarierten Zeitplans (SCHEDULE).

	Statt im Game-Loop jede Welle hart zu coden, reicht es ein dict pro Welle
	in die SCHEDULE-Liste einzutragen. Der SpawnManager prüft jeden Frame
	ob eine Welle fällig ist und spawnt sie dann automatisch.

	SCHEDULE-Format (jeder Eintrag ist ein dict):
	  "type"     → Gegnerklasse (NormalOpp, MiniOpp, SuperOpp …)
	  "count"    → Anzahl Gegner pro Spawn (Standard: 1)
	  "tick"     → einmaliger Spawn wenn roundtick == dieser Wert
	  "interval" → periodischer Spawn alle N Ticks (alternativ zu "tick")
	  "start"    → ab welchem Tick das Intervall gilt  (Standard: aktueller Tick)
	  "end"      → bis zu welchem Tick gespawnt wird    (Standard: 0)

	Hinweis: roundtick zählt von 3600 auf 0 hinunter (= 60 Sekunden bei 60 FPS).

	Diese Idee stammt von meinem Schwiegeronkel (Informatiker), wurde aber von mir umgesetzt.
	"""

	def __init__(self, schedule):
		self.schedule      = schedule
		self.all_opponents = []   # alle je gespawnten Gegner (auch tote bis Cleanup)
		self.opp_bars      = []   # Healthbars für alle gespawnten Gegner

	def tick(self, current_tick, player):
		"""
		Muss jeden Frame aufgerufen werden. Gibt neu gespawnte Gegner zurück,
		die sofort zur aktiven opponents-Liste im Game-Loop hinzugefügt werden.
		"""
		newly_spawned = []

		for entry in self.schedule:
			opp_type     = entry["type"]
			count        = entry.get("count", 1)
			should_spawn = False

			# ── Einmaliger Spawn ──
			if "tick" in entry and entry["tick"] == current_tick:
				should_spawn = True

			# ── Periodischer Spawn ──
			elif "interval" in entry:
				start = entry.get("start", current_tick)
				end   = entry.get("end", 0)
				# Gültigkeitsbereich: end (kleine Zahl) ≤ current_tick ≤ start (große Zahl)
				if end <= current_tick <= start:
					# Feuert wenn der Abstand zu start ein Vielfaches des Intervalls ist
					if (current_tick - start) % entry["interval"] == 0:
						should_spawn = True

			if should_spawn:
				for _ in range(count):
					new_opp = opp_type(0, 0)
					new_opp.set_position_out_of_range_of_player(player)
					newly_spawned.append(new_opp)
					# Healthbar direkt miterstellen; follow=True → schwebt über Gegner
					self.opp_bars.append(health_bar(-40, 0, 60, 7, new_opp, follow=True))

		self.all_opponents.extend(newly_spawned)
		return newly_spawned

	def cleanup(self):
		"""
		Entfernt tote Gegner und deren Healthbars aus den internen Listen.
		Muss nach dem collectible_tick-Aufruf, aber noch im selben Frame, aufgerufen werden.
		"""
		self.all_opponents = [o for o in self.all_opponents if o.alive]
		self.opp_bars      = [b for b in self.opp_bars      if b.object.alive]
