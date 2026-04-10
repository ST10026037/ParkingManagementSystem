"""
services/auth_service.py
─────────────────────────────────────────────────────────────────────────────
Authentication — login, registration, and password hashing.
KZN Smart Mall Parking Management System
─────────────────────────────────────────────────────────────────────────────
"""

import hashlib
from services.data_service import DataService


class AuthService:
    """Handles user authentication and registration."""

    @staticmethod
    def _hash(password: str) -> str:
        """Return SHA-256 hex digest of a password string."""
        return hashlib.sha256(password.encode('utf-8')).hexdigest()

    # ── Login ─────────────────────────────────────────────────────────────────

    def login(self, email: str, password: str) -> dict:
        """
        Attempt to log in with email and password.

        Returns:
            dict – { 'success': bool, 'user'?: dict, 'error'?: str }
        """
        if not email or not email.strip():
            return {'success': False, 'error': 'Email address is required.'}
        if not password:
            return {'success': False, 'error': 'Password is required.'}

        user = DataService.get_user_by_email(email.strip())
        if user is None:
            return {'success': False, 'error': 'No account found with that email address.'}

        if user['password_hash'] != self._hash(password):
            return {'success': False, 'error': 'Incorrect password. Please try again.'}

        return {'success': True, 'user': user}

    # ── Registration ──────────────────────────────────────────────────────────

    def register(self, name: str, email: str, password: str, confirm_password: str) -> dict:
        """
        Register a new customer account.

        Returns:
            dict – { 'success': bool, 'user'?: dict, 'error'?: str }
        """
        # Validation
        if not name or not name.strip():
            return {'success': False, 'error': 'Full name is required.'}
        if not email or not email.strip():
            return {'success': False, 'error': 'Email address is required.'}
        if not password:
            return {'success': False, 'error': 'Password is required.'}
        if len(password) < 6:
            return {'success': False, 'error': 'Password must be at least 6 characters.'}
        if password != confirm_password:
            return {'success': False, 'error': 'Passwords do not match.'}
        if '@' not in email or '.' not in email.split('@')[-1]:
            return {'success': False, 'error': 'Please enter a valid email address.'}

        # Check for duplicate
        if DataService.get_user_by_email(email.strip()) is not None:
            return {'success': False, 'error': 'An account with this email already exists.'}

        from datetime import datetime
        user = DataService.insert_user({
            'name': name.strip(),
            'email': email.strip().lower(),
            'password_hash': self._hash(password),
            'role': 'customer',
            'mall_id': None,
            'created_at': datetime.now().isoformat(),
        })

        return {'success': True, 'user': user}
