"""
ui/customer_menu.py
─────────────────────────────────────────────────────────────────────────────
Customer role menus — parking, active sessions, history, payments.
KZN Smart Mall Parking Management System
─────────────────────────────────────────────────────────────────────────────
"""

from ui.display import Display, bold, cyan, green, red, yellow, dim, CYAN, RESET, BOLD
from services.data_service import DataService
from services.parking_service import ParkingService
from services.payment_service import PaymentService
from services.report_service import ReportService


class CustomerMenu:
    """All menus and flows available to a logged-in customer."""

    def __init__(self, user: dict):
        self.user = user

    def run(self):
        """Main customer dashboard loop."""
        while True:
            Display.clear()
            Display.print_banner()
            print(f'  {BOLD}Customer Dashboard{RESET}   Welcome, {cyan(self.user["name"])}')
            Display.print_divider()

            Display.print_menu({
                '1': 'Park / Exit a Vehicle',
                '2': 'View Active Sessions',
                '3': 'View Parking History',
                '4': 'View Payment History',
                '0': 'Sign Out',
            }, title='MAIN MENU')

            choice = Display.get_choice()

            if choice == '1':
                self._park_menu()
            elif choice == '2':
                self._active_sessions_menu()
            elif choice == '3':
                self._history_menu()
            elif choice == '4':
                self._payments_menu()
            elif choice == '0':
                Display.print_info('You have been signed out.')
                break
            else:
                Display.print_error('Invalid choice. Please select a valid option.')
                Display.press_enter()

    # ── Park / Exit a Vehicle ─────────────────────────────────────────────────

    def _park_menu(self):
        """Show malls with live occupancy; let customer enter or exit."""
        while True:
            Display.clear()
            Display.print_banner()
            Display.print_header('Park / Exit a Vehicle')

            malls = DataService.get_all_malls()
            active_sessions = DataService.get_active_sessions_by_customer(self.user['id'])
            active_by_mall  = {s['mall_id']: s for s in active_sessions}

            print()
            for idx, mall in enumerate(malls, 1):
                occ = ParkingService.get_occupancy(mall['id'])
                active_here = active_by_mall.get(mall['id'])
                full = occ['available'] == 0

                # Mall header
                print(f'  {BOLD}{CYAN}[{idx}] {mall["name"]}{RESET}')
                print(f'      📍 {mall["location"]}')
                print(f'      💰 Pricing: {ParkingService.get_pricing_label(mall)}')
                print(f'      🅿️  Capacity: ', end='')
                Display.print_progress_bar(occ['percent'], occ['active'], occ['capacity'])

                if active_here:
                    print(f'      {green("✔ You are currently parked here")} — Plate: {bold(active_here["license_plate"])}')
                    print(f'      Entry: {ReportService.fmt_datetime(active_here["entry_time"])}')
                elif full:
                    print(f'      {red("✘ Mall is at full capacity — no bays available")}')

                print()

            Display.print_menu({
                '1': f'Enter {malls[0]["name"]}',
                '2': f'Enter {malls[1]["name"]}',
                '3': f'Enter {malls[2]["name"]}',
                '4': 'Exit a Mall (register vehicle exit)',
                '0': 'Back',
            }, title='SELECT ACTION')

            choice = Display.get_choice()

            if choice in ('1', '2', '3'):
                mall = malls[int(choice) - 1]
                active_here = active_by_mall.get(mall['id'])
                if active_here:
                    Display.print_warning(
                        f'You are already parked at {mall["name"]} '
                        f'(plate: {active_here["license_plate"]}).\n'
                        f'  Please exit that session first.'
                    )
                    Display.press_enter()
                else:
                    self._enter_mall(mall)

            elif choice == '4':
                self._exit_mall_menu(active_sessions)

            elif choice == '0':
                break
            else:
                Display.print_error('Invalid choice.')
                Display.press_enter()

    def _enter_mall(self, mall: dict):
        """Register vehicle entry at a specific mall."""
        Display.clear()
        Display.print_banner()
        Display.print_header(f'Enter {mall["name"]}')

        occ = ParkingService.get_occupancy(mall['id'])
        if occ['available'] == 0:
            Display.print_error(
                f'{mall["name"]} is at full capacity ({mall["capacity"]} vehicles). '
                f'No bays are available.'
            )
            Display.press_enter()
            return

        print(f'  📍 {mall["location"]}')
        print(f'  💰 Pricing: {ParkingService.get_pricing_label(mall)}')
        print(f'  🅿️  Available bays: {green(str(occ["available"]))} / {occ["capacity"]}')
        print()

        plate = Display.get_input('Enter your vehicle licence plate number:')
        if not plate:
            return

        result = ParkingService.enter(self.user['id'], mall['id'], plate)
        if result['success']:
            s = result['session']
            Display.print_success(
                f'Entry registered!\n'
                f'  Licence plate : {bold(s["license_plate"])}\n'
                f'  Mall          : {mall["name"]}\n'
                f'  Entry time    : {ReportService.fmt_datetime(s["entry_time"])}'
            )
        else:
            Display.print_error(result['error'])
        Display.press_enter()

    def _exit_mall_menu(self, active_sessions: list):
        """Choose a session to exit and process payment."""
        if not active_sessions:
            Display.print_warning('You have no active parking sessions to exit.')
            Display.press_enter()
            return

        Display.clear()
        Display.print_banner()
        Display.print_header('Exit a Mall')

        options = {}
        for i, s in enumerate(active_sessions, 1):
            mall = DataService.get_mall_by_id(s['mall_id'])
            options[str(i)] = f'{s["license_plate"]}  —  {mall["name"] if mall else "Unknown"}'
        options['0'] = 'Back'

        Display.print_menu(options, title='SELECT SESSION TO EXIT')
        choice = Display.get_choice()

        if choice == '0' or not choice.isdigit():
            return

        idx = int(choice) - 1
        if idx < 0 or idx >= len(active_sessions):
            Display.print_error('Invalid selection.')
            Display.press_enter()
            return

        session = active_sessions[idx]
        self._process_exit(session)

    def _process_exit(self, session: dict):
        """Show fee preview and process exit + payment."""
        Display.clear()
        Display.print_banner()
        Display.print_header('Exit & Pay')

        preview = ParkingService.preview_exit(session['id'])
        if not preview['success']:
            Display.print_error(preview['error'])
            Display.press_enter()
            return

        mall = preview['mall']

        # Show fee receipt
        Display.print_receipt({
            'Mall':         mall['name'],
            'Location':     mall['location'],
            'Licence Plate':session['license_plate'],
            'Entry Time':   ReportService.fmt_datetime(session['entry_time']),
            'Exit Time':    ReportService.fmt_datetime(preview['exit_time'].isoformat()),
            'Duration':     ReportService.fmt_duration(preview['duration_minutes']),
            'Pricing':      preview['label'],
            'Breakdown':    preview['breakdown'],
            'AMOUNT DUE':   f'{Display.fmt_currency(preview["amount"])}',
        }, title=f' PARKING FEE — {mall["name"].upper()} ')

        # Payment method
        Display.print_menu({
            '1': 'Card Payment',
            '2': 'Cash Payment',
            '0': 'Cancel (stay parked)',
        }, title='SELECT PAYMENT METHOD')

        method_choice = Display.get_choice()
        if method_choice == '0':
            Display.print_info('Exit cancelled. Your vehicle remains parked.')
            Display.press_enter()
            return

        method_map = {'1': 'card', '2': 'cash'}
        method = method_map.get(method_choice)
        if not method:
            Display.print_error('Invalid payment method selected.')
            Display.press_enter()
            return

        # Finalise exit
        exit_result = ParkingService.exit_mall(session['id'])
        if not exit_result['success']:
            Display.print_error(exit_result['error'])
            Display.press_enter()
            return

        # Process payment
        pay_result = PaymentService.pay(session['id'], method)
        if pay_result['success']:
            method_label = PaymentService.METHOD_LABELS.get(method, method)
            Display.print_success(
                f'Payment confirmed!\n'
                f'  Amount paid   : {bold(Display.fmt_currency(preview["amount"]))}\n'
                f'  Method        : {method_label}\n'
                f'  Thank you for visiting {mall["name"]}!'
            )
        else:
            Display.print_error(pay_result['error'])
        Display.press_enter()

    # ── Active Sessions ───────────────────────────────────────────────────────

    def _active_sessions_menu(self):
        """Display all active sessions for this customer."""
        Display.clear()
        Display.print_banner()
        Display.print_header('Active Parking Sessions')

        from datetime import datetime
        import math

        sessions = DataService.get_active_sessions_by_customer(self.user['id'])
        if not sessions:
            Display.print_info('You have no active parking sessions.')
        else:
            rows = []
            for s in sessions:
                mall = DataService.get_mall_by_id(s['mall_id'])
                elapsed_min = max(1, math.ceil(
                    (datetime.now() - datetime.fromisoformat(s['entry_time'])).total_seconds() / 60
                ))
                est_fee = ParkingService.get_occupancy  # just to avoid unused import
                from pricing.strategies import calculate_fee
                est = calculate_fee(mall, elapsed_min)
                rows.append([
                    s['license_plate'],
                    mall['name'] if mall else '—',
                    ReportService.fmt_datetime(s['entry_time']),
                    ReportService.fmt_duration(elapsed_min),
                    Display.fmt_currency(est['amount']),
                ])
            Display.print_table(
                ['Licence Plate', 'Mall', 'Entry Time', 'Duration (so far)', 'Est. Charge'],
                rows
            )
            Display.print_info(f'You have {len(sessions)} active session(s). Go to "Park / Exit" to exit.')

        Display.press_enter()

    # ── Parking History ───────────────────────────────────────────────────────

    def _history_menu(self):
        """Display completed parking session history."""
        Display.clear()
        Display.print_banner()
        Display.print_header('My Parking History')

        sessions = sorted(
            [s for s in DataService.get_sessions_by_customer(self.user['id']) if s['status'] == 'completed'],
            key=lambda s: s.get('exit_time', ''),
            reverse=True
        )

        if not sessions:
            Display.print_info('You have no completed parking sessions yet.')
        else:
            rows = []
            for s in sessions:
                mall = DataService.get_mall_by_id(s['mall_id'])
                rows.append([
                    s['license_plate'],
                    mall['name'] if mall else '—',
                    ReportService.fmt_datetime(s['entry_time']),
                    ReportService.fmt_datetime(s['exit_time']),
                    ReportService.fmt_duration(s['duration_minutes']),
                    Display.fmt_currency(s.get('fee')),
                    'Paid' if s.get('paid') else 'Unpaid',
                ])
            Display.print_table(
                ['Plate', 'Mall', 'Entry', 'Exit', 'Duration', 'Fee', 'Status'],
                rows
            )
            print(f'  {dim(f"Total sessions: {len(sessions)}")}')

        Display.press_enter()

    # ── Payment History ───────────────────────────────────────────────────────

    def _payments_menu(self):
        """Display all payment records for this customer."""
        Display.clear()
        Display.print_banner()
        Display.print_header('My Payment History')

        payments = PaymentService.get_customer_history(self.user['id'])
        total_spent = sum(p['amount'] for p in payments)

        if not payments:
            Display.print_info('You have no payment records yet.')
        else:
            rows = []
            for p in payments:
                mall = p.get('mall') or {}
                session = p.get('session') or {}
                rows.append([
                    ReportService.fmt_datetime(p['timestamp']),
                    mall.get('name', '—'),
                    session.get('license_plate', '—'),
                    ReportService.fmt_duration(session.get('duration_minutes')),
                    PaymentService.METHOD_LABELS.get(p['method'], p['method']),
                    Display.fmt_currency(p['amount']),
                ])
            Display.print_table(
                ['Date & Time', 'Mall', 'Licence Plate', 'Duration', 'Method', 'Amount'],
                rows,
                highlight_col=5
            )
            print(f'  Total paid: {bold(Display.fmt_currency(total_spent))}  |  '
                  f'Payments: {len(payments)}')

        Display.press_enter()
