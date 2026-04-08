# PriceFlow — Intelligent Dynamic Pricing Engine

![Project](https://img.shields.io/badge/Python-3.12+-blue) ![License](https://img.shields.io/badge/License-MIT-green)

Real-time dynamic pricing system with user simulation, demand scoring, rule-based pricing, and online ML forecasting. Simulates 200 synthetic users whose behavior drives demand signals, which feed both a rule engine and an online ML regressor — displayed through a Flask admin dashboard with Chart.js visualizations.

## Live Demo

- **Homepage:** `http://localhost:5000` — Browse products, add to cart, place orders
- **Admin Panel:** `http://localhost:5000/admin` — Monitor pricing, view trend analytics
- **Analytics:** `http://localhost:5000/admin/analytics` — ML-powered demand forecasting with EMA indicators

## Architecture

PriceFlow/
├── run.py                    # Entry point
├── config.yaml               # Environment credentials (admin/user)
├── app/
│   ├── __init__.py           # Flask app factory + blueprint registration
│   ├── config.py             # Config classes (dev/prod/test)
│   ├── extensions.py         # SQLAlchemy, Flask-Login, Migrate
│   ├── models.py             # All database models
│   └── routes/
│       ├── main.py           # Homepage + product detail
│       ├── admin.py          # Admin panel + pricing
│       ├── auth.py           # User login/register/logout
│       ├── cart.py           # Cart operations
│       ├── orders.py         # Checkout + order history
│       └── api.py            # REST API for dashboards
├── services/                 # Business logic (framework-agnostic)
│   ├── pricing_service.py    # Zone-based pricing logic
│   ├── inventory_service.py  # Stock management
│   └── analytics_service.py  # Dashboard statistics
├── modules/
│   ├── user_simulation.py    # 200 synthetic users with personalities
│   ├── demand_analysis.py    # Demand scoring + online ML training
│   ├── pricing_engine.py     # Background pricing loop
│   └── ml/
│       ├── classifier.py     # DemandClassifier (HIGH/MEDIUM/LOW)
│       └── regressor.py       # DemandRegressor (OLS + SGDRegressor online)
├── utils/
│   ├── datetime_utils.py     # Centralized timestamp helpers
│   └── validators.py        # Input validation
├── static/js/
│   └── charts.js             # Chart.js integration for dashboards
├── database/
│   ├── schema.sql            # Full SQLite schema
│   ├── seed.py              # Products, categories, sim users, pricing rules
│   └── seed_demand_history.py # Seed historical demand data for ML charts
└── tests/                    # 80+ unit tests

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, Flask 3 |
| Database | SQLite (dev), MySQL (prod) |
| Auth | Flask-Login |
| ML | Scikit-learn (SGDRegressor, OLS trend) |
| Charts | Chart.js 4 |
| Frontend | HTML, Tailwind CSS, Vanilla JS |

## Quick Start

```bash
# 1. Clone
git clone https://github.com/vincenkaze/PriceFlow.git
cd PriceFlow

# 2. Virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Seed database
python database/seed.py

# 5. Seed demand history (needed for ML trend charts)
python database/seed_demand_history.py

# 6. Run
python run.py
```

Visit http://localhost:5000

Default credentials:

- **Admin:** admin / admin123 → /admin
- **User:** Register at /auth/register

## How It Works

### Feedback Loop

1. **Simulated Users (200)** → actions (view/cart/purchase)
2. **UserAction table** → demand analysis (every 15s)
3. **DemandScore** (EMA-smoothed, decayed) → pricing engine (every 10s)
4. **PriceHistory** ← current_price updated → Homepage (real-time via WebSocket)
5. **Admin Dashboard** (polled every 30s)
6. **Analytics** (ML forecast updated on demand)

### Pricing Zones

| Zone | Condition | Action |
|------|-----------|--------|
| Zone 1 | High demand (>60) + low stock | Price ↑ |
| Zone 2 | Rising demand (>40) | Price ↑ |
| Zone 3 | Weak demand (<4) + excess stock (>80) | Price ↓ |
| Zone 4 | Critical demand (<2) OR stock near full | Price ↓ |
| Zone 5 | Everything else | Stable |

Price bounded by `base_price × [min_price_pct, max_price_pct]` from pricing rules.

### ML Trend Analysis

Two complementary approaches:

1. **Statistical (always available):** OLS regression slope on demand history → rising/stable/falling + velocity
2. **Online ML (sklearn, trained incrementally):**
   - `SGDRegressor.partial_fit()` called every demand refresh cycle
   - Learns from the last ~10 demand scores per product
   - Predicts T+1, T+2, T+3 demand → shown as amber dashed line on chart
   - Falls back to statistical forecast if sklearn unavailable

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/products` | GET | All products with current prices |
| `/api/dashboard/trends` | GET | Top products with trend analysis + chart data |
| `/api/dashboard/stats` | GET | Dashboard KPIs |
| `/api/dashboard/recent-changes` | GET | Latest price changes |
| `/api/admin/products` | GET/PUT | Product management |

## Running Tests

```bash
python -m pytest tests/ -v
```

Current coverage: pricing zones, simulation personalities, auth flows, cart operations, order placement, ML classifiers and regressors, validators.

## Viva Talking Points

- **Why online ML?** Demand patterns shift over time. SGDRegressor with partial_fit adapts continuously without retraining from scratch.
- **Why EMA smoothing?** Raw action counts spike and crash. EMA (α=0.3) smooths volatility while staying responsive.
- **Why demand decay?** Products with no recent attention should cool down. Decay rate of 0.60 means 40% decay per minute of inactivity.
- **Why dual EMA (short=3, long=7)?** Short EMA tracks momentum, long EMA confirms trend direction. Crossover pattern identifies trend shifts.
- **Zone pricing vs ML forecast?** Zones are rule-based guardrails (safe, explainable). ML forecast is advisory — used for visualization, not direct price decisions (yet).

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| ADMIN_USERNAME | admin | Admin login |
| ADMIN_PASSWORD | admin123 | Admin password |
| SECRET_KEY | (dev default) | Flask session secret |
| DATABASE_URL | sqlite:///instance/pricing_dev.db | DB connection |

## License

MIT — Built by vincenkaze.