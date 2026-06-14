"""
chemistry.py - Chemistry Lab Module.
Handles experiment management, chem tool building, and the path to creating life.
"""
import display as d
from player import Player, save_game
from constants import (
    EXPERIMENTS, CHEM_UNLOCK_THRESHOLDS, CHEM_TOOL_BUILD_COSTS,
    NEW_EXPERIMENT_COST, ITEM_DISPLAY_NAMES, BUILD_CHEM_TOOL_BASE_COST,
)


def run(player: Player) -> bool:
    """
    Main entry point for Chemistry Lab.
    Returns True if life was created (win condition), False otherwise.
    """
    while True:
        if player.is_dead:
            return False

        d.module_header("CHEMISTRY LAB", "Where life begins", "⚗️")
        d.mini_hud(player)

        choice = d.choose(
            ["Start / Check Experiments", "Build Chemistry Tools", "View Chemicals & Materials"],
            title="Chemistry Lab Menu"
        )
        if choice is None:
            return False   # back to main menu

        if choice == "Start / Check Experiments":
            result = _experiments_menu(player)
            if result == "win":
                return True

        elif choice == "Build Chemistry Tools":
            _build_chem_tools(player)

        elif choice == "View Chemicals & Materials":
            _view_inventory(player)

        if player.is_dead:
            return False


def _experiments_menu(player: Player) -> str:
    """Experiment hub. Returns 'win' or 'ok'."""
    while True:
        if player.is_dead:
            return "ok"

        d.section_header("Experiments", d.BRIGHT_GREEN)
        _show_lab_status(player)

        options = []
        if player.current_experiments:
            options.append("Check on a current experiment")
        options.append("Start a new experiment")

        choice = d.choose(options, title="What would you like to do?")
        if choice is None:
            return "ok"

        if choice == "Check on a current experiment":
            result = _check_experiment(player)
            if result == "win":
                return "win"
        elif choice == "Start a new experiment":
            _start_experiment(player)

        save_game(player)


