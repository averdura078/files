"""
engineering.py - Engineering Lab Module.
Handles ship repair, equipment build/upgrade/repair.
"""
import display as d
from player import Player, save_game
from constants import (
    BUILD_COSTS, UPGRADE_COSTS, REPAIR_COSTS, SHIP_REPAIR_COSTS,
    ENG_UNLOCK_THRESHOLDS, ENGINEERED_TOOL_USES, ITEM_DISPLAY_NAMES,
    STARTER_TOOL_USES,
)


def run(player: Player):
    """Main entry point for Engineering Lab."""
    while True:
        if player.is_dead:
            return

        d.module_header("ENGINEERING LAB", "Build. Upgrade. Repair.", "🔧")
        d.mini_hud(player)

        choice = d.choose(
            ["Repair Ship", "Build Equipment", "Upgrade Equipment", "Repair Equipment"],
            title="Engineering Lab Menu"
        )
        if choice is None:
            return   # back to main menu

        if choice == "Repair Ship":
            _repair_ship(player)
        elif choice == "Build Equipment":
            _build_equipment(player)
        elif choice == "Upgrade Equipment":
            _upgrade_equipment(player)
        elif choice == "Repair Equipment":
            _repair_equipment(player)

        save_game(player)
        if player.is_dead:
            return


# ── Ship Repair ────────────────────────────────────────────────────────────────

def _repair_ship(player: Player):
    d.section_header("Repair Ship", d.BRIGHT_CYAN)
    _display_ship_status(player)

    systems = {
        "Oxygen Levels":   ("oxygen",     player.oxygen_level),
        "Filters":         ("filter_health", player.filter_health),
        "Heat Shield":     ("heat_shield", player.heat_shield),
        "Glass Integrity": ("glass",       player.glass_integrity),
        "Frame Integrity": ("frame",       player.frame_integrity),
    }

    broken = {name: key for name, (key, val) in systems.items() if val == 0}

    if not broken:
        d.success("All ship systems are operational. Nothing to repair.")
        d.pause()
        return

    print()
    print(d.c("  Damaged systems:", d.BRIGHT_RED))
    for name, key in broken.items():
        cost = SHIP_REPAIR_COSTS.get(key, {})
        print(f"\n    {d.c('✗ ' + name, d.BRIGHT_RED)}")
        if key == "filter_health":
            print(f"      {d.c('FREE to replace', d.BRIGHT_GREEN)}")
        else:
            print(f"      Repair cost:")
            for mat, amt in cost.items():
                have = player.get_item_count(mat)
                ok = have >= amt
                icon = d.c("✓", d.BRIGHT_GREEN) if ok else d.c("✗", d.BRIGHT_RED)
                print(f"        {icon} {ITEM_DISPLAY_NAMES.get(mat, mat)}: need {amt}, have {have}")

    choice = d.choose(list(broken.keys()), title="Which system to repair?")
    if choice is None:
        return

    system_key = broken[choice]
    _perform_ship_repair(player, system_key, choice)
    save_game(player)


def _perform_ship_repair(player: Player, system_key: str, display_name: str):
    # Filters are free
    if system_key == "filter_health":
        player.filter_health = 1
        d.success("Filters replaced. Your ship can breathe again.")
        d.narrative("The old filter slid out with a wheeze. The new one clicked into place satisfyingly.")
        d.pause()
        return

    cost = SHIP_REPAIR_COSTS.get(system_key, {})
    can_repair = True
    for mat, amt in cost.items():
        if not player.has_item(mat, amt):
            d.error(f"Missing {ITEM_DISPLAY_NAMES.get(mat, mat)} (need {amt}, have {player.get_item_count(mat)}).")
            can_repair = False

    if not can_repair:
        d.info("Go explore to gather the missing materials.")
        d.pause()
        return

    if not d.yes_no(f"Repair {display_name}?"):
        return

    # Deduct materials
    for mat, amt in cost.items():
        player.remove_item(mat, amt)

    # Apply repair
    if system_key == "oxygen":
        player.oxygen_level = 1
        d.narrative("You patch the O₂ line and run a pressure test. The hiss stops. You can breathe.")
    elif system_key == "heat_shield":
        player.heat_shield = 1
        d.narrative("New shielding tiles bonded to the hull. The thermal sensors go green.")
    elif system_key == "glass":
        player.glass_integrity = 1
        d.narrative("The cracks are sealed with polymer resin. The viewport holds again.")
    elif system_key == "frame":
        player.frame_integrity = 1
        d.narrative("Structural braces welded back into position. The ship stops groaning.")

    d.success(f"{display_name} repaired! Ship health: {player.ship_health}/5")
    d.pause()


