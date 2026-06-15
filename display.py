"""
display.py - All terminal output helpers: colours, banners, prompts, status bars.
Uses only the standard library (no colorama needed — ANSI codes work on all modern terminals).
"""
import os
import sys
import time

# ── ANSI colour codes ──────────────────────────────────────────────────────────
RESET  = "\033[0m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
ITALIC = "\033[3m"

# Foreground colours
BLACK   = "\033[30m"
RED     = "\033[31m"
GREEN   = "\033[32m"
YELLOW  = "\033[33m"
BLUE    = "\033[34m"
MAGENTA = "\033[35m"
CYAN    = "\033[36m"
WHITE   = "\033[37m"

# Bright foreground
BRIGHT_RED     = "\033[91m"
BRIGHT_GREEN   = "\033[92m"
BRIGHT_YELLOW  = "\033[93m"
BRIGHT_BLUE    = "\033[94m"
BRIGHT_MAGENTA = "\033[95m"
BRIGHT_CYAN    = "\033[96m"
BRIGHT_WHITE   = "\033[97m"

# Background colours
BG_BLACK  = "\033[40m"
BG_BLUE   = "\033[44m"
BG_CYAN   = "\033[46m"

# ── Shorthand helpers ──────────────────────────────────────────────────────────

def c(text, *codes) -> str:
    """Wrap text in ANSI codes."""
    return "".join(codes) + str(text) + RESET

def error(text):   print(c(f"  ✗ {text}", BRIGHT_RED))
def success(text): print(c(f"  ✓ {text}", BRIGHT_GREEN))
def warn(text):    print(c(f"  ⚠ {text}", BRIGHT_YELLOW))
def info(text):    print(c(f"  ➤ {text}", BRIGHT_CYAN))
def dim_line(text):print(c(f"  {text}", DIM, WHITE))

def label(key, value, key_color=BRIGHT_CYAN, val_color=BRIGHT_WHITE):
    print(f"  {key_color}{BOLD}{key}{RESET}: {val_color}{value}{RESET}")

# ── Dividers ───────────────────────────────────────────────────────────────────

def divider(char="─", width=60, color=BLUE):
    print(c(char * width, color))

def thin_divider(color=DIM + WHITE):
    print(c("·" * 60, color))

# ── Section headers ────────────────────────────────────────────────────────────

def section_header(title: str, color=BRIGHT_CYAN):
    print()
    divider(color=color)
    print(c(f"  {title.upper()}", BOLD, color))
    divider(color=color)

def module_header(title: str, subtitle: str = "", icon: str = ""):
    clear()
    width = 58
    print()
    print(c("█" * width, BLUE))
    inner = f"  {title}  "
    pad = max(0, width - 2 - len(inner))
    left_pad = pad // 2
    right_pad = pad - left_pad
    print(c("█" + " " * left_pad + inner + " " * right_pad + "█", BOLD, BRIGHT_CYAN))
    if subtitle:
        sub_inner = f"  {subtitle}  "
        sub_pad = max(0, width - 2 - len(sub_inner))
        sub_left = sub_pad // 2
        sub_right = sub_pad - sub_left
        print(c("█" + " " * sub_left + sub_inner + " " * sub_right + "█", DIM, WHITE))
    print(c("█" * width, BLUE))
    print()

# ── Game title banner ──────────────────────────────────────────────────────────

def title_banner():
    clear()
    print()
    print(c("╔══════════════════════════════════════════════════════════╗", BRIGHT_BLUE))
    print(c("║", BRIGHT_BLUE) + c("                                                          ", BG_BLACK) + c("║", BRIGHT_BLUE))
    print(c("║", BRIGHT_BLUE) + c("   ██████╗ ██████╗ ██████╗ ██╗████████╗                   ", BRIGHT_CYAN) + c("║", BRIGHT_BLUE))
    print(c("║", BRIGHT_BLUE) + c("  ██╔═══██╗██╔══██╗██╔══██╗██║╚══██╔══╝                   ", BRIGHT_CYAN) + c("║", BRIGHT_BLUE))
    print(c("║", BRIGHT_BLUE) + c("  ██║   ██║██████╔╝██████╔╝██║   ██║                      ", BRIGHT_CYAN) + c("║", BRIGHT_BLUE))
    print(c("║", BRIGHT_BLUE) + c("  ██║   ██║██╔══██╗██╔══██╗██║   ██║                      ", BRIGHT_CYAN) + c("║", BRIGHT_BLUE))
    print(c("║", BRIGHT_BLUE) + c("  ╚██████╔╝██║  ██║██████╔╝██║   ██║                      ", BRIGHT_CYAN) + c("║", BRIGHT_BLUE))
    print(c("║", BRIGHT_BLUE) + c("   ╚═════╝ ╚═╝  ╚═╝╚═════╝ ╚═╝   ╚═╝                      ", BRIGHT_CYAN) + c("║", BRIGHT_BLUE))
    print(c("║", BRIGHT_BLUE) + c("                                                          ", BG_BLACK) + c("║", BRIGHT_BLUE))
    print(c("║", BRIGHT_BLUE) + c("         S P A C E   E X P L O R A T I O N                ", BRIGHT_MAGENTA) + c("║", BRIGHT_BLUE))
    print(c("║", BRIGHT_BLUE) + c("                                                          ", BG_BLACK) + c("║", BRIGHT_BLUE))
    print(c("╚══════════════════════════════════════════════════════════╝", BRIGHT_BLUE))
    print()

