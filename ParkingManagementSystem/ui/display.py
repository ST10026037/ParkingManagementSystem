"""
ui/display.py
─────────────────────────────────────────────────────────────────────────────
Terminal display helpers — ANSI colours, box-drawing, table formatter,
progress bars, banners, and input prompts.
KZN Smart Mall Parking Management System
─────────────────────────────────────────────────────────────────────────────
"""

import os
import sys
import io

# ── Windows: force UTF-8 output + enable ANSI before any print() calls ───────────────
if sys.platform == 'win32':
    # Only wrap if not already wrapped (prevents double-wrap crash)
    if hasattr(sys.stdout, 'buffer') and getattr(sys.stdout, 'encoding', '') != 'utf-8':
        try:
            sys.stdout = io.TextIOWrapper(
                sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True
            )
        except (AttributeError, io.UnsupportedOperation):
            pass
    os.system('')
    try:
        import ctypes
        ctypes.windll.kernel32.SetConsoleMode(
            ctypes.windll.kernel32.GetStdHandle(-11), 7
        )
    except Exception:
        pass

# ─── ANSI Colour Codes ────────────────────────────────────────────────────────

RESET   = '\033[0m'
BOLD    = '\033[1m'
DIM     = '\033[2m'

BLACK   = '\033[30m'
RED     = '\033[91m'
GREEN   = '\033[92m'
YELLOW  = '\033[93m'
BLUE    = '\033[94m'
MAGENTA = '\033[95m'
CYAN    = '\033[96m'
WHITE   = '\033[97m'

BG_BLUE    = '\033[44m'
BG_GREEN   = '\033[42m'
BG_RED     = '\033[41m'
BG_YELLOW  = '\033[43m'

# Convenience shortcuts
def bold(text):    return f'{BOLD}{text}{RESET}'
def dim(text):     return f'{DIM}{text}{RESET}'
def red(text):     return f'{RED}{text}{RESET}'
def green(text):   return f'{GREEN}{text}{RESET}'
def yellow(text):  return f'{YELLOW}{text}{RESET}'
def blue(text):    return f'{BLUE}{text}{RESET}'
def magenta(text): return f'{MAGENTA}{text}{RESET}'
def cyan(text):    return f'{CYAN}{text}{RESET}'
def white(text):   return f'{WHITE}{text}{RESET}'


# ─── Display Class ────────────────────────────────────────────────────────────