def _display_ship_status(player: Player):
    """Print current ship system status."""
    systems = [
        ("Oxygen",      player.oxygen_level),
        ("Filters",     player.filter_health),
        ("Heat Shield", player.heat_shield),
        ("Glass",       player.glass_integrity),
        ("Frame",       player.frame_integrity),
    ]
    print()
    print(d.c("  Ship System Status:", d.BRIGHT_WHITE))
    for name, val in systems:
        if val == 1:
            icon = d.c("■ ONLINE", d.BRIGHT_GREEN)
        else:
            icon = d.c("■ OFFLINE", d.BRIGHT_RED)
        print(f"    {name.ljust(14)}: {icon}")
    print()
    print(f"  Overall hull: {d.health_bar(player.ship_health)}")
    print()


# ── Build Equipment ────────────────────────────────────────────────────────────

def _build_equipment(player: Player):
    d.section_header("Build Equipment", d.BRIGHT_YELLOW)
    d.label("Engineering XP", str(player.engineering_progress))
    print()

    buildable = []
    locked = []

    for tool_name, threshold in ENG_UNLOCK_THRESHOLDS.items():
        if tool_name in player.engineered_tools:
            continue   # already built
        if player.engineering_progress >= threshold:
            buildable.append(tool_name)
        else:
            locked.append((tool_name, threshold))

    if locked:
        print(d.c("  Locked (need more Engineering XP):", d.DIM + d.WHITE))
        for tool, threshold in locked:
            needed = threshold - player.engineering_progress
            print(f"    {d.c('○ ' + ITEM_DISPLAY_NAMES.get(tool, tool), d.DIM + d.WHITE)}"
                  f"  — {needed} more Eng XP needed")
        print()

    if not buildable:
        if not locked:
            d.success("All available equipment has been built!")
        else:
            d.warn("No equipment available to build yet. Keep exploring to raise Engineering XP.")
        d.pause()
        return

    print(d.c("  Available to build:", d.BRIGHT_GREEN))
    for tool in buildable:
        cost = BUILD_COSTS[tool]
        print(f"\n  {d.c(ITEM_DISPLAY_NAMES.get(tool, tool), d.BRIGHT_CYAN)}")
        print(f"    Energy: {d.c(str(cost['energy']) + ' E', d.BRIGHT_YELLOW)}")
        print(f"    Materials:")
        for mat, amt in cost["materials"].items():
            have = player.get_item_count(mat)
            ok = have >= amt
            icon = d.c("✓", d.BRIGHT_GREEN) if ok else d.c("✗", d.BRIGHT_RED)
            print(f"      {icon} {ITEM_DISPLAY_NAMES.get(mat, mat)}: need {amt}, have {have}")

    options = [ITEM_DISPLAY_NAMES.get(t, t) for t in buildable]
    choice = d.choose(options, title="What would you like to build?")
    if choice is None:
        return

    tool_key = next((t for t in buildable if ITEM_DISPLAY_NAMES.get(t, t) == choice), None)
    if tool_key is None:
        return

    _perform_build(player, tool_key)
    save_game(player)


def _perform_build(player: Player, tool_key: str):
    cost = BUILD_COSTS[tool_key]
    display = ITEM_DISPLAY_NAMES.get(tool_key, tool_key)

    can_build = True
    if player.energy < cost["energy"]:
        d.error(f"Not enough energy. Need {cost['energy']}, have {player.energy}.")
        can_build = False

    for mat, amt in cost["materials"].items():
        if not player.has_item(mat, amt):
            d.error(f"Missing {ITEM_DISPLAY_NAMES.get(mat, mat)} (need {amt}).")
            can_build = False

    if not can_build:
        d.pause()
        return

    if not d.yes_no(f"Build {display}?"):
        return

    if player.spend_energy(cost["energy"]):
        d.error("Building the equipment drained your last reserves. The ship goes dark.")
        save_game(player)
        return
    for mat, amt in cost["materials"].items():
        player.remove_item(mat, amt)

    player.add_engineered_tool(tool_key)

    d.success(f"{display} built! Added to your exploration tools.")
    _tool_unlock_narrative(tool_key)
    d.pause()


