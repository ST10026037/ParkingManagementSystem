"""
services/data_service.py
─────────────────────────────────────────────────────────────────────────────
Data Layer — JSON file read/write, CRUD helpers, and seed data initialisation.
KZN Smart Mall Parking Management System
─────────────────────────────────────────────────────────────────────────────
"""

import hashlib
import json
import os
import random
import string
from datetime import datetime, timedelta

# ─── Paths ────────────────────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')

_FILES = {
    'users':    os.path.join(DATA_DIR, 'users.json'),
    'malls':    os.path.join(DATA_DIR, 'malls.json'),
    'sessions': os.path.join(DATA_DIR, 'sessions.json'),
    'payments': os.path.join(DATA_DIR, 'payments.json'),
    'meta':     os.path.join(DATA_DIR, 'meta.json'),
}


# ─── Low-level JSON I/O ───────────────────────────────────────────────────────

def _load(key: str) -> list:
    """Load and return a list from the corresponding JSON file."""
    path = _FILES[key]
    if not os.path.exists(path):
        return []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, IOError):
        return []


def _save(key: str, records: list) -> None:
    """Save a list of records to the corresponding JSON file."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(_FILES[key], 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2, ensure_ascii=False)


def _load_meta() -> dict:
    path = _FILES['meta']
    if not os.path.exists(path):
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def _save_meta(meta: dict) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(_FILES['meta'], 'w', encoding='utf-8') as f:
        json.dump(meta, f, indent=2)


# ─── ID Generator ──────────────────────────────────────────────────────────────

def generate_id(prefix: str = '') -> str:
    """Generate a short unique ID."""
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    ts = datetime.now().strftime('%f')
    return f"{prefix}{ts[:4]}{suffix}"


# ─── Generic CRUD ─────────────────────────────────────────────────────────────

class DataService:
    """Provides all CRUD operations for every data entity."""

    # ── Users ──────────────────────────────────────────────────────────────

    @staticmethod
    def get_all_users() -> list:
        return _load('users')

    @staticmethod
    def get_user_by_id(user_id: str) -> dict | None:
        return next((u for u in _load('users') if u['id'] == user_id), None)

    @staticmethod
    def get_user_by_email(email: str) -> dict | None:
        return next(
            (u for u in _load('users') if u['email'].lower() == email.lower()),
            None
        )

    @staticmethod
    def insert_user(user: dict) -> dict:
        users = _load('users')
        if 'id' not in user:
            user['id'] = generate_id('usr_')
        users.append(user)
        _save('users', users)
        return user

    # ── Malls ──────────────────────────────────────────────────────────────

    @staticmethod
    def get_all_malls() -> list:
        return _load('malls')

    @staticmethod
    def get_mall_by_id(mall_id: str) -> dict | None:
        return next((m for m in _load('malls') if m['id'] == mall_id), None)

    # ── Sessions ───────────────────────────────────────────────────────────

    @staticmethod
    def get_all_sessions() -> list:
        return _load('sessions')

    @staticmethod
    def get_session_by_id(session_id: str) -> dict | None:
        return next((s for s in _load('sessions') if s['id'] == session_id), None)

    @staticmethod
    def get_sessions_by_customer(customer_id: str) -> list:
        return [s for s in _load('sessions') if s['customer_id'] == customer_id]

    @staticmethod
    def get_sessions_by_mall(mall_id: str) -> list:
        return [s for s in _load('sessions') if s['mall_id'] == mall_id]

    @staticmethod
    def get_active_sessions() -> list:
        return [s for s in _load('sessions') if s['status'] == 'active']

    @staticmethod
    def get_active_sessions_by_mall(mall_id: str) -> list:
        return [s for s in _load('sessions') if s['mall_id'] == mall_id and s['status'] == 'active']

    @staticmethod
    def get_active_sessions_by_customer(customer_id: str) -> list:
        return [s for s in _load('sessions') if s['customer_id'] == customer_id and s['status'] == 'active']

    @staticmethod
    def get_sessions_by_mall_and_date(mall_id: str, date_str: str) -> list:
        """date_str format: 'YYYY-MM-DD'"""
        result = []
        for s in _load('sessions'):
            if s['mall_id'] != mall_id:
                continue
            entry_date = s['entry_time'][:10]  # 'YYYY-MM-DD'
            if entry_date == date_str:
                result.append(s)
        return result

    @staticmethod
    def insert_session(session: dict) -> dict:
        sessions = _load('sessions')
        if 'id' not in session:
            session['id'] = generate_id('ses_')
        sessions.append(session)
        _save('sessions', sessions)
        return session

    @staticmethod
    def update_session(session_id: str, updates: dict) -> dict | None:
        sessions = _load('sessions')
        for i, s in enumerate(sessions):
            if s['id'] == session_id:
                sessions[i].update(updates)
                _save('sessions', sessions)
                return sessions[i]
        return None

    # ── Payments ───────────────────────────────────────────────────────────

    @staticmethod
    def get_all_payments() -> list:
        return _load('payments')

    @staticmethod
    def get_payments_by_customer(customer_id: str) -> list:
        return [p for p in _load('payments') if p['customer_id'] == customer_id]

    @staticmethod
    def get_payments_by_mall(mall_id: str) -> list:
        return [p for p in _load('payments') if p['mall_id'] == mall_id]

    @staticmethod
    def get_payment_by_session(session_id: str) -> dict | None:
        return next((p for p in _load('payments') if p['session_id'] == session_id), None)

    @staticmethod
    def insert_payment(payment: dict) -> dict:
        payments = _load('payments')
        if 'id' not in payment:
            payment['id'] = generate_id('pay_')
        payments.append(payment)
        _save('payments', payments)
        return payment

    # ─── Initialisation & Seeding ─────────────────────────────────────────

    @staticmethod
    def initialise() -> None:
        """
        Initialise the data layer.
        Seeds all JSON files on the very first run.
        On subsequent runs, existing data is preserved.
        """
        os.makedirs(DATA_DIR, exist_ok=True)
        meta = _load_meta()
        if meta.get('initialised'):
            return  # Data already seeded — do nothing

        DataService._seed()
        _save_meta({'initialised': True, 'seeded_at': datetime.now().isoformat()})
        print("  [System] First-run setup complete. Data initialised.")

    @staticmethod
    def _hash(password: str) -> str:
        return hashlib.sha256(password.encode('utf-8')).hexdigest()

    @staticmethod
    def _seed() -> None:
        """Load all initial seed data."""

        # ── Malls ──────────────────────────────────────────────────────────
        malls = [
            {
                'id': 'mall_gateway',
                'name': 'Gateway Theatre of Shopping',
                'location': 'Umhlanga, Durban',
                'capacity': 250,
                'pricing_type': 'flat',
                'pricing_config': {'flat_rate': 15.0},
            },
            {
                'id': 'mall_pavilion',
                'name': 'Pavilion Shopping Centre',
                'location': 'Westville, Durban',
                'capacity': 180,
                'pricing_type': 'hourly',
                'pricing_config': {'hourly_rate': 10.0},
            },
            {
                'id': 'mall_lucia',
                'name': 'La Lucia Mall',
                'location': 'La Lucia, Durban',
                'capacity': 150,
                'pricing_type': 'capped_hourly',
                'pricing_config': {'hourly_rate': 12.0, 'daily_cap': 60.0},
            },
        ]
        _save('malls', malls)

        # ── Users ──────────────────────────────────────────────────────────
        owner_pw  = DataService._hash('Owner@123')
        admin_pw  = DataService._hash('Admin@123')
        demo_pw   = DataService._hash('Demo@123')

        users = [
            # Owner / Shareholder
            {
                'id': 'user_owner',
                'name': 'Thabo Nkosi',
                'email': 'owner@kznmalls.co.za',
                'password_hash': owner_pw,
                'role': 'owner',
                'mall_id': None,
                'created_at': '2025-01-01T08:00:00',
            },
            # Parking Administrators (one per mall)
            {
                'id': 'user_admin_gateway',
                'name': 'Priya Govender',
                'email': 'admin.gateway@kzn.co.za',
                'password_hash': admin_pw,
                'role': 'admin',
                'mall_id': 'mall_gateway',
                'created_at': '2025-01-01T08:00:00',
            },
            {
                'id': 'user_admin_pavilion',
                'name': 'Sipho Dlamini',
                'email': 'admin.pavilion@kzn.co.za',
                'password_hash': admin_pw,
                'role': 'admin',
                'mall_id': 'mall_pavilion',
                'created_at': '2025-01-01T08:00:00',
            },
            {
                'id': 'user_admin_lucia',
                'name': 'Fatima Moosa',
                'email': 'admin.lucia@kzn.co.za',
                'password_hash': admin_pw,
                'role': 'admin',
                'mall_id': 'mall_lucia',
                'created_at': '2025-01-01T08:00:00',
            },
            # Demo Customers
            {
                'id': 'user_demo1',
                'name': 'Zanele Mthembu',
                'email': 'zanele@demo.co.za',
                'password_hash': demo_pw,
                'role': 'customer',
                'mall_id': None,
                'created_at': '2025-06-01T09:00:00',
            },
            {
                'id': 'user_demo2',
                'name': 'Rajan Pillay',
                'email': 'rajan@demo.co.za',
                'password_hash': demo_pw,
                'role': 'customer',
                'mall_id': None,
                'created_at': '2025-06-15T09:00:00',
            },
        ]
        _save('users', users)

        # ── Sessions (demo history) ─────────────────────────────────────────
        sessions = [
            # Zanele — Gateway (flat rate, 2h 30m)
            {
                'id': 'ses_demo01',
                'customer_id': 'user_demo1',
                'mall_id': 'mall_gateway',
                'license_plate': 'NDE 123 GP',
                'entry_time': '2026-04-08T09:00:00',
                'exit_time':  '2026-04-08T11:30:00',
                'duration_minutes': 150,
                'fee': 15.0,
                'pricing_label': 'Flat Rate – R15.00 per visit',
                'pricing_breakdown': 'Duration parked: 2h 30m | Fixed charge: R15.00 (duration does not affect the fee)',
                'status': 'completed',
                'paid': True,
            },
            # Zanele — Pavilion (hourly, 90 min = 2 hrs = R20)
            {
                'id': 'ses_demo02',
                'customer_id': 'user_demo1',
                'mall_id': 'mall_pavilion',
                'license_plate': 'NDE 123 GP',
                'entry_time': '2026-04-07T10:00:00',
                'exit_time':  '2026-04-07T11:30:00',
                'duration_minutes': 90,
                'fee': 20.0,
                'pricing_label': 'Hourly Rate – R10.00/hr',
                'pricing_breakdown': 'Duration parked: 1h 30m | Billable hours: 2 × R10.00 = R20.00',
                'status': 'completed',
                'paid': True,
            },
            # Rajan — La Lucia (capped hourly, 7h 30m → 8 hrs × R12 = R96 → cap R60)
            {
                'id': 'ses_demo03',
                'customer_id': 'user_demo2',
                'mall_id': 'mall_lucia',
                'license_plate': 'KZN 456 NP',
                'entry_time': '2026-04-06T08:00:00',
                'exit_time':  '2026-04-06T15:30:00',
                'duration_minutes': 450,
                'fee': 60.0,
                'pricing_label': 'R12.00/hr (capped at R60.00)',
                'pricing_breakdown': 'Duration parked: 7h 30m | 8 hrs × R12.00 = R96.00 | Daily cap applied → R60.00',
                'status': 'completed',
                'paid': True,
            },
            # Rajan — Gateway (flat rate, 1h 45m)
            {
                'id': 'ses_demo04',
                'customer_id': 'user_demo2',
                'mall_id': 'mall_gateway',
                'license_plate': 'KZN 456 NP',
                'entry_time': '2026-04-05T13:00:00',
                'exit_time':  '2026-04-05T14:45:00',
                'duration_minutes': 105,
                'fee': 15.0,
                'pricing_label': 'Flat Rate – R15.00 per visit',
                'pricing_breakdown': 'Duration parked: 1h 45m | Fixed charge: R15.00 (duration does not affect the fee)',
                'status': 'completed',
                'paid': True,
            },
            # Zanele — La Lucia (capped hourly, 2h → 2 × R12 = R24, no cap)
            {
                'id': 'ses_demo05',
                'customer_id': 'user_demo1',
                'mall_id': 'mall_lucia',
                'license_plate': 'NDE 123 GP',
                'entry_time': '2026-04-04T14:00:00',
                'exit_time':  '2026-04-04T16:00:00',
                'duration_minutes': 120,
                'fee': 24.0,
                'pricing_label': 'R12.00/hr',
                'pricing_breakdown': 'Duration parked: 2h | 2 hrs × R12.00 = R24.00',
                'status': 'completed',
                'paid': True,
            },
        ]
        _save('sessions', sessions)

        # ── Payments (demo) ────────────────────────────────────────────────
        payments = [
            {'id': 'pay_demo01', 'session_id': 'ses_demo01', 'customer_id': 'user_demo1',
             'mall_id': 'mall_gateway',  'amount': 15.0, 'method': 'card',
             'timestamp': '2026-04-08T11:32:00'},
            {'id': 'pay_demo02', 'session_id': 'ses_demo02', 'customer_id': 'user_demo1',
             'mall_id': 'mall_pavilion', 'amount': 20.0, 'method': 'card',
             'timestamp': '2026-04-07T11:35:00'},
            {'id': 'pay_demo03', 'session_id': 'ses_demo03', 'customer_id': 'user_demo2',
             'mall_id': 'mall_lucia',    'amount': 60.0, 'method': 'cash',
             'timestamp': '2026-04-06T15:33:00'},
            {'id': 'pay_demo04', 'session_id': 'ses_demo04', 'customer_id': 'user_demo2',
             'mall_id': 'mall_gateway',  'amount': 15.0, 'method': 'card',
             'timestamp': '2026-04-05T14:48:00'},
            {'id': 'pay_demo05', 'session_id': 'ses_demo05', 'customer_id': 'user_demo1',
             'mall_id': 'mall_lucia',    'amount': 24.0, 'method': 'card',
             'timestamp': '2026-04-04T16:03:00'},
        ]
        _save('payments', payments)
