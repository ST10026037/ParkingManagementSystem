"""
pricing/strategies.py
─────────────────────────────────────────────────────────────────────────────
Pricing Strategy Pattern — KZN Smart Mall Parking Management System

All pricing logic lives here. Each mall's fee policy is an independent class
that inherits from PricingStrategy and implements calculate().

To add a new pricing model in the future:
  1. Create a new subclass of PricingStrategy
  2. Implement calculate(duration_minutes) -> dict
  3. Register it in PRICING_CLASSES with a new key string
  4. Create a mall record in the data layer with that pricing_type
  No other code changes are required.
─────────────────────────────────────────────────────────────────────────────
"""

import math
from abc import ABC, abstractmethod


# ─── Abstract Base ────────────────────────────────────────────────────────────

class PricingStrategy(ABC):
    """Abstract base class that all pricing strategies must implement."""

    @abstractmethod
    def calculate(self, duration_minutes: int) -> dict:
        """
        Calculate the parking fee for a given duration.

        Args:
            duration_minutes (int): Total time parked in minutes (minimum 1).

        Returns:
            dict with keys:
                amount      (float) – Amount due in ZAR
                label       (str)   – Short description for receipts/reports
                breakdown   (str)   – Detailed fee calculation explanation
        """
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable name shown on receipts and reports."""
        pass

    @staticmethod
    def _format_duration(minutes: int) -> str:
        """Convert minutes to 'Xh Ym' string."""
        h, m = divmod(int(minutes), 60)
        if h > 0 and m > 0:
            return f"{h}h {m}m"
        elif h > 0:
            return f"{h}h"
        else:
            return f"{m}m"


# ─── Mall 1: Gateway Theatre of Shopping ─────────────────────────────────────
# Flat Rate: R15.00 per visit (regardless of duration)

class FlatRatePricing(PricingStrategy):
    """
    Flat rate pricing: a single fixed fee per visit, regardless of how
    long the vehicle is parked.

    Config keys:
        flat_rate (float): Fee per visit in ZAR.

    Example:
        Gateway Theatre of Shopping — R15.00 per visit.
    """

    def __init__(self, config: dict):
        self.flat_rate: float = config['flat_rate']

    @property
    def display_name(self) -> str:
        return 'Flat Rate'

    def calculate(self, duration_minutes: int) -> dict:
        dur = self._format_duration(duration_minutes)
        return {
            'amount': self.flat_rate,
            'label': f'Flat Rate – R{self.flat_rate:.2f} per visit',
            'breakdown': (
                f'Duration parked: {dur} | '
                f'Fixed charge: R{self.flat_rate:.2f} (duration does not affect the fee)'
            ),
        }


# ─── Mall 2: Pavilion Shopping Centre ────────────────────────────────────────
# Hourly Rate: R10.00 per hour (or part thereof)

class HourlyRatePricing(PricingStrategy):
    """
    Hourly rate pricing: charged per hour or part thereof (ceiling).

    Config keys:
        hourly_rate (float): Fee per hour in ZAR.

    Example:
        Pavilion Shopping Centre — R10.00/hr
        90 minutes → 2 billable hours → R20.00
    """

    def __init__(self, config: dict):
        self.hourly_rate: float = config['hourly_rate']

    @property
    def display_name(self) -> str:
        return 'Hourly Rate'

    def calculate(self, duration_minutes: int) -> dict:
        billable_hours = math.ceil(duration_minutes / 60)
        amount = billable_hours * self.hourly_rate
        dur = self._format_duration(duration_minutes)
        return {
            'amount': amount,
            'label': f'Hourly Rate – R{self.hourly_rate:.2f}/hr',
            'breakdown': (
                f'Duration parked: {dur} | '
                f'Billable hours: {billable_hours} × R{self.hourly_rate:.2f} = R{amount:.2f}'
            ),
        }


# ─── Mall 3: La Lucia Mall ────────────────────────────────────────────────────
# Hourly Rate with Daily Cap: R12.00/hr capped at R60.00

class CappedHourlyPricing(PricingStrategy):
    """
    Hourly rate with a daily cap: charged per hour (or part thereof),
    but the total is never more than the daily cap.

    Config keys:
        hourly_rate (float): Fee per hour in ZAR.
        daily_cap   (float): Maximum fee per visit in ZAR.

    Example:
        La Lucia Mall — R12.00/hr, cap R60.00
        7 hours → 7 × R12.00 = R84.00 → capped at R60.00
    """

    def __init__(self, config: dict):
        self.hourly_rate: float = config['hourly_rate']
        self.daily_cap: float = config['daily_cap']

    @property
    def display_name(self) -> str:
        return 'Hourly Rate (Capped)'

    def calculate(self, duration_minutes: int) -> dict:
        billable_hours = math.ceil(duration_minutes / 60)
        raw_amount = billable_hours * self.hourly_rate
        amount = min(raw_amount, self.daily_cap)
        capped = raw_amount > self.daily_cap
        dur = self._format_duration(duration_minutes)

        breakdown = (
            f'Duration parked: {dur} | '
            f'{billable_hours} hrs × R{self.hourly_rate:.2f} = R{raw_amount:.2f}'
        )
        if capped:
            breakdown += f' | Daily cap applied → R{self.daily_cap:.2f}'

        label = f'R{self.hourly_rate:.2f}/hr'
        if capped:
            label += f' (capped at R{self.daily_cap:.2f})'

        return {
            'amount': amount,
            'label': label,
            'breakdown': breakdown,
        }


# ─── Registry & Factory ───────────────────────────────────────────────────────

# Maps the pricing_type string (stored in malls.json) to its strategy class.
# Adding a new pricing model = add one entry here + a new class above.
PRICING_CLASSES: dict = {
    'flat':          FlatRatePricing,
    'hourly':        HourlyRatePricing,
    'capped_hourly': CappedHourlyPricing,
    # Future examples:
    # 'daily':       DailyRatePricing,
    # 'weekend':     WeekendRatePricing,
    # 'member':      MemberDiscountPricing,
}


def get_pricing_strategy(mall: dict) -> PricingStrategy:
    """
    Factory: return a configured PricingStrategy instance for a mall record.

    Args:
        mall (dict): Mall record from data layer (must contain
                     'pricing_type' and 'pricing_config' keys).

    Returns:
        PricingStrategy instance.

    Raises:
        ValueError if pricing_type is not registered.
    """
    pricing_type = mall.get('pricing_type')
    cls = PRICING_CLASSES.get(pricing_type)
    if cls is None:
        raise ValueError(
            f"Unknown pricing type: '{pricing_type}'. "
            f"Registered types: {list(PRICING_CLASSES.keys())}"
        )
    return cls(mall['pricing_config'])


def calculate_fee(mall: dict, duration_minutes: int) -> dict:
    """
    Convenience wrapper: calculate parking fee for a mall + duration.

    Args:
        mall             (dict): Mall record.
        duration_minutes (int):  Total duration in minutes.

    Returns:
        dict – see PricingStrategy.calculate() for structure.
    """
    return get_pricing_strategy(mall).calculate(duration_minutes)