def _tool_unlock_narrative(tool_key: str):
    narratives = {
        "telescope": (
            "The lenses click into alignment. Through the eyepiece, deep space snaps "
            "into impossible clarity. Signals that were noise are now data."
        ),
        "scanner": (
            "The scanner array powers up with a rising hum. It reads materials, "
            "atmospheres, biologics — a second pair of eyes that never blink."
        ),
        "probe": (
            "The probe sits in the launch bay, compact and ready. For the first time, "
            "you can land somewhere other than the ship's orbit. New worlds await."
        ),
    }
    d.narrative(narratives.get(tool_key, "New equipment ready for deployment."))


# ── Upgrade Equipment ──────────────────────────────────────────────────────────

def _upgrade_equipment(player: Player):
    d.section_header("Upgrade Equipment", d.BRIGHT_MAGENTA)
    d.dim_line("Higher level tools yield better results and higher success rates.")
    print()

    all_tools = player.all_explore_tools()
    upgradeable = {k: v for k, v in all_tools.items() if v["level"] < 3}

    if not upgradeable:
        d.success("All tools are at maximum level (Level 3). You're running peak kit.")
        d.pause()
        return

    print(d.c("  Upgradeable tools:", d.BRIGHT_WHITE))
    for name, tool in upgradeable.items():
        current_lvl = tool["level"]
        next_lvl = current_lvl + 1
        cost = UPGRADE_COSTS[next_lvl]
        display = ITEM_DISPLAY_NAMES.get(name, name)

        print(f"\n  {d.c(display, d.BRIGHT_CYAN)} — Level {current_lvl} → {d.c(str(next_lvl), d.BRIGHT_GREEN)}")
        print(f"    Energy: {d.c(str(cost['energy']) + ' E', d.BRIGHT_YELLOW)}")
        print(f"    Materials:")
        for mat, amt in cost["materials"].items():
            have = player.get_item_count(mat)
            ok = have >= amt
            icon = d.c("✓", d.BRIGHT_GREEN) if ok else d.c("✗", d.BRIGHT_RED)
            print(f"      {icon} {ITEM_DISPLAY_NAMES.get(mat, mat)}: need {amt}, have {have}")

    options = [ITEM_DISPLAY_NAMES.get(t, t) for t in upgradeable.keys()]
    choice = d.choose(options, title="Which tool to upgrade?")
    if choice is None:
        return

    tool_key = next((t for t in upgradeable if ITEM_DISPLAY_NAMES.get(t, t) == choice), None)
    if tool_key is None:
        return

    _perform_upgrade(player, tool_key)
    save_game(player)


def _perform_upgrade(player: Player, tool_key: str):
    tool = player.get_tool(tool_key)
    if tool is None:
        return

    current_lvl = tool["level"]
    next_lvl = current_lvl + 1
    cost = UPGRADE_COSTS[next_lvl]
    display = ITEM_DISPLAY_NAMES.get(tool_key, tool_key)

    can_upgrade = True
    if player.energy < cost["energy"]:
        d.error(f"Not enough energy. Need {cost['energy']}, have {player.energy}.")
        can_upgrade = False

    for mat, amt in cost["materials"].items():
        if not player.has_item(mat, amt):
            d.error(f"Missing {ITEM_DISPLAY_NAMES.get(mat, mat)} (need {amt}).")
            can_upgrade = False

    if not can_upgrade:
        d.pause()
        return

    if not d.yes_no(f"Upgrade {display} to Level {next_lvl}?"):
        return

    if player.spend_energy(cost["energy"]):
        d.error("The upgrade drained your last reserves. The ship goes dark.")
        save_game(player)
        return
    for mat, amt in cost["materials"].items():
        player.remove_item(mat, amt)

    player.upgrade_tool(tool_key)
    d.success(f"{display} upgraded to Level {next_lvl}!")

    upgrade_bonuses = {
        2: "Yield increased by 50%. Success rate improved.",
        3: "Maximum yield unlocked (×2.2). This tool is now operating at peak capacity.",
    }
    d.info(upgrade_bonuses.get(next_lvl, "Performance improved."))
    d.pause()


