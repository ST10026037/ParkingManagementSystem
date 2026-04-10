"""
ui/admin_menu.py
─────────────────────────────────────────────────────────────────────────────
Parking Administrator menus — capacity, parked vehicles, daily activity.
KZN Smart Mall Parking Management System
─────────────────────────────────────────────────────────────────────────────
"""

from datetime import datetime
from ui.display import Display, bold, cyan, green, red, yellow, dim, CYAN, RESET, BOLD
from services.data_service import DataService
from services.parking_service import ParkingService
from services.report_service import ReportService
from pricing.strategies import calculate_fee


class AdminMenu:
    """All menus available to a logged-in parking administrator."""

    def __init__(self, user: dict):
        self.user = user
        self.mall = DataService.get_mall_by_id(user['mall_id'])

    def run(self):
        """Main admin dashboard loop."""
        if self.mall is None:
            Display.print_error('Administrator mall not found. Please contact system support.')
            Display.press_enter()
            return

        while True:
            Display.clear()
            Display.print_banner()
            print(f'  {BOLD}Admin Dashboard{RESET}   {cyan(self.mall["name"])}')
            print(f'  Logged in as: {self.user["name"]}  |  📍 {self.mall["location"]}')
            Display.print_divider()

            occ = ParkingService.get_occupancy(self.mall['id'])
            if occ['percent'] >= 90:
                cap_status = red(f'⚠ CRITICAL — {occ["active"]}/{occ["capacity"]} bays used')
            elif occ['percent'] >= 70:
                cap_status = yellow(f'▲ HIGH — {occ["active"]}/{occ["capacity"]} bays used')
            else:
                cap_status = green(f'✔ OK — {occ["active"]}/{occ["capacity"]} bays used')
            print(f'  Capacity: {cap_status}')

            Display.print_menu({
                '1': 'View Vehicles Currently Parked',
                '2': 'Monitor Parking Capacity',
                '3': "View Today's Activity Log",
                '0': 'Sign Out',
            }, title='MAIN MENU')

            choice = Display.get_choice()

            if choice == '1':
                self._parked_vehicles()
            elif choice == '2':
                self._capacity_monitor()
            elif choice == '3':
                self._daily_activity()
            elif choice == '0':
                Display.print_info('You have been signed out.')
                break
            else:
                Display.print_error('Invalid choice.')
                Display.press_enter()

    # ── Parked Vehicles ───────────────────────────────────────────────────────

    def _parked_vehicles(self):
        """Show all vehicles currently parked at the admin's mall."""
        Display.clear()
        Display.print_banner()
        Display.print_header(f'Vehicles Currently Parked — {self.mall["name"]}')

        active = DataService.get_active_sessions_by_mall(self.mall['id'])

        if not active:
            Display.print_info('No vehicles are currently parked at this mall.')
        else:
            rows = []
            for s in sorted(active, key=lambda x: x['entry_time']):
                customer = DataService.get_user_by_id(s['customer_id'])
                elapsed  = max(1, round(
                    (datetime.now() - datetime.fromisoformat(s['entry_time'])).total_seconds() / 60
                ))
                est = calculate_fee(self.mall, elapsed)
                rows.append([
                    s['license_plate'],
                    customer['name'] if customer else '—',
                    ReportService.fmt_datetime(s['entry_time']),
                    ReportService.fmt_duration(elapsed),
                    Display.fmt_currency(est['amount']),
                ])
            Display.print_table(
                ['Licence Plate', 'Customer', 'Entry Time', 'Duration', 'Est. Charge'],
                rows
            )
            print(f'  {bold(str(len(active)))} vehicle{"s" if len(active) != 1 else ""} currently parked.')

        Display.press_enter()

    # ── Capacity Monitor ──────────────────────────────────────────────────────

    def _capacity_monitor(self):
        """Show detailed live capacity information."""
        Display.clear()
        Display.print_banner()
        Display.print_header(f'Parking Capacity Monitor — {self.mall["name"]}')

        occ = ParkingService.get_occupancy(self.mall['id'])
        print()
        print(f'  Mall      : {bold(self.mall["name"])}')
        print(f'  Location  : {self.mall["location"]}')
        print(f'  Pricing   : {ParkingService.get_pricing_label(self.mall)}')
        print()
        Display.print_subheader('LIVE OCCUPANCY')
        Display.print_progress_bar(occ['percent'], occ['active'], occ['capacity'])
        print()

        # Status label
        if occ['percent'] >= 90:
            status_msg = red('⚠  CRITICAL — Consider notifying incoming drivers.')
        elif occ['percent'] >= 70:
            status_msg = yellow('▲  HIGH — Monitor closely; approaching capacity.')
        elif occ['percent'] >= 50:
            status_msg = yellow('●  MODERATE — Bay availability is fair.')
        else:
            status_msg = green('✔  LOW — Plenty of bays available.')

        print(f'  Status: {status_msg}')
        print()

        # Breakdown
        Display.print_subheader('CAPACITY BREAKDOWN')
        Display.print_table(
            ['Metric', 'Value'],
            [
                ['Total Capacity',     str(occ['capacity'])],
                ['Currently Occupied', str(occ['active'])],
                ['Available Bays',     str(occ['available'])],
                ['Occupancy Rate',     f'{occ["percent"]}%'],
            ]
        )
        Display.press_enter()

    # ── Daily Activity ────────────────────────────────────────────────────────

    def _daily_activity(self):
        """Show today's parking sessions at the admin's mall."""
        Display.clear()
        Display.print_banner()

        today_str = datetime.now().strftime('%Y-%m-%d')
        today_display = datetime.now().strftime('%d %B %Y')
        Display.print_header(f"Today's Activity — {self.mall['name']} ({today_display})")

        sessions = DataService.get_sessions_by_mall_and_date(self.mall['id'], today_str)
        completed = [s for s in sessions if s['status'] == 'completed']
        active    = [s for s in sessions if s['status'] == 'active']
        revenue   = sum(s.get('fee', 0) or 0 for s in completed if s.get('paid'))

        # Stats row
        print()
        print(f'  Visits today      : {bold(str(len(sessions)))}')
        print(f'  Currently parked  : {bold(str(len(active)))}')
        print(f'  Completed sessions: {bold(str(len(completed)))}')
        print(f'  Revenue today     : {bold(Display.fmt_currency(revenue))}')
        print()

        if not sessions:
            Display.print_info('No parking activity recorded today.')
        else:
            rows = []
            for s in sorted(sessions, key=lambda x: x['entry_time'], reverse=True):
                rows.append([
                    s['license_plate'],
                    ReportService.fmt_datetime(s['entry_time']),
                    ReportService.fmt_datetime(s['exit_time']) if s['exit_time'] else 'Still parked',
                    ReportService.fmt_duration(s.get('duration_minutes')),
                    Display.fmt_currency(s.get('fee')) if s.get('fee') is not None else '—',
                    'Active' if s['status'] == 'active' else ('Paid' if s.get('paid') else 'Unpaid'),
                ])
            Display.print_table(
                ['Plate', 'Entry', 'Exit', 'Duration', 'Fee', 'Status'],
                rows
            )

        Display.press_enter()