# ── Prompt helpers ─────────────────────────────────────────────────────────────

def prompt(text: str) -> str:
    """Standard input prompt. Returns stripped lowercase string."""
    print()
    try:
        val = input(c(f"  ❯ {text}: ", BRIGHT_YELLOW))
    except (KeyboardInterrupt, EOFError):
        print()
        return ""
    return val.strip()

def prompt_raw(text: str) -> str:
    """Input prompt that preserves case (for names etc)."""
    print()
    try:
        val = input(c(f"  ❯ {text}: ", BRIGHT_YELLOW))
    except (KeyboardInterrupt, EOFError):
        print()
        return ""
    return val.strip()

def choose(options: list[str], title: str = "Choose an option") -> str | None:
    """
    Display a numbered menu, return the chosen option string.
    Always prepends 'Main Menu' as option 0.
    Returns None if user chose Main Menu.
    'options' should NOT include Main Menu — it's added automatically.
    """
    print()
    print(c(f"  {title}", BOLD, BRIGHT_WHITE))
    thin_divider()
    print(c(f"  0. ↩  Main Menu", DIM, WHITE))
    for i, opt in enumerate(options, 1):
        print(c(f"  {i}. ", BRIGHT_YELLOW) + c(opt, BRIGHT_WHITE))
    while True:
        raw = prompt("Enter number")
        if raw.isdigit():
            idx = int(raw)
            if idx == 0:
                return None
            if 1 <= idx <= len(options):
                return options[idx - 1]
        error(f"Please enter an integer between 0 and {len(options)}.")

def choose_no_menu(options: list[str], title: str = "Choose an option") -> str:
    """
    Same as choose() but WITHOUT the automatic Main Menu prepend.
    Returns the chosen option string.
    """
    print()
    print(c(f"  {title}", BOLD, BRIGHT_WHITE))
    thin_divider()
    for i, opt in enumerate(options, 1):
        print(c(f"  {i}. ", BRIGHT_YELLOW) + c(opt, BRIGHT_WHITE))
    while True:
        raw = prompt("Enter number")
        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(options):
                return options[idx]
        error(f"Please enter an integer between 1 and {len(options)}.")

def yes_no(question: str) -> bool:
    """Returns True for yes, False for no."""
    print()
    print(c(f"  {question}", BRIGHT_WHITE))
    while True:
        raw = prompt("y / n").lower()
        if raw in ("y", "yes"):
            return True
        if raw in ("n", "no"):
            return False
        error("Please enter y or n.")

# ── Typing effect ──────────────────────────────────────────────────────────────

# Safe column width for narrative text. Keeps well inside an 80-col terminal
# accounting for the 2-space indent that narrative() adds.
_WRAP_WIDTH = 70

def _wrap_text(text: str, width: int = _WRAP_WIDTH, indent: str = "  ") -> list[str]:
    """
    Word-wrap `text` into lines of at most `width` visible characters,
    preserving the leading `indent` on every line. Returns a list of lines
    (each already indented) ready to be typed out one at a time.
    Never splits mid-word — if a word doesn't fit, it moves to the next line.
    """
    words = text.split()
    lines = []
    current = indent
    for word in words:
        # +1 for the space before the word (except at line start)
        needs = len(word) if current == indent else len(word) + 1
        if len(current) + needs > width and current != indent:
            lines.append(current)
            current = indent + word
        else:
            current = current + word if current == indent else current + " " + word
    if current != indent:
        lines.append(current)
    return lines


def typewrite(text: str, delay: float = 0.018, color: str = WHITE):
    """Print text character by character for dramatic effect.
    Write the colour code once at the start and reset once at the end —
    never wrap individual characters, which floods the terminal with escape
    sequences and causes a visible stutter/instant-dump bug on longer strings.
    """
    try:
        sys.stdout.write(color)
        for ch in text:
            sys.stdout.write(ch)
            sys.stdout.flush()
            time.sleep(delay)
        sys.stdout.write(RESET + "\n")
        sys.stdout.flush()
    except (KeyboardInterrupt, EOFError):
        # Print the rest of the line instantly so layout doesn't break
        sys.stdout.write(RESET + "\n")
        sys.stdout.flush()


