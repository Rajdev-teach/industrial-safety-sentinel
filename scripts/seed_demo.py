from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from safety_sentinel.config import DB_PATH, MODEL_PATH  # noqa: E402
from safety_sentinel.database import SafetyDatabase  # noqa: E402
from safety_sentinel.generator import SafetyDataGenerator  # noqa: E402
from safety_sentinel.model import AnomalyModel  # noqa: E402
from safety_sentinel.pipeline import process_reading  # noqa: E402


def main() -> None:
    for path in (DB_PATH, MODEL_PATH):
        if Path(path).exists(): Path(path).unlink()
    baseline = SafetyDataGenerator(seed=7, incident_rate=0).generate(600)
    model = AnomalyModel().train(baseline); model.save(MODEL_PATH)
    database = SafetyDatabase(DB_PATH)
    readings = SafetyDataGenerator(seed=21, incident_rate=0.22).generate(160)
    alert_count = sum(len(process_reading(database, model, row)[1]) for row in readings)
    print(f"Seeded {len(readings)} readings and {alert_count} alerts")


if __name__ == "__main__": main()

