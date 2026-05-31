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
    # === PUNCH ATTACK ===
    PUNCH_RANGE         = 200           # pixels: melee attack triggers below this distance
    PUNCH_DELAY         = 45            # frames: wind-up time before punch lands
    PUNCH_COOLDOWN      = 120           # frames: time between punch attacks
    PUNCH_DAMAGE        = 35            # HP removed per punch hit
    PUNCH_FRAMES        = 3             # number of animation frames
    PUNCH_FRAME_DUR     = 15            # frames per animation frame

    # === PHASE 2 - CAST/IMPACT ATTACK ===
    PHASE_2_THRESHOLD   = 500           # HP at which boss enters Phase 2
    CAST_COOLDOWN_BASE  = (150, 250)    # (min, max) frames between casts
    CAST_DELAY          = 90            # frames: animation delay before impact area activates
    CAST_FRAMES         = 2             # number of animation frames
    CAST_FRAME_DUR      = 30            # frames per animation frame
    
    # === PROJECTILE ===
    PROJECTILE_SPEED    = 5             # pixels per frame during flight
    PROJECTILE_SPAWN_DLY = 30           # frames: delay before projectile spawns after cast
    IMPACT_DAMAGE       = 20            # HP removed per impact area hit

    def __init__(self, player, aoi):
        # ── HP & Damage ──────────────────────────────────────────────────────
        self.max_health         = 1000
        self.health_points      = self.max_health
        self.punch_damage       = self.PUNCH_DAMAGE
        self.impact_damage      = self.IMPACT_DAMAGE
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
        script_dir = SCRIPT_DIR

        # Idle animation: single frame shown when Olaf is standing still

        self.scale = 2

        self.anim_idle = load_image(
            os.path.join(script_dir, "assets", "animations", "olaf", "idle_olaf", "idle_olaf.png"),
            scale=self.scale
        )

        # Walk animation: single frame shown when Olaf is moving
        self.anim_walk = load_image(
            os.path.join(script_dir, "assets", "animations", "olaf", "walk_olaf", "walk_olaf.png"),
            scale=self.scale
        )

        # Punch animation: 3 frames; played over 45 ticks (15 ticks per frame)
        self.anim_punch = [
            load_image(os.path.join(script_dir, "assets", "animations", "olaf", "punch_olaf", "punch_olaf_1.png"), scale=self.scale),
            load_image(os.path.join(script_dir, "assets", "animations", "olaf", "punch_olaf", "punch_olaf_2.png"), scale=self.scale),
            load_image(os.path.join(script_dir, "assets", "animations", "olaf", "punch_olaf", "punch_olaf_3.png"), scale=self.scale),
        ]

        # Cast animation: 2 frames; played over 30 ticks (15 ticks per frame)
        # Only used in Phase 2 when creating impact areas
        self.anim_cast = [
            load_image(os.path.join(script_dir, "assets", "animations", "olaf", "cast_olaf", "cast_olaf_1.png"), scale=self.scale),
            load_image(os.path.join(script_dir, "assets", "animations", "olaf", "cast_olaf", "cast_olaf_2.png"), scale=self.scale),
        ]
        
        # Precalculate animation durations - SYNCED MIT DELAYS!
        # Punch-Animation dauert GENAU so lange wie PUNCH_DELAY
        self.punch_anim_duration = self.PUNCH_DELAY
        # Cast-Animation dauert GENAU so lange wie CAST_DELAY
        self.cast_anim_duration = self.CAST_DELAY

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
            # Spread punch frames evenly over PUNCH_DELAY
            frame_duration = self.punch_anim_duration / len(self.anim_punch)
            frame_idx = min(len(self.anim_punch) - 1, int(self._punch_tick / frame_duration))
            self.image = self.anim_punch[frame_idx]
            return

        # -- Cast animation takes second priority -----------------------------
        if self._cast_active:
            # Spread cast frames evenly over CAST_DELAY
            frame_duration = self.cast_anim_duration / len(self.anim_cast)
            frame_idx = min(len(self.anim_cast) - 1, int(self._cast_tick / frame_duration))
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
        Deactivates the punch after punch_anim_duration frames.
        Duration syncs automatically with PUNCH_DELAY!
        """
        if not self._punch_active:
            return

        self._punch_tick += 1
        if self._punch_tick >= self.punch_anim_duration:
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
        Trigger an impact area and spawn a visual projectile if Olaf is in Phase 2
        and the cooldown is expired.
        
        The cast animation plays while the impact area is locked in place at Marx's
        current position. A projectile flies visually toward the impact area (purely
        for show; damage comes from the impact area itself).
        
        Parameters
        ----------
        projectiles : list
            List to append new boss_projectile objects to
        """
        if self.phase == 2 and self._cast_cd == 0:
            self._cast_active  = True
            self._cast_tick    = 0
            # Set cooldown to a random value between min and max
            self._cast_cd      = randint(self.CAST_COOLDOWN_BASE[0], self.CAST_COOLDOWN_BASE[1])
            # Activate the impact area: it locks to Marx's current position
            # and fades in red over the delay period
            self.impact_area.activate(self.impact_damage, delay_frames=self.CAST_DELAY)
            # Spawn a visual projectile (flies to the locked impact area position)
            proj = boss_projectile(self.position[0], self.position[1], 
                                   target_x=self.impact_area.locked_x,
                                   target_y=self.impact_area.locked_y)
            projectiles.append(proj)

    def _update_cast_animation(self):
        """
        Advance the cast animation tick.
        Deactivates the cast after cast_anim_duration frames.
        Duration syncs automatically with CAST_DELAY!
        """
        if not self._cast_active:
            return

        self._cast_tick += 1
        if self._cast_tick >= self.cast_anim_duration:
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
        Per-frame update for the boss. Called by boss_fight.py every iteration.

        Parameters
        ----------
        player      : marx – the player character
        projectiles : list – list to append new boss_projectile objects to
        punch_area  : punch_area – the punch_area instance that visualises and applies melee hits
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

    RADIUS = 200   # radius of the attack circle in pixels
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
    Impact area: A red circle appears at Marx's current position (when activated)
    and fades in red over the delay period.
    
    Once fully faded and Marx is still in the radius, damage is applied.
    The position is locked when activated; otherwise it follows the player.
    
    The system repeats every few seconds based on the cooldown timer.
    """

    RADIUS = 80         # Radius of the impact area in pixels
    ALPHA  = 0          # Current alpha value (0 = invisible, 255 = fully opaque)

    def __init__(self, player):
        """
        Parameters
        ----------
        player : marx – reference to the player character
        """
        self.player       = player
        self.active       = False      # Is the area currently active?
        self.tick_count   = 0          # Remaining frames until damage is applied
        self.max_ticks    = 0          # Stores the initial value for colour interpolation
        self.damage       = 0          # Damage to apply when countdown reaches 0
        
        # Locked position (when inactive, follows the player for preview)
        self.locked_x     = 0
        self.locked_y     = 0

    def activate(self, damage, delay_frames):
        """
        Activate the impact area.
        Ignored if an area is already active (no interrupt/reset).

        Parameters
        ----------
        damage       : int – HP to remove from Marx when countdown expires
        delay_frames : int – number of frames until damage is applied
        """
        if not self.active:
            self.damage     = damage
            self.tick_count = delay_frames
            self.max_ticks  = delay_frames
            self.active     = True
            
            # Lock position: where is Marx right now?
            self.locked_x = self.player.x
            self.locked_y = self.player.y

    def tick(self):
        """
        Per-frame update. Must be called every frame (from boss_opp.tick()).
        Counts down the delay; when it reaches 0, checks collision and applies damage.
        """
        if not self.active:
            return

        if self.tick_count > 0:
            self.tick_count -= 1        # One frame closer to damage
        else:
            # Countdown expired → apply damage if Marx is in the collision area
            if self.player.get_rect().colliderect(self._get_collision_rect()):
                self.player.get_damage(self.damage)
            self.active = False         # Area effect is complete

    def draw(self, screen):
        """
        Draw the semi-transparent circle using SRCALPHA technique:
          1. Create a Surface with SRCALPHA (per-pixel alpha)
          2. Draw the circle onto it with the current colour
          3. Blit the surface onto the main screen
        """
        if not self.active:
            return
        
        # Use the locked position for the active area
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
    Visual projectile that flies from Olaf to the impact area position.
    
    No damage is applied by this projectile—damage comes from the impact area.
    The projectile is purely aesthetic to support the cast animation.

    Lifecycle:
      1. Spawns at the boss's position
      2. Waits for PROJECTILE_SPAWN_DELAY (cast animation plays)
      3. Flies toward the impact area's target position at SPEED pixels/frame
      4. On arrival (within 20 px of target): disappears
      5. alive is set to False → removed from the list by boss_fight.py
    """

    SPEED  = 5                  # Pixels per frame during flight
    SPAWN_DELAY = 30            # Frames: delay before projectile starts flying

    def __init__(self, start_x, start_y, target_x, target_y):
        """
        Parameters
        ----------
        start_x, start_y : float – spawn position (Olaf's position)
        target_x, target_y : float – destination (impact area's locked position)
        """
        self.x            = float(start_x)
        self.y            = float(start_y)
        self.target_x     = float(target_x)
        self.target_y     = float(target_y)
        self.alive        = True

        # Delay tracking - waits before starting to move
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
            self.image = load_image(os.path.join(SCRIPT_DIR, "assets", "effects", "projectile.png"), scale=0.25)
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
        Hidden during the spawn delay phase (before flight starts) and after arrival.
        """
        if self.alive and self.tick_count >= self.SPAWN_DELAY and self.image:
            self.rect.topleft = (int(self.x), int(self.y))
            screen.blit(self.image, self.rect)

    # ── Main Tick ────────────────────────────────────────────────────────────

    def tick(self):
        """
        Per-frame update. Called by boss_fight.py every iteration.
        Moves toward target; marks as dead on arrival.
        """
        if not self.alive:
            return

        self.tick_count += 1

        # During the delay phase: do nothing (boss plays cast animation)
        if self.tick_count < self.SPAWN_DELAY:
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
            self.alive = False   # Arrived → mark as dead, no collision check