def _start_experiment(player: Player):
    """Let player pick and start a new experiment."""
    d.section_header("Start New Experiment", d.BRIGHT_CYAN)

    available = _get_available_experiments(player)
    if not available:
        d.warn("No experiments available yet. Explore more to raise your Chemistry XP!")
        d.label("Your Chemistry XP", str(player.chemistry_progress))
        _show_locked_experiments(player)
        d.pause()
        return

    # Show available experiments
    print(d.c("  Available experiments:", d.BRIGHT_WHITE))
    for name in available:
        exp = EXPERIMENTS[name]
        already_running = any(e["name"] == name for e in player.current_experiments)
        already_done = name in player.completed_experiments
        status = ""
        if already_running:
            status = d.c("  [IN PROGRESS]", d.YELLOW)
        elif already_done:
            status = d.c("  [COMPLETED]", d.DIM + d.WHITE)
        print(f"    {d.c(exp['display_name'], d.BRIGHT_CYAN)}{status}")
        d.dim_line(f"    {exp['description']}")
        print()

    exp_names = [EXPERIMENTS[n]["display_name"] for n in available]
    choice = d.choose(exp_names, title="Which experiment?")
    if choice is None:
        return

    # Map display name → key
    exp_key = None
    for k in available:
        if EXPERIMENTS[k]["display_name"] == choice:
            exp_key = k
            break
    if exp_key is None:
        return

    exp = EXPERIMENTS[exp_key]

    # ── Check if already running ─────────────────────────────────────────
    if any(e["name"] == exp_key for e in player.current_experiments):
        d.warn("That experiment is already in progress. Check on it instead.")
        d.pause()
        return

    # ── Show requirements ─────────────────────────────────────────────────
    d.section_header(f"Starting: {exp['display_name']}", d.BRIGHT_CYAN)
    d.dim_line(exp["description"])
    print()

    print(d.c("  Required chemistry tools:", d.BRIGHT_WHITE))
    tools_ok = True
    for tool in exp["required_tools"]:
        owned = player.has_chem_tool(tool)
        icon = d.c("✓", d.BRIGHT_GREEN) if owned else d.c("✗", d.BRIGHT_RED)
        print(f"    {icon} {d.c(ITEM_DISPLAY_NAMES.get(tool, tool), d.WHITE)}")
        if not owned:
            tools_ok = False

    print()
    print(d.c("  Required ingredients:", d.BRIGHT_WHITE))
    ingredients_ok = True
    missing = []
    for item, amount in exp["required_ingredients"].items():
        have = player.get_item_count(item)
        ok = have >= amount
        icon = d.c("✓", d.BRIGHT_GREEN) if ok else d.c("✗", d.BRIGHT_RED)
        display = ITEM_DISPLAY_NAMES.get(item, item)
        print(f"    {icon} {d.c(display, d.WHITE)} — need {amount}, have {d.c(str(have), d.BRIGHT_YELLOW)}")
        if not ok:
            ingredients_ok = False
            missing.append(display)

    print()
    d.label("Energy cost", f"{exp['energy_cost']} E")
    d.label("Your energy",  f"{player.energy} E")
    print()
    d.label("Check-ins required", str(exp["checkins_required"]) if exp["checkins_required"] > 0 else "Instant")

    if not tools_ok:
        d.error("You are missing required chemistry tools. Build them first.")
        d.pause()
        return

    if not ingredients_ok:
        d.error(f"Missing ingredients: {', '.join(missing)}")
        d.info("Go explore to collect them, or check your vault rewards.")
        d.pause()
        return

    if player.energy < exp["energy_cost"]:
        d.error(f"Not enough energy. Need {exp['energy_cost']}, have {player.energy}.")
        d.pause()
        return

    if not d.yes_no(f"Begin '{exp['display_name']}'? This costs {exp['energy_cost']} energy."):
        return

    # ── Deduct ingredients and energy ────────────────────────────────────
    for item, amount in exp["required_ingredients"].items():
        player.remove_item(item, amount)
    if player.spend_energy(exp["energy_cost"]):
        d.error("The experiment drained your last reserves. The ship goes dark.")
        save_game(player)
        return

    # ── Add to current experiments ────────────────────────────────────────
    new_exp = {
        "name": exp_key,
        "display_name": exp["display_name"],
        "checkins": 0,
        "checkins_required": exp["checkins_required"],
        "yield_penalty": 1.0,  # 1.0 = no penalty; 0.75 = 25% penalty
        "needs_checkin": exp["checkins_required"] == 0,  # instant experiments need one "check"
        "status": "running" if exp["checkins_required"] > 0 else "ready",
    }
    player.current_experiments.append(new_exp)

    if exp["checkins_required"] == 0:
        # Instant: resolve immediately
        d.narrative(f"You mix the ingredients with practiced hands. The reaction is immediate.")
        _resolve_experiment(player, new_exp)
    else:
        d.narrative(
            f"Experiment started. The {exp['display_name']} is underway. "
            f"Come back to check on it (check-ins needed: {exp['checkins_required']})."
        )
        d.pause()

    save_game(player)


def _check_experiment(player: Player) -> str:
    """Check in on a running experiment. Returns 'win' or 'ok'."""
    if not player.current_experiments:
        d.info("No experiments currently running.")
        d.pause()
        return "ok"

    d.section_header("Current Experiments", d.BRIGHT_GREEN)

    names = [e["display_name"] for e in player.current_experiments]
    choice = d.choose(names, title="Which experiment to check on?")
    if choice is None:
        return "ok"

    exp_state = next((e for e in player.current_experiments if e["display_name"] == choice), None)
    if exp_state is None:
        return "ok"

    exp_def = EXPERIMENTS.get(exp_state["name"])
    if exp_def is None:
        return "ok"

    d.section_header(f"Checking: {exp_state['display_name']}", d.BRIGHT_CYAN)
    d.dim_line(exp_def["description"])
    print()

    # Instant/ready experiments resolve now
    if exp_state["status"] in ("ready", "instant"):
        _resolve_experiment(player, exp_state)
        save_game(player)
        if exp_state["name"] == "replication_attempt":
            return "win"
        return "ok"

    # Increment check-in counter
    exp_state["checkins"] += 1
    remaining = exp_state["checkins_required"] - exp_state["checkins"]

    d.label("Check-in", f"{exp_state['checkins']} / {exp_state['checkins_required']}")

    # Check if optional ingredient add is needed
    # (some experiments ask if you want to add something to boost yield)
    _optional_ingredient_boost(player, exp_state, exp_def)

    if remaining <= 0:
        # Final check-in — resolve
        d.narrative("The experiment has run its course. Time to see the results.")
        _resolve_experiment(player, exp_state)
        save_game(player)
        if exp_state["name"] == "replication_attempt":
            return "win"
    else:
        if remaining == 1:
            d.info(f"Almost done — one more check-in needed.")
        else:
            d.info(f"Experiment progressing. {remaining} more check-in(s) needed.")
        exp_state["needs_checkin"] = False
        d.pause()

    save_game(player)
    return "ok"


