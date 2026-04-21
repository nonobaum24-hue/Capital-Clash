# =============================================================================
# game_classes.py  –  Player Classes and Combat Helpers
# =============================================================================
# Contains everything that belongs to the player character (Marx) and the
# supporting visual/combat objects around him:
#
#   load_image()    – cached image loader (avoids redundant disk reads)
#   marx            – the player character: movement, attack, health, animation
#   damage_area     – the visible attack circle around Marx
#   damage_screen   – red screen flash when Marx takes damage
#   health_bar      – HP bar used both by Marx and by enemies
# =============================================================================

import os
import pygame
from random import randint, uniform

# =============================================================================
# Module-level Constants
# =============================================================================

# Absolute path to the directory that contains this script.
# Used to build asset paths that work regardless of the working directory.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# =============================================================================
# Image Cache
# =============================================================================

# Global dictionary that stores already-loaded images.
# Key: (absolute_path, scale_factor)  →  Value: scaled pygame.Surface
# Avoids loading the same image multiple times from disk, which is expensive.
_IMAGE_CACHE = {}

def load_image(path, scale=0.25):
    """
    Load an image from disk, scale it, and cache the result.

    If the same (path, scale) combination was loaded before, the cached
    surface is returned immediately without touching the disk again.

    Parameters
    ----------
    path  : str   – file path to the image
    scale : float – scale factor applied to width and height (default 0.25)

    Returns
    -------
    pygame.Surface – the scaled image surface with alpha channel preserved
    """
    key = (os.path.abspath(path), float(scale))

    # Cache hit: return the already-loaded surface
    if key in _IMAGE_CACHE:
        return _IMAGE_CACHE[key]

    # Cache miss: load from disk, scale, then store
    img = pygame.image.load(path).convert_alpha()   # keep transparency (RGBA)
    img = pygame.transform.scale(img, (
        int(img.get_width()  * scale),
        int(img.get_height() * scale)))

    _IMAGE_CACHE[key] = img   # store for future calls
    return img


# =============================================================================
# Player Class – marx
# =============================================================================

