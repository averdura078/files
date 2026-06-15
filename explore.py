"""
explore.py - Explore Module.
Handles galaxy selection, mission choice, tool selection, outcomes, vaults.
"""
import random
import time
import display as d
from player import Player, save_game
from constants import (
    MISSIONS, BEST_TOOL, COMPATIBLE_TOOLS, BASE_SUCCESS_CHANCE,
    LEVEL_MULTIPLIER, WRONG_TOOL_MULTIPLIER, MISSION_YIELDS,
    STAR_ENERGY_BASE, DAMAGE_CHANCE_MW, DAMAGE_CHANCE_AND,
    ANDROMEDA_YIELD_BONUS, MAX_ENERGY,
    PLANET_CRASH_CHANCE, GALAXY_TRAVEL_COST,
    VAULT_RARE_MATERIALS, VAULT_RARE_CHEMICALS, VAULT_ENERGY_RANGE,
    EXPLORE_WIN_GALAXY, EXPLORE_WIN_TOOL, EXPLORE_WIN_LEVEL,
    EXPLORE_WIN_SCANNER_LEVEL, EXPLORE_WIN_CRASH_CHANCE,
    ITEM_DISPLAY_NAMES, ENG_UNLOCK_THRESHOLDS,
)

# Narrative flavour text per mission type
MISSION_FLAVOUR = {
    "Asteroid": [
        "You manoeuvre through a dense belt of spinning rock.",
        "The asteroid tumbles slowly, riddled with glinting ore veins.",
        "Your ship grazes the surface — sensors scrambling to catalogue the minerals.",
    ],
    "Nebula": [
        "The gas cloud glows violet and green as you drift through it.",
        "Your filters hum overtime, sifting through the chemical soup.",
        "Wisps of ionised gas curl around the hull like slow-motion smoke.",
    ],
    "Moon": [
        "The barren grey surface stretches to a razor-sharp horizon.",
        "Under low gravity, your tools move in strange, floaty arcs.",
        "Deep craters hide pockets of material compressed over billions of years.",
    ],
    "Planet": [
        "Atmospheric entry rattles the hull — then suddenly, silence and sky.",
        "Cloud layers part to reveal a surface that has never been touched.",
        "Your instruments buzz with readings. Something about this place feels different.",
    ],
    "Deep Space": [
        "Darkness and silence. Then — a blip on the scanner.",
        "The stars here are strangers. Nothing in the charts matches what you see.",
        "An ancient signal — too structured to be noise — pulses from somewhere nearby.",
    ],
    "Star": [
        "Heat warnings cascade across your console as you approach.",
        "The solar panels spin open, drinking in the furious light.",
        "At this distance, the star fills your entire viewport. Magnificent and terrifying.",
    ],
}

CRASH_FLAVOUR = [
    "A sudden systems failure — the landing gear buckles on impact.",
    "Warning klaxons blare. Something hit you on the way down.",
    "The probe cuts out mid-descent. You go in blind and come out battered.",
    "A debris strike at entry shreds a stabiliser. You land hard.",
]

DAMAGE_FLAVOUR = {
    "oxygen":      "A micro-fracture in the O₂ line — oxygen reserves are bleeding out.",
    "filter_health": "Exposure to compounds choked the filters. They need replacing.",
    "heat_shield": "A thermal bloom scorched the shield plating. It needs repair.",
    "glass":       "The glass warped under the gravitational stress. Hairline cracks spreading.",
    "frame":       "The frame took a hit — structural integrity has dropped.",
}


def run(player: Player) -> bool:
    """
    Main entry point for the Explore module.
    Returns True if a win condition was triggered, False otherwise.
    """
    while True:
        if player.is_dead:
            return False

        d.module_header("EXPLORE MODULE", f"Galaxy: {player.galaxy}", "🌌")
        d.mini_hud(player)

        choice = d.choose(
            ["Choose Galaxy", "Launch Mission"],
            title="Explore Menu"
        )
        if choice is None:
            return False   # back to main menu

        if choice == "Choose Galaxy":
            _choose_galaxy(player)
            save_game(player)

        elif choice == "Launch Mission":
            result = _launch_mission(player)
            save_game(player)
            if result == "win":
                return True
            if player.is_dead:
                return False