# ── Repair Equipment ───────────────────────────────────────────────────────────

def _repair_equipment(player: Player):
    d.section_header("Repair Exploration Tools", d.BRIGHT_RED)

    all_tools = player.all_explore_tools()
    broken = {k: v for k, v in all_tools.items() if v["broken"]}
    low_uses = {k: v for k, v in all_tools.items() if not v["broken"] and v["uses_left"] <= 1}

    if not broken and not low_uses:
        d.success("All exploration tools are in good condition.")
        d.pause()
        return

    if broken:
        print(d.c("  Broken tools:", d.BRIGHT_RED))
        for name, tool in broken.items():
            display = ITEM_DISPLAY_NAMES.get(name, name)
            cost = REPAIR_COSTS.get(name, {})
            print(f"\n  {d.c('✗ ' + display, d.BRIGHT_RED)}  (Level {tool['level']})")
            energy_cost = cost.get("energy", 0)
            mats = cost.get("materials", {})
            if energy_cost:
                print(f"    Energy: {d.c(str(energy_cost) + ' E', d.BRIGHT_YELLOW)}")
            else:
                print(f"    Energy: {d.c('Free', d.BRIGHT_GREEN)}")
            if mats:
                print(f"    Materials:")
                for mat, amt in mats.items():
                    have = player.get_item_count(mat)
                    ok = have >= amt
                    icon = d.c("✓", d.BRIGHT_GREEN) if ok else d.c("✗", d.BRIGHT_RED)
                    print(f"      {icon} {ITEM_DISPLAY_NAMES.get(mat, mat)}: need {amt}, have {have}")

    if low_uses:
        print()
        print(d.c("  Tools almost worn out:", d.BRIGHT_YELLOW))
        for name, tool in low_uses.items():
            display = ITEM_DISPLAY_NAMES.get(name, name)
            print(f"    {d.c('⚠ ' + display, d.BRIGHT_YELLOW)} — {tool['uses_left']} use(s) remaining")

    options = [ITEM_DISPLAY_NAMES.get(t, t) for t in broken.keys()]
    if not options:
        d.info("No broken tools to repair right now.")
        d.pause()
        return

    choice = d.choose(options, title="Which tool to repair?")
    if choice is None:
        return

    tool_key = next((t for t in broken if ITEM_DISPLAY_NAMES.get(t, t) == choice), None)
    if tool_key is None:
        return

    _perform_tool_repair(player, tool_key)
    save_game(player)


def _perform_tool_repair(player: Player, tool_key: str):
    cost = REPAIR_COSTS.get(tool_key, {})
    display = ITEM_DISPLAY_NAMES.get(tool_key, tool_key)
    energy_cost = cost.get("energy", 0)
    mats = cost.get("materials", {})

    can_repair = True
    if player.energy < energy_cost:
        d.error(f"Not enough energy (need {energy_cost}, have {player.energy}).")
        can_repair = False

    for mat, amt in mats.items():
        if not player.has_item(mat, amt):
            d.error(f"Missing {ITEM_DISPLAY_NAMES.get(mat, mat)} (need {amt}).")
            can_repair = False

    if not can_repair:
        d.info("Go explore to gather missing materials.")
        d.pause()
        return

    if not d.yes_no(f"Repair {display}?"):
        return

    if energy_cost:
        if player.spend_energy(energy_cost):
            d.error("The repair drained your last reserves. The ship goes dark.")
            save_game(player)
            return
    for mat, amt in mats.items():
        player.remove_item(mat, amt)

    player.repair_tool(tool_key)
    is_engineered = tool_key in player.engineered_tools
    uses = ENGINEERED_TOOL_USES if is_engineered else STARTER_TOOL_USES

    d.success(f"{display} repaired! {uses} uses restored.")
    d.narrative(f"Piece by piece, the {display} comes back together. "
                f"Good as new — or close enough.")
    d.pause()