class marx:
    """
    Represents the player character Marx.

    Responsibilities:
      - Movement across the screen (arrow keys, clamped to window borders)
      - Melee attack (space bar) with cooldown and random target selection
      - Taking damage from enemies, triggering the red screen flash
      - Healing from collectibles (capped at max_health)
      - Toggling between idle and run sprites based on movement state
    """

    def __init__(self, x, y, idle_path, run_path, scale=0.25,
                 health_points=100, screen_w=1250, screen_h=720):
        """
        Parameters
        ----------
        x, y           – starting position (top-left corner of the sprite)
        idle_path      – file path for the standing/idle sprite
        run_path       – file path for the running sprite
        scale          – scale factor applied to both sprites (default 0.25)
        health_points  – starting HP; also used as the initial max_health
        screen_w/h     – window dimensions for movement clamping and spawn logic
        """
        self.x = x
        self.y = y
        self.alive = True

        self.scale          = scale
        self.health_points  = health_points
        self.max_health     = health_points   # upper HP cap; raised by Revive collectibles
        self.damage         = 30              # damage per attack hit

        # Minimum safe distance around Marx where enemies are not allowed to spawn.
        # Prevents enemies from spawning directly on top of the player.
        self.exception_radius = 150

        # Window boundaries used for movement clamping and spawn-exclusion zone
        self.screen_w = screen_w
        self.screen_h = screen_h

        # Pre-load both animation sprites via the cache
        self.stand_bild = load_image(idle_path, scale=self.scale)   # idle frame
        self.lauf_bild  = load_image(run_path,  scale=self.scale)   # run frame

        # Start with the idle sprite active
        self.image = self.stand_bild
        self.rect  = self.image.get_rect(topleft=(self.x, self.y))

        # Animation state tracking
        self.framecount_skin = 0      # frames elapsed since last sprite toggle
        self.is_first_skin   = True   # which sprite is currently shown (toggle)
        self.prev_is_moving  = False  # was Marx moving last frame? (for transition)

        # Attack cooldown counter (frames remaining; 0 = ready to attack)
        self.attack_cooldown = 0

    # -------------------------------------------------------------------------
    # State Control
    # -------------------------------------------------------------------------

    def dead(self):
        """Mark Marx as dead.  Called by get_damage() when HP reaches 0."""
        self.alive = False

    # -------------------------------------------------------------------------
    # Movement
    # -------------------------------------------------------------------------

    def move(self, dx, dy):
        """
        Move Marx by (dx, dy) pixels, clamped to the window borders.
        The collision rect (self.rect) is kept in sync after every move.
        """
        # Only apply horizontal movement if Marx stays inside the window
        if 0 < self.x + dx < self.screen_w - self.rect.width:
            self.x += dx
        # Only apply vertical movement if Marx stays inside the window
        if 0 < self.y + dy < self.screen_h - self.rect.height:
            self.y += dy

        # Keep the collision rect aligned with the logical position
        self.rect.topleft = (self.x, self.y)

    # -------------------------------------------------------------------------
    # Drawing
    # -------------------------------------------------------------------------

    def draw(self, screen):
        """Draw Marx onto the screen.  Does nothing if Marx is dead."""
        if self.alive:
            screen.blit(self.image, (self.x, self.y))

    # -------------------------------------------------------------------------
    # Accessors
    # -------------------------------------------------------------------------

    def get_rect(self):
        """Return the current collision rect (used by enemies and attack checks)."""
        return self.rect

    # -------------------------------------------------------------------------
    # Animation
    # -------------------------------------------------------------------------

    def tick_animation(self, is_moving):
        """
        Switch between the idle and run sprite based on movement state.

        Called once per frame.  Sprite switches happen every 15 frames to
        avoid flickering.  When movement starts, the run sprite is applied
        immediately (no delay).

        Parameters
        ----------
        is_moving : bool – True if any arrow key is currently held
        """
        if is_moving and not self.prev_is_moving:
            # Movement just started → switch to run sprite immediately
            self.image           = self.lauf_bild
            self.is_first_skin   = False
            self.framecount_skin = 0
            self.rect = self.image.get_rect(topleft=(self.x, self.y))

        elif is_moving:
            # Still moving → toggle sprites every 15 frames
            self.framecount_skin += 1
            if self.framecount_skin >= 15:
                self.image = self.stand_bild if not self.is_first_skin else self.lauf_bild
                self.is_first_skin   = not self.is_first_skin
                self.rect = self.image.get_rect(topleft=(self.x, self.y))
                self.framecount_skin = 0

        else:
            # Not moving → always show the idle sprite
            self.image           = self.stand_bild
            self.framecount_skin = 0
            self.is_first_skin   = True

        # Remember this frame's movement state for the next frame's transition check
        self.prev_is_moving = is_moving

    # -------------------------------------------------------------------------
    # Game State
    # -------------------------------------------------------------------------

    def update(self):
        """
        Return the current game state as a tuple: (alive, (x, y)).
        Called every frame by the game loop to check whether Marx is still alive.
        """
        return self.alive, (self.x, self.y)

    # -------------------------------------------------------------------------
    # Input Handling
    # -------------------------------------------------------------------------

    def input_monitoring(self, keys, area, opponents):
        """
        Process keyboard input for movement and attacking.

        Parameters
        ----------
        keys      – result of pygame.key.get_pressed() for the current frame
        area      – damage_area object (used to colour the attack circle)
        opponents – list of currently active enemy objects (for hit detection)
        """
        # Movement: 5 pixels per frame in the pressed direction
        if keys[pygame.K_LEFT]:  self.move(-5,  0)
        if keys[pygame.K_RIGHT]: self.move( 5,  0)
        if keys[pygame.K_UP]:    self.move( 0, -5)
        if keys[pygame.K_DOWN]:  self.move( 0,  5)

        # Cooldown tick: count down by 1 each frame and colour the area accordingly
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
            area.turnred()    # red = attack on cooldown, cannot strike yet
        else:
            area.turnwhite()  # white = ready to attack

        # Attack: SPACE bar, only when cooldown is 0
        if keys[pygame.K_SPACE] and self.attack_cooldown == 0:
            # Collect all enemies whose rect overlaps the attack circle rect
            if isinstance(opponents, list):
                # Fighting normal enemies (list of opp_classes instances)
                in_range = [o for o in opponents if o.rect.colliderect(area.getrect())]
                if in_range:
                    # Pick one enemy at random to prevent always hitting the same target
                    in_range[randint(0, len(in_range) - 1)].getdamage(self.damage)
            else:
                # Fighting the boss (boss_opp instance)
                if opponents.rect.colliderect(area.getrect()):
                    opponents.getdamage(self.damage)
            # Start the cooldown: 30 frames = 0.5 seconds at 60 FPS
            self.attack_cooldown = 30

    # -------------------------------------------------------------------------
    # Combat
    # -------------------------------------------------------------------------

    def get_damage(self, damage, damage_screen=None):
        """
        Subtract damage from HP.  Optionally triggers the red screen flash.
        If HP drops to 0 or below, Marx is marked as dead.

        Parameters
        ----------
        damage        – amount of HP to remove
        damage_screen – optional damage_screen instance to trigger the red flash
        """
        if self.alive:
            self.health_points -= damage
            if damage_screen:
                damage_screen.trigger()   # start the red overlay effect
            if self.health_points <= 0:
                self.dead()

    def heal(self, amount):
        """
        Restore 'amount' HP, but never above max_health.
        Has no effect if Marx is already dead.
        """
        if self.alive:
            self.health_points = min(self.max_health, self.health_points + amount)

    def gethealth(self):
        """Return current HP.  Used by health_bar to calculate the fill ratio."""
        return self.health_points

    def get_exception_area(self):
        """
        Return the square exclusion zone around Marx where enemies must not spawn.
        The zone is centred on Marx's sprite centre with a radius of exception_radius.

        Returns
        -------
        (x_start, x_end, y_start, y_end) as pixel coordinates
        """
        x, y = self.get_rect().center
        r = self.exception_radius
        return (x - r, x + r, y - r, y + r)


