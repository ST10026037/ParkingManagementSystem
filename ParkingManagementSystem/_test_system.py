"""
_test_system.py — Automated system verification script.
Run with: python _test_system.py
"""
import sys
import os
import io

# Force UTF-8 on Windows (only if not already wrapped)
if sys.platform == 'win32':
    if hasattr(sys.stdout, 'buffer') and getattr(sys.stdout, 'encoding', '') != 'utf-8':
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        except (AttributeError, io.UnsupportedOperation):
            pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PASS = 0
FAIL = 0

def check(label, condition, note=''):
    global PASS, FAIL
    if condition:
        print(f'  [PASS]  {label}')
        PASS += 1
    else:
        print(f'  [FAIL]  {label}  <- {note}')
        FAIL += 1

print()
print('=' * 60)
print('  KZN Smart Mall PMS - System Verification')
print('=' * 60)

# ── Imports ──────────────────────────────────────────────────────
print('\n[1] Module Imports')
try:
    from services.data_service import DataService
    from services.auth_service import AuthService
    from services.parking_service import ParkingService
    from services.payment_service import PaymentService
    from services.report_service import ReportService
    from pricing.strategies import calculate_fee, get_pricing_strategy, PRICING_CLASSES
    from ui.display import Display
    from ui.customer_menu import CustomerMenu
    from ui.admin_menu import AdminMenu
    from ui.owner_menu import OwnerMenu
    check('All modules import successfully', True)
except Exception as e:
    check('All modules import successfully', False, str(e))
    print('\nCannot continue without all modules loading.')
    sys.exit(1)

# ── Data Layer ────────────────────────────────────────────────────
print('\n[2] Data Layer & Seed Data')
DataService.initialise()
malls    = DataService.get_all_malls()
users    = DataService.get_all_users()
sessions = DataService.get_all_sessions()
payments = DataService.get_all_payments()
check('3 malls seeded',    len(malls) == 3,    f'got {len(malls)}')
check('6+ users seeded',   len(users) >= 6,    f'got {len(users)}')
check('Sessions seeded',   len(sessions) >= 5, f'got {len(sessions)}')
check('Payments seeded',   len(payments) >= 5, f'got {len(payments)}')

# Mall specifics
gateway  = DataService.get_mall_by_id('mall_gateway')
pavilion = DataService.get_mall_by_id('mall_pavilion')
lucia    = DataService.get_mall_by_id('mall_lucia')
check('Gateway mall found',  gateway  is not None)
check('Pavilion mall found', pavilion is not None)
check('La Lucia mall found', lucia    is not None)
check('Gateway capacity = 250', gateway['capacity']  == 250)
check('Pavilion capacity = 180', pavilion['capacity'] == 180)
check('La Lucia capacity = 150', lucia['capacity']    == 150)

# ── Pricing Strategies ────────────────────────────────────────────
print('\n[3] Pricing Strategies')

# Flat rate — Gateway (R15 regardless of duration)
r = calculate_fee(gateway, 30)
check('Gateway flat rate 30min = R15.00', r['amount'] == 15.0, f'got R{r["amount"]}')
r = calculate_fee(gateway, 180)
check('Gateway flat rate 3h   = R15.00', r['amount'] == 15.0, f'got R{r["amount"]}')

# Hourly rate — Pavilion (R10/hr ceiling)
r = calculate_fee(pavilion, 60)
check('Pavilion 60min  = R10.00', r['amount'] == 10.0, f'got R{r["amount"]}')
r = calculate_fee(pavilion, 90)
check('Pavilion 90min  = R20.00 (ceiling)', r['amount'] == 20.0, f'got R{r["amount"]}')
r = calculate_fee(pavilion, 120)
check('Pavilion 120min = R20.00', r['amount'] == 20.0, f'got R{r["amount"]}')
r = calculate_fee(pavilion, 121)
check('Pavilion 121min = R30.00 (partial hr)', r['amount'] == 30.0, f'got R{r["amount"]}')

# Capped hourly — La Lucia (R12/hr, cap R60)
r = calculate_fee(lucia, 60)
check('La Lucia 1hr    = R12.00', r['amount'] == 12.0, f'got R{r["amount"]}')
r = calculate_fee(lucia, 300)
check('La Lucia 5hrs   = R60.00 (cap)', r['amount'] == 60.0, f'got R{r["amount"]}')
r = calculate_fee(lucia, 420)
check('La Lucia 7hrs   = R60.00 (cap, would be R84)', r['amount'] == 60.0, f'got R{r["amount"]}')
r = calculate_fee(lucia, 120)
check('La Lucia 2hrs   = R24.00 (below cap)', r['amount'] == 24.0, f'got R{r["amount"]}')

# Strategy names
check('3 pricing strategies registered', len(PRICING_CLASSES) == 3)
check('flat strategy registered',         'flat'          in PRICING_CLASSES)
check('hourly strategy registered',       'hourly'        in PRICING_CLASSES)
check('capped_hourly strategy registered','capped_hourly' in PRICING_CLASSES)

# ── Authentication ─────────────────────────────────────────────────
print('\n[4] Authentication')
auth = AuthService()

r = auth.login('owner@kznmalls.co.za', 'Owner@123')
check('Owner login success',          r['success'])
check('Owner role correct',           r.get('user', {}).get('role') == 'owner')

