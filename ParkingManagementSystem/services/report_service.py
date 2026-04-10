"""
services/report_service.py
─────────────────────────────────────────────────────────────────────────────
Report generation — per-mall reports, cross-mall comparison, system summary.
KZN Smart Mall Parking Management System
─────────────────────────────────────────────────────────────────────────────
"""

from datetime import datetime, timedelta
from services.data_service import DataService
from services.parking_service import ParkingService
from pricing.strategies import get_pricing_strategy


class ReportService:
    """Generates management reports for malls and owners."""

    # ── Per-Mall Report ────────────────────────────────────────────────────────

    @staticmethod
    def get_mall_report(mall_id: str) -> dict | None:
        """
        Generate a complete report for a single mall.

        Returns:
            dict or None if mall not found.
        """
        mall = DataService.get_mall_by_id(mall_id)
        if mall is None:
            return None

        all_sessions   = DataService.get_sessions_by_mall(mall_id)
        completed      = [s for s in all_sessions if s['status'] == 'completed']
        active         = [s for s in all_sessions if s['status'] == 'active']
        paid_completed = [s for s in completed if s.get('paid')]

        total_vehicles = len(all_sessions)
        total_revenue  = sum(s.get('fee', 0) or 0 for s in paid_completed)

        durations = [s['duration_minutes'] for s in completed if s.get('duration_minutes') is not None]
        avg_duration = round(sum(durations) / len(durations)) if durations else 0

        # Daily revenue – last 7 days
        daily_revenue = {}
        for i in range(6, -1, -1):
            d = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            daily_revenue[d] = 0.0
        for s in paid_completed:
            if s.get('exit_time'):
                day = s['exit_time'][:10]
                if day in daily_revenue:
                    daily_revenue[day] += s.get('fee', 0) or 0

        occupancy = ParkingService.get_occupancy(mall_id)
        strategy  = get_pricing_strategy(mall)

        today_str     = datetime.now().strftime('%Y-%m-%d')
        today_sessions = DataService.get_sessions_by_mall_and_date(mall_id, today_str)

        return {
            'mall':             mall,
            'total_vehicles':   total_vehicles,
            'active_vehicles':  len(active),
            'completed_count':  len(completed),
            'paid_count':       len(paid_completed),
            'total_revenue':    total_revenue,
            'avg_duration':     avg_duration,
            'occupancy':        occupancy,
            'daily_revenue':    daily_revenue,
            'pricing_name':     strategy.display_name,
            'pricing_label':    ParkingService.get_pricing_label(mall),
            'today_sessions':   today_sessions,
            'recent_sessions':  sorted(completed, key=lambda s: s.get('exit_time', ''), reverse=True)[:10],
        }

    # ── Cross-Mall Comparison ──────────────────────────────────────────────────

    @staticmethod
    def get_all_malls_report() -> list:
        """
        Generate reports for ALL malls.

        Returns:
            list of mall report dicts.
        """
        return [ReportService.get_mall_report(m['id']) for m in DataService.get_all_malls()]

    # ── System Summary ─────────────────────────────────────────────────────────

    @staticmethod
    def get_system_summary() -> dict:
        """
        Generate a high-level overview of the entire system.

        Returns:
            dict with aggregated statistics across all malls.
        """
        mall_reports  = ReportService.get_all_malls_report()
        total_revenue = sum(r['total_revenue'] for r in mall_reports)
        total_vehicles = sum(r['total_vehicles'] for r in mall_reports)
        total_active  = sum(r['active_vehicles'] for r in mall_reports)

        top_revenue = max(mall_reports, key=lambda r: r['total_revenue'], default=None)
        top_volume  = max(mall_reports, key=lambda r: r['total_vehicles'], default=None)

        return {
            'total_revenue':     total_revenue,
            'total_vehicles':    total_vehicles,
            'total_active':      total_active,
            'mall_count':        len(mall_reports),
            'top_by_revenue':    top_revenue,
            'top_by_volume':     top_volume,
            'mall_reports':      mall_reports,
        }

    # ── Formatting Helpers ─────────────────────────────────────────────────────

    @staticmethod
    def fmt_currency(amount) -> str:
        """Format a number as South African Rands."""
        return f'R{(amount or 0):.2f}'

    @staticmethod
    def fmt_date(iso_str: str) -> str:
        """Format an ISO datetime string as 'DD Mon YYYY'."""
        if not iso_str:
            return '—'
        try:
            return datetime.fromisoformat(iso_str).strftime('%d %b %Y')
        except ValueError:
            return iso_str[:10]

    @staticmethod
    def fmt_datetime(iso_str: str) -> str:
        """Format an ISO datetime string as 'DD Mon YYYY HH:MM'."""
        if not iso_str:
            return '—'
        try:
            return datetime.fromisoformat(iso_str).strftime('%d %b %Y %H:%M')
        except ValueError:
            return iso_str[:16]

    @staticmethod
    def fmt_duration(minutes) -> str:
        return ParkingService.format_duration(minutes)
