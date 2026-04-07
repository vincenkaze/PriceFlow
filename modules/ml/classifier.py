import numpy as np
from typing import List, Dict, Union


class DemandClassifier:
    THRESHOLDS = {"HIGH": 70, "MEDIUM": 40, "LOW": 0}

    def __init__(self, alpha: float = 0.3):
        self.alpha = alpha

    def classify(self, demand_score: int) -> str:
        if demand_score >= self.THRESHOLDS["HIGH"]:
            return "HIGH"
        elif demand_score >= self.THRESHOLDS["MEDIUM"]:
            return "MEDIUM"
        return "LOW"

    def analyze(self, score_history: List[int]) -> Dict:
        if not score_history:
            return {
                "level": "LOW",
                "ema": 0.0,
                "raw_avg": 0.0,
                "sample_size": 0
            }

        raw_avg = sum(score_history) / len(score_history)
        ema = self._calculate_ema(score_history)
        level = self.classify(int(ema))

        return {
            "level": level,
            "ema": round(ema, 2),
            "raw_avg": round(raw_avg, 2),
            "sample_size": len(score_history)
        }

    def _calculate_ema(self, values: List[float]) -> float:
        if not values:
            return 0.0
        ema = values[0]
        for val in values[1:]:
            ema = self.alpha * val + (1 - self.alpha) * ema
        return ema

    def predict(self, X: Union[List[int], np.ndarray]) -> np.ndarray:
        X = np.array(X)
        return np.array([self.classify(int(x)) for x in X])


demand_classifier = DemandClassifier()