"""
services/parking_service.py
─────────────────────────────────────────────────────────────────────────────
Parking operations — vehicle entry, exit preview, exit finalisation,
capacity monitoring, and duration formatting.
KZN Smart Mall Parking Management System
─────────────────────────────────────────────────────────────────────────────
"""

import math
from datetime import datetime
from services.data_service import DataService
from pricing.strategies import calculate_fee, get_pricing_strategy


class ParkingService:
    """Handles all vehicle entry/exit operations and fee calculations."""

    # ── Entry ──────────────────────────────────────────────────────────────────

    @staticmethod
    def enter(customer_id: str, mall_id: str, license_plate: str) -> dict:
        """
        Register a vehicle entering a mall parking area.

        Checks:
          - License plate is provided
          - Customer has no existing active session at this mall
          - Mall has available capacity

        Returns:
            dict – { 'success': bool, 'session'?: dict, 'error'?: str }
        """
        plate = license_plate.strip().upper() if license_plate else ''
        if len(plate) < 2:
            return {'success': False, 'error': 'Please enter a valid licence plate number.'}

        mall = DataService.get_mall_by_id(mall_id)
        if mall is None:
            return {'success': False, 'error': 'Mall not found.'}

        # Check for existing active session at this mall
        existing = [
            s for s in DataService.get_active_sessions_by_customer(customer_id)
            if s['mall_id'] == mall_id
        ]
        if existing:
            return {
                'success': False,
                'error': f'You already have an active parking session at {mall["name"]}.'
            }

        # Capacity check
        active_count = len(DataService.get_active_sessions_by_mall(mall_id))
        if active_count >= mall['capacity']:
            return {
                'success': False,
                'error': (
                    f'{mall["name"]} is at full capacity '
                    f'({mall["capacity"]} vehicles). No bays available.'
                )
            }

        session = DataService.insert_session({
            'customer_id': customer_id,
            'mall_id': mall_id,
            'license_plate': plate,
            'entry_time': datetime.now().isoformat(),
            'exit_time': None,
            'duration_minutes': None,
            'fee': None,
            'pricing_label': None,
            'pricing_breakdown': None,
            'status': 'active',
            'paid': False,
        })
        return {'success': True, 'session': session}

    # ── Exit Preview ───────────────────────────────────────────────────────────

    @staticmethod
    def preview_exit(session_id: str) -> dict:
        """
        Calculate the fee for an active session without finalising the exit.
        Used to show the amount due before the customer confirms payment.

        Returns:
            dict – {
                'success': bool,
                'session': dict, 'mall': dict,
                'entry_time': datetime, 'exit_time': datetime,
                'duration_minutes': int,
                'amount': float, 'label': str, 'breakdown': str,
                'error'?: str
            }
        """
        session = DataService.get_session_by_id(session_id)
        if session is None:
            return {'success': False, 'error': 'Session not found.'}
        if session['status'] != 'active':
            return {'success': False, 'error': 'This session is not currently active.'}

        mall = DataService.get_mall_by_id(session['mall_id'])
        if mall is None:
            return {'success': False, 'error': 'Mall record not found.'}

        entry_time = datetime.fromisoformat(session['entry_time'])
        exit_time  = datetime.now()
        duration   = max(1, math.ceil((exit_time - entry_time).total_seconds() / 60))

        fee_result = calculate_fee(mall, duration)

        return {
            'success': True,
            'session': session,
            'mall': mall,
            'entry_time': entry_time,
            'exit_time': exit_time,
            'duration_minutes': duration,
            **fee_result,
        }

    # ── Exit ───────────────────────────────────────────────────────────────────

    @staticmethod
    def exit_mall(session_id: str) -> dict:
        """
        Finalise vehicle exit: record exit time, duration, and calculated fee.

        Returns:
            dict – { 'success': bool, 'session'?: dict, 'error'?: str }
        """
        session = DataService.get_session_by_id(session_id)
        if session is None:
            return {'success': False, 'error': 'Session not found.'}
        if session['status'] != 'active':
            return {'success': False, 'error': 'This session is not currently active.'}

        mall = DataService.get_mall_by_id(session['mall_id'])
        entry_time = datetime.fromisoformat(session['entry_time'])
        exit_time  = datetime.now()
        duration   = max(1, math.ceil((exit_time - entry_time).total_seconds() / 60))
        fee_result = calculate_fee(mall, duration)

        updated = DataService.update_session(session_id, {
            'exit_time':         exit_time.isoformat(),
            'duration_minutes':  duration,
            'fee':               fee_result['amount'],
            'pricing_label':     fee_result['label'],
            'pricing_breakdown': fee_result['breakdown'],
            'status':            'completed',
        })
        return {'success': True, 'session': updated}

    # ── Occupancy ──────────────────────────────────────────────────────────────

    @staticmethod
    def get_occupancy(mall_id: str) -> dict | None:
        """
        Return live occupancy statistics for a mall.

        Returns:
            dict – { 'active': int, 'capacity': int, 'available': int, 'percent': int }
        """
        mall = DataService.get_mall_by_id(mall_id)
        if mall is None:
            return None
        active    = len(DataService.get_active_sessions_by_mall(mall_id))
        available = max(0, mall['capacity'] - active)
        percent   = round((active / mall['capacity']) * 100) if mall['capacity'] else 0
        return {
            'active':    active,
            'capacity':  mall['capacity'],
            'available': available,
            'percent':   percent,
        }

    # ── Helpers ────────────────────────────────────────────────────────────────

    @staticmethod
    def format_duration(minutes) -> str:
        """Convert minutes to a human-readable string like '1h 30m'."""
        if minutes is None:
            return '—'
        minutes = int(minutes)
        h, m = divmod(minutes, 60)
        if h > 0 and m > 0:
            return f'{h}h {m}m'
        elif h > 0:
            return f'{h}h'
        else:
            return f'{m}m'

    @staticmethod
    def get_pricing_label(mall: dict) -> str:
        """Return a short description of a mall's pricing policy."""
        pt = mall.get('pricing_type')
        pc = mall.get('pricing_config', {})
        if pt == 'flat':
            return f"R{pc.get('flat_rate', 0):.2f} per visit (flat rate)"
        elif pt == 'hourly':
            return f"R{pc.get('hourly_rate', 0):.2f}/hr (hourly)"
        elif pt == 'capped_hourly':
            return (
                f"R{pc.get('hourly_rate', 0):.2f}/hr, "
                f"capped at R{pc.get('daily_cap', 0):.2f}"
            )
        return 'Custom pricing'
