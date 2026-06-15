"""
main_menu.py - Main Menu module. Entry point after startup.
"""
import display as d
from player import Player, save_game
from constants import ITEM_DISPLAY_NAMES, EXPLORE_WIN_GALAXY


def run(player: Player) -> str:
    """
    Show the main menu. Returns a string indicating where to go:
    'explore', 'chemistry', 'engineering', 'stats', 'quit'
    """
    while True:
        if player.is_dead:
            return "dead"

        d.module_header("MAIN MENU", f"Commander {player.name}", "🚀")

        # Contextual guide tip — always relevant to current progress
        _show_guide(player)

        d.mini_hud(player)

        # Mission statement — always visible, sized to match the module header (58 cols)
        _W = 52
        print(d.c("  ┌" + "─" * 54 + "┐", d.BRIGHT_MAGENTA))
        mission_lines = [
            "MISSION  Explore the universe, build your",
            "         lab, and answer the question that",
            "         has haunted humanity for ages.",
            "         Discover life in Andromeda — or",
            "         synthesise it in the Chemistry Lab.",
        ]
        for line in mission_lines:
            print(
                d.c("  │ ", d.BRIGHT_MAGENTA) +
                d.c(line.ljust(_W), d.WHITE) +
                d.c(" │", d.BRIGHT_MAGENTA)
            )
        print(d.c("  └" + "─" * 54 + "┘", d.BRIGHT_MAGENTA))
        print()

        # Check for any warnings
        _show_warnings(player)

        choice = d.choose(
            ["Explore", "Chemistry Lab", "Engineering Lab", "View Stats", "Save & Quit"],
            title="What would you like to do?"
        )

        if choice is None:
            continue
        elif choice == "Explore":
            return "explore"
        elif choice == "Chemistry Lab":
            return "chemistry"
        elif choice == "Engineering Lab":
            return "engineering"
        elif choice == "View Stats":
            return "stats"
        elif choice == "Save & Quit":
            save_game(player)
            d.success("Game saved. See you out there, Commander.")
            d.pause()
            return "quit"


def _show_guide(player: Player):
    """
    Print a single contextual tip in a blue box sized to match the module
    header (58 chars wide). First line: 'GUIDE  ' prefix (7 chars) + 45 chars
    of text. Continuation lines: 52 chars of text.
    """
    tip = _get_tip(player)
    if not tip:
        return
    print(d.c("  ┌" + "─" * 54 + "┐", d.BRIGHT_BLUE))
    first = tip[0]
    print(
        d.c("  │ ", d.BRIGHT_BLUE) +
        d.c("GUIDE  ", d.BOLD + d.BRIGHT_BLUE) +
        d.c(first.ljust(45), d.BRIGHT_WHITE) +
        d.c(" │", d.BRIGHT_BLUE)
    )
    for line in tip[1:]:
        print(
            d.c("  │ ", d.BRIGHT_BLUE) +
            d.c(line.ljust(52), d.BRIGHT_WHITE) +
            d.c(" │", d.BRIGHT_BLUE)
        )
    print(d.c("  └" + "─" * 54 + "┘", d.BRIGHT_BLUE))
    print()


