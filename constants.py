"""
constants.py - All game-wide constants, costs, thresholds, and data tables.
"""

# ── Save file ─────────────────────────────────────────────────────────────────
SAVE_FILE = "save.json"

# ── Energy ────────────────────────────────────────────────────────────────────
STARTING_ENERGY = 1000
MAX_ENERGY = 2000
GALAXY_TRAVEL_COST = 500
NEW_EXPERIMENT_COST = 75
BUILD_TOOL_BASE_COST = 150      # engineering build cost (energy)
UPGRADE_TOOL_BASE_COST = 100    # engineering upgrade cost (energy)
BUILD_CHEM_TOOL_BASE_COST = 120 # chem tool build cost (energy)

# ── Ship health ───────────────────────────────────────────────────────────────
MAX_SHIP_HEALTH = 5
GAME_OVER_HEALTH = 3            # below 3 → instant death

# ── Tool durability ───────────────────────────────────────────────────────────
STARTER_TOOL_USES = 5
ENGINEERED_TOOL_USES = 3

# ── Progress thresholds (unlock new experiments / equipment) ──────────────────
CHEM_UNLOCK_THRESHOLDS = {
    "saline_solution":             0,    # unlocked after water_synthesis complete
    "organic_compound_synthesis":  15,
    "amino_acid_synthesis":        35,
    "protein_folding":             60,
    "cell_membrane_synthesis":     90,
    "replication_attempt":         130,
}

ENG_UNLOCK_THRESHOLDS = {
    "telescope": 10,   # engineering_progress needed to BUILD
    "scanner":   30,
    "probe":     60,
}

# ── Explore missions ──────────────────────────────────────────────────────────
MISSIONS = ["Asteroid", "Nebula", "Moon", "Planet", "Deep Space", "Star"]

# Best tool per mission (highest yield)
BEST_TOOL = {
    "Asteroid":    "net",
    "Nebula":      "gas_filter",
    "Moon":        "scanner",
    "Planet":      "probe",
    "Deep Space":  "telescope",
    "Star":        "solar_panel",
}

# Compatible tools per mission (give reduced yield)
COMPATIBLE_TOOLS = {
    "Asteroid":   ["net", "binoculars"],
    "Nebula":     ["gas_filter", "binoculars"],
    "Moon":       ["scanner", "net", "binoculars"],
    "Planet":     ["probe", "scanner", "binoculars"],
    "Deep Space": ["telescope", "binoculars"],
    "Star":       ["solar_panel", "scanner"],
}

# Milky Way ship-damage chance on mission failure (0.0 – 1.0)
DAMAGE_CHANCE_MW = 0.25
DAMAGE_CHANCE_AND = 0.50

# Andromeda yield bonus — flat +1 added to each material/chemical amount,
# +1 to XP gains, and +50 to Star energy, when the player is in Andromeda.
ANDROMEDA_YIELD_BONUS = 1

# Planet crash / systems-failure chance even on "success" (always present)
PLANET_CRASH_CHANCE = 0.20

# Base success chance per mission (with best tool at level 1)
BASE_SUCCESS_CHANCE = {
    "Asteroid":   0.80,
    "Nebula":     0.75,
    "Moon":       0.70,
    "Planet":     0.60,
    "Deep Space": 0.65,
    "Star":       0.75,
}

# Yield multiplier per tool level
LEVEL_MULTIPLIER = {1: 1.0, 2: 1.5, 3: 2.2}

# Wrong-tool yield penalty
WRONG_TOOL_MULTIPLIER = 0.5

# ── Materials & chemicals produced per mission ────────────────────────────────
# Each entry: list of (item, base_amount) tuples
MISSION_YIELDS = {
    "Asteroid": [
        ("iron_ore", 2), ("silicon", 1), ("glass_shard", 1),
    ],
    "Nebula": [
        ("hydrogen", 2), ("oxygen", 1), ("nitrogen", 1),
    ],
    "Moon": [
        ("titanium", 1), ("graphene", 1), ("crystal_compounds", 1),
    ],
    "Planet": [
        ("carbon_compounds", 2), ("lipids", 1), ("mineral_samples", 1),
    ],
    "Deep Space": [
        # Vault loot handled separately; base yield is small
        ("stellar_dust", 1),
    ],
    "Star": [
        # Energy handled separately; small material bonus
        ("plasma_extract", 1),
    ],
}

