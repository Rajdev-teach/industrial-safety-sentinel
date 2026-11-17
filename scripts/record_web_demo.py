"""Record synthetic replay output using the real model and rules."""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from safety_sentinel.generator import SafetyDataGenerator
from safety_sentinel.model import AnomalyModel
from safety_sentinel.detector import detect_rule_violations

def main():
    model = AnomalyModel().train(SafetyDataGenerator(seed=7, incident_rate=0).generate(600))
    generator = SafetyDataGenerator(seed=21, incident_rate=0.22)
    start = datetime(2026, 11, 17, 12, 0, tzinfo=timezone.utc)
    frames = []
    for index in range(160):
        reading = generator.next_reading(index)
        reading["timestamp"] = (start + timedelta(seconds=index * 2)).isoformat(timespec="seconds")
        score, anomaly = model.score(reading)
        reading.update(id=index + 1, anomaly_score=score, is_anomaly=int(anomaly))
        alerts = [dict(a, reading_id=index + 1, status="OPEN") for a in detect_rule_violations(reading)]
        frames.append({"reading": reading, "alerts": alerts})
    output = ROOT / "demo" / "recording.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"mode": "recorded-synthetic-replay", "model": "IsolationForest, 150 estimators, random_state=42", "baseline_seed": 7, "event_seed": 21, "frames": frames}, indent=2) + "\n")
    print(f"Recorded {len(frames)} synthetic events with offline model scores and rule alerts.")

if __name__ == "__main__":
    main()