def _optional_ingredient_boost(player: Player, exp_state: dict, exp_def: dict):
    """Offer the player a chance to add optional ingredients mid-experiment."""
    # Only applies to multi-checkin experiments
    if exp_state["checkins_required"] < 2:
        return

    # Mid-experiment: ask about supplemental water or saline (generic boost)
    boost_item = "water"
    boost_amount = 1

    if player.has_item(boost_item, boost_amount):
        print()
        if d.yes_no(f"Add {boost_amount}x {ITEM_DISPLAY_NAMES.get(boost_item, boost_item)} to improve yield?"):
            if player.remove_item(boost_item, boost_amount):
                # Boost yield — represented by reducing penalty
                exp_state["yield_penalty"] = min(1.0, exp_state["yield_penalty"] + 0.10)
                d.success("Ingredient added — experiment quality improved.")
            else:
                d.error("Not enough in inventory.")
    else:
        d.warn(f"Warning: Adding {ITEM_DISPLAY_NAMES.get(boost_item)} would improve results, but you have none.")
        exp_state["yield_penalty"] = max(0.5, exp_state["yield_penalty"] - 0.10)
        d.dim_line("Yield reduced by 10% this check-in.")


def _resolve_experiment(player: Player, exp_state: dict):
    """Complete the experiment, award outputs, update progress."""
    exp_def = EXPERIMENTS.get(exp_state["name"])
    if exp_def is None:
        return

    penalty = exp_state.get("yield_penalty", 1.0)

    # Remove from current experiments
    player.current_experiments = [
        e for e in player.current_experiments if e["display_name"] != exp_state["display_name"]
    ]

    # Add to completed
    if exp_state["name"] not in player.completed_experiments:
        player.completed_experiments.append(exp_state["name"])

    # Replication attempt — this is the WIN
    if exp_state["name"] == "replication_attempt":
        player.life_created_chem = True
        player.chemistry_progress += exp_def["chem_progress_gain"]
        return  # Win is handled by caller

    # Award output
    if exp_def["output"]:
        print()
        print(d.c("  Experiment results:", d.BRIGHT_GREEN))
        for item, base_amount in exp_def["output"].items():
            amount = max(1, int(base_amount * penalty))
            player.add_item(item, amount)
            display = ITEM_DISPLAY_NAMES.get(item, item)
            print(f"    {d.c('+' + str(amount), d.BRIGHT_GREEN)} {d.c(display, d.WHITE)}")
            if penalty < 1.0:
                d.dim_line(f"    (Yield reduced to {int(penalty*100)}% due to missing check-ins or ingredients)")

    # Chemistry progress
    gain = int(exp_def["chem_progress_gain"] * penalty)
    player.chemistry_progress += gain
    d.success(f"+{gain} Chemistry XP")

    # Unlock message
    if exp_def.get("unlocks"):
        for unlocked in exp_def["unlocks"]:
            exp_u = EXPERIMENTS.get(unlocked)
            if exp_u:
                d.info(f"New experiment unlocked: {exp_u['display_name']}")

    # Check if any new experiments are available due to progress gain
    _check_progress_unlocks(player)

    d.pause()


def _check_progress_unlocks(player: Player):
    """Notify player if chemistry_progress has unlocked new experiments."""
    for exp_name, threshold in CHEM_UNLOCK_THRESHOLDS.items():
        if player.chemistry_progress >= threshold:
            if exp_name not in player.completed_experiments:
                exp = EXPERIMENTS.get(exp_name)
                if exp:
                    # Check it wasn't already announced by checking if it's newly reached
                    pass  # handled at experiment start time


