import os
import pygame
from random import randint, uniform

# ─────────────────────────────────────────────────────────────────────────────
# Bild-Cache
# ─────────────────────────────────────────────────────────────────────────────

# Globales Dictionary, das bereits geladene Bilder speichert.
# Schlüssel ist ein Tupel aus (absoluter Pfad, Scale-Faktor), damit dasselbe
# Bild in verschiedenen Größen separat gecacht werden kann.
_IMAGE_CACHE = {}

def load_image(path, scale=0.25):
	"""
	Lädt ein Bild von der Festplatte, skaliert es und gibt es zurück.
	Wurde dasselbe Bild (gleicher Pfad + gleiche Scale) schon einmal geladen,
	kommt es direkt aus dem Cache — kein doppeltes Laden nötig.
	
	Für diese Funktion wurde KI verwendet, da ich an der Performance und Fehlerlosigkeit verzwifelt bin.
	"""
	key = (os.path.abspath(path), float(scale))
	if key in _IMAGE_CACHE:
		return _IMAGE_CACHE[key]                        # Cache-Treffer → sofort zurück
	img = pygame.image.load(path).convert_alpha()      # mit Alpha laden (Transparenz)
	img = pygame.transform.scale(img,
		(int(img.get_width()  * scale),
		 int(img.get_height() * scale)))
	_IMAGE_CACHE[key] = img                            # für spätere Aufrufe speichern
	return img


# ─────────────────────────────────────────────────────────────────────────────
# Spieler-Klasse
# ─────────────────────────────────────────────────────────────────────────────