def narrative(text: str, delay: float = 0.012):
    """
    Print a narrative paragraph with a typewrite effect, word-wrapped so that
    no word is ever split across a line by the terminal.
    """
    lines = _wrap_text(text, width=_WRAP_WIDTH, indent="  ")
    print()
    for line in lines:
        typewrite(line, delay=delay, color=BRIGHT_WHITE)
    print()

def pause(msg: str = "Press Enter to continue..."):
    print()
    try:
        input(c(f"  [{msg}]", DIM, WHITE))
    except (KeyboardInterrupt, EOFError):
        print()

# ── Status bars ────────────────────────────────────────────────────────────────

def health_bar(current: int, maximum: int = 5, width: int = 10) -> str:
    filled = int((current / maximum) * width)
    bar = "█" * filled + "░" * (width - filled)
    if current >= 4:
        color = BRIGHT_GREEN
    elif current == 3:
        color = BRIGHT_YELLOW
    else:
        color = BRIGHT_RED
    return c(f"[{bar}]", color) + c(f" {current}/{maximum}", BOLD, color)

def energy_bar(current: int, maximum: int = 2000, width: int = 10) -> str:
    clamped = max(0, min(current, maximum))
    filled = int((clamped / maximum) * width)
    bar = "█" * filled + "░" * (width - filled)
    if clamped > 1200:
        color = BRIGHT_CYAN
    elif clamped > 600:
        color = BRIGHT_YELLOW
    else:
        color = BRIGHT_RED
    return c(f"[{bar}]", color) + c(f" {current} E", BOLD, color)

def tool_status_icon(broken: bool) -> str:
    return c("✗ BROKEN", BRIGHT_RED) if broken else c("✓ OK", BRIGHT_GREEN)

# ── Mini HUD (printed at top of most screens) ─────────────────────────────────

def mini_hud(player):
    print(c("  " + "─" * 54, BLUE))
    print(
        c("  Energy: ", BRIGHT_YELLOW) + energy_bar(player.energy) +
        c("    Hull: ", BRIGHT_CYAN) + health_bar(player.ship_health)
    )
    print(
        c("  Galaxy: ", BRIGHT_MAGENTA) + c(player.galaxy.ljust(12), BRIGHT_WHITE) +
        c("  Chem XP: ", BRIGHT_GREEN) + c(str(player.chemistry_progress).ljust(5), BRIGHT_WHITE) +
        c("  Eng XP: ", BRIGHT_CYAN) + c(str(player.engineering_progress), BRIGHT_WHITE)
    )
    print(c("  " + "─" * 54, BLUE))
    print()

# ── Clear screen ──────────────────────────────────────────────────────────────

def clear():
    os.system("cls" if os.name == "nt" else "clear")

# ── Game over / win screens ────────────────────────────────────────────────────

def game_over_screen(reason: str):
    clear()
    print()
    print(c("╔══════════════════════════════════════════╗", BRIGHT_RED))
    print(c("║          ☠  G A M E   O V E R  ☠        ║", BOLD, BRIGHT_RED))
    print(c("╚══════════════════════════════════════════╝", BRIGHT_RED))
    print()
    warn(reason)
    print()

def win_screen(player, win_type: str, score: int, prev_high: int):
    clear()
    print()
    print(c("╔══════════════════════════════════════════════════════════╗", BRIGHT_GREEN))
    print(c("║                                                          ║", BRIGHT_GREEN))
    print(c("║       ★  Y O U   W I N ,  " + player.name[:10].ljust(10) + "  ★         ║", BOLD, BRIGHT_GREEN))
    print(c("║                                                          ║", BRIGHT_GREEN))
    print(c("╚══════════════════════════════════════════════════════════╝", BRIGHT_GREEN))
    print()
    if win_type == "chem":
        narrative("In the sterile hum of your lab, something shifted. The cell membranes pulsed. "
                  "The amino acids rearranged. And then — it divided. Life. You created life.")
    else:
        narrative("As your probe broke through the cloud layer, your scanner lit up with signatures "
                  "no instrument had ever recorded before. Movement. Heat. Biology. Life — discovered.")
    print()
    divider(color=BRIGHT_GREEN)
    label("Win Type",    win_type.upper(), BRIGHT_YELLOW, BRIGHT_WHITE)
    label("Your Score",  str(score), BRIGHT_CYAN, BRIGHT_WHITE)
    label("Previous Best", str(prev_high), BRIGHT_MAGENTA, BRIGHT_WHITE)
    if score > prev_high:
        success(f"🏆 NEW HIGH SCORE! {score} beats {prev_high}!")
    elif score == prev_high:
        info("You matched your previous best. Impressive consistency.")
    else:
        dim_line(f"High score remains {prev_high}. You'll beat it next time.")
    divider(color=BRIGHT_GREEN)
    print()
    pause("Press Enter to return to main menu")
