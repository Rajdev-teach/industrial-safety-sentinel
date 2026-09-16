from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from safety_sentinel.generator import SafetyDataGenerator  # noqa: E402


def main() -> None:
    output = ROOT / "data" / "sample_readings.csv"
    output.parent.mkdir(exist_ok=True)
    rows = SafetyDataGenerator(seed=42).generate(1000)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader(); writer.writerows(rows)
    print(f"Generated {len(rows)} readings at {output}")


if __name__ == "__main__": main()

