import json
import threading
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer

from safety_sentinel.database import SafetyDatabase
from safety_sentinel.server import DashboardHandler


def test_api_status_codes_distinguish_missing_routes(tmp_path):
    class Handler(DashboardHandler):
        database = SafetyDatabase(tmp_path / 'events.db')

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    connection = HTTPConnection(*server.server_address, timeout=3)
    try:
        connection.request('GET', '/api/metrics')
        response = connection.getresponse()
        assert response.status == 200
        assert json.loads(response.read())['readings'] == 0

        connection.request('GET', '/api/readings')
        response = connection.getresponse()
        assert response.status == 200
        assert json.loads(response.read()) == []

        connection.request('GET', '/api/missing')
        response = connection.getresponse()
        assert response.status == 404
        assert response.getheader('Content-Type') == 'application/json'
        assert json.loads(response.read()) == {'error': 'not found'}
    finally:
        connection.close()
        server.shutdown()
        server.server_close()
        worker.join(timeout=3)
