"""
stats.py - Stats Module. Displays all player attributes and progress.
"""
import display as d
from player import Player, save_game
from constants import ITEM_DISPLAY_NAMES, STARTER_TOOL_USES, ENGINEERED_TOOL_USES


def run(player: Player):
    """Display full stats screen."""
    while True:
        d.module_header("STATS", f"Commander {player.name}", "📊")
        d.mini_hud(player)

        choice = d.choose(
            ["Full Stats", "Inventory", "Exploration Tools", "Experiment Log"],
            title="Stats Menu"
        )
        if choice is None:
            return

        if choice == "Full Stats":
            _full_stats(player)
        elif choice == "Inventory":
            _inventory(player)
        elif choice == "Exploration Tools":
            _tool_summary(player)
        elif choice == "Experiment Log":
            _experiment_log(player)


def _full_stats(player: Player):
    d.section_header("Full Stats", d.BRIGHT_CYAN)

    # Identity
    d.label("Commander",       player.name)
    d.label("Current Galaxy",  player.galaxy)
    d.label("Previous Galaxy", player.prev_galaxy)
    print()

    # Energy
    d.label("Energy", "")
    print(f"          {d.energy_bar(player.energy)}")
    print()

    # Ship Health
    d.label("Ship Hull", "")
    print(f"          {d.health_bar(player.ship_health)}")
    print()

    # Ship systems detail
    systems = [
        ("Oxygen",      player.oxygen_level),
        ("Filters",     player.filter_health),
        ("Heat Shield", player.heat_shield),
        ("Glass",       player.glass_integrity),
        ("Frame",       player.frame_integrity),
    ]
    print(d.c("  Ship Systems:", d.BRIGHT_WHITE))
    for name, val in systems:
        icon = d.c("■ ONLINE", d.BRIGHT_GREEN) if val else d.c("■ OFFLINE", d.BRIGHT_RED)
        print(f"    {name.ljust(14)}: {icon}")
    print()

    # Progress
    d.label("Engineering XP", str(player.engineering_progress), d.BRIGHT_CYAN)
    d.label("Chemistry XP",   str(player.chemistry_progress),   d.BRIGHT_GREEN)
    print()

    # Exploration
    d.label("Missions Completed", str(player.missions_completed))
    d.label("Vaults Found",       str(player.vaults_found))
    d.label("Vault Find Chance",  f"{int(player.vault_chance * 100)}%")
    print()

    # Win flags
    if player.life_created_chem:
        d.success("Life created in the Chemistry Lab! ★")
    if player.life_discovered_explore:
        d.success("Life discovered via Exploration! ★")

    # Score
    score = player.calculate_score()
    print()
    d.label("Current Score",  str(score),            d.BRIGHT_YELLOW)
    d.label("Personal Best",  str(player.high_score), d.BRIGHT_MAGENTA)

    d.pause()


def _inventory(player: Player):
    d.section_header("Inventory", d.BRIGHT_MAGENTA)

    if not player.inventory:
        d.dim_line("Your inventory is empty. Go explore!")
        d.pause()
        return

    # Separate into categories
    chemicals = ["hydrogen", "oxygen", "water", "nitrogen", "carbon_compounds",
                 "lipids", "mineral_samples", "saline_solution", "organic_compounds",
                 "amino_acids", "proteins", "cell_membranes", "stellar_dust", "plasma_extract"]
    materials = ["iron_ore", "silicon", "titanium", "graphene",
                 "crystal_compounds", "glass_shard"]

    def _print_category(title: str, items: list, color: str):
        found_any = False
        rows = []
        for item in items:
            amt = player.get_item_count(item)
            if amt > 0:
                rows.append((item, amt))
                found_any = True
        if rows:
            print(d.c(f"  {title}:", color))
            for item, amt in rows:
                print(f"    {d.c(str(amt).rjust(4), d.BRIGHT_GREEN)}  {ITEM_DISPLAY_NAMES.get(item, item)}")
            print()
        return found_any

    _print_category("Chemicals", chemicals, d.BRIGHT_CYAN)
    _print_category("Materials", materials, d.BRIGHT_YELLOW)

    # Anything else
    all_known = set(chemicals + materials)
    other = {k: v for k, v in player.inventory.items() if k not in all_known and v > 0}
    if other:
        print(d.c("  Other:", d.WHITE))
        for item, amt in other.items():
            print(f"    {d.c(str(amt).rjust(4), d.BRIGHT_GREEN)}  {ITEM_DISPLAY_NAMES.get(item, item)}")
        print()

    d.pause()


