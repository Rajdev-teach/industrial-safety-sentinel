from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    device_id TEXT NOT NULL,
    zone TEXT NOT NULL,
    temperature_c REAL NOT NULL,
    vibration_mm_s REAL NOT NULL,
    forklift_speed_mph REAL NOT NULL,
    noise_db REAL NOT NULL,
    worker_present INTEGER NOT NULL,
    helmet_detected INTEGER NOT NULL,
    vest_detected INTEGER NOT NULL,
    restricted_zone INTEGER NOT NULL,
    anomaly_score REAL DEFAULT 0,
    is_anomaly INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    reading_id INTEGER,
    device_id TEXT NOT NULL,
    zone TEXT NOT NULL,
    alert_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    message TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'OPEN',
    FOREIGN KEY(reading_id) REFERENCES readings(id)
);
CREATE INDEX IF NOT EXISTS idx_readings_timestamp ON readings(timestamp);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);
"""


class SafetyDatabase:
    def __init__(self, path: str | Path):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(SCHEMA)

    def insert_reading(self, reading: dict) -> int:
        fields = [
            "timestamp", "device_id", "zone", "temperature_c", "vibration_mm_s",
            "forklift_speed_mph", "noise_db", "worker_present", "helmet_detected",
            "vest_detected", "restricted_zone", "anomaly_score", "is_anomaly",
        ]
        values = [reading.get(field, 0) for field in fields]
        with self.connect() as connection:
            cursor = connection.execute(
                f"INSERT INTO readings ({','.join(fields)}) VALUES ({','.join('?' for _ in fields)})",
                values,
            )
            return int(cursor.lastrowid)

    def insert_alerts(self, reading_id: int, alerts: list[dict]) -> None:
        if not alerts:
            return
        with self.connect() as connection:
            connection.executemany(
                """INSERT INTO alerts
                (timestamp, reading_id, device_id, zone, alert_type, severity, message)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                [
                    (
                        item["timestamp"], reading_id, item["device_id"], item["zone"],
                        item["alert_type"], item["severity"], item["message"],
                    )
                    for item in alerts
                ],
            )

    def latest_readings(self, limit: int = 40) -> list[dict]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM readings ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(row) for row in reversed(rows)]

    def latest_alerts(self, limit: int = 20) -> list[dict]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM alerts ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(row) for row in rows]

    def metrics(self) -> dict:
        with self.connect() as connection:
            readings = connection.execute("SELECT COUNT(*) FROM readings").fetchone()[0]
            alerts = connection.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
            critical = connection.execute(
                "SELECT COUNT(*) FROM alerts WHERE severity='CRITICAL'"
            ).fetchone()[0]
            open_alerts = connection.execute(
                "SELECT COUNT(*) FROM alerts WHERE status='OPEN'"
            ).fetchone()[0]
        return {"readings": readings, "alerts": alerts, "critical": critical, "open": open_alerts}

