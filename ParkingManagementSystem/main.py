"""
main.py
─────────────────────────────────────────────────────────────────────────────
KZN Smart Mall Parking Management System
Entry point — initialises data layer, handles login/register, and
routes each user to their role-specific dashboard.

Run with:
    python main.py

Default Credentials
───────────────────
Role              │ Email                        │ Password
──────────────────┼──────────────────────────────┼──────────────
Owner             │ owner@kznmalls.co.za          │ Owner@123
Admin (Gateway)   │ admin.gateway@kzn.co.za       │ Admin@123
Admin (Pavilion)  │ admin.pavilion@kzn.co.za      │ Admin@123
Admin (La Lucia)  │ admin.lucia@kzn.co.za         │ Admin@123
Customer (demo)   │ zanele@demo.co.za             │ Demo@123
Customer (demo)   │ rajan@demo.co.za              │ Demo@123
─────────────────────────────────────────────────────────────────────────────
"""

import sys
import os
import io

# ── Windows: force UTF-8 output + enable ANSI before any print() calls ────────
if sys.platform == 'win32':
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



# ── Make sure project root is on the Python path ──────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.data_service import DataService
from services.auth_service import AuthService
from ui.display import Display, bold, cyan, dim
from ui.customer_menu import CustomerMenu
from ui.admin_menu import AdminMenu
from ui.owner_menu import OwnerMenu


# ─── Role Router ──────────────────────────────────────────────────────────────

def route_to_dashboard(user: dict) -> None:
    """Send the logged-in user to their role-specific menu."""
    role = user.get('role')
    if role == 'customer':
        CustomerMenu(user).run()
    elif role == 'admin':
        AdminMenu(user).run()
    elif role == 'owner':
        OwnerMenu(user).run()
    else:
        Display.print_error(f'Unknown role: "{role}". Please contact system support.')
        Display.press_enter()


# ─── Login Flow ───────────────────────────────────────────────────────────────

def login_flow(auth: AuthService) -> dict | None:
    """Prompt for credentials, return the user dict on success or None."""
    Display.clear()
    Display.print_banner()
    Display.print_header('SIGN IN')

    email    = Display.get_input('Email address   :')
    password = Display.get_password('Password')

    if not email:
        return None

    result = auth.login(email, password)
    if result['success']:
        Display.print_success(f'Welcome back, {result["user"]["name"]}!')
        Display.press_enter('Press Enter to open your dashboard…')
        return result['user']
    else:
        Display.print_error(result['error'])
        Display.press_enter()
        return None


# ─── Register Flow ────────────────────────────────────────────────────────────

def register_flow(auth: AuthService) -> dict | None:
    """Collect new-customer details, return the created user dict or None."""
    Display.clear()
    Display.print_banner()
    Display.print_header('CREATE A NEW ACCOUNT')
    print(f'  {dim("Note: Administrator and owner accounts are pre-configured.")}')
    print()

    name     = Display.get_input('Full name       :')
    email    = Display.get_input('Email address   :')
    password = Display.get_password('Password (min. 6 characters)')
    confirm  = Display.get_password('Confirm password')

    if not name or not email:
        Display.print_warning('Registration cancelled — required fields were left blank.')
        Display.press_enter()
        return None

    result = auth.register(name, email, password, confirm)
    if result['success']:
        Display.print_success(
            f'Account created successfully!\n'
            f'  Welcome to KZN Smart Mall PMS, {result["user"]["name"]}.'
        )
        Display.press_enter('Press Enter to open your dashboard…')
        return result['user']
    else:
        Display.print_error(result['error'])
        Display.press_enter()
        return None


# ─── Credentials Reference ────────────────────────────────────────────────────

def show_credentials() -> None:
    """Print the default demo login credentials for quick reference."""
    Display.clear()
    Display.print_banner()
    Display.print_header('DEFAULT DEMO CREDENTIALS')
    Display.print_table(
        ['Role', 'Email', 'Password'],
        [
            ['Owner / Shareholder',       'owner@kznmalls.co.za',        'Owner@123'],
            ['Admin — Gateway',           'admin.gateway@kzn.co.za',     'Admin@123'],
            ['Admin — Pavilion',          'admin.pavilion@kzn.co.za',    'Admin@123'],
            ['Admin — La Lucia',          'admin.lucia@kzn.co.za',       'Admin@123'],
            ['Customer (demo)',           'zanele@demo.co.za',           'Demo@123'],
            ['Customer (demo)',           'rajan@demo.co.za',            'Demo@123'],
        ]
    )
    Display.press_enter()


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    """Application entry point."""
    # Initialise data layer (seeds JSON files on first run)
    DataService.initialise()

    auth = AuthService()

    while True:
        Display.clear()
        Display.print_banner()

        # Quick system status line
        from services.report_service import ReportService
        try:
            summary = ReportService.get_system_summary()
            print(
                f'  {dim("Live:")}  '
                f'{bold(str(summary["total_active"]))} vehicles parked  │  '
                f'{bold(str(summary["mall_count"]))} malls online  │  '
                f'Total revenue: {bold(Display.fmt_currency(summary["total_revenue"]))}'
            )
        except Exception:
            pass  # Gracefully skip status line if data not ready

        Display.print_divider()
        Display.print_menu({
            '1': 'Sign In',
            '2': 'Register as a Customer',
            '3': 'View Demo Credentials',
            '0': 'Exit System',
        }, title='WELCOME — SELECT AN OPTION')

        choice = Display.get_choice()

        if choice == '1':
            user = login_flow(auth)
            if user:
                route_to_dashboard(user)

        elif choice == '2':
            user = register_flow(auth)
            if user:
                route_to_dashboard(user)

        elif choice == '3':
            show_credentials()

        elif choice == '0':
            Display.clear()
            print()
            print(f'  {cyan(bold("Thank you for using KZN Smart Mall Parking Management System."))}')
            print(f'  {dim("© KZN Mall Group — KwaZulu-Natal, South Africa")}')
            print()
            sys.exit(0)

        else:
            Display.print_error('Invalid selection. Please enter 1, 2, 3, or 0.')
            Display.press_enter()


if __name__ == '__main__':
    main()
