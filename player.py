"""
player.py - Player class and all associated state management.
"""
import json
import os
from constants import (
    SAVE_FILE, STARTING_ENERGY, MAX_SHIP_HEALTH, GAME_OVER_HEALTH,
    STARTER_TOOL_USES, ENGINEERED_TOOL_USES
)


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
        self.vault_chance: float = 0.10   # 10% base chance in deep space

        # Missions completed (for stats)
        self.missions_completed: int = 0

        # Inventory: materials, chemicals, all tools
        # Tools stored as dict: tool_name -> {"level": int, "uses_left": int, "broken": bool}
        self.inventory: dict = {
            # Starting chemicals
            "hydrogen": 3,
            "oxygen": 3,
            # Starting materials (none to start beyond explore tools)
        }

        # Exploration tools
        self.explore_tools: dict = {
            "binoculars": {"level": 1, "uses_left": STARTER_TOOL_USES, "broken": False},
            "net":         {"level": 1, "uses_left": STARTER_TOOL_USES, "broken": False},
            "gas_filter":  {"level": 1, "uses_left": STARTER_TOOL_USES, "broken": False},
            "solar_panel": {"level": 1, "uses_left": STARTER_TOOL_USES, "broken": False},
        }

        # Engineered exploration tools (unlocked via engineering lab)
        # These start empty and are built in engineering lab
        self.engineered_tools: dict = {}
        # e.g. "telescope": {"level": 1, "uses_left": ENGINEERED_TOOL_USES, "broken": False}

        # Chemistry lab state
        self.chemistry_tools: dict = {
            "beaker": False,
            "microscope": False,
            "incubator": False,
            "centrifuge": False,
        }
        # beaker starts owned (implied by starting chem setup)
        self.chemistry_tools["beaker"] = True

        # Current experiments: list of dicts
        # {"name": str, "checkins": int, "required_checkins": int, "status": str, "yield_penalty": float}
        self.current_experiments: list = []

        # Completed experiments (names)
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
        """Returns combined starter + engineered tools."""
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
            return False   # False = broke this mission
        return True

    def repair_tool(self, tool_name: str):
        """Reset uses on a tool after paying repair cost."""
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
        p = cls(data["name"])
        p.energy = data["energy"]
        p.oxygen_level = data["oxygen_level"]
        p.filter_health = data["filter_health"]
        p.heat_shield = data["heat_shield"]
        p.glass_integrity = data["glass_integrity"]
        p.frame_integrity = data["frame_integrity"]
        p.galaxy = data["galaxy"]
        p.prev_galaxy = data["prev_galaxy"]
        p.engineering_progress = data["engineering_progress"]
        p.chemistry_progress = data["chemistry_progress"]
        p.vaults_found = data["vaults_found"]
        p.vault_chance = data["vault_chance"]
        p.missions_completed = data.get("missions_completed", 0)
        p.inventory = data["inventory"]
        p.explore_tools = data["explore_tools"]
        p.engineered_tools = data["engineered_tools"]
        p.chemistry_tools = data["chemistry_tools"]
        p.current_experiments = data["current_experiments"]
        p.completed_experiments = data["completed_experiments"]
        p.life_created_chem = data.get("life_created_chem", False)
        p.life_discovered_explore = data.get("life_discovered_explore", False)
        p.score = data.get("score", 0)
        p.high_score = data.get("high_score", 0)
        return p


def save_game(player: Player):
    with open(SAVE_FILE, "w") as f:
        json.dump(player.to_dict(), f, indent=2)


def load_game() -> Player | None:
    if not os.path.exists(SAVE_FILE):
        return None
    with open(SAVE_FILE, "r") as f:
        data = json.load(f)
    return Player.from_dict(data)


def save_exists() -> bool:
    return os.path.exists(SAVE_FILE)
