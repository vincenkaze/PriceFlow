from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy import func, case, distinct
from app.extensions import db
from app.config import Config
from app.models import DemandScore, Product, UserAction
import time
import threading
import math


class DemandAnalyzer:
    """
    Demand scoring engine — fast, batchable, only cares about products that actually moved.
    Now with DECAY: demand fades over time so things can cool down.
    """

    DEFAULT_WEIGHTS = {
        "view": 1.0,
        "cart": 3.0,
        "purchase": 5.0,
    }

    # Decay factor: older actions count less
    DECAY_RATE = Config.DEMAND_DECAY_RATE  # 0.85 per minute = 15% decay

    def __init__(
        self,
        lookback_minutes: int = 15,
        action_weights: Optional[Dict[str, float]] = None,
    ):
        self.lookback_minutes = lookback_minutes
        self.action_weights = action_weights or self.DEFAULT_WEIGHTS.copy()
        self.recent_minutes = Config.DEMAND_RECENT_MINUTES  # For trend detection

        # Pre-build case clauses once → tiny perf + safety win
        self._case_clauses = [
            (UserAction.action_type == action, weight)
            for action, weight in self.action_weights.items()
        ]

    def start(self, flask_app, interval: int = 15):
        """Run demand analysis periodically in background"""
        self.app = flask_app
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        print(f"[DEMAND] Analyzer started - refreshing every {interval}s")

    def _run_loop(self):
        with self.app.app_context():
            while self.running:
                try:
                    self.refresh_active_products()
                except Exception as e:
                    print(f"[DEMAND] Analysis error: {e}")
                time.sleep(15)  # Refresh every 15 seconds
    
    def _get_window(self, end_time: Optional[datetime] = None) -> Tuple[datetime, datetime]:
        end = end_time or datetime.utcnow()
        start = end - timedelta(minutes=self.lookback_minutes)
        return start, end

    def calculate_weighted_demand(
        self,
        product_id: int,
        end_time: Optional[datetime] = None,
    ) -> Dict:
        """Single-product demand score with decay — older actions count less."""
        now = end_time or datetime.utcnow()
        window_start = now - timedelta(minutes=self.lookback_minutes)

        # Get all actions in window (we need timestamp for decay)
        # Only fetch needed columns to avoid loading full objects
        actions = db.session.query(
            UserAction.timestamp, 
            UserAction.action_type
        ).filter(
            UserAction.product_id == product_id,
            UserAction.timestamp >= window_start,
            UserAction.timestamp <= now
        ).all()

        # Apply decay: each minute older = multiply by DECAY_RATE
        decayed_score = 0.0
        recent_score = 0.0
        recent_window = now - timedelta(minutes=self.recent_minutes)
        
        for action in actions:
            minutes_ago = (now - action.timestamp).total_seconds() / 60.0
            weight = self.action_weights.get(action.action_type, 1.0)
            # Exponential decay: decay^minutes_ago
            decay_factor = math.pow(self.DECAY_RATE, minutes_ago)
            decayed_score += weight * decay_factor
            
            # Track recent window for trend detection
            if action.timestamp >= recent_window:
                recent_score += weight * decay_factor

        # Calculate trend: recent vs older activity
        older_window_start = now - timedelta(minutes=self.lookback_minutes)
        older_score = decayed_score - recent_score
        
        # Determine trend direction
        trend = "stable"
        if older_score > 0:
            ratio = recent_score / older_score
            if ratio >= Config.DEMAND_TREND_THRESHOLD:
                trend = "rising"
            elif ratio <= (1.0 / Config.DEMAND_TREND_THRESHOLD):
                trend = "falling"

        return {
            "product_id": product_id,
            "demand_score": int(decayed_score),
            "recent_score": int(recent_score),
            "trend": trend,
            "period_start": window_start,
            "period_end": now,
        }

    def refresh_active_products(
        self,
        end_time: Optional[datetime] = None,
        batch_size: int = 1000,
        keep_only_latest_per_product: bool = True,
    ) -> List[DemandScore]:
        """
        The money-maker: only processes products with recent activity.
        NOW WITH DECAY: demand fades over time for realistic rising/falling trends.
        Batch inserts, optional cleanup of old scores.
        """
        now = end_time or datetime.utcnow()
        window_start = now - timedelta(minutes=self.lookback_minutes)
        recent_window = now - timedelta(minutes=self.recent_minutes)

        # Step 1: Find only products that had *any* action in window
        active_pids_query = (
            db.session.query(distinct(UserAction.product_id))
            .filter(UserAction.timestamp >= window_start)
            .filter(UserAction.timestamp <= now)
        )
        active_pids = [row[0] for row in active_pids_query.all()]

        if not active_pids:
            print("[DEMAND] No active products in window - skipping refresh")
            return []

        records = []
        session = db.session

        # Step 2: Batch compute & save with DECAY
        for i in range(0, len(active_pids), batch_size):
            batch = active_pids[i : i + batch_size]

            # Get all actions for products in this batch (need timestamps for decay)
            actions = (
                session.query(UserAction)
                .filter(UserAction.product_id.in_(batch))
                .filter(UserAction.timestamp >= window_start)
                .filter(UserAction.timestamp <= now)
                .all()
            )

            # Group by product and apply decay
            product_scores = {}
            product_recent = {}
            
            for action in actions:
                pid = action.product_id
                if pid not in product_scores:
                    product_scores[pid] = 0.0
                    product_recent[pid] = 0.0
                
                weight = self.action_weights.get(action.action_type, 1.0)
                minutes_ago = (now - action.timestamp).total_seconds() / 60.0
                decay_factor = math.pow(self.DECAY_RATE, minutes_ago)
                
                product_scores[pid] += weight * decay_factor
                
                # Track recent window
                if action.timestamp >= recent_window:
                    product_recent[pid] += weight * decay_factor

            # Save scores with trend information
            for pid in batch:
                decayed_score = product_scores.get(pid, 0.0)
                recent_score = product_recent.get(pid, 0.0)
                older_score = decayed_score - recent_score
                
                # Determine trend
                trend = "stable"
                if older_score > 0:
                    ratio = recent_score / older_score
                    if ratio >= Config.DEMAND_TREND_THRESHOLD:
                        trend = "rising"
                    elif ratio <= (1.0 / Config.DEMAND_TREND_THRESHOLD):
                        trend = "falling"
                elif recent_score > 0 and decayed_score > 0:
                    # No older activity but has recent = newly active
                    trend = "rising"

                record = DemandScore(
                    product_id=pid,
                    demand_score=int(decayed_score),
                    period_start=window_start,
                    period_end=now,
                    calculated_at=datetime.utcnow(),
                )
                session.add(record)
                records.append(record)

            session.flush()

        session.commit()

        # Step 3: Apply penalty to inactive products (products with no recent activity)
        # This lets demand naturally fade for ignored products
        self._apply_inactivity_penalty(active_pids, now)

        # Optional: keep table lean — delete old scores per product
        if keep_only_latest_per_product:
            self._prune_old_scores(active_pids)

        print(f"[DEMAND] Refreshed {len(records)} active products")
        return records

    def _apply_inactivity_penalty(self, active_pids: List[int], now: datetime):
        """Apply penalty to products with NO recent activity - lets demand fade naturally.
        
        Optimized: Uses single SQL query to find inactive products with existing scores,
        then batch inserts penalized records.
        """
        if not active_pids:
            # No active products means all products are inactive
            inactive_with_scores = db.session.query(
                DemandScore.product_id,
                DemandScore.demand_score
            ).join(
                Product, DemandScore.product_id == Product.product_id
            ).filter(
                DemandScore.demand_score > 0
            ).all()
        else:
            # Find products NOT in active_pids that have scores > 0
            inactive_with_scores = db.session.query(
                DemandScore.product_id,
                DemandScore.demand_score
            ).join(
                Product, DemandScore.product_id == Product.product_id
            ).filter(
                ~DemandScore.product_id.in_(active_pids),
                DemandScore.demand_score > 0
            ).all()
        
        penalized = 0
        window_start = now - timedelta(minutes=self.lookback_minutes)
        
        # Batch create penalized records
        for product_id, last_score in inactive_with_scores:
            new_score = max(0, last_score - Config.DEMAND_INACTIVE_PENALTY)
            if new_score != last_score:
                record = DemandScore(
                    product_id=product_id,
                    demand_score=new_score,
                    period_start=window_start,
                    period_end=now,
                    calculated_at=now,
                )
                db.session.add(record)
                penalized += 1
        
        if penalized > 0:
            db.session.commit()
            print(f"[DEMAND] Applied inactivity penalty to {penalized} products")

    def _prune_old_scores(self, product_ids: List[int]) -> None:
        """Keep only the most recent score per product (SQLite-compatible)."""
        if not product_ids:
            return

        try:
            # SQLite-compatible approach: get latest times per product, then delete older ones
            # Step 1: Get the max calculated_at for each product
            latest_times = (
                db.session.query(
                    DemandScore.product_id,
                    func.max(DemandScore.calculated_at).label("max_time")
                )
                .filter(DemandScore.product_id.in_(product_ids))
                .group_by(DemandScore.product_id)
                .all()
            )

            if not latest_times:
                return

            # Step 2: Delete all but the latest for each product
            # Process each product individually to avoid SQLite multi-table issues
            for product_id, max_time in latest_times:
                # Delete older records for this specific product
                deleted = (
                    db.session.query(DemandScore)
                    .filter(
                        DemandScore.product_id == product_id,
                        DemandScore.calculated_at < max_time
                    )
                    .delete(synchronize_session='fetch')
                )
                if deleted > 0:
                    print(f"[DEMAND] Pruned {deleted} old scores for product {product_id}")

            db.session.commit()
            print(f"[DEMAND] Pruning complete for {len(latest_times)} products")

        except Exception as e:
            print(f"[DEMAND] Pruning error (non-fatal): {e}")
            db.session.rollback()

# Singleton / global instance (your call)
demand_analyzer = DemandAnalyzer(lookback_minutes=15)