from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest

FEATURES = ["temperature_c", "vibration_mm_s", "forklift_speed_mph", "noise_db"]


class AnomalyModel:
    def __init__(self, model: IsolationForest | None = None):
        self.model = model

    def train(self, readings: list[dict]) -> "AnomalyModel":
        matrix = np.array([[row[field] for field in FEATURES] for row in readings], dtype=float)
        self.model = IsolationForest(n_estimators=150, contamination=0.08, random_state=42)
        self.model.fit(matrix)
        return self

    def score(self, reading: dict) -> tuple[float, bool]:
        if self.model is None:
            return 0.0, False
        matrix = np.array([[reading[field] for field in FEATURES]], dtype=float)
        score = float(self.model.decision_function(matrix)[0])
        return round(score, 5), bool(self.model.predict(matrix)[0] == -1)

    def save(self, path: str | Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model, path)

    @classmethod
    def load(cls, path: str | Path) -> "AnomalyModel":
        return cls(joblib.load(path))

