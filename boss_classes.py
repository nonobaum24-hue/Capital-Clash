from game_classes import load_image, SCRIPT_DIR
import os
import pygame
from random import uniform

# ─────────────────────────────────────────────────────────────────────────────
# Boss-Gegner-Klasse
# ─────────────────────────────────────────────────────────────────────────────

class boss_opp:
	"""
	Boss Olaf mit 1000 HP, komplexem Animations-System und zwei Phasen:
	
	Phase 1 (1000–501 HP):
	  - Bewegungen auf Marx zu (idle/walk Animation mit Rotation)
	  - Nahkampf-Angriffe (punch Animation)
	  - Nur in Reichweite aktiv
	
	Phase 2 (500–0 HP):
	  - Alle Phase-1-Fähigkeiten
	  - PLUS: Projektil-Schüsse (cast Animation) in zufälligen Intervallen
	  - Schnellere Reaktion und Angriffe werden häufiger
	
	Animationen:
	  - idle: Standbild (passiv)
	  - walk: Laufbild (aktiv bei Bewegung)
	  - punch: 3-Frame-Angriff mit Timing
	  - cast: 2-Frame-Übernatürlich-Effekt für Projektile (Phase 2)
	"""

	# ── Konstanten ─────────────────────────────────────────────────────────

	PUNCH_RANGE         = 150   # Pixel Abstand unter dem Nahkampf ausgelöst wird
	PUNCH_DELAY         = 60    # Frames Vorlaufzeit für den Punch (visuelles Feedback)
	PUNCH_COOLDOWN      = 120   # Frames Pause zwischen zwei Punch-Auslösungen
	
	PHASE_2_THRESHOLD   = 500   # HP-Grenze für Phase 2 (50% von 1000)
	CAST_COOLDOWN_BASE  = 180   # Frames zwischen Projektil-Angriffen in Phase 2 (3 Sek)
	CAST_DELAY          = 40    # Frames Vorlaufzeit für Cast-Animation

	def __init__(self):
		# ── Lebenspunkte & Schaden ────────────────────────────────────────
		self.max_health        = 1000
		self.health_points     = self.max_health
		self.punch_damage      = 40
		self.projectile_damage = 20
		self.alive             = True

		# ── Phase-System ───────────────────────────────────────────────────
		self.phase             = 1   # Phase 1 oder 2
		self.lifelong_tick     = 0   # Gesamtlebensdauer in Frames

		# ── Punch-System ───────────────────────────────────────────────────
		self._punch_cd         = 0   # Cooldown-Zähler für Punch-Angriffe
		self._punch_active     = False  # Ist gerade ein Punch aktiv?
		self._punch_tick       = 0   # Frame-Zähler innerhalb des Punch

		# ── Cast-System (Phase 2) ──────────────────────────────────────────
		self._cast_cd          = 0   # Cooldown-Zähler für Cast-Angriffe
		self._cast_active      = False  # Ist gerade ein Cast aktiv?
		self._cast_tick        = 0   # Frame-Zähler innerhalb des Cast

		# ── Animationen ────────────────────────────────────────────────────
		# (alle mit scale=0.5 wie im Original)
		script_dir = SCRIPT_DIR
		
		# Idle-Animation (Standbild)
		self.anim_idle = load_image(
			os.path.join(script_dir, "olaf", "idle_olaf", "idle_olaf.png"), 
			scale=0.5
		)
		
		# Walk-Animation (Laufbild)
		self.anim_walk = load_image(
			os.path.join(script_dir, "olaf", "walk_olaf", "walk_olaf.png"), 
			scale=0.5
		)
		
		# Punch-Animationen (3 Frames)
		self.anim_punch = [
			load_image(os.path.join(script_dir, "olaf", "punch_olaf", "punch_olaf_1.png"), scale=0.5),
			load_image(os.path.join(script_dir, "olaf", "punch_olaf", "punch_olaf_2.png"), scale=0.5),
			load_image(os.path.join(script_dir, "olaf", "punch_olaf", "punch_olaf_3.png"), scale=0.5),
		]
		
		# Cast-Animationen (2 Frames, nur Phase 2)
		self.anim_cast = [
			load_image(os.path.join(script_dir, "olaf", "cast_olaf", "cast_olaf_1.png"), scale=0.5),
			load_image(os.path.join(script_dir, "olaf", "cast_olaf", "cast_olaf_2.png"), scale=0.5),
		]

		# Aktuelles Animations-Sprite
		self.image = self.anim_idle
		
		# ── Animation-Zustand ──────────────────────────────────────────────
		self.animation_tick   = 0    # Frame-Zähler für idle/walk-Togglel
		self.is_walking       = False  # Gerade Laufanimation?
		self.is_first_skin    = True   # Welches Sprite (idle/walk toggle)

		# ── Position & Collision ───────────────────────────────────────────
		width, height = 1250, 720
		bx = width  // 2 - self.image.get_width()  // 2
		by = height - self.image.get_height() - 10
		self.position = [bx, by]  # liste statt tuple für in-place updates
		self.rect     = self.image.get_rect(topleft=self.position)

		# ── Bewegung ───────────────────────────────────────────────────────
		self.speed = 1.5   # Pixel pro Frame auf Marx zu
		self.vx = 0        # aktuelle Geschwindigkeit X
		self.vy = 0        # aktuelle Geschwindigkeit Y

	# ── Hilfsmethoden ─────────────────────────────────────────────────────────

	def draw(self, screen):
		"""Zeichnet Olaf auf den Screen (nur wenn lebendig)."""
		if self.alive:
			screen.blit(self.image, self.position)

	def get_rect(self):
		"""Gibt das Kollisionsrechteck zurück."""
		return self.rect

	def get_center_position(self):
		"""Gibt die Mittelpunkt-Koordinaten zurück."""
		return self.rect.center

	def gethealth(self):
		"""Wird von health_bar benötigt."""
		return self.health_points

	def getdamage(self, damage):
		"""Zieht Schaden ab; markiert Boss als tot wenn HP <= 0."""
		self.health_points -= damage
		if self.health_points <= 0:
			self.alive = False

	def get_distance_to_player(self, player):
		"""Berechnet euklidische Entfernung von Olaf zu Marx."""
		bx, by = self.rect.center
		px = player.x + player.rect.width  // 2
		py = player.y + player.rect.height // 2
		return ((bx - px) ** 2 + (by - py) ** 2) ** 0.5

	# ── Bewegung zum Spieler ──────────────────────────────────────────────────

	def follow_player(self, player):
		"""
		Bewegt Olaf sanft auf Marx zu (wie die normalen Gegner).
		Nutzt smooth-movement mit 10% Beschleunigung pro Frame.
		"""
		target_x = player.x + uniform(-20, 20)  # kleine zufällige Variation
		target_y = player.y + uniform(-20, 20)

		dx = target_x - self.position[0]
		dy = target_y - self.position[1]
		dist = (dx ** 2 + dy ** 2) ** 0.5

		if dist < 5:
			self.vx = self.vy = 0
			self.is_walking = False
			return

		# Normalisieren
		dx /= dist
		dy /= dist

		# Smooth acceleration (10% pro Frame)
		self.vx += (dx * self.speed - self.vx) * 0.1
		self.vy += (dy * self.speed - self.vy) * 0.1

		# Position aktualisieren
		self.position[0] += self.vx
		self.position[1] += self.vy
		self.rect.topleft = self.position
		
		# walking-Zustand aktualisieren (für Animation)
		self.is_walking = abs(self.vx) > 0.1 or abs(self.vy) > 0.1

	# ── Animation-System ──────────────────────────────────────────────────────

	def update_animation(self):
		"""
		Aktualisiert das aktuelle Animations-Sprite basierend auf Olaf's Zustand.
		
		Priorität:
		  1. Wenn Punch aktiv → punch_animation
		  2. Wenn Cast aktiv → cast_animation
		  3. Wenn laufen → walk/idle Rotation
		  4. Sonst → idle
		"""
		# -- Punch-Animation läuft gerade -----
		if self._punch_active:
			# 3 Frames (punch_olaf 1, 2, 3) über 45 Frames insgesamt (15 Frames pro Frame)
			frame_idx = min(2, self._punch_tick // 15)
			self.image = self.anim_punch[frame_idx]
			return

		# -- Cast-Animation läuft gerade -----
		if self._cast_active:
			# 2 Frames (cast_olaf 1, 2) über 30 Frames insgesamt (15 Frames pro Frame)
			frame_idx = min(1, self._cast_tick // 15)
			self.image = self.anim_cast[frame_idx]
			return

		# -- Normale Idle/Walk-Animation -----
		if self.is_walking:
			self.animation_tick += 1
			if self.animation_tick >= 15:
				# Alle 15 Frames zwischen idle und walk togglen
				self.image = self.anim_walk if self.is_first_skin else self.anim_idle
				self.is_first_skin = not self.is_first_skin
				self.animation_tick = 0
		else:
			# Steht: Idle-Animation
			self.image = self.anim_idle
			self.animation_tick = 0
			self.is_first_skin = True

	# ── Punch-System ──────────────────────────────────────────────────────────

	def _update_punch_cooldown(self):
		"""Zählt den Punch-Cooldown runter."""
		if self._punch_cd > 0:
			self._punch_cd -= 1

	def _check_and_trigger_punch(self, player, punch_area):
		"""
		Prüft ob Olaf Marx schlagen soll und aktiviert punch_area ggf.
		Bedingungen:
		  - Marx ist in Reichweite (< PUNCH_RANGE pixels)
		  - Kein Punch-Cooldown mehr aktiv
		"""
		if self.get_distance_to_player(player) < self.PUNCH_RANGE and self._punch_cd == 0:
			# Punch starten und punch_area aktivieren
			self._punch_active = True
			self._punch_tick = 0
			punch_area.activate(self.punch_damage, delay_frames=self.PUNCH_DELAY)
			self._punch_cd = self.PUNCH_COOLDOWN

	def _update_punch_animation(self):
		"""Tickt die aktive Punch-Animation."""
		if not self._punch_active:
			return

		self._punch_tick += 1
		# Punch dauert 45 Frames (3 Frames * 15 Frames pro Frame)
		if self._punch_tick >= 45:
			self._punch_active = False
			self._punch_tick = 0

	# ── Cast-System (Phase 2) ─────────────────────────────────────────────────

	def _update_cast_cooldown(self):
		"""Zählt den Cast-Cooldown runter."""
		if self._cast_cd > 0:
			self._cast_cd -= 1

	def _check_and_trigger_cast(self, projectiles):
		"""
		Prüft ob Olaf (in Phase 2) ein Projektil schießen soll.
		Cast hat niedrigeres Cooldown als Punch um mehr Abwechslung zu schaffen.
		"""
		if self.phase == 2 and self._cast_cd == 0:
			self._cast_active = True
			self._cast_tick = 0
			self._cast_cd = self.CAST_COOLDOWN_BASE
			
			# Projektil spawnen (nach CAST_DELAY Frames)
			self._spawn_projectile(projectiles)

	def _spawn_projectile(self, projectiles):
		"""
		Spawnt ein Projektil von Olaf's Position mit Richtung zu Marx.
		Wird vom Cast-Angriff aufgerufen.
		"""
		# Projektil landet auf dem Boss, fliegt zu zufälligem Punkt relativ zu Marx
		cx, cy = self.get_center_position()
		projectile = boss_projectile(
			start_x=cx,
			start_y=cy,
			damage=self.projectile_damage,
			delay_frames=self.CAST_DELAY
		)
		projectiles.append(projectile)

	def _update_cast_animation(self):
		"""Tickt die aktive Cast-Animation."""
		if not self._cast_active:
			return

		self._cast_tick += 1
		# Cast dauert 30 Frames (2 Frames * 15 Frames pro Frame)
		if self._cast_tick >= 30:
			self._cast_active = False
			self._cast_tick = 0

	# ── Phase-System ──────────────────────────────────────────────────────────

	def _check_phase(self):
		"""
		Prüft ob Olaf in Phase 2 wechseln soll (bei 50% Health).
		Phase 2 → Projektile werden verfügbar.
		"""
		if self.health_points <= self.PHASE_2_THRESHOLD and self.phase == 1:
			self.phase = 2

	# ── Haupt-Tick ────────────────────────────────────────────────────────────

	def tick(self, player, projectiles, punch_area):
		"""
		Wird jeden Frame aufgerufen.
		  player       – Marx-Objekt
		  projectiles  – Liste für Projektile (wird bei Phase 2 befüllt)
		  punch_area   – punch_area-Objekt für Nahkampf-Angriffe
		"""
		if not self.alive:
			return

		self.lifelong_tick += 1

		# ── Phase-Check ────────────────────────────────────────────────────
		self._check_phase()

		# ── Bewegung ───────────────────────────────────────────────────────
		self.follow_player(player)

		# ── Punch-System ───────────────────────────────────────────────────
		self._update_punch_cooldown()
		self._check_and_trigger_punch(player, punch_area)
		self._update_punch_animation()
		punch_area.tick(player)  # punch_area jeden Frame ticken (Damage-Auslösung)

		# ── Cast-System (Phase 2) ──────────────────────────────────────────
		if self.phase == 2:
			self._update_cast_cooldown()
			self._check_and_trigger_cast(projectiles)
			self._update_cast_animation()

		# ── Animation aktualisieren ───────────────────────────────────────
		self.update_animation()

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


# ─────────────────────────────────────────────────────────────────────────────
# Boss-Projektil-Klasse
# ─────────────────────────────────────────────────────────────────────────────

class boss_projectile:
	"""
	Projektil schießt von Boss zu zufälligem Punkt relativ zu Marx.
	Wird von Olaf's Cast-Angriff in Phase 2 gespawnt.
	
	Mechanik:
	  - Startet auf Boss-Position mit Verzögerung (für Animation)
	  - Nach Verzögerung: schneide zu Zielposition
	  - Erreicht Zielposition → Explosion & Schaden-Prüfung
	  - Wird danach aus der Liste entfernt (alive = False)
	"""

	SPEED       = 3  # Pixel pro Frame während des Flugs
	RADIUS      = 30  # Radius des Explosionsradius (Kollisión mit Marx)

	def __init__(self, start_x, start_y, damage, delay_frames):
		"""
		start_x, start_y – Spawn-Position (auf Olaf)
		damage           – Schaden bei Treffer
		delay_frames     – Frames bis der Flug startet (Animation)
		"""
		self.start_x        = start_x
		self.start_y        = start_y
		self.x              = float(start_x)
		self.y              = float(start_y)
		self.damage         = damage
		self.alive          = True
		self.has_exploded   = False

		# Verzögerung & Flug-Tracking
		self.delay_frames   = delay_frames
		self.tick_count     = 0

		# Zielposition: zufällig um (0, 0) relativ zum Spawn-Punkt
		offset_range = 200
		self.target_x = start_x + uniform(-offset_range, offset_range)
		self.target_y = start_y + uniform(-offset_range, offset_range)

		# Richtungs-Vektor normalisieren & mit Speed multiplizieren
		dx = self.target_x - self.x
		dy = self.target_y - self.y
		dist = (dx ** 2 + dy ** 2) ** 0.5
		if dist > 0:
			self.vx = (dx / dist) * self.SPEED
			self.vy = (dy / dist) * self.SPEED
		else:
			self.vx = self.vy = 0

		# Sprite (projectile.png)
		try:
			self.image = load_image(os.path.join(SCRIPT_DIR, "projectile.png"), scale=0.25)
		except Exception as e:
			print(f"Projektil-Texture nicht gefunden: {e}")
			self.image = None

		self.rect = self.image.get_rect(topleft=(int(self.x), int(self.y))) if self.image else pygame.Rect(0, 0, 0, 0)

	# ── Hilfsmethoden ─────────────────────────────────────────────────────────

	def draw(self, screen):
		"""Zeichnet das Projektil (nur während und nach Flug, nicht während Verzögerung)."""
		if self.alive and self.tick_count >= self.delay_frames and self.image:
			self.rect.topleft = (int(self.x), int(self.y))
			screen.blit(self.image, self.rect)

	def get_rect(self):
		"""Gibt das Kollisionsrechteck zurück."""
		return self.rect

	def get_center_position(self):
		"""Gibt die Mittelpunkt-Koordinaten zurück."""
		return (int(self.x + self.rect.width // 2), int(self.y + self.rect.height // 2))

	# ── Haupt-Tick ────────────────────────────────────────────────────────────

	def tick(self, player):
		"""
		Wird jeden Frame aufgerufen.
		  player – Marx-Objekt (für Kollisionsprüfung nach Träffer)
		"""
		if not self.alive:
			return

		self.tick_count += 1

		# ── Während Verzögerung: nichts tun ───────────────────────────────
		if self.tick_count < self.delay_frames:
			return

		# ── Flugphase: auf Zielposition zubewegen ────────────────────────
		self.x += self.vx
		self.y += self.vy
		self.rect.topleft = (int(self.x), int(self.y))

		# Prüfe ob Zielposition erreicht (innerhalb 20 Pixel)
		dx = self.target_x - self.x
		dy = self.target_y - self.y
		dist = (dx ** 2 + dy ** 2) ** 0.5

		if dist < 20:
			# Ziel erreicht → Explosion
			self._explode(player)

	def _explode(self, player):
		"""
		Explosion bei Zielposition:
		  - Prüfe Kollision mit Marx (Radius = RADIUS)
		  - Wenn Treffer → Schaden
		  - Mark als nicht lebendig (wird aus Liste entfernt)
		"""
		if not self.has_exploded:
			self.has_exploded = True
			
			# Explosionsbereich (Kreis um Zielposition)
			explosion_rect = pygame.Rect(
				self.target_x - self.RADIUS,
				self.target_y - self.RADIUS,
				self.RADIUS * 2,
				self.RADIUS * 2
			)

			# Kollisionsprüfung mit Marx
			if player.get_rect().colliderect(explosion_rect):
				player.get_damage(self.damage)

			self.alive = False