class marx:
	"""
	Repräsentiert den Spielercharakter Marx.
	Kümmert sich um Bewegung, Angriff, Schadensnahme, Heilung und Animation.
	"""

	def __init__(self, x, y, idle_path, run_path, scale=0.25,
	             health_points=100, screen_w=1250, screen_h=720):
		"""
		x, y          – Startposition (relativ zu obere linke Ecke)
		idle_path     – Pfad zum Standbild
		run_path      – Pfad zum Laufbild
		scale         – Skalierungsfaktor für die Sprites
		health_points – Startleben (und gleichzeitig das Maximum)
		screen_w/h    – Bildschirmgröße; nötig damit Marx nicht rausläuft
		"""
		self.x = x
		self.y = y
		self.alive = True

		self.scale         = scale
		self.health_points = health_points
		self.max_health    = health_points   # Obergrenze für heal(); wird von Revive erhöht
		self.damage        = 30              # Schaden pro Angriff

		# Radius um Marx herum, in dem keine Gegner spawnen dürfen
		self.exception_radius = 150

		# Bildschirmgrenzen für die Bewegungsbegrenzung
		self.screen_w = screen_w
		self.screen_h = screen_h

		# Beide Animations-Sprites vorladen
		self.stand_bild = load_image(idle_path, scale=self.scale)  # stehendes Bild
		self.lauf_bild  = load_image(run_path,  scale=self.scale)  # laufendes Bild

		# Beim Start: Idle-Bild aktiv
		self.image = self.stand_bild
		self.rect  = self.image.get_rect(topleft=(self.x, self.y))

		# Animations-Zustand
		self.framecount_skin = 0     # Zählt Frames seit letztem Skin-Wechsel
		self.is_first_skin   = True  # Welcher Skin gerade aktiv ist (toggle)
		self.prev_is_moving  = False # War Marx im letzten Frame in Bewegung?

		# Angriffs-Cooldown in Frames (0 = kann angreifen)
		self.attack_cooldown = 0

	def dead(self):
		"""Markiert Marx als tot (wird von get_damage aufgerufen)."""
		self.alive = False

	def move(self, dx, dy):
		"""
		Bewegt Marx um (dx, dy) Pixel, solange er dabei nicht
		über den Bildschirmrand hinausläuft.
		"""
		if 0 < self.x + dx < self.screen_w - self.rect.width:
			self.x += dx
		if 0 < self.y + dy < self.screen_h - self.rect.height:
			self.y += dy
		self.rect.topleft = (self.x, self.y)  # Kollisionsrechteck synchron halten

	def draw(self, screen):
		"""Zeichnet Marx auf den Bildschirm (nur wenn er lebt)."""
		if self.alive:
			screen.blit(self.image, (self.x, self.y))

	def get_rect(self):
		"""Gibt das aktuelle Kollisionsrechteck zurück."""
		return self.rect

	def tick_animation(self, is_moving):
		"""
		Schaltet zwischen Idle- und Lauf-Sprite um.
		Wird einmal pro Frame aufgerufen; is_moving gibt an ob Marx sich bewegt.
		Wechsel erfolgt alle 15 Frames um ein Flackern zu vermeiden.
		"""
		if is_moving and not self.prev_is_moving:
			# Bewegung gerade gestartet → sofort zum Lauf-Sprite wechseln
			self.image           = self.lauf_bild
			self.is_first_skin   = False
			self.framecount_skin = 0
			self.rect = self.image.get_rect(topleft=(self.x, self.y))

		elif is_moving:
			# Bereits in Bewegung → alle 15 Frames togglen
			self.framecount_skin += 1
			if self.framecount_skin >= 15:
				self.image = self.stand_bild if not self.is_first_skin else self.lauf_bild
				self.is_first_skin   = not self.is_first_skin
				self.rect = self.image.get_rect(topleft=(self.x, self.y))
				self.framecount_skin = 0

		else:
			# Keine Bewegung → Idle-Sprite
			self.image           = self.stand_bild
			self.framecount_skin = 0
			self.is_first_skin   = True

		self.prev_is_moving = is_moving  # für nächsten Frame merken

	def update(self):
		"""Gibt den aktuellen Zustand zurück: (alive, (x, y))."""
		return self.alive, (self.x, self.y)

	def input_monitoring(self, keys, area, opponents):
		"""
		Verarbeitet Tastatureingaben für Bewegung und Angriff.
		  keys      – aktueller Tastaturzustand (pygame.key.get_pressed())
		  area      – damage_area-Objekt, das den Angriffsbereich visualisiert
		  opponents – Liste aktiver Gegner (für Kollisionsprüfung beim Angriff)
		"""
		# Bewegung mit Pfeiltasten (5 Pixel pro Frame)
		if keys[pygame.K_LEFT]:  self.move(-5,  0)
		if keys[pygame.K_RIGHT]: self.move( 5,  0)
		if keys[pygame.K_UP]:    self.move( 0, -5)
		if keys[pygame.K_DOWN]:  self.move( 0,  5)

		# Cooldown jeden Frame um 1 reduzieren; Angriffsbereich färben
		if self.attack_cooldown > 0:
			self.attack_cooldown -= 1
			area.turnred()    # rot = noch auf Cooldown
		else:
			area.turnwhite()  # weiß = bereit zum Angriff

		# Angriff mit Leertaste (nur wenn kein Cooldown aktiv)
		if keys[pygame.K_SPACE] and self.attack_cooldown == 0:
			# Alle Gegner im Angriffsbereich sammeln
			in_range = [o for o in opponents if o.rect.colliderect(area.getrect())]
			if in_range:
				# Zufällig einen treffen (verhindert immer denselben zu targeten)
				in_range[randint(0, len(in_range) - 1)].getdamage(self.damage)
			self.attack_cooldown = 30  # 30 Frames = 0,5 Sekunden bei 60 FPS

	def get_damage(self, damage, damage_screen=None):
		"""
		Zieht damage von den Lebenspunkten ab.
		Löst optional den Bildschirm-Rot-Effekt aus.
		Tötet Marx wenn HP auf 0 oder darunter fallen.
		"""
		if self.alive:
			self.health_points -= damage
			if damage_screen:
				damage_screen.trigger()          # roten Overlay-Effekt starten
			if self.health_points <= 0:
				self.dead()

	def heal(self, amount):
		"""
		Heilt Marx um 'amount' HP, aber nie über max_health hinaus.
		Funktioniert nur solange Marx lebt.
		"""
		if self.alive:
			self.health_points = min(self.max_health, self.health_points + amount)

	def gethealth(self):
		"""Gibt die aktuellen Lebenspunkte zurück (wird von health_bar genutzt)."""
		return self.health_points

	def get_exception_area(self):
		"""
		Berechnet den Bereich um Marx (quadratisch, Radius = exception_radius),
		in dem Gegner nicht spawnen dürfen.
		Rückgabe: (x_start, x_end, y_start, y_end)
		"""
		x, y = self.get_rect().center
		return (x - self.exception_radius, x + self.exception_radius,
		        y - self.exception_radius, y + self.exception_radius)


# ─────────────────────────────────────────────────────────────────────────────
# Kampf-Hilfsobjekte
# ─────────────────────────────────────────────────────────────────────────────

