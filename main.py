"""
main.py - Entry point. Handles startup, save/load, game loop, death/win handling.
"""
import sys
import display as d
from player import Player, save_game, load_game, save_exists

MAX_NAME_LENGTH = 20


def startup() -> Player:
    """Handle startup: title screen, load/new game, name entry."""
    d.title_banner()

    if save_exists():
        d.info("A save file was found.")
        if d.yes_no("Load your previous game?"):
            player = load_game()
            if player:
                d.success(f"Welcome back, Commander {player.name}!")
                d.pause()
                return player
            else:
                d.error("Save file corrupted. Starting a new game.")

    # New game
    d.narrative(
        "The year is 2387. Humanity's last research vessel — yours — drifts at the "
        "edge of the known universe. Your mission: explore, experiment, and answer "
        "the question that has haunted civilisation since the beginning. "
        "Are we alone?"
    )

    name = ""
    while not name:
        raw = d.prompt_raw(
            f"What is your name, Commander? (max {MAX_NAME_LENGTH} chars)")
        # Strip non-printable characters and leading/trailing whitespace
        name = "".join(ch for ch in raw if ch.isprintable()).strip()
        if not name:
            d.error("You'll need a name for the mission logs.")
        elif len(name) > MAX_NAME_LENGTH:
            d.error(f"Name too long — maximum {MAX_NAME_LENGTH} characters.")
            name = ""

    player = Player(name)
    d.success(f"Commander {player.name}. The mission begins.")
    d.narrative(
        "Your ship — battered but functional — carries you into the dark. "
        "In the lab, hydrogen and oxygen sit waiting. In the hold, your basic tools. "
        "And somewhere out there, in the gas clouds and the asteroid fields and the "
        "deep silence between stars: answers."
    )
    print()
    d.divider(color=d.BRIGHT_MAGENTA)
    print(d.c("  YOUR MISSION:", d.BOLD + d.BRIGHT_MAGENTA))
    print(d.c("  Engineer a Probe and Scanner to Level 3, travel to Andromeda,", d.BRIGHT_WHITE))
    print(d.c("  and land on a Planet to discover life among the stars —", d.BRIGHT_WHITE))
    print(d.c("  or synthesise life itself, step by step, in the Chemistry Lab.", d.BRIGHT_WHITE))
    d.divider(color=d.BRIGHT_MAGENTA)
    save_game(player)
    d.pause()
    return player


def death_screen(player: Player, reason: str) -> bool:
    """
    Show game over screen.
    Returns True if the player chose to respawn, False to exit.
    """
    d.game_over_screen(reason)
    score = player.calculate_score()
    d.label("Final Score",        str(score))
    d.label("Missions Completed", str(player.missions_completed))
    d.label("Vaults Found",       str(player.vaults_found))

    if score > player.high_score:
        player.high_score = score
        d.success(f"New high score: {score}!")
    else:
        d.dim_line(f"Your best remains: {player.high_score}")

    save_game(player)
    print()

    choice = d.choose_no_menu(
        ["Respawn (restart with same name, all progress reset)",
         "Exit to desktop"],
        title="What would you like to do?"
    )
    if choice.startswith("Respawn"):
        player.reset()
        save_game(player)
        d.success(f"Welcome back, Commander {player.name}. The stars await.")
        d.pause()
        return True
    else:
        d.narrative("The ship falls silent. Your story ends here — for now.")
        d.pause("Press Enter to exit")
        return False


def win(player: Player, win_type: str):
    """Handle win condition."""
    score = player.calculate_score()
    prev_high = player.high_score

    if score > player.high_score:
        player.high_score = score

    save_game(player)
    d.win_screen(player, win_type, score, prev_high)


def game_loop(player: Player):
    """Main game loop. Orchestrates all modules."""
    import main_menu
    import explore
    import chemistry
    import engineering
    import stats

    while True:
        # Check death before each loop
        if player.is_dead:
            reason = ("Your ship's hull dropped below critical levels."
                      if player.ship_health < 3
                      else "You ran out of energy. The ship went dark.")
            respawn = death_screen(player, reason)
            if not respawn:
                return
            # Respawned — loop continues with reset player

        destination = main_menu.run(player)

        if destination == "dead" or player.is_dead:
            reason = ("Your ship's hull dropped below critical levels."
                      if player.ship_health < 3
                      else "You ran out of energy. The ship went dark.")
            respawn = death_screen(player, reason)
            if not respawn:
                return
            continue

        if destination == "quit":
            d.clear()
            d.narrative(
                "The stars drift past as your ship goes into standby. Until next time, Commander.")
            d.pause("Press Enter to exit")
            sys.exit(0)

        elif destination == "explore":
            won = explore.run(player)
            if won:
                win(player, "explore")
            if player.is_dead:
                reason = ("Your ship took too much damage."
                          if player.ship_health < 3
                          else "You ran out of energy far from home.")
                respawn = death_screen(player, reason)
                if not respawn:
                    return

        elif destination == "chemistry":
            won = chemistry.run(player)
            if won:
                win(player, "chem")
            if player.is_dead:
                reason = "You ran out of energy in the Chemistry Lab. The ship went dark."
                respawn = death_screen(player, reason)
                if not respawn:
                    return

        elif destination == "engineering":
            engineering.run(player)
            if player.is_dead:
                reason = ("Your ship took too much damage."
                          if player.ship_health < 3
                          else "You ran out of energy in the Engineering Lab.")
                respawn = death_screen(player, reason)
                if not respawn:
                    return

        elif destination == "stats":
            stats.run(player)

        # Auto-save after every module visit
        save_game(player)


def main():
    player = None
    try:
        player = startup()
        game_loop(player)
    except KeyboardInterrupt:
        print()
        d.warn("Game interrupted. Saving...")
        try:
            if player is not None:
                save_game(player)
                d.success("Saved. Goodbye, Commander.")
            else:
                d.info("Goodbye.")
        except Exception:
            d.error("Could not save. Goodbye.")
        sys.exit(0)


if __name__ == "__main__":
    main()
