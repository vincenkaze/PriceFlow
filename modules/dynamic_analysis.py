from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy import func, case, distinct
from app.extensions import db
from app.models import DemandScore, Product, UserAction


class DemandAnalyzer:
    """
    Demand scoring engine — fast, batchable, only cares about products that actually moved.
    Use this instead of polling everything forever.
    """

    DEFAULT_WEIGHTS = {
        "view": 1.0,
        "cart": 3.0,
        "purchase": 5.0,
        # Add more: "wishlist": 2.0, "quick_view": 0.8, etc.
    }

    def __init__(
        self,
        lookback_minutes: int = 15,
        action_weights: Optional[Dict[str, float]] = None,
    ):
        self.lookback_minutes = lookback_minutes
        self.action_weights = action_weights or self.DEFAULT_WEIGHTS.copy()

        # Pre-build case clauses once → tiny perf + safety win
        self._case_clauses = [
            (UserAction.action_type == action, weight)
            for action, weight in self.action_weights.items()
        ]

    def _get_window(self, end_time: Optional[datetime] = None) -> Tuple[datetime, datetime]:
        end = end_time or datetime.utcnow()
        start = end - timedelta(minutes=self.lookback_minutes)
        return start, end

    def calculate_weighted_demand(
        self,
        product_id: int,
        end_time: Optional[datetime] = None,
    ) -> Dict:
        """Single-product demand score — SQL-fast, no row loading."""
        start, end = self._get_window(end_time)

        score = (
            db.session.query(
                func.coalesce(
                    func.sum(case(*self._case_clauses, else_=0.0)),
                    0.0
                )
            )
            .filter(UserAction.product_id == product_id)
            .filter(UserAction.timestamp >= start)
            .filter(UserAction.timestamp <= end)
            .scalar()
        )

        return {
            "product_id": product_id,
            "demand_score": int(score),
            "period_start": start,
            "period_end": end,
        }

    def refresh_active_products(
        self,
        end_time: Optional[datetime] = None,
        batch_size: int = 1000,
        keep_only_latest_per_product: bool = True,
    ) -> List[DemandScore]:
        """
        The money-maker: only processes products with recent activity.
        Batch inserts, optional cleanup of old scores.
        """
        start, end = self._get_window(end_time)

        # Step 1: Find only products that had *any* action in window
        active_pids_query = (
            db.session.query(distinct(UserAction.product_id))
            .filter(UserAction.timestamp >= start)
            .filter(UserAction.timestamp <= end)
        )
        active_pids = [row[0] for row in active_pids_query.all()]

        if not active_pids:
            print("No active products in window — skipping refresh")
            return []

        records = []
        session = db.session

        # Step 2: Batch compute & save
        for i in range(0, len(active_pids), batch_size):
            batch = active_pids[i : i + batch_size]

            # Bulk demand scores in one query (group by)
            results = (
                session.query(
                    UserAction.product_id,
                    func.coalesce(
                        func.sum(case(*self._case_clauses, else_=0.0)),
                        0.0
                    ).label("score"),
                )
                .filter(UserAction.product_id.in_(batch))
                .filter(UserAction.timestamp >= start)
                .filter(UserAction.timestamp <= end)
                .group_by(UserAction.product_id)
                .all()
            )

            score_map = {r.product_id: int(r.score) for r in results}

            for pid in batch:
                score = score_map.get(pid, 0)
                record = DemandScore(
                    product_id=pid,
                    demand_score=score,
                    period_start=start,
                    period_end=end,
                    calculated_at=datetime.utcnow(),
                )
                session.add(record)
                records.append(record)

            session.flush()  # optional — can commit less often if paranoid

        session.commit()

        # Optional: keep table lean — delete old scores per product
        if keep_only_latest_per_product:
            self._prune_old_scores(active_pids)

        print(f"Refreshed demand scores for {len(records)} active products")
        return records

    def _prune_old_scores(self, product_ids: List[int]) -> None:
        """Keep only the most recent score per product (optional cleanup)."""
        if not product_ids:
            return

        # Subquery to find latest per product
        latest_subq = (
            db.session.query(
                DemandScore.product_id,
                func.max(DemandScore.calculated_at).label("max_time"),
            )
            .filter(DemandScore.product_id.in_(product_ids))
            .group_by(DemandScore.product_id)
            .subquery()
        )

        # Delete everything older
        db.session.query(DemandScore).filter(
            DemandScore.product_id.in_(product_ids),
            ~(
                (DemandScore.product_id == latest_subq.c.product_id)
                & (DemandScore.calculated_at == latest_subq.c.max_time)
            ),
        ).delete(synchronize_session=False)

        db.session.commit()

# Singleton / global instance (your call)
demand_analyzer = DemandAnalyzer(lookback_minutes=15)