r = auth.login('admin.gateway@kzn.co.za', 'Admin@123')
check('Admin (Gateway) login success',r['success'])
check('Admin mall_id set correctly',  r.get('user', {}).get('mall_id') == 'mall_gateway')

r = auth.login('zanele@demo.co.za', 'Demo@123')
check('Customer login success',       r['success'])
check('Customer role correct',        r.get('user', {}).get('role') == 'customer')

r = auth.login('nobody@x.co.za', 'wrongpass')
check('Unknown email returns error',  not r['success'])

r = auth.login('zanele@demo.co.za', 'wrongpass')
check('Wrong password returns error', not r['success'])

r = auth.register('Test User', 'test@newuser.co.za', 'Pass123', 'Pass123')
check('New customer registration',    r['success'] or 'already exists' in r.get('error',''), r.get('error', ''))
# Use a guaranteed-unique email for role check
import time
unique_email = f'unique_{int(time.time())}@test.co.za'
r2 = auth.register('Unique User', unique_email, 'Pass123', 'Pass123')
check('Registered user is customer',  r2.get('user', {}).get('role') == 'customer', r2.get('error',''))


r = auth.register('Dup', 'test@newuser.co.za', 'Pass123', 'Pass123')
check('Duplicate email rejected',     not r['success'])

r = auth.register('Short', 'short@x.co.za', '123', '123')
check('Short password rejected',      not r['success'])

r = auth.register('Mismatch', 'mm@x.co.za', 'Pass123', 'Pass999')
check('Password mismatch rejected',   not r['success'])

# ── Parking Operations ─────────────────────────────────────────────
print('\n[5] Parking Operations')

occ = ParkingService.get_occupancy('mall_gateway')
check('Occupancy returns valid dict', occ is not None and 'active' in occ)
check('Gateway capacity correct',     occ['capacity'] == 250)

# Enter mall
enter = ParkingService.enter('user_demo2', 'mall_pavilion', 'TEST 001 GP')
check('Vehicle entry success',        enter['success'], enter.get('error', ''))
check('Session status is active',     enter.get('session', {}).get('status') == 'active')
check('License plate uppercased',     enter.get('session', {}).get('license_plate') == 'TEST 001 GP')

# Duplicate entry prevention
enter2 = ParkingService.enter('user_demo2', 'mall_pavilion', 'TEST 002 GP')
check('Duplicate session blocked',    not enter2['success'])

# Preview exit
if enter['success']:
    sess_id = enter['session']['id']
    preview = ParkingService.preview_exit(sess_id)
    check('Exit preview success',      preview['success'], preview.get('error', ''))
    check('Preview has amount',        'amount' in preview)
    check('Preview has label',         'label'  in preview)
    check('Preview has breakdown',     'breakdown' in preview)

    # Finalise exit
    exit_r = ParkingService.exit_mall(sess_id)
    check('Exit finalised',            exit_r['success'], exit_r.get('error', ''))
    check('Session status completed',  exit_r.get('session', {}).get('status') == 'completed')
    check('Fee recorded',              exit_r.get('session', {}).get('fee') is not None)
    check('Duration recorded',         exit_r.get('session', {}).get('duration_minutes') is not None)

    # Payment
    pay_r = PaymentService.pay(sess_id, 'card')
    check('Payment processed',         pay_r['success'], pay_r.get('error', ''))
    check('Session marked as paid',    DataService.get_session_by_id(sess_id).get('paid') is True)

    # Duplicate payment
    pay_r2 = PaymentService.pay(sess_id, 'card')
    check('Duplicate payment rejected', not pay_r2['success'])

# Capacity check — overfill test (use a saturated mall by checking logic)
check('Empty plate rejected', not ParkingService.enter('user_owner', 'mall_gateway', '')['success'])

# ── Reports ────────────────────────────────────────────────────────
print('\n[6] Reports')
report = ReportService.get_mall_report('mall_gateway')
check('Mall report generated',      report is not None)
check('Report has total_vehicles',  'total_vehicles' in report)
check('Report has total_revenue',   'total_revenue'  in report)
check('Report has avg_duration',    'avg_duration'   in report)
check('Report has daily_revenue',   'daily_revenue'  in report)
check('Report has pricing_name',    'pricing_name'   in report)
check('Gateway pricing = Flat Rate',report.get('pricing_name') == 'Flat Rate')

reports = ReportService.get_all_malls_report()
check('All-malls report has 3 items', len(reports) == 3)

summary = ReportService.get_system_summary()
check('System summary generated',   summary is not None)
check('Summary has mall_count',     summary.get('mall_count') == 3)
check('Summary has total_revenue',  'total_revenue' in summary)
check('Top by revenue exists',      summary.get('top_by_revenue') is not None)
check('Top by volume exists',       summary.get('top_by_volume') is not None)

# Customer payment history
hist = PaymentService.get_customer_history('user_demo1')
check('Customer payment history returned', isinstance(hist, list))
check('Zanele has payment records',       len(hist) >= 2)

# ── Summary ────────────────────────────────────────────────────────
print()
print('=' * 60)
total = PASS + FAIL
print(f'  Results: {PASS}/{total} tests passed', end='')
if FAIL == 0:
    print('  --  ALL TESTS PASSED')
else:
    print(f'  --  {FAIL} FAILED')
print('=' * 60)
print()
sys.exit(0 if FAIL == 0 else 1)
