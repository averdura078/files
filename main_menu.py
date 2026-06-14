"""
main_menu.py - Main Menu module. Entry point after startup.
"""
import display as d
from player import Player, save_game
from constants import ITEM_DISPLAY_NAMES


def run(player: Player) -> str:
    """
    Show the main menu. Returns a string indicating where to go:
    'explore', 'chemistry', 'engineering', 'stats', 'quit'
    """
    while True:
        if player.is_dead:
            return "dead"

        d.module_header("MAIN MENU", f"Commander {player.name}", "🚀")
        d.mini_hud(player)

        # Mission statement — always visible
        _W = 57
        print(d.c("  ┌" + "─" * 59 + "┐", d.BRIGHT_MAGENTA))
        mission_lines = [
            "MISSION  Explore the universe, build your lab, and answer",
            "         the question that has haunted humanity for ages.",
            "         Discover life on a planet in Andromeda — or",
            "         synthesise it yourself in the Chemistry Lab.",
        ]
        for line in mission_lines:
            print(
                d.c("  │ ", d.BRIGHT_MAGENTA) +
                d.c(line.ljust(_W), d.WHITE) +
                d.c(" │", d.BRIGHT_MAGENTA)
            )
        print(d.c("  └" + "─" * 59 + "┘", d.BRIGHT_MAGENTA))
        print()

        # Check for any warnings
        _show_warnings(player)

        choice = d.choose(
            ["Explore", "Chemistry Lab", "Engineering Lab", "View Stats", "Save & Quit"],
            title="What would you like to do?"
        )

        if choice is None:
            # chose "Main Menu" from main menu — just loop
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
        print(d.c("  " + "!" * 59, d.BRIGHT_YELLOW))
        for w in warnings:
            print(d.c(f"  {w}", d.BRIGHT_YELLOW))
        print(d.c("  " + "!" * 59, d.BRIGHT_YELLOW))
        print()
