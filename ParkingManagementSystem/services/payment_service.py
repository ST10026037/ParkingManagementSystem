"""
services/payment_service.py
─────────────────────────────────────────────────────────────────────────────
Payment processing — recording payments, customer history, mall revenue.
KZN Smart Mall Parking Management System
─────────────────────────────────────────────────────────────────────────────
"""

from datetime import datetime
from services.data_service import DataService


class PaymentService:
    """Handles payment processing and payment record retrieval."""

    METHODS = {
        '1': 'card',
        '2': 'cash',
    }
    METHOD_LABELS = {
        'card': 'Card Payment',
        'cash': 'Cash Payment',
    }

    # ── Process Payment ────────────────────────────────────────────────────────

    @staticmethod
    def pay(session_id: str, method: str = 'card') -> dict:
        """
        Process payment for a completed (exited) parking session.

        Args:
            session_id (str): ID of the completed session.
            method     (str): 'card' or 'cash'.

        Returns:
            dict – { 'success': bool, 'payment'?: dict, 'error'?: str }
        """
        session = DataService.get_session_by_id(session_id)
        if session is None:
            return {'success': False, 'error': 'Session not found.'}
        if session['status'] != 'completed':
            return {'success': False, 'error': 'Vehicle must exit the mall before payment can be processed.'}
        if session.get('paid'):
            existing = DataService.get_payment_by_session(session_id)
            return {'success': False, 'error': 'This session has already been paid.', 'payment': existing}

        payment = DataService.insert_payment({
            'session_id':   session_id,
            'customer_id':  session['customer_id'],
            'mall_id':      session['mall_id'],
            'amount':       session['fee'],
            'method':       method,
            'timestamp':    datetime.now().isoformat(),
        })

        # Mark session as paid
        DataService.update_session(session_id, {'paid': True})

        return {'success': True, 'payment': payment}

    # ── Customer History ───────────────────────────────────────────────────────

    @staticmethod
    def get_customer_history(customer_id: str) -> list:
        """
        Return a customer's full payment history enriched with session & mall data.

        Returns:
            list of dicts, sorted newest-first.
        """
        payments = DataService.get_payments_by_customer(customer_id)
        enriched = []
        for p in payments:
            session = DataService.get_session_by_id(p['session_id'])
            mall    = DataService.get_mall_by_id(p['mall_id'])
            enriched.append({**p, 'session': session, 'mall': mall})
        return sorted(enriched, key=lambda x: x['timestamp'], reverse=True)

    # ── Mall Revenue Summary ───────────────────────────────────────────────────

    @staticmethod
    def get_mall_summary(mall_id: str) -> dict:
        """
        Return payment summary for a mall (used in reports).

        Returns:
            dict – { 'total_revenue': float, 'total_payments': int, 'payments': list }
        """
        payments = DataService.get_payments_by_mall(mall_id)
        total_revenue = sum(p['amount'] for p in payments)
        return {
            'total_revenue':  total_revenue,
            'total_payments': len(payments),
            'payments':       sorted(payments, key=lambda x: x['timestamp'], reverse=True),
        }
