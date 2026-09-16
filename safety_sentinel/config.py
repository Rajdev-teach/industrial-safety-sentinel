from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
MODEL_DIR = ROOT / "models"
STATIC_DIR = ROOT / "dashboard"
DB_PATH = DATA_DIR / "safety_events.db"
MODEL_PATH = MODEL_DIR / "isolation_forest.joblib"

THRESHOLDS = {
    "temperature_c": {"warning": 75.0, "critical": 85.0},
    "vibration_mm_s": {"warning": 8.0, "critical": 12.0},
    "forklift_speed_mph": {"warning": 8.0, "critical": 10.0},
    "noise_db": {"warning": 85.0, "critical": 95.0},
}