def _build_chem_tools(player: Player):
    """Build chemistry tools (microscope, incubator, centrifuge)."""
    d.section_header("Build Chemistry Tools", d.BRIGHT_YELLOW)
    d.dim_line("Chemistry tools are required for more advanced experiments.")
    print()

    buildable = []
    for tool, data in CHEM_TOOL_BUILD_COSTS.items():
        if not player.chemistry_tools.get(tool, False):
            buildable.append(tool)

    if not buildable:
        d.success("You have all chemistry tools!")
        d.pause()
        return

    for tool in buildable:
        data = CHEM_TOOL_BUILD_COSTS[tool]
        display = ITEM_DISPLAY_NAMES.get(tool, tool)
        print(d.c(f"  {display}", d.BRIGHT_CYAN))
        print(f"    Energy: {d.c(str(data['energy']) + ' E', d.BRIGHT_YELLOW)}")
        print(f"    Materials:")
        for mat, amt in data["materials"].items():
            have = player.get_item_count(mat)
            ok = have >= amt
            icon = d.c("✓", d.BRIGHT_GREEN) if ok else d.c("✗", d.BRIGHT_RED)
            print(f"      {icon} {ITEM_DISPLAY_NAMES.get(mat, mat)}: need {amt}, have {have}")
        print()

    options = [ITEM_DISPLAY_NAMES.get(t, t) for t in buildable]
    choice = d.choose(options, title="Which tool to build?")
    if choice is None:
        return

    tool_key = None
    for t in buildable:
        if ITEM_DISPLAY_NAMES.get(t, t) == choice:
            tool_key = t
            break
    if tool_key is None:
        return

    data = CHEM_TOOL_BUILD_COSTS[tool_key]

    # Check costs
    can_build = True
    if player.energy < data["energy"]:
        d.error(f"Not enough energy. Need {data['energy']}, have {player.energy}.")
        can_build = False

    for mat, amt in data["materials"].items():
        if not player.has_item(mat, amt):
            d.error(f"Missing {ITEM_DISPLAY_NAMES.get(mat, mat)} (need {amt}).")
            can_build = False

    if not can_build:
        d.pause()
        return

    if not d.yes_no(f"Build {ITEM_DISPLAY_NAMES.get(tool_key, tool_key)}?"):
        return

    if player.spend_energy(data["energy"]):
        d.error("Building the tool drained your last reserves. The ship goes dark.")
        save_game(player)
        return
    for mat, amt in data["materials"].items():
        player.remove_item(mat, amt)
    player.chemistry_tools[tool_key] = True

    d.success(f"{ITEM_DISPLAY_NAMES.get(tool_key, tool_key)} built and added to your lab!")
    d.narrative(f"You install the {ITEM_DISPLAY_NAMES.get(tool_key, tool_key)}. "
                f"Your lab capabilities have expanded.")
    save_game(player)
    d.pause()


def _view_inventory(player: Player):
    """Display chemicals and materials in inventory."""
    d.section_header("Chemicals & Materials", d.BRIGHT_MAGENTA)

    chemicals = ["hydrogen", "oxygen", "water", "nitrogen", "carbon_compounds",
                 "lipids", "mineral_samples", "saline_solution", "organic_compounds",
                 "amino_acids", "proteins", "cell_membranes", "stellar_dust", "plasma_extract"]
    materials = ["iron_ore", "silicon", "titanium", "graphene",
                 "crystal_compounds", "glass_shard"]

    print(d.c("  Chemicals:", d.BRIGHT_CYAN))
    any_chem = False
    for item in chemicals:
        amt = player.get_item_count(item)
        if amt > 0:
            print(f"    {d.c(str(amt).rjust(3), d.BRIGHT_GREEN)}  {ITEM_DISPLAY_NAMES.get(item, item)}")
            any_chem = True
    if not any_chem:
        d.dim_line("  None. Go explore some nebulae and planets.")

    print()
    print(d.c("  Materials:", d.BRIGHT_YELLOW))
    any_mat = False
    for item in materials:
        amt = player.get_item_count(item)
        if amt > 0:
            print(f"    {d.c(str(amt).rjust(3), d.BRIGHT_GREEN)}  {ITEM_DISPLAY_NAMES.get(item, item)}")
            any_mat = True
    if not any_mat:
        d.dim_line("  None. Try mining an asteroid or a moon.")

    print()
    print(d.c("  Chemistry Tools Owned:", d.BRIGHT_WHITE))
    for tool, owned in player.chemistry_tools.items():
        icon = d.c("✓", d.BRIGHT_GREEN) if owned else d.c("✗", d.DIM + d.WHITE)
        print(f"    {icon}  {ITEM_DISPLAY_NAMES.get(tool, tool)}")

    d.pause()


