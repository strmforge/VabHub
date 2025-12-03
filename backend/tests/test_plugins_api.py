from __future__ import annotations

from pathlib import Path
import sys

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings
from main import app

client = TestClient(app)


def _api_path(path: str) -> str:
    prefix = settings.API_PREFIX or ""
    if prefix.endswith("/"):
        prefix = prefix[:-1]
    if not path.startswith("/"):
        path = f"/{path}"
    return f"{prefix}{path}"


def test_plugin_rest_endpoint():
    resp = client.get(_api_path("/plugins/example_extension_plugin/ping"))
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["success"] is True
    assert payload["data"]["plugin"] == "example_extension_plugin"
    assert payload["data"]["message"] == "pong"


def test_plugin_graphql_field():
    query = """
    query {
      pluginEcho(text: "hi")
    }
    """
    resp = client.post("/graphql", json={"query": query})
    assert resp.status_code == 200
    payload = resp.json()
    assert "errors" not in payload
    assert payload["data"]["pluginEcho"] == "example_extension_plugin:hi"


if __name__ == "__main__":
    test_plugin_rest_endpoint()
    test_plugin_graphql_field()
    print("Plugin extension tests passed.")


