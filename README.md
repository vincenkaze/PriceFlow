# Intelligent Dynamic Pricing System for E-Commerce

![Project Banner](https://via.placeholder.com/1200x300?text=Dynamic+Pricing+Engine)  <!-- Add a real image later, maybe a flowchart -->

## Overview
This project is a standalone simulation engine (not a full shopping site) that automatically adjusts product prices based on simulated user behavior, demand patterns, and inventory levels. It treats pricing as a decision-making problem, using a feedback loop: User actions → Demand scores → Heuristic rules → Price updates. Perfect for academic demos or scaling to real e-com platforms.

Key Features:
- ~200 synthetic users with probabilistic behaviors (e.g., price-sensitive browsers vs impulse buyers).
- Demand calculated via weighted actions (views +1, cart +3, purchases +5).
- Prices fluctuate within min/max limits (e.g., 70-150% of base).
- Optional ML regression for trend prediction.
- Admin dashboard for monitoring (graphs with Matplotlib/Plotly) and rule config—no manual price tweaks.

Inspired by real-world systems like Amazon or Uber, but simulation-only (no real payments or customers).

## Tech Stack
- **Backend:** Python 3, Flask (or Django)
- **DB:** SQLite/MySQL (schema included)
- **Libs:** NumPy, Pandas, Scikit-Learn, Matplotlib
- **Hardware:** Just a laptop—no GPU needed.

## Setup Instructions
1. Clone: `git clone https://github.com/yourusername/intelligent-dynamic-pricing-system.git`
2. Env: `python -m venv venv && source venv/bin/activate` (or `venv\Scripts\activate` on Windows)
3. Install: `pip install -r requirements.txt`
4. DB Init: `python database/seed.py` (creates tables and seeds data)
5. Run: `python run.py` — visit http://localhost:5000
6. Simulate: Background thread runs user sim—watch prices dance!

## Modules (From Project Docs)
1. **User Simulation:** Generates probabilistic interactions for synthetic users.
2. **Demand Analysis:** Computes scores from weighted user actions.
3. **Dynamic Pricing Engine:** Applies heuristics (high demand/low stock → ↑ price) with guards.
4. **ML Support:** Regression predicts trends (optional).
5. **Admin Dashboard:** Real-time insights, no direct control.

## Database Schema Summary
(Full in `database/schema.sql`—based on your PDF, expanded logically since it was truncated.)

- **categories:** category_id (PK), name, min_price_pct (default 0.7), max_price_pct (1.5)
- **user_types:** type_id (PK), type_name, view_prob (0.8), cart_prob (0.3), purchase_prob (0.1), price_sensitivity (0.5)
- **products:** product_id (PK), name, category_id (FK), base_price, current_price, stock, min/max_price, last_updated
- (Inferred from context: users, interactions, price_history tables—add as needed for logging actions and changes.)

## Algorithms Pipeline
1. Probabilistic Simulation → Input gen
2. Weighted Aggregation → Signal processing
3. Rule-Based Logic → Guardrails
4. Heuristic Adjustment → Decision engine
5. Regression → Advisory (optional)
6. Statistical Eval → Validation

## TODOs (Your Roadmap)
- Implement user sim in a thread (random probs for realism).
- Hook demand to pricing: If demand > threshold and stock < 50%, bump price by 5-10%.
- Add graphs: Pandas for data, Matplotlib for plots.
- Test: Compare static vs dynamic revenue in eval module.

Contributions welcome—fork and PR! Questions? Hit issues.

MIT License – Built with by vincenkaze.