def _get_available_experiments(player: Player) -> list:
    """Return experiment keys the player can currently attempt (based on progress and prerequisites)."""
    available = []

    for key, exp in EXPERIMENTS.items():
        # Check progress threshold
        threshold = CHEM_UNLOCK_THRESHOLDS.get(key, 0)
        if player.chemistry_progress < threshold:
            continue

        # Special unlock chain: saline_solution only after water_synthesis done
        if key == "saline_solution" and "water_synthesis" not in player.completed_experiments:
            continue

        # Organic compound synthesis requires saline done (or water done + 15 XP)
        if key == "organic_compound_synthesis":
            if "water_synthesis" not in player.completed_experiments:
                continue

        # Each subsequent experiment requires previous one done
        chain = [
            "water_synthesis", "saline_solution", "organic_compound_synthesis",
            "amino_acid_synthesis", "protein_folding", "cell_membrane_synthesis",
            "replication_attempt"
        ]
        if key in chain:
            idx = chain.index(key)
            if idx > 0:
                if chain[idx - 1] not in player.completed_experiments:
                    continue

        available.append(key)

    return available


def _show_locked_experiments(player: Player):
    """Show what XP is needed to unlock next experiments."""
    print()
    print(d.c("  Upcoming experiments (locked):", d.DIM + d.WHITE))
    for key, threshold in CHEM_UNLOCK_THRESHOLDS.items():
        if player.chemistry_progress < threshold and key not in player.completed_experiments:
            exp = EXPERIMENTS.get(key)
            if exp:
                needed = threshold - player.chemistry_progress
                print(f"    {d.c(exp['display_name'], d.DIM + d.WHITE)}  — needs {needed} more Chemistry XP")


def _show_lab_status(player: Player):
    """Show current lab status: tools, running experiments."""
    # Chemistry tools
    tools_owned = [t for t, owned in player.chemistry_tools.items() if owned]
    print(d.c("  Lab tools: ", d.BRIGHT_CYAN) +
          d.c(", ".join(ITEM_DISPLAY_NAMES.get(t, t) for t in tools_owned) or "Beaker only", d.WHITE))

    # Running experiments
    if player.current_experiments:
        print(d.c("  Active experiments:", d.BRIGHT_GREEN))
        for e in player.current_experiments:
            checkins_left = e["checkins_required"] - e["checkins"]
            if checkins_left <= 0 or e["status"] == "ready":
                status_str = d.c("READY TO RESOLVE", d.BRIGHT_GREEN + d.BOLD)
            else:
                status_str = d.c(f"{checkins_left} check-in(s) remaining", d.YELLOW)
            print(f"    • {d.c(e['display_name'], d.BRIGHT_WHITE)}  — {status_str}")
    else:
        d.dim_line("  No active experiments.")

    # Chemistry XP & next unlock
    print()
    d.label("Chemistry XP", str(player.chemistry_progress))
    _show_next_unlock(player)
    print()


def _show_next_unlock(player: Player):
    """Show what the next chemistry unlock is."""
    chain = [
        "water_synthesis", "saline_solution", "organic_compound_synthesis",
        "amino_acid_synthesis", "protein_folding", "cell_membrane_synthesis",
        "replication_attempt"
    ]
    for key in chain:
        if key not in player.completed_experiments:
            threshold = CHEM_UNLOCK_THRESHOLDS.get(key, 0)
            exp = EXPERIMENTS.get(key)
            if exp and player.chemistry_progress < threshold:
                needed = threshold - player.chemistry_progress
                d.dim_line(f"  Next unlock: {exp['display_name']} (need {needed} more Chemistry XP)")
            return