# =============================================================================
# Combat Helpers
# =============================================================================

class damage_area:
    """
    Visual attack circle drawn around Marx.

    The circle is white when Marx can attack and turns red while the cooldown
    is active.  It also serves as the collision rectangle for attack hit tests.

    The circle is drawn using its own SRCALPHA surface so transparency works
    correctly on top of other sprites.
    """

    def __init__(self, origin):
        """
        Parameters
        ----------
        origin – the object the area follows (normally the marx instance)
        """
        self.widthmulti   = 1    # multiplier for the attack radius (for power-ups)
        self.damagemulti  = 1    # damage multiplier (reserved for future power-ups)
        self.origin       = origin
        self.normal_width = 150  # base radius in pixels
        self.color = (255, 255, 255, 125)   # RGBA: white, half-transparent

    def getparentposition(self):
        """Return the centre coordinates of the tracked object."""
        return self.origin.get_rect().center

    def drawrect(self, screen):
        """
        Draw the semi-transparent circle onto the screen.

        A dedicated SRCALPHA surface is used so the circle's alpha channel is
        rendered correctly even when it overlaps other sprites.
        """
        radius = 200
        # Create a rect centred on Marx and inflate it to fit the circle
        target_rect = pygame.Rect(self.getparentposition(), (0, 0)).inflate(
                      (radius * 2, radius * 2))
        # Draw on a transparent surface so the circle blends with what is below
        shape_surf = pygame.Surface(target_rect.size, pygame.SRCALPHA)
        pygame.draw.circle(shape_surf, self.color, (radius, radius), radius)
        screen.blit(shape_surf, target_rect)

    def getrect(self):
        """
        Return the rectangular collision area for attack hit tests.
        The radius scales with widthmulti so power-ups can expand the range.
        """
        pos    = self.getparentposition()
        radius = self.normal_width * self.widthmulti
        return pygame.Rect(pos[0] - radius, pos[1] - radius, radius * 2, radius * 2)

    def turnred(self):
        """Colour the circle red to signal that Marx is on attack cooldown."""
        self.color = (255, 0, 0, 125)

    def turnwhite(self):
        """Colour the circle white to signal that Marx can attack again."""
        self.color = (255, 255, 255, 125)


class damage_screen:
    """
    Full-screen red overlay that fades out over ~0.33 seconds when Marx is hit.

    trigger() resets the counter to its maximum; draw() decrements it every
    frame and renders the overlay with alpha proportional to the remaining time.
    """

    def __init__(self):
        self.duration = 20   # total frames the effect lasts (20 / 60 fps ≈ 0.33 s)
        self.counter  = 0    # frames remaining; 0 = invisible

    def trigger(self):
        """Start (or restart) the red flash effect.  Called by marx.get_damage()."""
        self.counter = self.duration

    def draw(self, screen):
        """
        Draw the red overlay.  Must be called every frame.
        Alpha decreases linearly from 80 to 0 as the counter runs down.
        """
        if self.counter > 0:
            self.counter -= 1   # count down even when not visible to other callers

        # Alpha is proportional to the remaining counter: 80 at full, 0 at 0
        alpha = int(80 * self.counter / self.duration)
        surf  = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        surf.fill((255, 0, 0, alpha))
        screen.blit(surf, (0, 0))


class health_bar:
    """
    HP bar that can be attached to any game object with a gethealth() method.

    Renders as a red background rectangle with a green foreground rectangle
    whose width is proportional to the current HP.

    With follow=True the bar automatically positions itself above the object's
    sprite so it stays attached to moving enemies.
    """

    def __init__(self, x, y, width, height, object, follow=False):
        """
        Parameters
        ----------
        x, y   – fixed position (ignored when follow=True)
        width  – total bar width in pixels
        height – bar height in pixels
        object – the game object to track (must expose gethealth())
        follow – if True, the bar follows object.rect automatically
        """
        self.x          = x
        self.y          = y
        self.width      = width
        self.height     = height
        self.max_health = object.gethealth()   # stored once at creation time
        self.object     = object
        self.follow     = follow

    def draw(self, screen):
        """
        Draw the health bar.  Re-reads current HP every frame.

        When follow=True the position is computed from the object's rect so
        the bar moves with the sprite.
        """
        hp = self.object.gethealth()

        if self.follow:
            # Position the bar 10 px to the left of and 12 px above the sprite
            self.x = self.object.rect.x - 10
            self.y = self.object.rect.y - 12

        # Red background: represents the maximum (missing) health
        pygame.draw.rect(screen, (255, 0, 0),
                         (self.x, self.y, self.width, self.height))

        # Green foreground: represents the current health fraction
        pct = max(0, hp / self.max_health)   # clamp to [0, 1] so bar never goes negative
        pygame.draw.rect(screen, (0, 255, 0),
                         (self.x, self.y, self.width * pct, self.height))