# Energy yielded from a Star mission (base, before level multiplier)
STAR_ENERGY_BASE = 200

# ── Engineering: build costs ──────────────────────────────────────────────────
# Each tool: {"energy": int, "materials": {item: amount}}
BUILD_COSTS = {
    "telescope": {
        "energy": 150,
        "materials": {"iron_ore": 2, "glass_shard": 1},
    },
    "scanner": {
        "energy": 200,
        "materials": {"iron_ore": 3, "silicon": 2, "crystal_compounds": 1},
    },
    "probe": {
        "energy": 250,
        "materials": {"titanium": 2, "iron_ore": 2, "silicon": 2, "graphene": 1},
    },
}

# Upgrade costs (per level, same for all tools for simplicity)
UPGRADE_COSTS = {
    2: {"energy": 100, "materials": {"iron_ore": 1, "silicon": 1}},
    3: {"energy": 175, "materials": {"titanium": 1, "graphene": 1, "crystal_compounds": 1}},
}

# Repair costs per tool (flat)
REPAIR_COSTS = {
    "binoculars":  {"energy": 0,  "materials": {"iron_ore": 1}},
    "net":         {"energy": 0,  "materials": {"iron_ore": 1}},
    "gas_filter":  {"energy": 0,  "materials": {"silicon": 1}},
    "solar_panel": {"energy": 0,  "materials": {"silicon": 1, "stellar_dust": 1}},
    "telescope":   {"energy": 50, "materials": {"iron_ore": 1, "glass_shard": 1}},
    "scanner":     {"energy": 75, "materials": {"silicon": 1, "crystal_compounds": 1}},
    "probe":       {"energy": 100,"materials": {"titanium": 1, "iron_ore": 1}},
}

# Repair of ship systems (materials only; filters are FREE)
SHIP_REPAIR_COSTS = {
    "oxygen":     {"iron_ore": 1, "plasma_extract": 1},
    "heat_shield":{"titanium": 1, "graphene": 1},
    "glass":      {"glass_shard": 2},
    "frame":      {"titanium": 2, "iron_ore": 1},
}

# ── Chemistry lab build costs ─────────────────────────────────────────────────
CHEM_TOOL_BUILD_COSTS = {
    "microscope": {
        "energy": 120,
        "materials": {"glass_shard": 2, "iron_ore": 1, "crystal_compounds": 1},
    },
    "incubator": {
        "energy": 150,
        "materials": {"iron_ore": 2, "silicon": 2, "plasma_extract": 1},
    },
    "centrifuge": {
        "energy": 180,
        "materials": {"titanium": 1, "iron_ore": 2, "graphene": 1},
    },
}

