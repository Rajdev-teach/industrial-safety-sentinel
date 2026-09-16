from __future__ import annotations

from safety_sentinel.config import THRESHOLDS


def _alert(reading: dict, alert_type: str, severity: str, message: str) -> dict:
    return {
        "timestamp": reading["timestamp"],
        "device_id": reading["device_id"],
        "zone": reading["zone"],
        "alert_type": alert_type,
        "severity": severity,
        "message": message,
    }


def detect_rule_violations(reading: dict) -> list[dict]:
    alerts: list[dict] = []
    labels = {
        "temperature_c": ("HIGH_TEMPERATURE", "Temperature", "°C"),
        "vibration_mm_s": ("EXCESSIVE_VIBRATION", "Vibration", "mm/s"),
        "forklift_speed_mph": ("UNSAFE_SPEED", "Forklift speed", "mph"),
        "noise_db": ("HIGH_NOISE", "Noise", "dB"),
    }
    for field, limits in THRESHOLDS.items():
        value = float(reading[field])
        alert_type, label, unit = labels[field]
        if value >= limits["critical"]:
            alerts.append(_alert(reading, alert_type, "CRITICAL", f"{label} {value:.1f} {unit} exceeds critical limit"))
        elif value >= limits["warning"]:
            alerts.append(_alert(reading, alert_type, "WARNING", f"{label} {value:.1f} {unit} exceeds warning limit"))

    if reading["worker_present"] and not reading["helmet_detected"]:
        alerts.append(_alert(reading, "MISSING_HELMET", "CRITICAL", "Worker detected without a safety helmet"))
    if reading["worker_present"] and not reading["vest_detected"]:
        alerts.append(_alert(reading, "MISSING_VEST", "WARNING", "Worker detected without a high-visibility vest"))
    if reading["worker_present"] and reading["restricted_zone"]:
        alerts.append(_alert(reading, "RESTRICTED_ZONE", "CRITICAL", "Worker entered a restricted machine zone"))
    if reading.get("is_anomaly") and not alerts:
        alerts.append(_alert(reading, "ML_ANOMALY", "WARNING", "Machine-learning model detected an unusual sensor pattern"))
    return alerts

