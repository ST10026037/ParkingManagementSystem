# 🅿️ KZN Smart Mall Parking Management System

A command-line parking management system built in **Python**, designed to standardise parking operations across multiple KwaZulu-Natal shopping malls. Data is stored in **JSON files** and persists between sessions.

---

## 📋 Table of Contents

- [How to Run the System](#how-to-run-the-system)
- [Login Credentials](#login-credentials)
- [Shopping Malls & Pricing](#shopping-malls--pricing)
- [User Roles & Features](#user-roles--features)
  - [Customer](#customer)
  - [Parking Administrator](#parking-administrator)
  - [Owner / Shareholder](#owner--shareholder)
- [System Architecture](#system-architecture)
- [File Structure](#file-structure)
- [Data Storage](#data-storage)
- [Pricing Strategy Design](#pricing-strategy-design)
- [Running the Tests](#running-the-tests)

---

## ▶️ How to Run the System

### Requirements
- **Python 3.10 or higher** must be installed
- No external libraries or pip installs needed — uses Python standard library only

### Option 1 — Double-click (Easiest)
Double-click the file:
```
run.bat
```
This will open the system in a terminal window automatically.

### Option 2 — PowerShell or Command Prompt
Open a terminal, navigate to the project folder, and run:

```powershell
cd "C:\Users\Administrator\Documents\ParkingManagementSystem"
python -X utf8 main.py
```

> ⚠️ **Important:** Always use `python -X utf8 main.py` (not just `python main.py`).  
> The `-X utf8` flag is required on Windows so that table borders and special characters display correctly in the terminal.

### First Run
On the very first run, the system will automatically:
- Create the `data/` folder
- Seed all JSON files with mall data, user accounts, and demo parking history
- Display: `[System] First-run setup complete. Data initialised.`

All data is saved automatically and will be there the next time you run the system.

---

## 🔑 Login Credentials

These accounts are pre-loaded and ready to use immediately:

| Role | Email | Password |
|---|---|---|
| **Owner / Shareholder** | `owner@kznmalls.co.za` | `Owner@123` |
| **Admin — Gateway** | `admin.gateway@kzn.co.za` | `Admin@123` |
| **Admin — Pavilion** | `admin.pavilion@kzn.co.za` | `Admin@123` |
| **Admin — La Lucia** | `admin.lucia@kzn.co.za` | `Admin@123` |
| **Customer (demo)** | `zanele@demo.co.za` | `Demo@123` |
| **Customer (demo)** | `rajan@demo.co.za` | `Demo@123` |

> New customer accounts can also be registered directly from the main menu.

---

## 🏬 Shopping Malls & Pricing

The system manages three KwaZulu-Natal shopping malls, each with its own pricing policy:

| # | Mall | Location | Pricing Model | Rate | Capacity |
|---|---|---|---|---|---|
| 1 | **Gateway Theatre of Shopping** | Umhlanga, Durban | Flat Rate | R15.00 per visit (any duration) | 250 vehicles |
| 2 | **Pavilion Shopping Centre** | Westville, Durban | Hourly Rate | R10.00/hr (or part thereof) | 180 vehicles |
| 3 | **La Lucia Mall** | La Lucia, Durban | Hourly Rate with Daily Cap | R12.00/hr, capped at R60.00 | 150 vehicles |

### Pricing Examples
| Mall | Duration | Calculation | Amount Due |
|---|---|---|---|
| Gateway | 30 minutes | Fixed fee | **R15.00** |
| Gateway | 3 hours | Fixed fee | **R15.00** |
| Pavilion | 90 minutes | 2 hrs (ceiling) × R10.00 | **R20.00** |
| Pavilion | 2 hours | 2 hrs × R10.00 | **R20.00** |
| La Lucia | 2 hours | 2 hrs × R12.00 = R24.00 (below cap) | **R24.00** |
| La Lucia | 7 hours | 7 hrs × R12.00 = R84.00 → capped | **R60.00** |

---

## 👤 User Roles & Features

### Customer

After logging in (or registering), customers can:

#### 1. Park / Exit a Vehicle
- View all 3 malls with **live occupancy** displayed as a colour-coded bar
- Select a mall to **register vehicle entry** (enter licence plate, records entry time)
- **Exit a mall** — shows a full fee receipt before payment:
  - Licence plate, entry time, exit time
  - Duration parked
  - Pricing type applied and full fee breakdown
  - Amount due
- Select payment method: **Card** or **Cash**
- System prevents entry if a mall is at full capacity

#### 2. View Active Sessions
- Table of all currently active parking sessions
- Shows duration so far and **estimated current charge** (live calculation)

#### 3. View Parking History
- Full table of all completed parking sessions
- Includes entry/exit times, duration, fee, and payment status

#### 4. View Payment History
- All payments with mall, licence plate, duration, method, and amount
- Displays total amount spent

---

### Parking Administrator

Each admin account is linked to **one specific mall**. After login:

#### 1. View Vehicles Currently Parked
- Table of all vehicles currently in the mall's car park
- Shows customer name, entry time, duration parked so far, and estimated charge

#### 2. Monitor Parking Capacity
- Live colour-coded progress bar:
  - 🟢 **Green** — below 70% full (OK)
  - 🟡 **Yellow** — 70–89% full (HIGH)
  - 🔴 **Red** — 90%+ full (CRITICAL)
- Breakdown table: total capacity, occupied, available, occupancy rate

#### 3. View Today's Activity Log
- All parking sessions for today at their mall
- Shows entry time, exit time (or "Still parked"), duration, fee, and status
- Displays today's totals: visits, revenue, and currently parked count

---

### Owner / Shareholder

The owner has access to **data across all malls**:

#### 1. System Summary
- Combined portfolio totals: total revenue, total vehicles, currently parked
- Top mall by revenue and top mall by volume (highlighted)
- At-a-glance table for all 3 malls side by side

#### 2. Cross-Mall Comparison Report
- ASCII bar charts comparing **revenue** and **vehicle volume** across all malls
- Detailed metrics table: visits, active vehicles, revenue, average duration, occupancy
- Pricing rules summary for each mall
- **7-day revenue table** comparing all three malls day by day

#### 3. Detailed Report per Mall (×3)
- Key statistics: total visits, completed sessions, total revenue, average duration
- Live capacity progress bar
- 7-day revenue bar chart
- Table of the last 10 completed sessions with pricing applied and fee

---

## 🏗️ System Architecture

The system is built with clean **Object-Oriented Design** and uses the **Strategy Pattern** for pricing.

```
main.py
  │
  ├── services/auth_service.py       Login / Register / SHA-256 hashing
  ├── services/data_service.py       All JSON read/write operations
  ├── services/parking_service.py    Entry, exit, fee calc, capacity
  ├── services/payment_service.py    Payment processing & history
  ├── services/report_service.py     Mall & cross-mall report generation
  │
  ├── pricing/strategies.py          Strategy Pattern (see below)
  │
  └── ui/
      ├── display.py                 Terminal output: tables, bars, colours
      ├── customer_menu.py           Customer role menus
      ├── admin_menu.py              Admin role menus
      └── owner_menu.py              Owner role menus
```

---

## 📁 File Structure

```
ParkingManagementSystem/
│
├── main.py                  ← START HERE — entry point
├── run.bat                  ← Windows double-click launcher
├── _test_system.py          ← Automated tests (71 tests)
│
├── data/                    ← Auto-created on first run
│   ├── users.json
│   ├── malls.json
│   ├── sessions.json
│   ├── payments.json
│   └── meta.json
│
├── pricing/
│   ├── __init__.py
│   └── strategies.py        ← Pricing strategy classes
│
├── services/
│   ├── __init__.py
│   ├── data_service.py
│   ├── auth_service.py
│   ├── parking_service.py
│   ├── payment_service.py
│   └── report_service.py
│
└── ui/
    ├── __init__.py
    ├── display.py
    ├── customer_menu.py
    ├── admin_menu.py
    └── owner_menu.py
```

---

## 💾 Data Storage

All data is stored as **JSON files** in the `data/` folder. The files are created automatically — you do not need to create them manually.

| File | Contents |
|---|---|
| `users.json` | All user accounts (customers, admins, owner) |
| `malls.json` | Mall names, locations, capacity, and pricing configuration |
| `sessions.json` | All parking sessions — active and completed |
| `payments.json` | All payment records |
| `meta.json` | First-run flag (prevents re-seeding on subsequent runs) |

Data is saved after **every action** (entry, exit, payment, registration) so nothing is lost even if the program is closed mid-session.

---

## 💡 Pricing Strategy Design

The system uses the **Strategy design pattern** to keep pricing logic separate and extensible.

Each mall's pricing policy is its own independent class:

```python
# pricing/strategies.py

class PricingStrategy(ABC):          # Abstract base class
    def calculate(duration_minutes)  # Must be implemented by all

class FlatRatePricing(PricingStrategy):     # Gateway — R15 per visit
class HourlyRatePricing(PricingStrategy):   # Pavilion — R10/hr (ceiling)
class CappedHourlyPricing(PricingStrategy): # La Lucia — R12/hr, cap R60
```

All three are registered in a dictionary:
```python
PRICING_CLASSES = {
    'flat':          FlatRatePricing,
    'hourly':        HourlyRatePricing,
    'capped_hourly': CappedHourlyPricing,
}
```

**To add a new mall with a new pricing model in the future:**
1. Write a new class that extends `PricingStrategy` and implements `calculate()`
2. Add one entry to `PRICING_CLASSES`
3. Add a mall record to `data/malls.json` with the new `pricing_type`
4. No other code changes are required anywhere else in the system

---

## 🧪 Running the Tests

An automated test script verifies all system components:

```powershell
python -X utf8 _test_system.py
```

**Tests cover:**
- All module imports
- Data seeding (malls, users, sessions, payments)
- All 3 pricing strategies with edge cases (ceiling, cap)
- Login success, wrong password, unknown email
- Customer registration (including validation errors)
- Vehicle entry, duplicate prevention, capacity enforcement
- Exit preview, exit finalisation, fee recording
- Payment processing, duplicate payment prevention
- Per-mall reports, cross-mall comparison, system summary

**Expected result:**
```
Results: 71/71 tests passed  --  ALL TESTS PASSED
```

---

## 📝 Notes

- Passwords are hashed using **SHA-256** before being stored — plain-text passwords are never saved to disk
- The system prevents a customer from having two active sessions at the same mall simultaneously
- Vehicle entry is blocked when a mall reaches its maximum capacity
- All fees are displayed and confirmed **before** payment is processed
- The admin dashboard only shows data for their assigned mall; the owner sees all malls

---

*KZN Smart Mall Parking Management System — KwaZulu-Natal, South Africa*