# ── Chemistry experiments ─────────────────────────────────────────────────────
# checkins: number of check-ins before completion (0 = instant)
EXPERIMENTS = {
    "water_synthesis": {
        "display_name": "Water Synthesis",
        "required_tools": ["beaker"],
        "required_ingredients": {"hydrogen": 2, "oxygen": 1},
        "checkins_required": 0,
        "energy_cost": NEW_EXPERIMENT_COST,
        "unlocks": ["saline_solution"],
        "output": {"water": 3},
        "chem_progress_gain": 5,
        "description": "Combine hydrogen and oxygen in a beaker to produce water. Simple, but foundational.",
    },
    "saline_solution": {
        "display_name": "Saline Solution",
        "required_tools": ["beaker"],
        "required_ingredients": {"water": 1, "mineral_samples": 1},
        "checkins_required": 0,
        "energy_cost": NEW_EXPERIMENT_COST,
        "unlocks": [],
        "output": {"saline_solution": 2},
        "chem_progress_gain": 5,
        "description": "Dissolve mineral samples in water. A key medium for future biological experiments.",
    },
    "organic_compound_synthesis": {
        "display_name": "Organic Compound Synthesis",
        "required_tools": ["beaker", "microscope"],
        "required_ingredients": {"water": 2, "carbon_compounds": 2},
        "checkins_required": 2,
        "energy_cost": NEW_EXPERIMENT_COST,
        "unlocks": [],
        "output": {"organic_compounds": 3},
        "chem_progress_gain": 10,
        "description": "Using a microscope, synthesize complex organic molecules from carbon and water.",
    },
    "amino_acid_synthesis": {
        "display_name": "Amino Acid Synthesis",
        "required_tools": ["microscope", "incubator"],
        "required_ingredients": {"organic_compounds": 2, "nitrogen": 2, "saline_solution": 1},
        "checkins_required": 3,
        "energy_cost": NEW_EXPERIMENT_COST,
        "unlocks": [],
        "output": {"amino_acids": 2},
        "chem_progress_gain": 15,
        "description": "Incubate organic compounds with nitrogen under careful conditions. The building blocks of proteins await.",
    },
    "protein_folding": {
        "display_name": "Protein Folding",
        "required_tools": ["incubator", "centrifuge"],
        "required_ingredients": {"amino_acids": 3, "water": 1},
        "checkins_required": 3,
        "energy_cost": NEW_EXPERIMENT_COST,
        "unlocks": [],
        "output": {"proteins": 2},
        "chem_progress_gain": 20,
        "description": "Guide amino acids to fold into functional proteins using centrifugal force and careful incubation.",
    },
    "cell_membrane_synthesis": {
        "display_name": "Cell Membrane Synthesis",
        "required_tools": ["centrifuge", "microscope"],
        "required_ingredients": {"lipids": 3, "water": 2, "proteins": 1},
        "checkins_required": 3,
        "energy_cost": NEW_EXPERIMENT_COST,
        "unlocks": [],
        "output": {"cell_membranes": 2},
        "chem_progress_gain": 25,
        "description": "Arrange lipid bilayers around a protein core. You are building the walls of life itself.",
    },
    "replication_attempt": {
        "display_name": "Replication Attempt",
        "required_tools": ["beaker", "microscope", "incubator", "centrifuge"],
        "required_ingredients": {
            "cell_membranes": 2,
            "amino_acids": 2,
            "proteins": 2,
            "organic_compounds": 1,
            "water": 2,
        },
        "checkins_required": 3,
        "energy_cost": NEW_EXPERIMENT_COST * 2,
        "unlocks": [],
        "output": {},  # WIN condition
        "chem_progress_gain": 50,
        "description": (
            "The final step. All four tools. All prior outputs. You attempt to coax "
            "self-replicating chemistry into existence. This is how life begins."
        ),
    },
}

# ── Vault loot tables ─────────────────────────────────────────────────────────
VAULT_RARE_MATERIALS = ["titanium", "graphene", "crystal_compounds", "glass_shard"]
VAULT_RARE_CHEMICALS = ["nitrogen", "lipids", "carbon_compounds", "plasma_extract"]
VAULT_ENERGY_RANGE   = (200, 500)

# ── Win condition (explore path) ──────────────────────────────────────────────
EXPLORE_WIN_GALAXY   = "Andromeda"
EXPLORE_WIN_TOOL     = "probe"
EXPLORE_WIN_LEVEL    = 3
EXPLORE_WIN_SCANNER_LEVEL = 3
EXPLORE_WIN_CRASH_CHANCE = 0.20   # 20% failure even with perfect setup

# ── Display names for items ───────────────────────────────────────────────────
ITEM_DISPLAY_NAMES = {
    "hydrogen":          "Hydrogen (H₂)",
    "oxygen":            "Oxygen (O₂)",
    "water":             "Water (H₂O)",
    "nitrogen":          "Nitrogen (N₂)",
    "carbon_compounds":  "Carbon Compounds",
    "lipids":            "Lipids",
    "mineral_samples":   "Mineral Samples",
    "saline_solution":   "Saline Solution",
    "organic_compounds": "Organic Compounds",
    "amino_acids":       "Amino Acids",
    "proteins":          "Proteins",
    "cell_membranes":    "Cell Membranes",
    "iron_ore":          "Iron Ore",
    "silicon":           "Silicon",
    "titanium":          "Titanium",
    "graphene":          "Graphene",
    "crystal_compounds": "Crystal Compounds",
    "glass_shard":       "Glass Shards",
    "stellar_dust":      "Stellar Dust",
    "plasma_extract":    "Plasma Extract",
    "binoculars":        "Binoculars",
    "net":               "Collection Net",
    "gas_filter":        "Gas Filter",
    "solar_panel":       "Solar Panel",
    "telescope":         "Telescope",
    "scanner":           "Scanner",
    "probe":             "Probe",
    "beaker":            "Beaker",
    "microscope":        "Microscope",
    "incubator":         "Incubator",
    "centrifuge":        "Centrifuge",
}
