from game_classes import load_image, SCRIPT_DIR
import os
from random import randint, uniform

class Collectible:
	"""
	Basisklasse für alle aufsammelbaren Gegenstände.
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
		  health → heilt Marx um 15 HP (gecappt auf max_health)
		  aoe    → fügt ALLEN aktiven Gegnern 30 Schaden zu
		  revive → erhöht Max-HP um 10 und füllt HP komplett auf
		"""
		if self.effect == "health":
			self.player.heal(15)
		elif self.effect == "aoe":
			for opp in opponents:
				opp.getdamage(30)
		elif self.effect == "revive":
			self.player.max_health    += 10                      # Max-HP dauerhaft erhöhen
			self.player.health_points  = self.player.max_health  # HP voll auffüllen


class Heal(Collectible):
	"""Heilt Marx um 15 HP. Wird von MiniOpp gedroppt."""
	def __init__(self, x, y, player):
		super().__init__(x, y, os.path.join(SCRIPT_DIR, "heal.png"), "health", player)

class Aoe(Collectible):
	"""Fügt allen Gegnern auf dem Bildschirm 30 Schaden zu. Wird von NormalOpp gedroppt."""
	def __init__(self, x, y, player):
		super().__init__(x, y, os.path.join(SCRIPT_DIR, "aoe.png"), "aoe", player)

class Revive(Collectible):
	"""Füllt HP komplett auf und erhöht Max-HP um 10. Wird von SuperOpp gedroppt."""
	def __init__(self, x, y, player):
		super().__init__(x, y, os.path.join(SCRIPT_DIR, "revive.png"), "revive", player)


# Lookup-Tabelle: Drop-String aus Gegner-Klasse → Collectible-Klasse
# Wird im CollectibleManager genutzt um den richtigen Typ zu instanziieren.
_COLLECTIBLE_MAP = {
	"heal":   Heal,
	"aoe":    Aoe,
	"revive": Revive,
}


# ─────────────────────────────────────────────────────────────────────────────
# CollectibleManager
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

		# _dropped-Set gelegentlich bereinigen um Speicher zu sparen.
		# Da Python object-ids wiederverwendet werden können, erst leeren
		# wenn keine Gegner mehr tot auf dem Feld liegen.
		dead_ids = {id(o) for o in opponents if not o.alive}
		if not dead_ids:
			self._dropped.clear()