def _choose_galaxy(player: Player):
    d.section_header("Galaxy Selection", d.BRIGHT_MAGENTA)
    d.label("Current Galaxy", player.galaxy)
    print()
    d.info("Milky Way  — familiar and forgiving. Lower damage risk on failed missions (25%),")
    print(d.c("    but modest rewards. A good place to build up your resources.", d.BRIGHT_CYAN))
    print()
    d.info("Andromeda  — uncharted and dangerous. Failed missions carry a 50% chance of")
    print(d.c("    ship damage, but all yields — materials, chemicals, and XP — are", d.BRIGHT_CYAN))
    print(d.c("    50% higher. Life can only be discovered here.", d.BRIGHT_CYAN))
    print()

    choice = d.choose_no_menu(["Milky Way", "Andromeda", "Stay in current galaxy"],
                               title="Which galaxy?")

    if choice == "Stay in current galaxy":
        d.info(f"Staying in {player.galaxy}.")
        return

    if choice == player.galaxy:
        d.info(f"You're already in {player.galaxy}.")
        return

    # Different galaxy — pay 500 energy
    d.warn(f"Travelling to {choice} costs {GALAXY_TRAVEL_COST} energy.")
    d.label("Your energy", str(player.energy))
    if player.energy < GALAXY_TRAVEL_COST:
        d.error("Not enough energy to travel.")
        d.pause()
        return

    if not d.yes_no(f"Spend {GALAXY_TRAVEL_COST} energy to travel to {choice}?"):
        d.info("Travel cancelled.")
        return

    player.prev_galaxy = player.galaxy
    player.galaxy = choice
    if player.spend_energy(GALAXY_TRAVEL_COST):
        d.error("The jump drive drained your last reserves. The ship goes dark.")
        save_game(player)
        return

    d.narrative(
        f"Engaging jump drive... The stars blur and stretch. After what feels like "
        f"both an eternity and a heartbeat, you arrive in {player.galaxy}."
    )
    d.pause()
    save_game(player)


def _launch_mission(player: Player) -> str:
    """Run a full mission. Returns 'win', 'death', or 'ok'."""
    d.section_header("Launch Mission", d.BRIGHT_CYAN)

    # ── Step 1: Choose mission ──────────────────────────────────────────
    mission = d.choose(MISSIONS, title="Where do you want to explore?")
    if mission is None:
        return "ok"

    _print_mission_info(mission)

    # ── Step 2: Choose tool ─────────────────────────────────────────────
    tool_name = _choose_tool(player, mission)
    if tool_name is None:
        return "ok"

    # ── Step 3: Confirm and launch ──────────────────────────────────────
    best = BEST_TOOL.get(mission)
    tool_display = ITEM_DISPLAY_NAMES.get(tool_name, tool_name)
    best_display = ITEM_DISPLAY_NAMES.get(best, best) if best else "?"
    tool = player.get_tool(tool_name)
    level = tool["level"]

    print()
    d.label("Mission",    mission)
    d.label("Tool",       f"{tool_display}  (Level {level})")
    d.label("Best Tool",  best_display)
    is_best = (tool_name == best)
    if is_best:
        d.success("Optimal tool selected — maximum yield.")
    else:
        d.warn("Sub-optimal tool — yield will be reduced.")
    if mission == "Planet":
        d.warn(f"Note: Even a perfect landing carries a {int(PLANET_CRASH_CHANCE*100)}% failure risk.")

    if not d.yes_no("Launch mission?"):
        return "ok"

    # ── Step 4: Narrative and outcome ───────────────────────────────────
    d.narrative(random.choice(MISSION_FLAVOUR.get(mission, ["You head out into the unknown."])))

    time.sleep(1.0)   # brief pause before results appear

    # Check for special Planet crash
    planet_crash = False
    if mission == "Planet":
        if random.random() < PLANET_CRASH_CHANCE:
            planet_crash = True

    # Calculate success
    base_chance = BASE_SUCCESS_CHANCE.get(mission, 0.70)
    level_bonus = (level - 1) * 0.10   # +10% per level above 1
    compatible_penalty = 0.0 if is_best else (1 - WRONG_TOOL_MULTIPLIER) * base_chance
    success_chance = min(0.95, base_chance + level_bonus - compatible_penalty)

    success = random.random() < success_chance and not planet_crash

    # Use the tool (decrement durability)
    tool_survived = player.use_tool(tool_name)
    if not tool_survived:
        d.warn(f"Your {tool_display} broke from the strain of the mission! Repair it in Engineering Lab.")
        time.sleep(1.5)

    print()
    # ── Step 5: Apply outcome ───────────────────────────────────────────
    if success:
        return _handle_success(player, mission, tool_name, level, is_best)
    else:
        return _handle_failure(player, mission, planet_crash)


