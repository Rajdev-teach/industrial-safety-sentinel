from __future__ import annotations

from safety_sentinel.database import SafetyDatabase
from safety_sentinel.detector import detect_rule_violations
from safety_sentinel.model import AnomalyModel


def process_reading(database: SafetyDatabase, model: AnomalyModel, reading: dict) -> tuple[int, list[dict]]:
    score, anomaly = model.score(reading)
    enriched = {**reading, "anomaly_score": score, "is_anomaly": int(anomaly)}
    reading_id = database.insert_reading(enriched)
    alerts = detect_rule_violations(enriched)
    database.insert_alerts(reading_id, alerts)
    return reading_id, alerts

