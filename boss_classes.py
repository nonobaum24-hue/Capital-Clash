from game_classes import load_image, SCRIPT_DIR
import os
import pygame

class boss_opp:
	"""
	Boss-Gegner mit 1000 HP, Nahkampf- und (vorbereitetem) Projektil-Angriff.
	
	Phasen-System (vorbereitet, ausbaubar):
	  Phase 1 → aktuell aktiv; weitere Phasen können in tick() ergänzt werden
	
	Nahkampf:
	  Kommt Marx auf unter PUNCH_RANGE Pixel heran, startet punch_area einen
	  verzögerten Angriff (Weiß→Rot-Fade als visuelle Warnung).
	"""

	PUNCH_RANGE    = 100   # Pixel Abstand unter dem der Nahkampf ausgelöst wird
	PUNCH_DELAY    = 60    # Frames Vorlaufzeit für den Punch (= 1 Sek bei 60 FPS)
	PUNCH_COOLDOWN = 90    # Frames Pause zwischen zwei Punch-Auslösungen

	def __init__(self):
		self.health_points     = 1000
		self.punch_damage      = 40
		self.projectile_damage = 20
		self.alive             = True
		self.phase             = 1

		self.lifelong_tick  = 0   # Gesamtlebensdauer in Frames
		self._punch_cd      = 0   # interner Cooldown-Zähler

		self.image = load_image(os.path.join(SCRIPT_DIR, "boss_opp.png"), scale=0.5)

		# Position: horizontal zentriert, knapp über dem unteren Bildrand
		width, height = 1250, 720
		bx = width  // 2 - self.image.get_width()  // 2
		by = height - self.image.get_height() - 10
		self.position = (bx, by)
		self.rect     = self.image.get_rect(topleft=self.position)

	# ── Hilfsmethoden ─────────────────────────────────────────────────────────

	def draw(self, screen):
		if self.alive:
			screen.blit(self.image, self.position)

	def get_rect(self):
		"""Kollisionsrechteck (direkt aus self.position, kein Doppel-Offset)."""
		return self.rect

	def get_center_position(self):
		return self.rect.center

	def gethealth(self):
		"""Wird von health_bar benötigt."""
		return self.health_points

	def getdamage(self, damage):
		self.health_points -= damage
		if self.health_points <= 0:
			self.alive = False

	def get_distance_to_player(self, player):
		bx, by = self.rect.center
		px = player.x + player.rect.width  // 2
		py = player.y + player.rect.height // 2
		return ((bx - px) ** 2 + (by - py) ** 2) ** 0.5

	# ── Haupt-Tick ────────────────────────────────────────────────────────────

	def tick(self, player, projectiles, punch_area):
		"""
		Wird jeden Frame aufgerufen.
		  player      – Marx-Objekt
		  projectiles – Liste für Projektile (Phase 2, noch in Arbeit)
		  punch_area  – punch_area-Objekt das zu diesem Boss gehört
		"""
		if not self.alive:
			return

		self.lifelong_tick += 1

		# ── Punch-Cooldown runterzählen ───────────────────────────────────────
		if self._punch_cd > 0:
			self._punch_cd -= 1

		# ── Nahkampf auslösen ─────────────────────────────────────────────────
		# Nur wenn Marx nah genug IST und der Cooldown abgelaufen ist
		if self.get_distance_to_player(player) < self.PUNCH_RANGE and self._punch_cd == 0:
			punch_area.activate(self.punch_damage, delay_frames=self.PUNCH_DELAY)
			self._punch_cd = self.PUNCH_COOLDOWN   # nächsten Punch verzögern

		# punch_area jeden Frame ticken (zählt Delay runter, löst Schaden aus)
		punch_area.tick(player)

