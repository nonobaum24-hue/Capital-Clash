# =============================================================================
# boss_classes.py  –  Boss Enemy Classes
# =============================================================================
# Contains the classes that make up the boss fight against Olaf:
#
#   boss_opp          – the boss character itself (movement, AI, phases, animations)
#   punch_area        – melee attack circle around the boss (visual + hit detection)
#   impact_area       – impact warning circle that marks where damage will happen
#   boss_projectile   – visual projectile that flies toward the impact area (aesthetic only)
# =============================================================================

from game_classes import load_image, SCRIPT_DIR
import os
import pygame
from random import uniform, randint
from resource_path import get_resource_path


# =============================================================================
# boss_opp  –  Boss Character (Olaf)
# =============================================================================

class boss_opp:
    """
    Boss Olaf with 1000 HP, a complex animation system, and two fight phases.

    Phase 1  (1000 – 501 HP):
      - Moves toward Marx smoothly (idle / walk animation with rotation)
      - Melee punch attacks (3-frame punch animation) when Marx is close
      - No impact areas

    Phase 2  (500 – 0 HP):
      - All Phase 1 behaviour, PLUS:
      - Creates impact areas (2-frame cast animation) on a cooldown

    Animations:
      idle   – standing still (passive)
      walk   – moving (active during movement)
      punch  – 3-frame melee animation (triggered when in punch range)
      cast   – 2-frame casting animation (Phase 2 only, before impact area)
    """

    # ── Class-level constants (same for every boss_opp instance) ────────────

    PUNCH_RANGE         = 150   # pixels: melee attack triggers below this distance
    PUNCH_DELAY         = 45    # frames of wind-up before the punch hit is checked (matches animation duration)
    PUNCH_COOLDOWN      = 120   # frames between two punch attacks (2 s at 60 FPS)

    PHASE_2_THRESHOLD   = 500   # HP at which Olaf enters Phase 2
    CAST_COOLDOWN_BASE  = randint(150, 250)   # frames between impact area casts in Phase 2 (3 s)
    CAST_DELAY          = 60*1.5  # frames of cast animation before the impact area activates

    def __init__(self, player, aoi):
        # ── HP & Damage ──────────────────────────────────────────────────────
        self.max_health         = 1000
        self.health_points      = self.max_health
        self.punch_damage       = 40   # HP removed per punch hit
        self.impact_damage      = 20   # HP removed per impact area hit
        self.alive              = True

        # ── Phase System ─────────────────────────────────────────────────────
        self.phase          = 1   # 1 or 2; transitions at PHASE_2_THRESHOLD

        # ── Punch System ─────────────────────────────────────────────────────
        self._punch_cd      = 0      # cooldown counter (decrements each frame)
        self._punch_active  = False  # True while the punch animation is playing
        self._punch_tick    = 0      # frame counter within the current punch

        # ── Cast System (Phase 2) ─────────────────────────────────────────────
        self._cast_cd       = 0      # cooldown counter for casts
        self._cast_active   = False  # True while the cast animation is playing
        self._cast_tick     = 0      # frame counter within the current cast

        # ── Target ──────────────────────────────────────────────────────
        self.player = player
        self.impact_area = aoi

        # ── Animations ──────────────────────────────────────────────────────
        # All sprites are loaded at scale 0.5 (half of their original size)

        # Idle animation: single frame shown when Olaf is standing still

        self.scale = 2

        self.anim_idle = load_image(
            get_resource_path("olaf/idle_olaf/idle_olaf.png"),
            scale=self.scale
        )

        # Walk animation: single frame shown when Olaf is moving
        self.anim_walk = load_image(
            get_resource_path("olaf/walk_olaf/walk_olaf.png"),
            scale=self.scale
        )

        # Punch animation: 3 frames; played over 45 ticks (15 ticks per frame)
        self.anim_punch = [
            load_image(get_resource_path("olaf/punch_olaf/punch_olaf_1.png"), scale=self.scale),
            load_image(get_resource_path("olaf/punch_olaf/punch_olaf_2.png"), scale=self.scale),
            load_image(get_resource_path("olaf/punch_olaf/punch_olaf_3.png"), scale=self.scale),
        ]

        # Cast animation: 2 frames; played over 30 ticks (15 ticks per frame)
        # Only used in Phase 2 when creating impact areas
        self.anim_cast = [
            load_image(get_resource_path("olaf/cast_olaf/cast_olaf_1.png"), scale=self.scale),
            load_image(get_resource_path("olaf/cast_olaf/cast_olaf_2.png"), scale=self.scale),
        ]

        # Start with the idle sprite
        self.image = self.anim_idle

        # ── Animation State ──────────────────────────────────────────────────
        self.animation_tick  = 0      # frame counter for idle/walk toggle
        self.is_walking      = False  # True while Olaf is moving toward Marx
        self.is_first_skin   = True   # toggle flag for idle/walk sprite swap

        # ── Position & Collision ─────────────────────────────────────────────
        # Olaf spawns at the bottom-centre of the screen
        w, h = 1250, 720
        bx = w // 2 - self.image.get_width()  // 2
        by = h      - self.image.get_height() - 10
        self.position = [bx, by]   # list (not tuple) so values can be updated in place
        self.rect     = self.image.get_rect(topleft=self.position)

        # ── Movement ─────────────────────────────────────────────────────────
        self.speed = 1   # maximum pixels per frame toward Marx
        self.vx    = 0.0   # current horizontal velocity
        self.vy    = 0.0   # current vertical velocity

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def draw(self, screen):
        """Draw Olaf's current sprite onto the screen.  Does nothing if dead."""
        if self.alive:
            screen.blit(self.image, self.position)

    def get_rect(self):
        """Return the collision rect (used by punch_area and attack checks)."""
        return self.rect

    def get_center_position(self):
        """Return the centre-point coordinates of Olaf's sprite."""
        return self.rect.center

    def gethealth(self):
        """Return current HP.  Called by health_bar every frame."""
        return self.health_points

    def getdamage(self, damage):
        """
        Subtract damage from HP.
        Sets alive = False when HP drops to 0 or below.
        """
        self.health_points -= damage
        if self.health_points <= 0:
            self.alive = False

    def get_distance_to_player(self, player):
        """
        Calculate the Euclidean distance between Olaf's centre and Marx's centre.
        Used to decide when to trigger the punch attack.
        """
        bx, by = self.rect.center
        px     = player.x + player.rect.width  // 2
        py     = player.y + player.rect.height // 2
        return ((bx - px) ** 2 + (by - py) ** 2) ** 0.5

    # =========================================================================
    # Movement
    # =========================================================================

    def follow_player(self, player):
        """
        Move Olaf smoothly toward Marx using 10 % acceleration per frame.
        A small random offset is added to the target position each frame to
        create slightly erratic movement (harder to dodge).
        """
        # Add slight jitter to the target to prevent perfectly predictable paths
        target_x = player.x + uniform(-20, 20)
        target_y = player.y + uniform(-20, 20)

        dx   = target_x - self.position[0]
        dy   = target_y - self.position[1]
        dist = (dx ** 2 + dy ** 2) ** 0.5

        if dist < 5:
            # Already close enough – stop moving
            self.vx = self.vy = 0
            self.is_walking = False
            return

        # Normalise the direction vector
        dx /= dist
        dy /= dist

        # Smooth acceleration: blend current velocity toward the target velocity
        # by 10 % each frame.  This gives a natural ease-in / ease-out feel.
        self.vx += (dx * self.speed - self.vx) * 0.1
        self.vy += (dy * self.speed - self.vy) * 0.1

        # Apply velocity to position
        self.position[0] += self.vx
        self.position[1] += self.vy
        self.rect.topleft  = self.position

        # Update walking state for the animation system
        self.is_walking = abs(self.vx) > 0.1 or abs(self.vy) > 0.1

    # =========================================================================
    # Animation System
    # =========================================================================

    def update_animation(self):
        """
        Select the correct sprite for this frame based on Olaf's current state.

        Priority order:
          1. Punch animation is active → show punch frame
          2. Cast animation is active  → show cast frame
          3. Walking                   → toggle between walk and idle every 15 frames
          4. Standing still            → show idle frame
        """
        # -- Punch animation takes highest priority ----------------------------
        if self._punch_active:
            # 3 sprites spread over 60 frames (20 frames per sprite)
            frame_idx  = min(2, self._punch_tick // 20)
            self.image = self.anim_punch[frame_idx]
            return

        # -- Cast animation takes second priority -----------------------------
        if self._cast_active:
            # 2 sprites spread over 30 frames (15 frames per sprite)
            frame_idx  = min(1, self._cast_tick // 15)
            self.image = self.anim_cast[frame_idx]
            return

        # -- Normal idle / walk animation -------------------------------------
        if self.is_walking:
            self.animation_tick += 1
            if self.animation_tick >= 15:
                # Toggle between walk and idle every 15 frames
                self.image = self.anim_walk if self.is_first_skin else self.anim_idle
                self.is_first_skin  = not self.is_first_skin
                self.animation_tick = 0
        else:
            # Not moving → always idle
            self.image          = self.anim_idle
            self.animation_tick = 0
            self.is_first_skin  = True

    # =========================================================================
    # Punch System
    # =========================================================================

    def _update_punch_cooldown(self, punch_area):
        """Decrement the punch cooldown counter by 1 each frame."""
        if self._punch_cd > 0:
            self._punch_cd -= 1
        if self._punch_cd == 0 and not self._punch_active:
            punch_area.active = False   # ensure the punch_area is inactive when cooldown ends

    def _check_and_trigger_punch(self, player, punch_area):
        """
        Trigger a punch attack if Marx is close enough and the cooldown is over.

        Conditions:
          - Distance to Marx < PUNCH_RANGE pixels
          - _punch_cd == 0 (no cooldown active)
        """
        if self.get_distance_to_player(player) < self.PUNCH_RANGE and self._punch_cd == 0:
            # Start the punch animation and arm the punch_area
            self._punch_active = True
            self._punch_tick   = 0
            punch_area.activate(self.punch_damage, delay_frames=self.PUNCH_DELAY)
            self._punch_cd = self.PUNCH_COOLDOWN   # start cooldown

    def _update_punch_animation(self):
        """
        Advance the punch animation tick.
        Deactivates the punch after 45 frames (3 sprites × 15 frames each).
        """
        if not self._punch_active:
            return

        self._punch_tick += 1
        if self._punch_tick >= 45:
            self._punch_active = False
            self._punch_tick   = 0

    # =========================================================================
    # Cast System (Phase 2)
    # =========================================================================

    def _update_cast_cooldown(self):
        """Decrement the cast cooldown counter by 1 each frame."""
        if self._cast_cd > 0:
            self._cast_cd -= 1

    def _check_and_trigger_cast(self, projectiles):
        """
        Trigger eine Impact-Area und spawne ein Projektil wenn Olaf in Phase 2 ist und der Cooldown vorbei.
        Startet die Cast-Animation und aktiviert die Impact-Area mit Schaden.
        Das Projektil fliegt nur visual zur Impact-Area Position (kein Schaden vom Projektil).
        """
        if self.phase == 2 and self._cast_cd == 0:
            self._cast_active  = True
            self._cast_tick    = 0
            self._cast_cd      = self.CAST_COOLDOWN_BASE
            # Aktiviere die Impact-Area: sie wird an Marx's aktueller Position 
            # eingefrostet und blendet sich rot ein
            self.impact_area.activate(self.impact_damage, delay_frames=self.CAST_DELAY)
            # Spawne ein visuelles Projektil (fliegt zur eingefrorenen Impact-Area Position)
            proj = boss_projectile(self.position[0], self.position[1], 
                                   target_x=self.impact_area.locked_x,
                                   target_y=self.impact_area.locked_y,
                                   delay_frames=self.CAST_DELAY)
            projectiles.append(proj)

    def _update_cast_animation(self):
        """
        Advance the cast animation tick.
        Deactivates the cast after 30 frames (2 sprites × 15 frames each).
        """
        if not self._cast_active:
            return

        self._cast_tick += 1
        if self._cast_tick >= 30:
            self._cast_active = False
            self._cast_tick   = 0

    # =========================================================================
    # Phase System
    # =========================================================================

    def _check_phase(self):
        """
        Transition Olaf from Phase 1 to Phase 2 when his HP drops to
        PHASE_2_THRESHOLD (50 % = 500 HP).  Can only happen once.
        """
        if self.health_points <= self.PHASE_2_THRESHOLD and self.phase == 1:
            self.phase = 2

    # =========================================================================
    # Main Tick (called every frame by boss_fight.py)
    # =========================================================================

    def tick(self, player, projectiles, punch_area):
        """
        Per-frame update for the boss.  Called by boss_fight.py each iteration.

        Parameters
        ----------
        player      – the marx object
        projectiles – list to append new boss_projectile objects to
        punch_area  – the punch_area instance that visualises and applies the hit
        """
        if not self.alive:
            return

        # 1. Check whether Phase 2 should start
        self._check_phase()

        # 2. Move toward Marx
        self.follow_player(player)

        # 3. Melee punch system
        self._update_punch_cooldown(punch_area)
        self._check_and_trigger_punch(player, punch_area)
        self._update_punch_animation()
        punch_area.tick(player)   # tick punch_area so it counts down and deals damage

        # 4. Impact Area system (Phase 2 only)
        # Die neue Impact-Area Animation und Schaden-Anwendung
        if self.phase == 2:
            self._update_cast_cooldown()
            self._check_and_trigger_cast(projectiles)
            self._update_cast_animation()
            self.impact_area.tick()   # tick impact_area so it counts down and deals damage

        # 5. Update the displayed sprite
        self.update_animation()


# =============================================================================
# punch_area  –  Boss Melee Attack Zone
# =============================================================================

class punch_area:
    """
    Semi-transparent circle drawn around the boss during a melee attack.

    Behaviour:
      Inactive   → white, half-transparent circle (always visible)
      Activated  → the circle fades from transparent to red over the delay period
      On expiry  → collision with Marx is checked; if hit, damage is applied;
                   then the area becomes inactive again

    The SRCALPHA surface technique is identical to damage_area.drawrect() used
    for Marx's attack circle.
    """

    RADIUS = 150   # radius of the attack circle in pixels
    ALPHA  = 0     # current alpha value (0 = invisible, 255 = fully opaque)

    def __init__(self, boss):
        self.boss        = boss
        self.active      = False
        self.tick_count  = 0   # remaining frames until the hit is applied
        self.max_ticks   = 0   # initial value of tick_count (for colour interpolation)
        self.damage      = 0   # damage to apply when the countdown reaches 0

    # ── Controls ─────────────────────────────────────────────────────────────

    def activate(self, damage, delay_frames):
        """
        Start the attack countdown.
        Ignored if an attack is already in progress (no interrupt / reset).

        Parameters
        ----------
        damage       – HP to remove from Marx when the delay expires
        delay_frames – number of frames until the hit is applied
        """
        if not self.active:
            self.damage     = damage
            self.tick_count = delay_frames
            self.max_ticks  = delay_frames
            self.active     = True

    def tick(self, player):
        """
        Must be called every frame (from boss_opp.tick()).
        Counts down the delay; when it reaches 0, checks collision and deals damage.
        """
        if not self.active:
            return

        if self.tick_count > 0:
            self.tick_count -= 1   # one frame closer to the hit
        else:
            # Delay expired → apply damage if Marx is inside the area
            if player.get_rect().colliderect(self._get_collision_rect()):
                player.get_damage(self.damage)
            self.active = False   # attack is over

    # ── Internal Helpers ─────────────────────────────────────────────────────

    def _get_color(self):
        """
        Compute the current fill colour as an RGBA tuple.

        Inactive            → transparent red  (255, 0, 0, ALPHA=0)
        Activating (start)  → slowly increasing alpha
        Just before impact  → red at roughly 75 % opacity

        The green and blue channels are scaled linearly with `progress` while
        red stays at 255, producing a clean white → red transition.
        """
        if self.active == False or self.max_ticks == 0:
            self.ALPHA = 0  # Reset alpha when inactive
            return (255, 0, 0, self.ALPHA)

        progress   = (1 - (self.tick_count / self.max_ticks)) / 1.33   # 0.0 → ~0.75
        if not self.active:
            progress = 0
        self.ALPHA = int(255 * progress)
        return (255, 0, 0, self.ALPHA)

    def _get_collision_rect(self):
        """Return a rect centred on the boss used for hit detection."""
        cx, cy = self.boss.get_center_position()
        r      = self.RADIUS
        return pygame.Rect(cx - r, cy - r, r * 2, r * 2)

    # ── Drawing ───────────────────────────────────────────────────────────────

    def draw(self, screen):
        """
        Draw the semi-transparent circle using the same SRCALPHA technique as
        damage_area.drawrect():
          1. Create a Surface with SRCALPHA (per-pixel alpha)
          2. Draw the circle onto it with the current colour
          3. Blit the surface onto the main screen
        """
        cx, cy = self.boss.get_center_position()
        r      = self.RADIUS
        color  = self._get_color()

        target_rect = pygame.Rect(cx - r, cy - r, r * 2, r * 2)
        shape_surf  = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(shape_surf, color, (r, r), r)
        screen.blit(shape_surf, target_rect)



class impact_area:
	"""
	Impact-Area: Ein roter Kreis erscheint auf der aktuellen Position des Gegners
	und blendet sich langsam rot ein (wie punch_area).
	
	Wenn der Kreis voll eingefadet ist und Marx noch im Radius steht, wird der
	Schaden angewendet. Die Position wird eingefrostet wenn die Area aktiviert wird,
	sonst folgt sie immer dem Player.
	
	Das System wiederholt sich alle paar Sekunden (Cooldown-basiert).
	"""

	RADIUS = 150		# Radius des Impactbereichs in Pixeln
	ALPHA  = 0			# Aktuelle Alphavalue (0 = unsichtbar, 255 = vollständig opak)

	def __init__(self, player):
		self.player       = player
		self.active       = False		# Ist die Area gerade aktiv?
		self.tick_count   = 0			# Verbleibende Frames bis zum Hit
		self.max_ticks    = 0			# Speichert den Ausgangswert für Farbinterpolation
		self.damage       = 0			# Schaden zum Anwenden wenn Countdown = 0
		
		# Eingefrorene Position (wenn inaktiv, folgt sie dem Player)
		self.locked_x     = 0
		self.locked_y     = 0

	# ── Controls ─────────────────────────────────────────────────────────────

	def activate(self, damage, delay_frames):
		"""
		Aktiviert die Impact-Area.
		Wird ignoriert wenn eine Area bereits aktiv ist (kein Interrupt).

		Parameter
		---------
		damage       – HP abgezogen von Marx wenn Countdown = 0
		delay_frames – Frames bis der Hit angewendet wird
		"""
		if not self.active:
			self.damage     = damage
			self.tick_count = delay_frames
			self.max_ticks  = delay_frames
			self.active     = True
			
			# Position einfrieren: wo ist Marx jetzt?
			self.locked_x = self.player.x
			self.locked_y = self.player.y

	def tick(self):
		"""
		Muss jeden Frame aufgerufen werden (vom Boss).
		Zählt den Countdown runter; wenn 0 erreicht, prüft Kollision und wendet Schaden an.
		"""
		if not self.active:
			return

		if self.tick_count > 0:
			self.tick_count -= 1		# Ein Frame näher zum Hit
		else:
			# Countdown abgelaufen → Schaden anwenden wenn Marx im Bereich
			if self.player.get_rect().colliderect(self._get_collision_rect()):
				self.player.get_damage(self.damage)
			self.active = False		# Area ist vorbei

	# ── Internal Helpers ─────────────────────────────────────────────────────

	def _get_color(self):
		"""
		Berechnet die aktuelle Füllfarbe als RGBA Tuple.

		Inaktiv           → transparentes Rot (255, 0, 0, ALPHA=0)
		Aktiviert (Start) → Alpha langsam erhöhen
		Kurz vor Impact   → Rot ca. 75% opak

		Die Farbe übergeht von weiß zu rot während Alpha hochgeht.
		"""
		if self.active == False or self.max_ticks == 0:
			self.ALPHA = 0		# Alpha zurücksetzen wenn inaktiv
			return (255, 0, 0, self.ALPHA)

		progress   = (1 - (self.tick_count / self.max_ticks)) / 1.33		# 0.0 → ~0.75
		if not self.active:
			progress = 0
		self.ALPHA = int(255 * progress)
		return (255, 0, 0, self.ALPHA)

	def _get_collision_rect(self):
		"""Gibt ein Rechteck centerd auf die eingefrorene Position zurück (für Hit-Detection)."""
		# Wenn nicht aktiv, gibt die Position des Players zur Referenz
		if self.active:
			cx, cy = self.locked_x, self.locked_y
		else:
			cx, cy = self.player.x, self.player.y
		
		r = self.RADIUS
		return pygame.Rect(cx - r, cy - r, r * 2, r * 2)

	# ── Drawing ───────────────────────────────────────────────────────────────

	def draw(self, screen):
		"""
		Zeichnet den semi-transparenten Kreis mit SRCALPHA-Technik:
		  1. Surface mit SRCALPHA erstellen (Pro-Pixel Alpha)
		  2. Kreis drauf zeichnen mit aktueller Farbe
		  3. Surface auf den Screen blitten
		"""
		if not self.active:
			return
		
		# Wenn aktiv, nutzen wir die eingefrorene Position
		cx, cy = self.locked_x, self.locked_y
		r      = self.RADIUS
		color  = self._get_color()

		target_rect = pygame.Rect(cx - r, cy - r, r * 2, r * 2)
		shape_surf  = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
		pygame.draw.circle(shape_surf, color, (r, r), r)
		screen.blit(shape_surf, target_rect)


# =============================================================================
# boss_projectile  – Visual Projectile (Aesthetic Only)
# =============================================================================

class boss_projectile:
	"""
	Visuelles Projektil das von Olaf zur Impact-Area Position fliegt.
	
	Keine Schaden-Anwendung – der Schaden kommt von der Impact-Area.
	Das Projektil ist nur optisch um die Cast-Animation zu unterstützen.

	Lifecycle:
	  1. Spawns at the boss's position.
	  2. Waits for delay_frames (plays cast animation on the boss side).
	  3. Flies toward the impact area's target position at SPEED pixels per frame.
	  4. On arrival (within 20 px of target): disappears, no damage or collision.
	  5. alive is set to False → removed from the list by boss_fight.py.
	"""

	SPEED  = 3    # pixels per frame during flight

	def __init__(self, start_x, start_y, target_x, target_y, delay_frames):
		"""
		Parameters
		----------
		start_x, start_y – spawn position (Olaf's position)
		target_x, target_y – destination (impact area's locked position)
		delay_frames     – frames to wait before the projectile starts flying
		"""
		self.x            = float(start_x)
		self.y            = float(start_y)
		self.target_x     = float(target_x)
		self.target_y     = float(target_y)
		self.alive        = True

		# Delay tracking
		self.delay_frames = delay_frames
		self.tick_count   = 0

		# Pre-compute the normalised direction vector scaled by SPEED
		dx   = self.target_x - self.x
		dy   = self.target_y - self.y
		dist = (dx ** 2 + dy ** 2) ** 0.5
		if dist > 0:
			self.vx = (dx / dist) * self.SPEED
			self.vy = (dy / dist) * self.SPEED
		else:
			self.vx = self.vy = 0   # edge case: spawn == target

		# Load the projectile sprite (projectile.png)
		try:
			self.image = load_image(get_resource_path("projectile.png"), scale=0.25)
		except Exception as e:
			print(f"Projektil-Textur nicht gefunden: {e}")
			self.image = None

		# Collision rect (updated every frame during flight)
		if self.image:
			self.rect = self.image.get_rect(topleft=(int(self.x), int(self.y)))
		else:
			self.rect = pygame.Rect(0, 0, 0, 0)

	# ── Drawing ──────────────────────────────────────────────────────────────

	def draw(self, screen):
		"""
		Draw the projectile sprite.
		Hidden during the delay phase (before flight starts) and after arrival.
		"""
		if self.alive and self.tick_count >= self.delay_frames and self.image:
			self.rect.topleft = (int(self.x), int(self.y))
			screen.blit(self.image, self.rect)

	# ── Main Tick ────────────────────────────────────────────────────────────

	def tick(self):
		"""
		Per-frame update.  Called by boss_fight.py every iteration.
		Moves toward target; marks as dead on arrival.
		"""
		if not self.alive:
			return

		self.tick_count += 1

		# During the delay phase: do nothing (boss plays cast animation)
		if self.tick_count < self.delay_frames:
			return

		# --- Flight phase: move toward the target position -------------------
		self.x += self.vx
		self.y += self.vy
		self.rect.topleft = (int(self.x), int(self.y))

		# Check whether the target has been reached (within 20 px)
		dx   = self.target_x - self.x
		dy   = self.target_y - self.y
		dist = (dx ** 2 + dy ** 2) ** 0.5

		if dist < 20:
			self.alive = False   # arrived → mark as dead, no collision check