def _handle_success(player: Player, mission: str, tool_name: str,
                    level: int, is_best: bool) -> str:
    """Apply positive results. Returns 'win' or 'ok'."""
    d.success("Mission successful!")

    multiplier = LEVEL_MULTIPLIER[level]
    if not is_best:
        multiplier *= WRONG_TOOL_MULTIPLIER

    in_andromeda = player.galaxy == "Andromeda"
    galaxy_bonus = ANDROMEDA_YIELD_BONUS if in_andromeda else 0

    # ── Star: energy gain ───────────────────────────────────────────────
    if mission == "Star":
        energy_gained = int(STAR_ENERGY_BASE * multiplier) + (50 * galaxy_bonus)
        player.energy = min(MAX_ENERGY, player.energy + energy_gained)
        d.narrative(f"Your solar panels drank deep. +{energy_gained} energy replenished.")
        player.missions_completed += 1
        _progress_gain(player, mission, tool_name, galaxy_bonus)
        _yield_materials(player, mission, multiplier, galaxy_bonus, quiet=True)
        d.pause()
        return "ok"

    # ── Deep Space: vault check ─────────────────────────────────────────
    if mission == "Deep Space":
        _yield_materials(player, mission, multiplier, galaxy_bonus)
        _progress_gain(player, mission, tool_name, galaxy_bonus)
        if random.random() < player.vault_chance:
            _open_vault(player)
        else:
            d.dim_line("The void yielded only dust this time.")
        player.missions_completed += 1
        d.pause()
        return "ok"

    # ── Planet: check win condition ─────────────────────────────────────
    if mission == "Planet":
        _yield_materials(player, mission, multiplier, galaxy_bonus)
        _progress_gain(player, mission, tool_name, galaxy_bonus)
        player.missions_completed += 1

        # Check life discovery win
        if (player.galaxy == EXPLORE_WIN_GALAXY
                and player.tool_level(EXPLORE_WIN_TOOL) >= EXPLORE_WIN_LEVEL
                and player.tool_level("scanner") >= EXPLORE_WIN_SCANNER_LEVEL):
            if random.random() > EXPLORE_WIN_CRASH_CHANCE:
                return "win"

        d.narrative("Samples collected. The surface here is more complex than expected.")
        d.pause()
        return "ok"

    # ── All other missions ──────────────────────────────────────────────
    _yield_materials(player, mission, multiplier, galaxy_bonus)
    _progress_gain(player, mission, tool_name, galaxy_bonus)
    player.missions_completed += 1
    d.pause()
    return "ok"


def _handle_failure(player: Player, mission: str, planet_crash: bool) -> str:
    """Apply negative results. Returns 'death' or 'ok'."""
    if planet_crash:
        d.error(random.choice(CRASH_FLAVOUR))
    else:
        d.error("Mission failed.")

    # Ship damage chance depends on galaxy
    dmg_chance = DAMAGE_CHANCE_AND if player.galaxy == "Andromeda" else DAMAGE_CHANCE_MW

    # Planet crash always damages
    if planet_crash:
        dmg_chance = max(dmg_chance, 0.60)

    systems = _get_likely_damaged_systems(mission)
    damaged = False
    for system in systems:
        if random.random() < dmg_chance:
            damaged = True
            _apply_ship_damage(player, system)
            break  # one damage event per mission

    if not damaged:
        # Still a failed mission — narrative only
        d.narrative("You limped back to the ship. No materials, but no injuries either. This time.")

    player.missions_completed += 1

    if player.is_dead:
        d.pause("Press Enter to continue...")
        return "death"
    d.pause()
    return "ok"