class punch_area:
	"""
	Halbtransparenter Angriffskreis um den Boss.
	
	Verhalten:
	  - Inaktiv    → weißer, halbtransparenter Kreis
	  - Aktiv      → Kreis fadet langsam von Weiß nach Rot während der Delay läuft
	  - Bei Ablauf → Kollisionsprüfung; trifft Marx → Schaden; danach wieder inaktiv
	
	Technik: identisch zu damage_area.drawrect() — eigene SRCALPHA-Surface
	damit die Transparenz korrekt über anderen Sprites liegt.
	"""

	RADIUS = 100   # Radius des Angriffskreises in Pixeln
	ALPHA  = 0  # Transparenz (0 = unsichtbar, 255 = untransparent)

	def __init__(self, boss):
		self.boss       = boss
		self.active     = False
		self.tick_count = 0    # verbleibende Frames bis zum Einschlag
		self.max_ticks  = 0    # Startwert des Countdowns (für Farbberechnung)
		self.damage     = 0

	# ── Steuerung ─────────────────────────────────────────────────────────────

	def activate(self, damage, delay_frames):
		"""
		Startet den Angriffsvorgang.
		Wird ignoriert wenn bereits ein Angriff läuft (kein Reset).
		  damage        – Schaden der bei Ablauf ausgelöst wird
		  delay_frames  – Vorlaufzeit in Frames (z.B. 60 = 1 Sek bei 60 FPS)
		"""
		if not self.active:
			self.damage     = damage
			self.tick_count = delay_frames
			self.max_ticks  = delay_frames
			self.active     = True

	def tick(self, player):
		"""
		Muss jeden Frame aufgerufen werden (vom boss_opp.tick() aus).
		Zählt den Delay-Counter runter; löst Schaden aus wenn er auf 0 fällt.
		"""
		if not self.active:
			return

		if self.tick_count > 0:
			self.tick_count -= 1
		else:
			# Delay abgelaufen → Kollision prüfen und Schaden vergeben
			if player.get_rect().colliderect(self._get_collision_rect()):
				player.get_damage(self.damage)
			self.active = False   # Angriff beendet

	# ── Intern ────────────────────────────────────────────────────────────────

	def _get_color(self):
		"""
		Berechnet die aktuelle Füllfarbe als RGBA-Tupel.
		
		Inaktiv          → Transparent  (255, 0, 0, ALPHA = 0)
		Aktiv, Beginn    → Rot  (progress von ALPHA bis 0.7)
		Aktiv, kurz vorm Einschlag → Rot (255, 0, 0, ALPHA = 0.7)
		
		Formel: G und B linear mit `progress` skalieren,
		        R bleibt immer 255 → ergibt sauberen Weiß→Rot-Übergang.
		"""
		if not self.active or self.max_ticks == 0:
			return (255, 0, 0, self.ALPHA)

		progress = (1-(self.tick_count / self.max_ticks))/1.33   # 0.0 -> 0.75 ungefähr
		self.ALPHA = int(255 * progress)
		return (255, 0, 0, self.ALPHA)

	def _get_collision_rect(self):
		"""Kollisionsrechteck zentriert auf die Boss-Mitte."""
		cx, cy = self.boss.get_center_position()
		r = self.RADIUS
		return pygame.Rect(cx - r, cy - r, r * 2, r * 2)

	# ── Zeichnen ──────────────────────────────────────────────────────────────

	def draw(self, screen):
		"""
		Zeichnet den halbtransparenten Kreis — exakt dieselbe Technik
		wie damage_area.drawrect() bei Marx:
		  1. Eigene Surface mit SRCALPHA erstellen
		  2. Kreis darauf zeichnen (mit Farbverlauf-Farbe)
		  3. Surface auf den Screen blitten
		"""
		cx, cy = self.boss.get_center_position()
		r      = self.RADIUS
		color  = self._get_color()

		# Ziel-Rechteck zentriert auf den Boss (wie bei damage_area)
		target_rect = pygame.Rect(0, 0, 0, 0).inflate(0, 0)
		target_rect = pygame.Rect(cx - r, cy - r, r * 2, r * 2)

		shape_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
		pygame.draw.circle(shape_surf, color, (r, r), r)
		screen.blit(shape_surf, target_rect)
