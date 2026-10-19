import json
import os
import shutil
import subprocess
import time
from urllib.error import HTTPError
from urllib.request import urlopen

import pytest


@pytest.mark.skipif(shutil.which("npm") is None, reason="npm is required for Vite proxy integration")
def test_vite_proxy_returns_structured_error_when_backend_is_unavailable():
    web_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web")
    env = os.environ.copy()
    env["INVARIANTQ_API_TARGET"] = "http://127.0.0.1:8765"
    port = "5174"
    npm = shutil.which("npm")
    process = subprocess.Popen(
        [npm, "run", "dev", "--", "--host", "127.0.0.1", "--port", port],
        cwd=web_dir,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        deadline = time.time() + 20
        while time.time() < deadline:
            try:
                urlopen(f"http://127.0.0.1:{port}/", timeout=1).read()
                break
            except Exception:
                time.sleep(0.25)
        else:
            output = process.stdout.read() if process.stdout else ""
            pytest.fail(f"Vite did not start: {output}")

        request = __import__("urllib.request", fromlist=["Request"]).Request(
            f"http://127.0.0.1:{port}/api/run",
            data=b'{"code":"qubit q[1];","shots":1}',
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with pytest.raises(HTTPError) as raised:
            urlopen(request, timeout=5)
        response = raised.value
        assert response.status == 503
        assert response.headers["Content-Type"].startswith("application/json")
        payload = json.loads(response.read())
        assert payload["status"] == "error"
        assert "backend is unavailable" in payload["message"]
    finally:
        process.terminate()
        process.wait(timeout=10)
