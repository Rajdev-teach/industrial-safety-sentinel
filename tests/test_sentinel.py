from pathlib import Path

from safety_sentinel.database import SafetyDatabase
from safety_sentinel.detector import detect_rule_violations
from safety_sentinel.generator import SafetyDataGenerator
from safety_sentinel.model import AnomalyModel
from safety_sentinel.pipeline import process_reading


def test_generator_is_reproducible():
    assert SafetyDataGenerator(42).next_reading() == SafetyDataGenerator(42).next_reading()


def test_critical_temperature_alert():
    reading = SafetyDataGenerator(1, 0).next_reading()
    reading["temperature_c"] = 95
    alerts = detect_rule_violations(reading)
    assert any(a["alert_type"] == "HIGH_TEMPERATURE" and a["severity"] == "CRITICAL" for a in alerts)


def test_missing_ppe_alert():
    reading = SafetyDataGenerator(2, 0).next_reading()
    reading.update(worker_present=1, helmet_detected=0)
    assert any(a["alert_type"] == "MISSING_HELMET" for a in detect_rule_violations(reading))


def test_restricted_zone_alert():
    reading = SafetyDataGenerator(3, 0).next_reading()
    reading.update(worker_present=1, restricted_zone=1)
    assert any(a["alert_type"] == "RESTRICTED_ZONE" for a in detect_rule_violations(reading))


def test_model_flags_extreme_pattern():
    baseline = SafetyDataGenerator(5, 0).generate(500)
    model = AnomalyModel().train(baseline)
    extreme = baseline[0] | {"temperature_c": 140, "vibration_mm_s": 35, "noise_db": 130}
    _, anomaly = model.score(extreme)
    assert anomaly


def test_pipeline_persists_reading_and_alert(tmp_path: Path):
    database = SafetyDatabase(tmp_path / "test.db")
    baseline = SafetyDataGenerator(5, 0).generate(300)
    model = AnomalyModel().train(baseline)
    dangerous = baseline[0] | {"forklift_speed_mph": 14}
    reading_id, alerts = process_reading(database, model, dangerous)
    assert reading_id > 0 and alerts
    assert database.metrics()["readings"] == 1
    assert database.metrics()["alerts"] >= 1

