"""
ui/owner_menu.py
─────────────────────────────────────────────────────────────────────────────
Owner / Shareholder menus — system summary, cross-mall comparison,
and per-mall detailed reports.
KZN Smart Mall Parking Management System
─────────────────────────────────────────────────────────────────────────────
"""

from ui.display import Display, bold, cyan, green, red, yellow, dim, CYAN, RESET, BOLD
from services.data_service import DataService
from services.parking_service import ParkingService
from services.report_service import ReportService


class OwnerMenu:
    """All menus available to a logged-in owner/shareholder."""

    def __init__(self, user: dict):
        self.user = user

    def run(self):
        """Main owner dashboard loop."""
        while True:
            Display.clear()
            Display.print_banner()
            print(f'  {BOLD}Owner / Shareholder Dashboard{RESET}   Welcome, {cyan(self.user["name"])}')
            Display.print_divider()

            Display.print_menu({
                '1': 'System Summary (All Malls)',
                '2': 'Cross-Mall Comparison Report',
                '3': 'Detailed Report — Gateway Theatre of Shopping',
                '4': 'Detailed Report — Pavilion Shopping Centre',
                '5': 'Detailed Report — La Lucia Mall',
                '0': 'Sign Out',
            }, title='MAIN MENU')

            choice = Display.get_choice()

            if choice == '1':
                self._system_summary()
            elif choice == '2':
                self._compare_malls()
            elif choice == '3':
                self._mall_detail('mall_gateway')
            elif choice == '4':
                self._mall_detail('mall_pavilion')
            elif choice == '5':
                self._mall_detail('mall_lucia')
            elif choice == '0':
                Display.print_info('You have been signed out.')
                break
            else:
                Display.print_error('Invalid choice.')
                Display.press_enter()

    # ── System Summary ────────────────────────────────────────────────────────

    def _system_summary(self):
        """High-level overview of all malls combined."""
        Display.clear()
        Display.print_banner()
        Display.print_header('System Summary — All KZN Malls')

        summary = ReportService.get_system_summary()

        print()
        print(f'  {bold("Portfolio Overview")}')
        print()
        Display.print_table(
            ['Metric', 'Value'],
            [
                ['Total Revenue (All Malls)',   Display.fmt_currency(summary['total_revenue'])],
                ['Total Vehicles (All Time)',   str(summary['total_vehicles'])],
                ['Currently Parked (Live)',     str(summary['total_active'])],
                ['Number of Managed Malls',     str(summary['mall_count'])],
            ]
        )

        # Top performers
        if summary['top_by_revenue']:
            t = summary['top_by_revenue']
            print(f'  {bold("Top Mall by Revenue")}  :  '
                  f'{cyan(t["mall"]["name"])}  —  '
                  f'{bold(Display.fmt_currency(t["total_revenue"]))}')
        if summary['top_by_volume']:
            t = summary['top_by_volume']
            print(f'  {bold("Top Mall by Volume")}   :  '
                  f'{cyan(t["mall"]["name"])}  —  '
                  f'{bold(str(t["total_vehicles"]))} total visits')

        # Quick glance table
        Display.print_subheader('ALL MALLS AT A GLANCE')
        rows = []
        for r in summary['mall_reports']:
            occ = r['occupancy']
            rows.append([
                r['mall']['name'],
                r['mall']['location'],
                r['pricing_name'],
                str(r['mall']['capacity']),
                str(r['active_vehicles']),
                str(r['total_vehicles']),
                Display.fmt_currency(r['total_revenue']),
                ReportService.fmt_duration(r['avg_duration']),
            ])
        Display.print_table(
            ['Mall', 'Location', 'Pricing', 'Capacity', 'Now', 'Total Visits', 'Revenue', 'Avg Duration'],
            rows,
            highlight_col=6
        )

        Display.press_enter()

    # ── Cross-Mall Comparison ──────────────────────────────────────────────────

    def _compare_malls(self):
        """Side-by-side comparison of all malls."""
        Display.clear()
        Display.print_banner()
        Display.print_header('Cross-Mall Comparison Report')

        reports = ReportService.get_all_malls_report()

        print()
        print(f'  Generated: {bold(Display.fmt_currency(0).replace("R0.00", ReportService.fmt_datetime(__import__("datetime").datetime.now().isoformat())))}')
        print()

        # Revenue comparison
        Display.print_subheader('REVENUE COMPARISON')
        max_rev = max((r['total_revenue'] for r in reports), default=1) or 1
        for r in reports:
            bar_len = round((r['total_revenue'] / max_rev) * 30)
            bar     = '█' * bar_len
            print(f'  {r["mall"]["name"][:35]:<35}  '
                  f'{cyan(bar):<30}  '
                  f'{bold(Display.fmt_currency(r["total_revenue"]))}')
        print()

        # Volume comparison
        Display.print_subheader('VEHICLE VOLUME COMPARISON')
        max_vol = max((r['total_vehicles'] for r in reports), default=1) or 1
        for r in reports:
            bar_len = round((r['total_vehicles'] / max_vol) * 30)
            bar     = '█' * bar_len
            print(f'  {r["mall"]["name"][:35]:<35}  '
                  f'{yellow(bar):<30}  '
                  f'{bold(str(r["total_vehicles"]))} visits')
        print()

        # Detailed comparison table
        Display.print_subheader('DETAILED METRICS')
        Display.print_table(
            ['Mall', 'Pricing Model', 'Total Visits', 'Active Now', 'Revenue', 'Avg Duration', 'Occ %'],
            [
                [
                    r['mall']['name'],
                    r['pricing_name'],
                    str(r['total_vehicles']),
                    str(r['active_vehicles']),
                    Display.fmt_currency(r['total_revenue']),
                    ReportService.fmt_duration(r['avg_duration']),
                    f'{r["occupancy"]["percent"]}%',
                ]
                for r in reports
            ],
            highlight_col=4
        )

        # Pricing rules summary
        Display.print_subheader('PRICING RULES SUMMARY')
        for r in reports:
            mall = r['mall']
            print(f'  {bold(mall["name"])}')
            print(f'    Pricing model : {r["pricing_name"]}')
            print(f'    Policy        : {ParkingService.get_pricing_label(mall)}')
            print(f'    Capacity      : {mall["capacity"]} vehicles')
            print()

        # Revenue last 7 days per mall
        Display.print_subheader('REVENUE — LAST 7 DAYS')
        # Collect all dates
        dates = sorted(reports[0]['daily_revenue'].keys()) if reports else []
        header = ['Mall'] + [d[5:] for d in dates]  # 'MM-DD' format
        rows = []
        for r in reports:
            name_short = r['mall']['name'].split()[0]  # first word
            daily_vals = [Display.fmt_currency(r['daily_revenue'].get(d, 0)) for d in dates]
            rows.append([name_short] + daily_vals)
        if rows:
            Display.print_table(header, rows)

        Display.press_enter()

    # ── Per-Mall Detailed Report ──────────────────────────────────────────────

    def _mall_detail(self, mall_id: str):
        """Detailed report for a single mall."""
        Display.clear()
        Display.print_banner()

        report = ReportService.get_mall_report(mall_id)
        if report is None:
            Display.print_error('Mall not found.')
            Display.press_enter()
            return

        mall = report['mall']
        occ  = report['occupancy']

        Display.print_header(f'Detailed Report — {mall["name"]}')

        print()
        print(f'  {bold("Mall")}         : {cyan(mall["name"])}')
        print(f'  {bold("Location")}     : {mall["location"]}')
        print(f'  {bold("Pricing Model")}: {report["pricing_name"]}')
        print(f'  {bold("Pricing Policy")}: {ParkingService.get_pricing_label(mall)}')
        print(f'  {bold("Capacity")}     : {mall["capacity"]} vehicles')
        print()

        # Key Stats
        Display.print_subheader('KEY STATISTICS')
        Display.print_table(
            ['Metric', 'Value'],
            [
                ['Total Visits (All Time)',       str(report['total_vehicles'])],
                ['Completed Sessions',            str(report['completed_count'])],
                ['Currently Active / Parked',     str(report['active_vehicles'])],
                ['Paid Sessions',                 str(report['paid_count'])],
                ['Total Revenue Generated',       Display.fmt_currency(report['total_revenue'])],
                ['Average Parking Duration',      ReportService.fmt_duration(report['avg_duration'])],
                ['Current Occupancy Rate',        f'{occ["percent"]}%'],
                ['Bays Available Now',            str(occ['available'])],
            ]
        )

        # Live capacity bar
        Display.print_subheader('LIVE CAPACITY')
        Display.print_progress_bar(occ['percent'], occ['active'], occ['capacity'])
        print()

        # Revenue last 7 days
        Display.print_subheader('REVENUE — LAST 7 DAYS')
        if report['daily_revenue']:
            max_val = max(report['daily_revenue'].values(), default=1) or 1
            for date, amount in sorted(report['daily_revenue'].items()):
                bar_len = round((amount / max_val) * 25) if max_val > 0 else 0
                bar     = '█' * bar_len
                date_lbl = date[5:]  # MM-DD
                print(f'    {date_lbl}  {cyan(f"{bar:<25}")}  {Display.fmt_currency(amount)}')
        print()

        # Recent sessions
        Display.print_subheader('RECENT COMPLETED SESSIONS (Last 10)')
        if not report['recent_sessions']:
            Display.print_info('No completed sessions on record.')
        else:
            rows = []
            for s in report['recent_sessions']:
                rows.append([
                    s['license_plate'],
                    ReportService.fmt_datetime(s['entry_time']),
                    ReportService.fmt_datetime(s['exit_time']),
                    ReportService.fmt_duration(s.get('duration_minutes')),
                    s.get('pricing_label', '—'),
                    Display.fmt_currency(s.get('fee')),
                    'Yes' if s.get('paid') else 'No',
                ])
            Display.print_table(
                ['Plate', 'Entry', 'Exit', 'Duration', 'Pricing Applied', 'Fee', 'Paid'],
                rows,
                highlight_col=5
            )

        Display.press_enter()