def _choose_tool(player: Player, mission: str) -> str | None:
    """Show available tools, let player pick one. Returns tool_name or None."""
    d.section_header("Select Exploration Tool", d.BRIGHT_YELLOW)
    compatible = COMPATIBLE_TOOLS.get(mission, [])
    best = BEST_TOOL.get(mission)

    all_tools = player.all_explore_tools()
    available = []
    broken_list = []

    for tool_name, tool_data in all_tools.items():
        if tool_name in compatible:
            if tool_data["broken"]:
                broken_list.append(tool_name)
            else:
                available.append(tool_name)

    print()
    if available:
        print(d.c("  Available tools for this mission:", d.BRIGHT_WHITE))
        for t in available:
            td = all_tools[t]
            flag = d.c("★ BEST", d.BRIGHT_GREEN) if t == best else d.c("  OK", d.YELLOW)
            display = ITEM_DISPLAY_NAMES.get(t, t)
            print(
                f"    {flag}  {d.c(display, d.BRIGHT_WHITE)}"
                f"  Level {d.c(str(td['level']), d.BRIGHT_CYAN)}"
                f"  {d.c(str(td['uses_left']) + ' uses left', d.DIM + d.WHITE)}"
            )
    if broken_list:
        print()
        print(d.c("  Broken (need repair in Engineering Lab):", d.BRIGHT_RED))
        for t in broken_list:
            print(f"    {d.c('✗ ' + ITEM_DISPLAY_NAMES.get(t, t), d.BRIGHT_RED)}")

    # Tools that are compatible but not owned
    owned_all = list(player.all_explore_tools().keys())
    not_owned = [t for t in compatible if t not in owned_all]
    if not_owned:
        print()
        print(d.c("  Not yet built (can be engineered in Engineering Lab):", d.DIM + d.WHITE))
        for t in not_owned:
            print(f"    {d.c('○ ' + ITEM_DISPLAY_NAMES.get(t, t), d.DIM + d.WHITE)}")

    if not available:
        d.error("No working tools available for this mission! Repair tools in Engineering Lab.")
        d.pause()
        return None

    options = [ITEM_DISPLAY_NAMES.get(t, t) for t in available]
    choice_display = d.choose(options, title="Which tool will you use?")
    if choice_display is None:
        return None

    # Map display name back to tool key
    for t in available:
        if ITEM_DISPLAY_NAMES.get(t, t) == choice_display:
            return t
    return None


def _yield_materials(player: Player, mission: str, multiplier: float,
                     galaxy_bonus: int = 0, quiet: bool = False):
    """Add materials/chemicals to inventory based on mission and multiplier."""
    yields = MISSION_YIELDS.get(mission, [])
    gained = []
    for item, base_amt in yields:
        amt = max(1, int(base_amt * multiplier)) + galaxy_bonus
        player.add_item(item, amt)
        gained.append((item, amt))

    if not quiet and gained:
        print()
        print(d.c("  Materials collected:", d.BRIGHT_GREEN))
        for item, amt in gained:
            display = ITEM_DISPLAY_NAMES.get(item, item)
            print(f"    {d.c('+' + str(amt), d.BRIGHT_GREEN)} {d.c(display, d.WHITE)}")


def _progress_gain(player: Player, mission: str, tool_name: str, galaxy_bonus: int = 0):
    """Award engineering_progress or chemistry_progress based on mission type."""
    base_gain = 3

    # Binoculars and telescope always give both types of progress
    if tool_name in ("binoculars", "telescope"):
        gain = base_gain + galaxy_bonus
        player.engineering_progress += gain
        player.chemistry_progress += gain
        d.dim_line(f"+{gain} Engineering XP  +{gain} Chemistry XP (observation tool)")
        return

    # Mission-specific progress
    eng_missions = {"Asteroid", "Moon", "Star"}
    chem_missions = {"Nebula", "Planet"}

    tool_level = player.tool_level(tool_name)
    gain = base_gain + (tool_level - 1) + galaxy_bonus

    if mission in eng_missions:
        player.engineering_progress += gain
        d.dim_line(f"+{gain} Engineering XP")
    elif mission in chem_missions:
        player.chemistry_progress += gain
        d.dim_line(f"+{gain} Chemistry XP")
    elif mission == "Deep Space":
        player.engineering_progress += gain
        player.chemistry_progress += gain
        d.dim_line(f"+{gain} Engineering XP  +{gain} Chemistry XP")


