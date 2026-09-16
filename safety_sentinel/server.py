from __future__ import annotations

import json
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from safety_sentinel.config import DB_PATH, MODEL_PATH, STATIC_DIR
from safety_sentinel.database import SafetyDatabase
from safety_sentinel.generator import SafetyDataGenerator
from safety_sentinel.model import AnomalyModel
from safety_sentinel.pipeline import process_reading


class DashboardHandler(SimpleHTTPRequestHandler):
    database = SafetyDatabase(DB_PATH)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def do_GET(self):
        path = urlparse(self.path).path
        if path.startswith("/api/"):
            payload = self.api_payload(path)
            body = json.dumps(payload).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()

    def api_payload(self, path: str):
        if path == "/api/readings": return self.database.latest_readings()
        if path == "/api/alerts": return self.database.latest_alerts()
        if path == "/api/metrics": return self.database.metrics()
        return {"error": "not found"}

    def log_message(self, format, *args):
        return


def stream_events(stop: threading.Event, interval: float = 1.0) -> None:
    database = SafetyDatabase(DB_PATH)
    generator = SafetyDataGenerator(seed=int(time.time()))
    if Path(MODEL_PATH).exists():
        model = AnomalyModel.load(MODEL_PATH)
    else:
        baseline = SafetyDataGenerator(seed=42, incident_rate=0).generate(500)
        model = AnomalyModel().train(baseline)
        model.save(MODEL_PATH)
    index = 0
    while not stop.is_set():
        process_reading(database, model, generator.next_reading(index))
        index += 1
        stop.wait(interval)


def main(host: str = "0.0.0.0", port: int = 8000) -> None:
    stop = threading.Event()
    producer = threading.Thread(target=stream_events, args=(stop,), daemon=True)
    producer.start()
    server = ThreadingHTTPServer((host, port), DashboardHandler)
    print(f"Industrial Safety Sentinel running at http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        server.server_close()


if __name__ == "__main__":
    main()

