import os
import pygame
from random import randint, uniform

# ─────────────────────────────────────────────────────────────────────────────
# Modul-Konstante
# ─────────────────────────────────────────────────────────────────────────────

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

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

		# Bildschirmgrenzen für die Bewegungsbegrenzung und Spawn-Logik
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
		  area      – DamageArea-Objekt, das den Angriffsbereich visualisiert
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
		"""Gibt die aktuellen Lebenspunkte zurück (wird von HealthBar genutzt)."""
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
	Erscheint sofort und klingt sanft über 'duration' Frames ab.
	"""

	def __init__(self):
		self.duration = 20   # Effekt dauert 20 Frames (~0,33 Sek bei 60 FPS)
		self.counter  = 0    # Zählt runter bis Effekt endet

	def trigger(self):
		"""Startet den Effekt (wird von Marx.get_damage() aufgerufen)."""
		self.counter = self.duration

	def draw(self, screen):
		"""
		Zeichnet den Overlay über den gesamten Screen.
		Muss jeden Frame aufgerufen werden; blendet sanft aus (Fade-out).
		"""
		if self.counter > 0:
			self.counter -= 1
		# Alpha proportional zum verbleibenden Counter → sanfter Fade-out
		alpha = int(80 * self.counter / self.duration)
		surf = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
		surf.fill((255, 0, 0, alpha))
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