def _get_tip(player: Player) -> list[str] | None:
    """
    Return a list of lines for the most relevant tip, or None.
    First line max 45 chars. Continuation lines max 52 chars.
    """
    all_tools = player.all_explore_tools()

    # ── Critical: energy ────────────────────────────────────────────────
    if player.energy < 300:
        return ["Energy low — go to Explore and run a Star",
                "mission with your Solar Panel right away."]

    # ── Critical: ship damage ────────────────────────────────────────────
    damaged = []
    if player.oxygen_level == 0:    damaged.append("Oxygen")
    if player.filter_health == 0:   damaged.append("Filters")
    if player.heat_shield == 0:     damaged.append("Heat Shield")
    if player.glass_integrity == 0: damaged.append("Glass")
    if player.frame_integrity == 0: damaged.append("Frame")
    if damaged:
        sys_str = ", ".join(damaged)
        return [f"System offline: {sys_str}.",
                "Repair it in Engineering Lab before next mission."]

    # ── Broken tools ─────────────────────────────────────────────────────
    broken = [n for n, t in all_tools.items() if t["broken"]]
    if broken:
        if len(broken) == 1:
            return ["A tool is broken — go to Engineering Lab",
                    "and repair it before your next mission."]
        else:
            return ["Some tools are broken — go to Engineering Lab",
                    "and repair them before your next mission."]

    # ── Experiment ready for check-in ────────────────────────────────────
    ready = [e for e in player.current_experiments
             if (e["checkins_required"] - e["checkins"]) <= 0
             or e.get("status") == "ready"]
    if ready:
        return [f"{ready[0]['display_name']} is ready for a check-in",
                "— head to the Chemistry Lab now."]

    # ── Very early game: nothing done yet ────────────────────────────────
    if not player.completed_experiments and not player.current_experiments:
        return ["Go to Chemistry Lab and start Water Synthesis",
                "using the Hydrogen and Oxygen in your inventory."]

    # ── Engineering: no engineered tools yet ─────────────────────────────
    if not player.engineered_tools:
        if player.engineering_progress < 10:
            return ["Explore Asteroids and Moons to gain Eng XP,",
                    "then build the Telescope in Engineering Lab."]
        else:
            return ["Enough Eng XP — head to Engineering Lab and",
                    "build your first tool: the Telescope."]

    # ── Has telescope but not scanner ────────────────────────────────────
    if "telescope" in player.engineered_tools and "scanner" not in player.engineered_tools:
        if player.engineering_progress >= 30:
            return ["Eng XP unlocked the Scanner — build it now",
                    "in Engineering Lab to improve Planet missions."]
        else:
            return ["Keep exploring to reach 30 Eng XP and unlock",
                    "the Scanner in the Engineering Lab."]

    # ── Has scanner but not probe ─────────────────────────────────────────
    if "scanner" in player.engineered_tools and "probe" not in player.engineered_tools:
        if player.engineering_progress >= 60:
            return ["Eng XP unlocked the Probe — build it now.",
                    "It's required to land on Planets and find life."]
        else:
            return ["Keep exploring to reach 60 Eng XP and unlock",
                    "the Probe — it's the key to discovering life."]

    # ── Chemistry falling behind engineering ─────────────────────────────
    if player.chemistry_progress < player.engineering_progress - 20:
        return ["Chemistry XP is lagging. Explore Nebulae and",
                "Planets, and run experiments in Chemistry Lab."]

    # ── Has probe but tools not maxed ────────────────────────────────────
    if "probe" in player.engineered_tools:
        probe_lvl = player.tool_level("probe")
        scanner_lvl = player.tool_level("scanner")
        if probe_lvl < 3 or scanner_lvl < 3:
            return ["Upgrade your Probe and Scanner to Level 3",
                    "in Engineering Lab before going to Andromeda."]

    # ── Tools maxed but still in Milky Way ───────────────────────────────
    if ("probe" in player.engineered_tools
            and player.tool_level("probe") >= 3
            and player.tool_level("scanner") >= 3
            and player.galaxy != EXPLORE_WIN_GALAXY):
        return ["Probe and Scanner are Level 3 — travel to",
                "Andromeda and land on a Planet to find life!"]

    # ── In Andromeda with maxed tools ────────────────────────────────────
    if (player.galaxy == EXPLORE_WIN_GALAXY
            and player.tool_level("probe") >= 3
            and player.tool_level("scanner") >= 3):
        return ["In Andromeda, tools maxed — launch a Planet",
                "mission now. Life is out there. Go find it."]

    # ── Chemistry endgame push ───────────────────────────────────────────
    remaining_chem = [
        k for k in ["water_synthesis", "saline_solution",
                    "organic_compound_synthesis", "amino_acid_synthesis",
                    "protein_folding", "cell_membrane_synthesis",
                    "replication_attempt"]
        if k not in player.completed_experiments
        and not any(e["name"] == k for e in player.current_experiments)
    ]
    if remaining_chem:
        from constants import EXPERIMENTS
        next_exp = EXPERIMENTS.get(remaining_chem[0])
        if next_exp:
            name = next_exp["display_name"]
            return [f"Next chemistry step: {name}.",
                    "Check Chemistry Lab to see if you can start it."]

    return None


def _show_warnings(player: Player):
    """Print relevant warnings the player should know about."""
    warnings = []

    if player.ship_health == 3:
        warnings.append("⚠  CRITICAL: Ship hull at minimum! One more system failure = death.")
    if player.energy < 200:
        warnings.append("⚠  CRITICAL: Energy critically low! Explore a star immediately.")
    if player.oxygen_level == 0:
        warnings.append("⚠  Oxygen depleted! Repair in Engineering Lab.")
    if player.filter_health == 0:
        warnings.append("⚠  Filters broken! Replace them for free in Engineering Lab.")
    if player.heat_shield == 0:
        warnings.append("⚠  Heat shield offline! Repair in Engineering Lab.")
    if player.glass_integrity == 0:
        warnings.append("⚠  Glass integrity compromised! Repair in Engineering Lab.")
    if player.frame_integrity == 0:
        warnings.append("⚠  Frame integrity failing! Repair in Engineering Lab.")

    # Broken tools
    all_tools = player.all_explore_tools()
    broken = [name for name, t in all_tools.items() if t["broken"]]
    if broken:
        names = ", ".join(ITEM_DISPLAY_NAMES.get(b, b) for b in broken)
        warnings.append(f"⚠  Broken tools need repair: {names}")

    # Experiments needing attention
    for exp in player.current_experiments:
        if exp.get("needs_checkin"):
            warnings.append(f"⚠  Experiment '{exp['name']}' is ready for a check-in!")

    if warnings:
        print(d.c("  " + "!" * 54, d.BRIGHT_YELLOW))
        for w in warnings:
            print(d.c(f"  {w}", d.BRIGHT_YELLOW))
        print(d.c("  " + "!" * 54, d.BRIGHT_YELLOW))
        print()