class Display:
    WIDTH = 72  # Terminal column target width

    # ── Screen ────────────────────────────────────────────────────────────────

    @staticmethod
    def clear():
        os.system('cls' if sys.platform == 'win32' else 'clear')

    @staticmethod
    def print_banner():
        w = Display.WIDTH
        print()
        print(f'  {CYAN}{"═" * w}{RESET}')
        print(f'  {BOLD}{CYAN}{"KZN SMART MALL PARKING MANAGEMENT SYSTEM".center(w)}{RESET}')
        print(f'  {CYAN}{"Managing Malls Across KwaZulu-Natal, South Africa".center(w)}{RESET}')
        print(f'  {CYAN}{"═" * w}{RESET}')
        print()

    @staticmethod
    def print_header(title: str, color=CYAN):
        w = Display.WIDTH
        print()
        print(f'  {color}{BOLD}  {title.upper()}{RESET}')
        print(f'  {color}  {"─" * (w - 2)}{RESET}')

    @staticmethod
    def print_subheader(title: str):
        w = Display.WIDTH
        print(f'\n  {YELLOW}{title}{RESET}')
        print(f'  {"─" * min(len(title) + 4, w - 2)}')

    @staticmethod
    def print_divider(char='─', color=DIM):
        print(f'  {color}{char * Display.WIDTH}{RESET}')

    # ── Messages ──────────────────────────────────────────────────────────────

    @staticmethod
    def print_success(msg: str):
        print(f'\n  {GREEN}✔  {msg}{RESET}')

    @staticmethod
    def print_error(msg: str):
        print(f'\n  {RED}✘  {msg}{RESET}')

    @staticmethod
    def print_warning(msg: str):
        print(f'\n  {YELLOW}⚠  {msg}{RESET}')

    @staticmethod
    def print_info(msg: str):
        print(f'\n  {CYAN}ℹ  {msg}{RESET}')

    # ── Menu ──────────────────────────────────────────────────────────────────

    @staticmethod
    def print_menu(options: dict, title: str = 'OPTIONS'):
        """
        Print a numbered menu.

        Args:
            options (dict): { '1': 'Option label', '0': 'Go back' }
            title   (str):  Section label above the menu.
        """
        print()
        Display.print_subheader(title)
        for key, label in options.items():
            if key == '0':
                print(f'    {dim(f"[{key}]")}  {dim(label)}')
            else:
                print(f'    {CYAN}[{key}]{RESET}  {label}')
        print()

    @staticmethod
    def get_choice(prompt: str = '  Enter choice: ') -> str:
        """Read a stripped string from the user."""
        try:
            return input(f'{BOLD}{prompt}{RESET}').strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return '0'

    @staticmethod
    def get_input(prompt: str, required: bool = True) -> str:
        """Prompt for a text value, re-asking if required and blank."""
        while True:
            try:
                value = input(f'  {YELLOW}{prompt}{RESET} ').strip()
            except (EOFError, KeyboardInterrupt):
                return ''
            if value or not required:
                return value
            Display.print_error('This field is required.')

    @staticmethod
    def get_password(prompt: str = 'Password') -> str:
        """Prompt for a password (shown as plain text for terminal compatibility)."""
        try:
            import getpass
            return getpass.getpass(f'  {YELLOW}{prompt}: {RESET}')
        except Exception:
            return Display.get_input(prompt)

    @staticmethod
    def press_enter(msg: str = 'Press Enter to continue…'):
        try:
            input(f'\n  {DIM}{msg}{RESET} ')
        except (EOFError, KeyboardInterrupt):
            pass

    # ── Table ─────────────────────────────────────────────────────────────────

    @staticmethod
    def print_table(headers: list, rows: list, highlight_col: int = -1):
        """
        Print a formatted table with box-drawing characters.

        Args:
            headers      (list): Column header strings.
            rows         (list): List of row tuples/lists.
            highlight_col (int): Column index to highlight in cyan (-1 = none).
        """
        if not rows:
            print(f'\n  {DIM}(No records to display){RESET}\n')
            return

        # Calculate column widths (content + padding)
        widths = [len(str(h)) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(widths):
                    widths[i] = max(widths[i], len(str(cell)))

        def row_line(cells, col_sep='│', pad=' '):
            parts = []
            for i, (cell, w) in enumerate(zip(cells, widths)):
                cell_str = str(cell).ljust(w)
                if i == highlight_col:
                    cell_str = f'{CYAN}{cell_str}{RESET}'
                parts.append(f'{pad}{cell_str}{pad}')
            return f'  {col_sep}' + f'{col_sep}'.join(parts) + f'{col_sep}'

        def sep_line(left, mid, right, fill='─'):
            segs = [fill * (w + 2) for w in widths]
            return f'  {left}' + mid.join(segs) + right

        print()
        print(sep_line('┌', '┬', '┐'))
        print(row_line([f'{BOLD}{h}{RESET}' for h in headers]))
        print(sep_line('├', '┼', '┤'))
        for row in rows:
            print(row_line(row))
        print(sep_line('└', '┴', '┘'))
        print()

    # ── Receipt ───────────────────────────────────────────────────────────────

    @staticmethod
    def print_receipt(fields: dict, title: str = 'RECEIPT'):
        """
        Print a formatted receipt/summary box.

        Args:
            fields (dict): { 'Label': 'Value' }
        """
        w = Display.WIDTH
        label_w = max(len(k) for k in fields) + 2

        print()
        print(f'  {CYAN}┌{"─" * (w - 2)}┐{RESET}')
        print(f'  {CYAN}│{BOLD}{title.center(w - 2)}{RESET}{CYAN}│{RESET}')
        print(f'  {CYAN}├{"─" * (w - 2)}┤{RESET}')
        for label, value in fields.items():
            label_str = f'  {label}:'.ljust(label_w + 4)
            value_str = str(value)
            line = f'{DIM}{label_str}{RESET}{BOLD}{value_str}{RESET}'
            # Pad to width
            visible_len = len(label_str) + len(value_str)
            padding = max(0, w - 4 - visible_len)
            print(f'  {CYAN}│{RESET} {line}{" " * padding} {CYAN}│{RESET}')
        print(f'  {CYAN}└{"─" * (w - 2)}┘{RESET}')
        print()

    # ── Progress Bar ──────────────────────────────────────────────────────────

    @staticmethod
    def print_progress_bar(percent: int, active: int, capacity: int, width: int = 40):
        """
        Print a coloured ASCII progress bar for parking capacity.
        """
        filled = round((percent / 100) * width)
        empty  = width - filled

        if percent >= 90:
            bar_color = RED
            status = red(f'CRITICAL ({percent}%)')
        elif percent >= 70:
            bar_color = YELLOW
            status = yellow(f'HIGH ({percent}%)')
        else:
            bar_color = GREEN
            status = green(f'OK ({percent}%)')

        bar = f'{bar_color}{"█" * filled}{DIM}{"░" * empty}{RESET}'
        print(f'  [{bar}] {status}')
        print(f'  {active} vehicle{"s" if active != 1 else ""} parked  |  {capacity - active} bay{"s" if capacity - active != 1 else ""} available  |  Capacity: {capacity}')

    # ── Formatting Helpers ────────────────────────────────────────────────────

    @staticmethod
    def fmt_currency(amount) -> str:
        return f'R{(amount or 0):.2f}'

    @staticmethod
    def fmt_bool(value: bool, true_label: str = 'Yes', false_label: str = 'No') -> str:
        if value:
            return green(true_label)
        return red(false_label)

    @staticmethod
    def fmt_status(status: str) -> str:
        if status == 'active':
            return yellow('● Active')
        elif status == 'completed':
            return green('✔ Completed')
        return dim(status)

    @staticmethod
    def fmt_paid(paid: bool) -> str:
        return green('✔ Paid') if paid else red('✘ Unpaid')
