"""
player.py - Player class and all associated state management.
"""
import json
import os
import tempfile
from constants import (
    SAVE_FILE, STARTING_ENERGY, MAX_ENERGY, MAX_SHIP_HEALTH, GAME_OVER_HEALTH,
    STARTER_TOOL_USES, ENGINEERED_TOOL_USES
)

# Valid experiment keys — used to sanitise saves
VALID_EXPERIMENTS = {
    "water_synthesis", "saline_solution", "organic_compound_synthesis",
    "amino_acid_synthesis", "protein_folding", "cell_membrane_synthesis",
    "replication_attempt",
}

# Valid galaxy names
VALID_GALAXIES = {"Milky Way", "Andromeda"}


class Player:
    def __init__(self, name: str):
        self.name = name

        # Core stats
        self.energy: int = STARTING_ENERGY
        self.oxygen_level: int = 1        # 0 or 1
        self.filter_health: int = 1       # 0 or 1
        self.heat_shield: int = 1         # 0 or 1
        self.glass_integrity: int = 1     # 0 or 1
        self.frame_integrity: int = 1     # 0 or 1

        # Galaxy
        self.galaxy: str = "Milky Way"
        self.prev_galaxy: str = "Milky Way"

        # Progress
        self.engineering_progress: int = 0
        self.chemistry_progress: int = 0

        # Vaults
        self.vaults_found: int = 0
        self.vault_chance: float = 0.10

        # Missions completed (for stats)
        self.missions_completed: int = 0

        # Inventory
        self.inventory: dict = {
            "hydrogen": 3,
            "oxygen": 3,
        }

        # Exploration tools
        self.explore_tools: dict = {
            "binoculars": {"level": 1, "uses_left": STARTER_TOOL_USES, "broken": False},
            "net":         {"level": 1, "uses_left": STARTER_TOOL_USES, "broken": False},
            "gas_filter":  {"level": 1, "uses_left": STARTER_TOOL_USES, "broken": False},
            "solar_panel": {"level": 1, "uses_left": STARTER_TOOL_USES, "broken": False},
        }

        self.engineered_tools: dict = {}

        # Chemistry lab state
        self.chemistry_tools: dict = {
            "beaker": False,
            "microscope": False,
            "incubator": False,
            "centrifuge": False,
        }
        self.chemistry_tools["beaker"] = True

        self.current_experiments: list = []
        self.completed_experiments: list = []

        # Life discovered flags
        self.life_created_chem: bool = False
        self.life_discovered_explore: bool = False

        # Score / high score
        self.score: int = 0
        self.high_score: int = 0

    # ------------------------------------------------------------------ #
    #  Computed properties
    # ------------------------------------------------------------------ #

    @property
    def ship_health(self) -> int:
        return (self.oxygen_level + self.filter_health +
                self.heat_shield + self.glass_integrity + self.frame_integrity)

    @property
    def is_dead(self) -> bool:
        return self.ship_health < GAME_OVER_HEALTH or self.energy <= 0

    # ------------------------------------------------------------------ #
    #  Inventory helpers
    # ------------------------------------------------------------------ #

    def spend_energy(self, amount: int) -> bool:
        """Deduct energy. Returns True if player is now dead (energy <= 0)."""
        self.energy -= amount
        return self.energy <= 0

    def add_item(self, item: str, amount: int = 1):
        self.inventory[item] = self.inventory.get(item, 0) + amount

    def remove_item(self, item: str, amount: int = 1) -> bool:
        """Returns True if successful, False if not enough."""
        if self.inventory.get(item, 0) >= amount:
            self.inventory[item] -= amount
            if self.inventory[item] == 0:
                del self.inventory[item]
            return True
        return False

    def has_item(self, item: str, amount: int = 1) -> bool:
        return self.inventory.get(item, 0) >= amount

    def get_item_count(self, item: str) -> int:
        return self.inventory.get(item, 0)

    # ------------------------------------------------------------------ #
    #  Explore tool helpers
    # ------------------------------------------------------------------ #

    def all_explore_tools(self) -> dict:
        combined = {}
        combined.update(self.explore_tools)
        combined.update(self.engineered_tools)
        return combined

    def get_tool(self, tool_name: str) -> dict | None:
        if tool_name in self.explore_tools:
            return self.explore_tools[tool_name]
        if tool_name in self.engineered_tools:
            return self.engineered_tools[tool_name]
        return None

    def has_tool(self, tool_name: str) -> bool:
        t = self.get_tool(tool_name)
        return t is not None and not t["broken"]

    def use_tool(self, tool_name: str) -> bool:
        """Decrement uses. Mark broken if uses hit 0. Returns True if tool survived."""
        t = self.get_tool(tool_name)
        if t is None or t["broken"]:
            return False
        t["uses_left"] -= 1
        if t["uses_left"] <= 0:
            t["broken"] = True
            t["uses_left"] = 0
            return False
        return True

    def repair_tool(self, tool_name: str):
        """Reset uses on a tool after paying repair cost. Only works if broken."""
        t = self.get_tool(tool_name)
        if t is None:
            return
        t["broken"] = False
        is_engineered = tool_name in self.engineered_tools
        t["uses_left"] = ENGINEERED_TOOL_USES if is_engineered else STARTER_TOOL_USES

    def add_engineered_tool(self, tool_name: str):
        """Add a newly built engineered tool at level 1."""
        self.engineered_tools[tool_name] = {
            "level": 1,
            "uses_left": ENGINEERED_TOOL_USES,
            "broken": False,
        }

    def upgrade_tool(self, tool_name: str) -> bool:
        """Upgrade a tool by 1 level (max 3). Returns True if successful."""
        t = self.get_tool(tool_name)
        if t is None or t["level"] >= 3:
            return False
        t["level"] += 1
        return True

    def tool_level(self, tool_name: str) -> int:
        t = self.get_tool(tool_name)
        return t["level"] if t else 0

    # ------------------------------------------------------------------ #
    #  Chemistry tool helpers
    # ------------------------------------------------------------------ #

    def has_chem_tool(self, tool_name: str) -> bool:
        return self.chemistry_tools.get(tool_name, False)

    def owns_all_chem_tools(self, tools: list) -> bool:
        return all(self.chemistry_tools.get(t, False) for t in tools)

    # ------------------------------------------------------------------ #
    #  Score
    # ------------------------------------------------------------------ #

    def calculate_score(self) -> int:
        score = (
            self.chemistry_progress * 10 +
            self.engineering_progress * 10 +
            self.vaults_found * 50 +
            self.missions_completed * 5 +
            len(self.completed_experiments) * 25 +
            self.energy // 10
        )
        if self.life_created_chem or self.life_discovered_explore:
            score += 1000
        self.score = score
        return score

    # ------------------------------------------------------------------ #
    #  Respawn
    # ------------------------------------------------------------------ #

    def reset(self):
        """Reset all stats to new-game defaults, keeping name and high_score."""
        saved_name = self.name
        saved_high = self.high_score
        self.__init__(saved_name)
        self.high_score = saved_high

    # ------------------------------------------------------------------ #
    #  Save / Load
    # ------------------------------------------------------------------ #

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "energy": self.energy,
            "oxygen_level": self.oxygen_level,
            "filter_health": self.filter_health,
            "heat_shield": self.heat_shield,
            "glass_integrity": self.glass_integrity,
            "frame_integrity": self.frame_integrity,
            "galaxy": self.galaxy,
            "prev_galaxy": self.prev_galaxy,
            "engineering_progress": self.engineering_progress,
            "chemistry_progress": self.chemistry_progress,
            "vaults_found": self.vaults_found,
            "vault_chance": self.vault_chance,
            "missions_completed": self.missions_completed,
            "inventory": self.inventory,
            "explore_tools": self.explore_tools,
            "engineered_tools": self.engineered_tools,
            "chemistry_tools": self.chemistry_tools,
            "current_experiments": self.current_experiments,
            "completed_experiments": self.completed_experiments,
            "life_created_chem": self.life_created_chem,
            "life_discovered_explore": self.life_discovered_explore,
            "score": self.score,
            "high_score": self.high_score,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Player":
        """
        Load a player from a save dict. Validates and clamps all values
        so a manually edited or corrupted save cannot crash the game.
        """
        # Sanitise name
        raw_name = str(data.get("name", "Commander"))
        name = "".join(ch for ch in raw_name if ch.isprintable()).strip()[:20] or "Commander"

        p = cls(name)

        # Clamp energy to valid range
        p.energy = max(0, min(MAX_ENERGY, int(data.get("energy", STARTING_ENERGY))))

        # Ship systems — must be 0 or 1
        def _clamp_system(val) -> int:
            return 1 if int(val) > 0 else 0

        p.oxygen_level    = _clamp_system(data.get("oxygen_level", 1))
        p.filter_health   = _clamp_system(data.get("filter_health", 1))
        p.heat_shield     = _clamp_system(data.get("heat_shield", 1))
        p.glass_integrity = _clamp_system(data.get("glass_integrity", 1))
        p.frame_integrity = _clamp_system(data.get("frame_integrity", 1))

        # Galaxy — must be a known value
        p.galaxy      = data.get("galaxy", "Milky Way") if data.get("galaxy") in VALID_GALAXIES else "Milky Way"
        p.prev_galaxy = data.get("prev_galaxy", "Milky Way") if data.get("prev_galaxy") in VALID_GALAXIES else "Milky Way"

        # Progress — non-negative ints
        p.engineering_progress = max(0, int(data.get("engineering_progress", 0)))
        p.chemistry_progress   = max(0, int(data.get("chemistry_progress", 0)))

        # Vaults
        p.vaults_found = max(0, int(data.get("vaults_found", 0)))
        p.vault_chance = max(0.0, min(1.0, float(data.get("vault_chance", 0.10))))

        p.missions_completed = max(0, int(data.get("missions_completed", 0)))

        # Inventory — keys and values must be strings/ints
        raw_inv = data.get("inventory", {})
        p.inventory = {str(k): max(0, int(v)) for k, v in raw_inv.items()
                       if isinstance(k, str) and str(v).lstrip("-").isdigit()}

        # Exploration tools — validate structure of each tool entry
        def _sanitise_tool(t) -> dict:
            if not isinstance(t, dict):
                return {"level": 1, "uses_left": STARTER_TOOL_USES, "broken": False}
            return {
                "level":     max(1, min(3, int(t.get("level", 1)))),
                "uses_left": max(0, int(t.get("uses_left", STARTER_TOOL_USES))),
                "broken":    bool(t.get("broken", False)),
            }

        raw_et = data.get("explore_tools", {})
        p.explore_tools = {k: _sanitise_tool(v) for k, v in raw_et.items()
                           if isinstance(k, str)}
        # Ensure starter tools always exist
        for tool in ("binoculars", "net", "gas_filter", "solar_panel"):
            if tool not in p.explore_tools:
                p.explore_tools[tool] = {"level": 1, "uses_left": STARTER_TOOL_USES, "broken": False}

        raw_eng = data.get("engineered_tools", {})
        p.engineered_tools = {k: _sanitise_tool(v) for k, v in raw_eng.items()
                               if isinstance(k, str)}

        # Chemistry tools — must be bool
        raw_ct = data.get("chemistry_tools", {})
        p.chemistry_tools = {
            "beaker":     bool(raw_ct.get("beaker", True)),
            "microscope": bool(raw_ct.get("microscope", False)),
            "incubator":  bool(raw_ct.get("incubator", False)),
            "centrifuge": bool(raw_ct.get("centrifuge", False)),
        }

        # Experiments — strip any unknown experiment keys
        raw_curr = data.get("current_experiments", [])
        p.current_experiments = [e for e in raw_curr
                                  if isinstance(e, dict) and e.get("name") in VALID_EXPERIMENTS]
        raw_comp = data.get("completed_experiments", [])
        p.completed_experiments = [e for e in raw_comp
                                    if isinstance(e, str) and e in VALID_EXPERIMENTS]

        p.life_created_chem     = bool(data.get("life_created_chem", False))
        p.life_discovered_explore = bool(data.get("life_discovered_explore", False))

        p.score      = max(0, int(data.get("score", 0)))
        p.high_score = max(0, int(data.get("high_score", 0)))
        return p


def save_game(player: Player):
    """
    Atomically write save data: write to a temp file first, then rename.
    This prevents corruption if the process is killed mid-write, and
    prevents two simultaneous instances from interleaving their writes.
    """
    try:
        dir_name = os.path.dirname(os.path.abspath(SAVE_FILE)) or "."
        with tempfile.NamedTemporaryFile(
            mode="w", dir=dir_name, suffix=".tmp", delete=False
        ) as tf:
            json.dump(player.to_dict(), tf, indent=2)
            tmp_path = tf.name
        os.replace(tmp_path, SAVE_FILE)
    except Exception:
        # Never crash the game because of a save failure
        pass


def load_game() -> Player | None:
    """Load and validate save file. Returns None on any error."""
    if not os.path.exists(SAVE_FILE):
        return None
    try:
        with open(SAVE_FILE, "r") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return None
        return Player.from_dict(data)
    except Exception:
        return None


def save_exists() -> bool:
    return os.path.exists(SAVE_FILE)