def _get_likely_damaged_systems(mission: str) -> list:
    """Return list of ship systems most likely to be damaged in this mission."""
    mapping = {
        "Asteroid":   ["glass", "frame"],
        "Nebula":     ["filter_health", "oxygen"],
        "Moon":       ["frame", "glass"],
        "Planet":     ["heat_shield", "glass", "frame"],
        "Deep Space": ["oxygen"],
        "Star":       ["heat_shield", "glass"],
    }
    return mapping.get(mission, ["oxygen"])


def _apply_ship_damage(player: Player, system: str):
    """Set a ship system to 0 and show narrative."""
    if system == "oxygen"       and player.oxygen_level == 1:
        player.oxygen_level = 0
    elif system == "filter_health" and player.filter_health == 1:
        player.filter_health = 0
    elif system == "heat_shield"  and player.heat_shield == 1:
        player.heat_shield = 0
    elif system == "glass"        and player.glass_integrity == 1:
        player.glass_integrity = 0
    elif system == "frame"        and player.frame_integrity == 1:
        player.frame_integrity = 0
    else:
        d.warn("You escaped without structural damage — this time.")
        return

    flavour = DAMAGE_FLAVOUR.get(system, "Systems took damage.")
    d.error(flavour)
    d.warn(f"Ship health: {player.ship_health}/5 — head to Engineering Lab to repair.")


def _open_vault(player: Player):
    """Randomly generate vault contents and award them."""
    d.section_header("Supply Vault Discovered!", d.BRIGHT_MAGENTA)
    d.narrative(
        "Buried under centuries of cosmic debris, a vault sits undisturbed. "
        "Its seals break with a hiss. The previous civilisation left things behind."
    )

    player.vaults_found += 1
    # Increase future vault chance slightly
    player.vault_chance = min(0.40, player.vault_chance + 0.02)

    loot = []

    # Roll for rare materials (1-3 items)
    num_materials = random.randint(1, 3)
    for _ in range(num_materials):
        item = random.choice(VAULT_RARE_MATERIALS)
        amt  = random.randint(1, 2)
        player.add_item(item, amt)
        loot.append((item, amt))

    # Roll for rare chemicals (0-2 items)
    num_chems = random.randint(0, 2)
    for _ in range(num_chems):
        item = random.choice(VAULT_RARE_CHEMICALS)
        amt  = random.randint(1, 2)
        player.add_item(item, amt)
        loot.append((item, amt))

    # Energy bonus
    energy_bonus = random.randint(*VAULT_ENERGY_RANGE)
    player.energy = min(MAX_ENERGY, player.energy + energy_bonus)
    loot.append(("energy", energy_bonus))

    # Rare: pre-built tool
    if random.random() < 0.25:
        for tool_name, threshold in ENG_UNLOCK_THRESHOLDS.items():
            if tool_name not in player.engineered_tools:
                player.add_engineered_tool(tool_name)
                loot.append((tool_name, 1))
                d.success(f"The vault contained a working {ITEM_DISPLAY_NAMES.get(tool_name, tool_name)}!")
                break

    print(d.c("  Vault contents:", d.BRIGHT_MAGENTA))
    for item, amt in loot:
        display = ITEM_DISPLAY_NAMES.get(item, item)
        if item == "energy":
            print(f"    {d.c('+' + str(amt), d.BRIGHT_YELLOW)} {d.c('Energy', d.WHITE)}")
        else:
            print(f"    {d.c('+' + str(amt), d.BRIGHT_GREEN)} {d.c(display, d.WHITE)}")

    d.pause()


def _print_mission_info(mission: str):
    """Print a description of what can be found at each location."""
    INFO = {
        "Asteroid":  "Mine basic raw materials (iron ore, silicon) for the Engineering Lab.",
        "Nebula":    "Collect chemical compounds (hydrogen, oxygen, nitrogen) for the Chemistry Lab.",
        "Moon":      "Gather complex raw materials (titanium, graphene, crystals) for Engineering.",
        "Planet":    "Collect biological samples and organic chemicals. Also: where life might be found.",
        "Deep Space":"Search for ancient supply vaults. Rare, but the rewards are unlike anything else.",
        "Star":      "Harvest raw energy via solar panels. Essential for keeping your ship running.",
    }
    d.dim_line(INFO.get(mission, "Unknown territory."))
