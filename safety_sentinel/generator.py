from __future__ import annotations

import random
from datetime import datetime, timezone

ZONES = ["Assembly-A", "Packaging-B", "Warehouse-C", "Welding-D"]
DEVICES = ["EDGE-01", "EDGE-02", "EDGE-03", "EDGE-04"]


class SafetyDataGenerator:
    def __init__(self, seed: int = 42, incident_rate: float = 0.12):
        self.random = random.Random(seed)
        self.incident_rate = incident_rate

    def next_reading(self, index: int = 0) -> dict:
        r = self.random
        incident = r.random() < self.incident_rate
        worker = r.random() < 0.72
        reading = {
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "device_id": DEVICES[index % len(DEVICES)],
            "zone": ZONES[index % len(ZONES)],
            "temperature_c": round(r.gauss(60, 5), 2),
            "vibration_mm_s": round(max(0.1, r.gauss(4.2, 1.1)), 2),
            "forklift_speed_mph": round(max(0, r.gauss(5.5, 1.2)), 2),
            "noise_db": round(r.gauss(78, 4), 2),
            "worker_present": int(worker),
            "helmet_detected": int(not worker or r.random() > 0.04),
            "vest_detected": int(not worker or r.random() > 0.05),
            "restricted_zone": 0,
        }
        if incident:
            kind = r.choice(["temperature", "vibration", "speed", "ppe", "restricted", "noise"])
            if kind == "temperature": reading["temperature_c"] = round(r.uniform(86, 104), 2)
            elif kind == "vibration": reading["vibration_mm_s"] = round(r.uniform(12.5, 19), 2)
            elif kind == "speed": reading["forklift_speed_mph"] = round(r.uniform(10.5, 16), 2)
            elif kind == "ppe" and worker: reading[r.choice(["helmet_detected", "vest_detected"])] = 0
            elif kind == "restricted" and worker: reading["restricted_zone"] = 1
            elif kind == "noise": reading["noise_db"] = round(r.uniform(96, 110), 2)
        return reading

    def generate(self, count: int) -> list[dict]:
        return [self.next_reading(index) for index in range(count)]

