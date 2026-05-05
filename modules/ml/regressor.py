import numpy as np
from typing import List, Dict, Optional


class DemandRegressor:
    def __init__(self, short_window: int = 3, long_window: int = 7):
        self.short_window = short_window
        self.long_window = long_window

    def predict_next(self, recent_scores: List[int]) -> Optional[float]:
        """Hybrid EMA + OLS: momentum-projected T+1 forecast (clamped to valid range)."""
        if len(recent_scores) < 5:
            return None

        arr = np.array(recent_scores[-15:])

        ema_short = self._calculate_ema(arr, self.short_window)
        ema_long = self._calculate_ema(arr, self.long_window)

        recent = recent_scores[-10:]
        x = np.arange(len(recent))
        slope, intercept = self._ols_slope(x, np.array(recent))

        damped_slope = slope * 0.6

        forecast = ema_short + damped_slope

        forecast = max(0, min(forecast, 150))
        return round(float(forecast), 2)

    def predict_series(self, recent_scores: List[int], steps: int = 3) -> List[float]:
        """OLS slope projection for T+1, T+2, T+3 — dampened, clamped."""
        if len(recent_scores) < 5:
            return []

        recent = recent_scores[-15:]
        x = np.arange(len(recent))
        slope, intercept = self._ols_slope(x, np.array(recent))

        n = len(recent)
        last_idx = n - 1

        predictions = []
        for step in range(1, steps + 1):
            pred = intercept + slope * (last_idx + step * 0.3)
            pred = max(0, min(pred, 150))
            predictions.append(round(float(pred), 2))

        return predictions

    def predict(self, X) -> np.ndarray:
        X = np.array(X)
        if len(X) < 3:
            return np.array([0])
        return np.array([np.mean(X[-3:])])

    def analyze_trend(self, score_history: List[int]) -> Dict:
        """Full trend analysis with OLS + EMA."""
        if len(score_history) < 3:
            return {
                "trend": "insufficient_data",
                "velocity": 0.0,
                "confidence": 0.0,
                "ema_short": 0.0,
                "ema_long": 0.0,
                "forecast": None,
                "ml_forecast": None
            }

        arr = np.array(score_history)
        n = len(arr)

        ema_short = self._calculate_ema(arr, self.short_window)
        ema_long = self._calculate_ema(arr, self.long_window)

        x = np.arange(n)
        slope, intercept = self._ols_slope(x, arr)

        residuals = arr - (slope * x + intercept)
        ss_res = np.sum(residuals ** 2)
        ss_tot = np.sum((arr - np.mean(arr)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

        if slope > 1.5:
            trend = "rising"
        elif slope < -1.5:
            trend = "falling"
        else:
            trend = "stable"

        ols_forecast = score_history[-1] + slope
        ols_forecast = max(0, min(ols_forecast, 150))

        ml_forecast = self.predict_next(score_history)

        return {
            "trend": trend,
            "velocity": round(float(slope), 2),
            "confidence": round(float(max(0, min(1, r_squared))), 2),
            "ema_short": round(float(ema_short), 2),
            "ema_long": round(float(ema_long), 2),
            "forecast": round(float(ols_forecast), 2),
            "ml_forecast": ml_forecast
        }

    def get_chart_data(self, score_history: List[int]) -> Dict:
        if not score_history:
            return {
                "ema_short": [], "ema_long": [], "raw_points": [],
                "trend_line": [], "timestamps": [], "ml_forecast_line": []
            }

        history = score_history[-30:]
        n = len(history)

        ema_short_values = self._ema_series(history, self.short_window)
        ema_long_values = self._ema_series(history, self.long_window)

        x = np.arange(n)
        y = np.array(history)
        slope, intercept = self._ols_slope(x, y)
        trend_line = [slope * i + intercept for i in range(n)]

        ml_forecast_line = list(history)
        ml_preds = self.predict_series(history, steps=3)
        if ml_preds:
            ml_forecast_line.append(history[-1])
            ml_forecast_line.extend(ml_preds)

        return {
            "ema_short": [round(v, 2) for v in ema_short_values],
            "ema_long": [round(v, 2) for v in ema_long_values],
            "raw_points": history,
            "trend_line": [round(v, 2) for v in trend_line],
            "timestamps": list(range(n)),
            "ml_forecast_line": [round(float(v), 2) for v in ml_forecast_line]
        }

    def _calculate_ema(self, values: np.ndarray, window: int) -> float:
        if len(values) < window:
            return float(np.mean(values))
        alpha = 2 / (window + 1)
        ema = float(values[0])
        for val in values[1:]:
            ema = alpha * float(val) + (1 - alpha) * ema
        return ema

    def _ema_series(self, values: List[float], window: int) -> List[float]:
        if not values:
            return []
        alpha = 2 / (window + 1)
        ema = float(values[0])
        ema_values = [ema]
        for val in values[1:]:
            ema = alpha * float(val) + (1 - alpha) * ema
            ema_values.append(ema)
        return ema_values

    def _ols_slope(self, x: np.ndarray, y: np.ndarray) -> tuple:
        n = len(x)
        if n < 2:
            return 0.0, float(np.mean(y)) if len(y) > 0 else 0.0
        x_mean = np.mean(x)
        y_mean = np.mean(y)
        numerator = np.sum((x - x_mean) * (y - y_mean))
        denominator = np.sum((x - x_mean) ** 2)
        if denominator == 0:
            return 0.0, y_mean
        slope = numerator / denominator
        intercept = y_mean - slope * x_mean
        return slope, intercept


demand_regressor = DemandRegressor()