def _tool_summary(player: Player):
    d.section_header("Exploration Tools", d.BRIGHT_YELLOW)

    all_tools = player.all_explore_tools()
    if not all_tools:
        d.dim_line("No tools. That shouldn't be possible — check the starter kit.")
        d.pause()
        return

    print(d.c("  Tool                  Lvl  Uses  Status", d.DIM + d.WHITE))
    d.thin_divider()
    for name, tool in sorted(all_tools.items()):
        display = ITEM_DISPLAY_NAMES.get(name, name).ljust(22)
        lvl   = str(tool["level"]).center(4)
        uses  = str(tool["uses_left"]).center(5)
        status = d.tool_status_icon(tool["broken"])
        print(f"  {d.c(display, d.BRIGHT_WHITE)}{d.c(lvl, d.BRIGHT_CYAN)}{d.c(uses, d.YELLOW)}  {status}")

    print()
    d.dim_line("Tip: Repair broken tools in Engineering Lab.")
    print()

    # Chemistry tools
    print(d.c("  Chemistry Lab Tools:", d.BRIGHT_WHITE))
    for tool, owned in player.chemistry_tools.items():
        icon = d.c("✓", d.BRIGHT_GREEN) if owned else d.c("✗", d.DIM + d.WHITE)
        print(f"    {icon}  {ITEM_DISPLAY_NAMES.get(tool, tool)}")

    d.pause()


def _experiment_log(player: Player):
    d.section_header("Experiment Log", d.BRIGHT_GREEN)

    if player.completed_experiments:
        print(d.c("  Completed:", d.BRIGHT_GREEN))
        from constants import EXPERIMENTS
        for key in player.completed_experiments:
            exp = EXPERIMENTS.get(key)
            name = exp["display_name"] if exp else key
            print(f"    {d.c('✓', d.BRIGHT_GREEN)} {name}")
        print()
    else:
        d.dim_line("  No completed experiments yet.")

    if player.current_experiments:
        print(d.c("  In Progress:", d.BRIGHT_YELLOW))
        for e in player.current_experiments:
            checkins_left = e["checkins_required"] - e["checkins"]
            if checkins_left <= 0:
                status = d.c("READY", d.BRIGHT_GREEN)
            else:
                status = d.c(f"{checkins_left} check-in(s) left", d.YELLOW)
            print(f"    {d.c('►', d.BRIGHT_YELLOW)} {e['display_name']}  — {status}")
        print()

    from constants import EXPERIMENTS, CHEM_UNLOCK_THRESHOLDS
    chain = [
        "water_synthesis", "saline_solution", "organic_compound_synthesis",
        "amino_acid_synthesis", "protein_folding", "cell_membrane_synthesis",
        "replication_attempt"
    ]
    locked_remaining = [
        k for k in chain
        if k not in player.completed_experiments
        and not any(e["name"] == k for e in player.current_experiments)
    ]
    if locked_remaining:
        print(d.c("  Remaining:", d.DIM + d.WHITE))
        for key in locked_remaining:
            exp = EXPERIMENTS.get(key)
            if exp:
                threshold = CHEM_UNLOCK_THRESHOLDS.get(key, 0)
                if player.chemistry_progress >= threshold:
                    lock_str = d.c("Unlocked — ready to start", d.BRIGHT_CYAN)
                else:
                    needed = threshold - player.chemistry_progress
                    lock_str = d.c(f"Locked — need {needed} more Chemistry XP", d.DIM + d.WHITE)
                print(f"    {d.c('○', d.DIM + d.WHITE)} {exp['display_name']}  — {lock_str}")

    d.pause()