class damage_area:
	"""
	Sichtbarer Angriffsbereich um Marx (halbtransparenter Kreis).
	Wird rot während des Cooldowns und weiß wenn Marx angreifen kann.
	Dient auch als Kollisionsrechteck für den Angriff.
	"""

	def __init__(self, origin):
		"""
		origin – das Objekt, dem die Area folgt (normalerweise marx_char).
		"""
		self.widthmulti   = 1    # Multiplikator für spätere Power-ups
		self.damagemulti  = 1    # Schadens-Multiplikator (noch ungenutzt)
		self.origin       = origin
		self.normal_width = 150  # Grundradius in Pixeln
		self.color = (255, 255, 255, 125)  # RGBA: Weiß, halbtransparent

	def getparentposition(self):
		"""Gibt die Mitte des verknüpften Objekts zurück."""
		return self.origin.get_rect().center

	def drawrect(self, screen):
		"""
		Zeichnet den halbtransparenten Kreis auf den Screen.
		Nutzt eine eigene Surface mit SRCALPHA damit die Transparenz funktioniert.
		"""
		radius = 200
		# Rechteck zentriert auf Marx
		target_rect = pygame.Rect(self.getparentposition(), (0, 0)).inflate(
		              (radius * 2, radius * 2))
		shape_surf = pygame.Surface(target_rect.size, pygame.SRCALPHA)
		pygame.draw.circle(shape_surf, self.color, (radius, radius), radius)
		screen.blit(shape_surf, target_rect)

	def getrect(self):
		"""
		Gibt das Kollisionsrechteck zurück (für Angriffsprüfung gegen Gegner).
		Radius wird durch widthmulti skalierbar gehalten (z.B. für Power-ups).
		"""
		pos    = self.getparentposition()
		radius = self.normal_width * self.widthmulti
		return pygame.Rect(pos[0] - radius, pos[1] - radius, radius * 2, radius * 2)

	def turnred(self):
		"""Färbt den Kreis rot → zeigt aktiven Cooldown an."""
		self.color = (255, 0, 0, 125)

	def turnwhite(self):
		"""Färbt den Kreis weiß → Angriff ist wieder möglich."""
		self.color = (255, 255, 255, 125)


class damage_screen:
	"""
	Roter Bildschirm-Overlay-Effekt wenn Marx Schaden nimmt.
	Erscheint sofort und klingt über 'duration' Frames ab.
	"""

	def __init__(self):
		self.color    = (255, 0, 0, 0)   # Alpha 0 = unsichtbar (Ausgangszustand)
		self.duration = 20               # Effekt dauert 20 Frames (~0,33 Sek bei 60 FPS)
		self.counter  = 0                # Zählt runter bis Effekt endet

	def trigger(self):
		"""Startet den Effekt (wird von marx.get_damage() aufgerufen)."""
		self.color   = (255, 0, 0, 80)  # Rot mit Alpha 80 (halbtransparent)
		self.counter = self.duration

	def draw(self, screen):
		"""
		Zeichnet den Overlay über den gesamten Screen.
		Muss jeden Frame aufgerufen werden; blendet automatisch aus.
		"""
		if self.counter > 0:
			self.counter -= 1
		else:
			self.color = (255, 0, 0, 0)  # Effekt beendet → unsichtbar
		surf = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
		surf.fill(self.color)
		screen.blit(surf, (0, 0))


class health_bar:
	"""
	Lebensanzeige für beliebige Objekte (Marx oder Gegner).
	Zeigt den aktuellen HP-Anteil als grünen Balken auf rotem Hintergrund.
	Mit follow=True positioniert sie sich automatisch über dem Objekt.
	"""

	def __init__(self, x, y, width, height, object, follow=False):
		"""
		x, y     – Startposition (wird bei follow=True ignoriert)
		width/h  – Balkenbreite und -höhe in Pixeln
		object   – das zu überwachende Objekt (muss gethealth() haben)
		follow   – True: Bar folgt dem Objekt; False: feste Position
		"""
		self.x          = x
		self.y          = y
		self.width      = width
		self.height     = height
		self.max_health = object.gethealth()  # einmalig beim Erstellen gespeichert
		self.object     = object
		self.follow     = follow

	def draw(self, screen):
		"""
		Zeichnet den Balken. Liest aktuelle HP jedes Frame neu aus.
		Bei follow=True wird die Position dynamisch aus dem Objekt-Rect berechnet.
		"""
		hp = self.object.gethealth()

		if self.follow:
			# 10px links vom Objekt-Rand, 12px über dem Kopf
			self.x = self.object.rect.x - 10
			self.y = self.object.rect.y - 12

		# Roter Hintergrund (volle Breite = maximales Leben)
		pygame.draw.rect(screen, (255, 0, 0), (self.x, self.y, self.width, self.height))
		# Grüner Vordergrund (proportionale Breite = aktuelles Leben)
		pct = max(0, hp / self.max_health)  # max(0,...) verhindert negative Breite
		pygame.draw.rect(screen, (0, 255, 0),
		                 (self.x, self.y, self.width * pct, self.height))


