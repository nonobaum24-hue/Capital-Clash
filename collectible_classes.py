# =============================================================================
# collectible_classes.py  –  Collectible Items (Drops)
# =============================================================================
# Enemies drop collectible items when they are killed.  Marx walks over them
# to collect them and trigger their effect.
#
# Class hierarchy:
#   Collectible            – base class (draw, collision check, effect dispatch)
#   ├── Heal               – restores 15 HP (dropped by MiniOpp)
#   ├── Aoe                – deals 30 damage to ALL enemies on screen (NormalOpp)
#   └── Revive             – raises max HP by 10 and fully refills HP (SuperOpp)
#
#   collectible_manager    – owns all active Collectibles; spawns, draws, collects
# =============================================================================

from game_classes import load_image, SCRIPT_DIR
import os
from random import randint, uniform


class Collectible:
    """
    Base class for all collectible items.

    When an enemy dies, the collectible_manager may spawn a Collectible at the
    enemy's position.  Each frame the collectible is drawn on screen; as soon
    as Marx's rect overlaps it, it is marked as collected and its effect fires.
    """

    def __init__(self, x, y, image_path, effect, player):
        """
        Parameters
        ----------
        x, y        – spawn position (equals the dead enemy's position)
        image_path  – path to the sprite image
        effect      – string identifying the effect: "health" | "aoe" | "revive"
        player      – reference to the marx object (for collision + effect application)
        """
        self.x         = x
        self.y         = y
        self.image     = load_image(image_path, scale=0.25)
        self.rect      = self.image.get_rect(topleft=(self.x, self.y))
        self.collected = False   # becomes True as soon as Marx walks over it
        self.effect    = effect
        self.player    = player

    def spawn(self, screen):
        """
        Draw the collectible onto the screen.
        Does nothing once collected (collected == True).
        """
        if not self.collected:
            screen.blit(self.image, (self.x, self.y))

    def collectcheck(self, opponents):
        """
        Check every frame whether Marx is touching this collectible.

        If Marx's rect overlaps the collectible's rect:
          - mark it as collected
          - trigger the effect (opponents list is forwarded for the AOE effect)
        """
        if not self.collected and self.rect.colliderect(self.player.get_rect()):
            self.collected = True
            self.trigger_effect(opponents)

    def trigger_effect(self, opponents):
        """
        Apply the collectible's effect to the game world.

        "health"  → heal Marx by 15 HP (capped at max_health)
        "aoe"     → deal 30 damage to every active enemy on screen
        "revive"  → permanently raise Marx's max HP by 10, then fully refill HP
        """
        if self.effect == "health":
            self.player.heal(15)

        elif self.effect == "aoe":
            # Deal damage to every enemy currently on the field
            for opp in opponents:
                opp.getdamage(30)

        elif self.effect == "revive":
            self.player.max_health    += 10                         # permanent max HP increase
            self.player.health_points  = self.player.max_health    # fill HP to new maximum


# =============================================================================
# Concrete Collectible Types
# =============================================================================

class Heal(Collectible):
    """Heals Marx by 15 HP.  Dropped by MiniOpp enemies."""
    def __init__(self, x, y, player):
        super().__init__(x, y, os.path.join(SCRIPT_DIR, "heal.png"), "health", player)


class Aoe(Collectible):
    """Deals 30 damage to all active enemies.  Dropped by NormalOpp enemies."""
    def __init__(self, x, y, player):
        super().__init__(x, y, os.path.join(SCRIPT_DIR, "aoe.png"), "aoe", player)


class Revive(Collectible):
    """Raises max HP by 10 and fully restores HP.  Dropped by SuperOpp enemies."""
    def __init__(self, x, y, player):
        super().__init__(x, y, os.path.join(SCRIPT_DIR, "revive.png"), "revive", player)


# =============================================================================
# Lookup Table
# =============================================================================

# Maps the drop-string stored on each enemy class to the corresponding
# Collectible subclass.  Used by collectible_manager to instantiate the right type.
_COLLECTIBLE_MAP = {
    "heal":   Heal,
    "aoe":    Aoe,
    "revive": Revive,
}


# =============================================================================
# collectible_manager
# =============================================================================

class collectible_manager:
    """
    Manages all active Collectibles on the game field.

    Responsibilities (in order, every frame):
      1. Detect newly dead enemies and maybe spawn their drop
      2. Draw all un-collected Collectibles
      3. Check whether Marx picked any of them up
      4. Remove collected Collectibles from the active list

    IMPORTANT: collectible_tick() MUST be called BEFORE the cleanup step in
    the game loop (where dead enemies are removed from the opponents list).
    The manager needs dead enemies still present so it can read their position
    and drop type.
    """

    def __init__(self, player):
        self.player       = player
        self.collectibles = []    # list of all currently visible Collectible objects
        self._dropped     = set() # set of id()s of enemies that already triggered a drop
                                  # prevents the same enemy from dropping twice

    def collectible_tick(self, screen, opponents):
        """
        Main per-frame update.  Must be called before the enemy cleanup step.

        Step 1 – Drop detection:
          Iterates over all opponents; for each dead enemy not yet processed,
          rolls against its drop chance and spawns a Collectible if successful.

        Step 2 – Draw & collect:
          Draws every active Collectible and checks whether Marx picked it up.

        Step 3 – Remove collected:
          Replaces self.collectibles with a new list that only contains items
          that have not been picked up yet.
        """

        # --- Step 1: Drop Detection -------------------------------------------
        for opp in opponents:
            if not opp.alive and id(opp) not in self._dropped:
                self._dropped.add(id(opp))   # mark as processed (drop checked)

                # Roll a random number 1–100 against the enemy's drop chance
                if opp.collectible and randint(1, 100) <= opp.collectible_chance:
                    cls = _COLLECTIBLE_MAP.get(opp.collectible)   # look up the type
                    if cls:
                        # Spawn the collectible at the enemy's death position
                        self.collectibles.append(cls(opp.x, opp.y, self.player))

        # --- Steps 2 & 3: Draw, Collect, Clean Up -----------------------------
        # Build a fresh list instead of removing items during iteration (avoids bugs)
        active = []
        for c in self.collectibles:
            c.collectcheck(opponents)   # check if Marx walked over it
            if not c.collected:
                c.spawn(screen)         # draw only if not yet collected
                active.append(c)        # keep in the active list
        self.collectibles = active      # discard collected items

        # --- Housekeeping: clear the _dropped set once no dead enemies remain --
        # Python re-uses object ids, so we only clear the set when there are no
        # dead enemies left on the field to avoid false-positive matches.
        dead_ids = {id(o) for o in opponents if not o.alive}
        if not dead_ids:
            self._dropped.clear()
