import json
import threading
from http.client import HTTPConnection

import pytest

from invariantq.distributed.server import InvariantQServerHandler
from http.server import ThreadingHTTPServer


@pytest.fixture
def api_server():
    server = ThreadingHTTPServer(("127.0.0.1", 0), InvariantQServerHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def request(server, method, path, body=None):
    connection = HTTPConnection("127.0.0.1", server.server_port, timeout=20)
    payload = None if body is None else json.dumps(body)
    connection.request(method, path, body=payload, headers={"Content-Type": "application/json"})
    response = connection.getresponse()
    raw = response.read()
    connection.close()
    return response.status, response.getheader("Content-Type"), json.loads(raw)


def test_health_and_real_circuit_execution(api_server):
    status, content_type, health = request(api_server, "GET", "/api/health")
    assert status == 200
    assert content_type.startswith("application/json")
    assert health["status"] == "ok"
    assert health["workers"] == 4

    status, _, result = request(
        api_server,
        "POST",
        "/api/run",
        {"code": "qubit q[1]; h q[0];", "backend": "statevector", "shots": 8, "seed": 42},
    )
    assert status == 200
    assert result["status"] == "success"
    assert sum(result["counts"].values()) == 8


def test_api_returns_structured_errors_for_bad_json_and_invalid_payload(api_server):
    connection = HTTPConnection("127.0.0.1", api_server.server_port, timeout=20)
    connection.request("POST", "/api/run", body="{bad", headers={"Content-Type": "application/json"})
    response = connection.getresponse()
    assert response.status == 400
    assert response.getheader("Content-Type").startswith("application/json")
    assert json.loads(response.read())["status"] == "error"
    connection.close()

    status, _, error = request(api_server, "POST", "/api/run", {"code": "qubit q[1];", "shots": "many"})
    assert status == 400
    assert "shots" in error["message"]

    status, _, error = request(api_server, "POST", "/api/does-not-exist", {})
    assert status == 404
    assert error["status"] == "error"


def test_compile_and_distributed_routes_return_real_results(api_server):
    code = "qubit q[2]; h q[0]; cx q[0], q[1];"
    status, _, compiled = request(api_server, "POST", "/api/compile", {"code": code, "opt_level": 2})
    assert status == 200
    assert compiled["status"] == "success"
    assert compiled["is_equivalent"] is True

    status, _, distributed = request(
        api_server, "POST", "/api/distributed/run", {"code": code, "shots": 16, "seed": 42}
    )
    assert status == 200
    assert distributed["status"] == "success"
    assert distributed["total_shots"] == 16


def test_protocol_routes_return_mathematical_results(api_server):
    status, _, entanglement = request(
        api_server, "POST", "/api/protocols/entanglement", {"state": "bell"}
    )
    assert status == 200
    assert entanglement["status"] == "success"
    assert entanglement["von_neumann_entropy_bits"] == pytest.approx(1.0)

    status, _, dense = request(
        api_server, "POST", "/api/protocols/superdense", {"shots": 2, "seed": 3}
    )
    assert status == 200
    assert all(item["correct"] for item in dense["messages"].values())

    status, _, teleport = request(
        api_server,
        "POST",
        "/api/protocols/teleportation",
        {
            "alpha": [2**-0.5, 0],
            "beta": [0, 2**-0.5],
            "shots": 4,
            "seed": 3,
        },
    )
    assert status == 200
    assert teleport["verified"] is True