# ─────────────────────────────────────────────────────────────────────────────
# Gegner-Basisklasse
# ─────────────────────────────────────────────────────────────────────────────

class opponent:
	"""
	Abstrakte Basisklasse für alle Gegnertypen.
	Enthält gemeinsame Logik: Bewegung, Schadennahme, Kollision, Animation.
	Konkrete Typen (normal_opp, super_opp, mini_opp) erben von hier
	und setzen typspezifische Werte (HP, Speed, Sprites, Drop-Typ).
	"""

	def __init__(self, health_points):
		self.alive          = True
		self.isfirst_skin   = False          # Welcher der zwei Animationsframes aktiv ist
		self.health_points  = health_points
		self.is_moving      = True           # Für die Animations-Logik
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
		Der Drop-Spawn passiert extern im collectible_manager (nicht hier).
		"""
		self.health_points -= damage
		if self.health_points <= 0:
			self.alive = False

	def gethealth(self):
		"""Gibt aktuelle HP zurück (wird von health_bar genutzt)."""
		return self.health_points

	def move(self, dx, dy):
		"""Verschiebt den Gegner und aktualisiert das Kollisionsrechteck."""
		self.x += dx
		self.y += dy
		self.rect.topleft = (self.x, self.y)
		self.is_moving = True

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

	def getplayerposition(self, player):
		"""Hilfsmethode: gibt (x, y) des Spielers zurück."""
		return player.x, player.y

	def set_position_out_of_range_of_player(self, player):
		"""
		Setzt die Spawn-Position zufällig, aber außerhalb des exception_radius
		von Marx. Verhindert Spawn direkt neben dem Spieler.
		X und Y werden unabhängig voneinander per while-Schleife gewürfelt.
		"""
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
		"""
		Schaltet alle 15 Frames zwischen image1 und image2 um (Lauf-Animation).
		Steht der Gegner still, bleibt image1 (Idle) aktiv.
		"""
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

		script_dir  = os.path.dirname(os.path.abspath(__file__))
		self.image1 = load_image(os.path.join(script_dir, "normal_opp1.png"), scale=0.28)
		self.image2 = load_image(os.path.join(script_dir, "normal_opp2.png"), scale=0.28)
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

		script_dir  = os.path.dirname(os.path.abspath(__file__))
		self.image1 = load_image(os.path.join(script_dir, "super_opp1.png"), scale=1)
		self.image2 = load_image(os.path.join(script_dir, "super_opp2.png"), scale=1)
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

		script_dir  = os.path.dirname(os.path.abspath(__file__))
		self.image1 = load_image(os.path.join(script_dir, "mini_opp1.png"), scale=0.09)
		self.image2 = load_image(os.path.join(script_dir, "mini_opp2.png"), scale=0.09)
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
	  "type"     → Gegnerklasse (normal_opp, mini_opp, super_opp …)
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


# ─────────────────────────────────────────────────────────────────────────────
# Collectibles
# ─────────────────────────────────────────────────────────────────────────────

class collectible:
	"""
	Basisklasse für alle aufsammelbare Gegenstände.
	Erscheint auf dem Boden wenn ein Gegner stirbt; Marx läuft drüber → Effekt.
	"""

	def __init__(self, x, y, image_path, effect, player):
		"""
		x, y        – Spawn-Position (= Todesposition des Gegners)
		image_path  – Pfad zum Sprite
		effect      – String: "health" | "aoe" | "revive"
		player      – Referenz auf Marx (für Kollisionsprüfung und Effektanwendung)
		"""
		self.x         = x
		self.y         = y
		self.image     = load_image(image_path, scale=0.25)
		self.rect      = self.image.get_rect(topleft=(self.x, self.y))
		self.collected = False   # True sobald Marx drüberläuft
		self.effect    = effect
		self.player    = player

	def spawn(self, screen):
		"""Zeichnet das Collectible auf den Screen (nur wenn noch nicht aufgesammelt)."""
		if not self.collected:
			screen.blit(self.image, (self.x, self.y))

	def collectcheck(self, opponents):
		"""
		Prüft jeden Frame ob Marx das Collectible berührt.
		Falls ja: collected = True und Effekt auslösen.
		opponents wird an trigger_effect weitergegeben (für den AOE-Effekt).
		"""
		if not self.collected and self.rect.colliderect(self.player.get_rect()):
			self.collected = True
			self.trigger_effect(opponents)

	def trigger_effect(self, opponents):
		"""
		Führt den Effekt des Collectibles aus:
		  health → heilt Marx um 25 HP (gecappt auf max_health)
		  aoe    → fügt ALLEN aktiven Gegnern 10 Schaden zu
		  revive → erhöht Max-HP um 10 und füllt HP komplett auf
		"""
		if self.effect == "health":
			self.player.heal(15)
		elif self.effect == "aoe":
			for opp in opponents:
				opp.getdamage(25)
		elif self.effect == "revive":
			self.player.max_health    += 10                      # Max-HP dauerhaft erhöhen
			self.player.health_points  = self.player.max_health  # HP voll auffüllen


class heal(collectible):
	"""Heilt Marx um 15 HP. Wird von mini_opp gedroppt."""
	def __init__(self, x, y, player):
		script_dir = os.path.dirname(os.path.abspath(__file__))
		super().__init__(x, y, os.path.join(script_dir, "heal.png"), "health", player)

class aoe(collectible):
	"""Fügt allen Gegnern auf dem Bildschirm 25 Schaden zu. Wird von normal_opp gedroppt."""
	def __init__(self, x, y, player):
		script_dir = os.path.dirname(os.path.abspath(__file__))
		super().__init__(x, y, os.path.join(script_dir, "aoe.png"), "aoe", player)

class revive(collectible):
	"""Füllt HP komplett auf und erhöht Max-HP um 10. Wird von super_opp gedroppt."""
	def __init__(self, x, y, player):
		script_dir = os.path.dirname(os.path.abspath(__file__))
		super().__init__(x, y, os.path.join(script_dir, "revive.png"), "revive", player)


# Lookup-Tabelle: Drop-String aus Gegner-Klasse → Collectible-Klasse
# Wird im collectible_manager genutzt um den richtigen Typ zu instanziieren.
_COLLECTIBLE_MAP = {
	"heal":   heal,
	"aoe":    aoe,
	"revive": revive,
}


# ─────────────────────────────────────────────────────────────────────────────
# collectible_manager
# ─────────────────────────────────────────────────────────────────────────────

class collectible_manager:
	"""
	Verwaltet alle aktiven Collectibles auf dem Spielfeld.

	Zuständigkeiten:
	  1. Erkennt tote Gegner und spawnt deren Drop (nach Zufallschance)
	  2. Zeichnet alle aktiven Collectibles jeden Frame
	  3. Prüft ob Marx ein Collectible aufgesammelt hat und löst den Effekt aus
	  4. Entfernt aufgesammelte Collectibles aus der Liste

	WICHTIG: collectible_tick() MUSS vor dem Cleanup-Schritt aufgerufen werden,
	damit tote Gegner (alive=False) noch in der opponents-Liste vorhanden sind
	und erkannt werden können.
	"""

	def __init__(self, player):
		self.player       = player
		self.collectibles = []    # Liste aller aktuell sichtbaren Collectibles
		self._dropped     = set() # Set aus id()s von Gegnern die schon einen Drop hatten
		                          # verhindert mehrfaches Droppen desselben Gegners

	def collectible_tick(self, screen, opponents):
		"""
		Wird einmal pro Frame aufgerufen (vor dem Cleanup!).

		1. Tote Gegner → Drop-Chance prüfen → ggf. Collectible spawnen
		2. Alle aktiven Collectibles zeichnen und auf Aufsammeln prüfen
		3. Aufgesammelte Collectibles entfernen
		"""

		# ── Schritt 1: Drop-Erkennung ─────────────────────────────────────────
		for opp in opponents:
			if not opp.alive and id(opp) not in self._dropped:
				self._dropped.add(id(opp))   # merken: dieser Gegner wurde schon verarbeitet
				# Zufallswurf 1–100 gegen die Dropchance des Gegners
				if opp.collectible and randint(1, 100) <= opp.collectible_chance:
					cls = _COLLECTIBLE_MAP.get(opp.collectible)  # passende Klasse nachschlagen
					if cls:
						# Collectible an der Todesposition des Gegners spawnen
						self.collectibles.append(cls(opp.x, opp.y, self.player))

		# ── Schritt 2 & 3: Zeichnen + Aufsammeln + Cleanup ───────────────────
		# Neue Liste statt Elemente während der Iteration zu entfernen (Bug-Vermeidung)
		active = []
		for c in self.collectibles:
			c.collectcheck(opponents)   # prüft ob Marx drüberläuft
			if not c.collected:
				c.spawn(screen)         # nur zeichnen wenn noch nicht aufgesammelt
				active.append(c)        # und in der aktiven Liste behalten
		self.collectibles = active      # aufgesammelte sind jetzt raus
