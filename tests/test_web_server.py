"""Unit tests for the STARFALL Textmode Web Companion API server."""

import json
import threading
import time
from http.server import ThreadingHTTPServer
from urllib.request import urlopen, Request

import pytest
from web.server import StarfallWebHandler


@pytest.fixture(scope="module")
def web_server():
    server = ThreadingHTTPServer(("127.0.0.1", 8912), StarfallWebHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.1)
    yield "http://127.0.0.1:8912"
    server.shutdown()
    server.server_close()


def test_web_status_endpoint(web_server):
    with urlopen(f"{web_server}/api/status") as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert data["status"] == "online"
        assert "app_name" in data
        assert "ai" in data
        assert "gameplay" in data


def test_web_matches_endpoint(web_server):
    with urlopen(f"{web_server}/api/matches") as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert "matches" in data
        assert isinstance(data["matches"], list)


def test_web_static_html_served(web_server):
    with urlopen(f"{web_server}/") as resp:
        assert resp.status == 200
        content = resp.read().decode("utf-8")
        assert "STARFALL" in content
        assert "textmodeCanvas" in content


def test_web_static_css_served(web_server):
    with urlopen(f"{web_server}/style.css") as resp:
        assert resp.status == 200
        content = resp.read().decode("utf-8")
        assert "--accent-red" in content
