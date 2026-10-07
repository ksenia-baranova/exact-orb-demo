"""REQ-UI-01/10, AS-UI-01/19: доставка страницы; приёмка полного UI ещё впереди.

Контракт: docs/requirements/changes/ui-birth-form-and-facts/requirements.md
на ce25dd0; DEV-UI-01/04/05 не добавляют бизнес-операций при доставке ресурсов.
"""

from __future__ import annotations

from html.parser import HTMLParser
from importlib.resources import files
import json
import logging
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from tests.http_api.conftest import http_settings


UI_RESOURCES = (
    "index.html", "styles.css", "main.mjs", "transport.mjs", "form.mjs",
    "places.mjs", "session.mjs", "facts.mjs", "recovery.mjs", "response.mjs",
)


class AssetReferences(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.paths: list[str] = []
        self.module_paths: list[str] = []
        self.language: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "html":
            self.language = values.get("lang")
        if tag == "link" and values.get("rel") == "stylesheet":
            self.paths.append(values["href"])
        if tag == "script":
            self.paths.append(values["src"])
            if values.get("type") == "module":
                self.module_paths.append(values["src"])


async def test_page_and_its_modules_are_same_origin_package_resources(app_client, runtime) -> None:
    async with app_client(runtime) as client:
        page = await client.get("/")
        assert page.status_code == 200
        assert page.headers["content-type"].startswith("text/html")
        assert page.headers["cache-control"] == "no-store"
        assert "Set-Cookie" not in page.headers
        parser = AssetReferences()
        parser.feed(page.text)
        assert parser.language == "ru"
        assert parser.paths == ["/ui/styles.css", "/ui/main.mjs"]
        assert parser.module_paths == ["/ui/main.mjs"]
        resource = files("exact_orb.http_api").joinpath("ui")
        assert page.content == resource.joinpath("index.html").read_bytes()
        for path in (*parser.paths, *("/ui/" + name for name in UI_RESOURCES
                                     if name.endswith(".mjs") and name != "main.mjs")):
            asset = await client.get(path)
            assert asset.status_code == 200
            # REQ-UI-01/10, AS-UI-01/10; TEST-FIND-UI-009, найдено другой моделью.
            assert asset.headers.get("cache-control") == "no-cache"
            assert asset.headers["etag"]
            assert asset.headers["last-modified"]
            for header, value in (
                ("If-None-Match", asset.headers["etag"]),
                ("If-Modified-Since", asset.headers["last-modified"]),
            ):
                cached = await client.get(path, headers={header: value})
                assert cached.status_code == 304
                assert cached.content == b""
                assert cached.headers.get("cache-control") == "no-cache"
                assert cached.headers["etag"] == asset.headers["etag"]
            assert "Set-Cookie" not in asset.headers
            assert asset.content == resource.joinpath(path.rsplit("/", 1)[1]).read_bytes()
            mime = asset.headers["content-type"].split(";", 1)[0]
            assert mime in ({"text/css"} if path.endswith(".css") else {
                "text/javascript", "application/javascript",
            })
        assert runtime.context.create_calls == []
        assert runtime.context.load_calls == []
        assert runtime.context.save_calls == []
        runtime.assert_no_calculation()
        # Позитивный контроль: существующий business route выполняет bootstrap/current.
        assert (await client.post("/session/bootstrap", json={})).status_code == 200
        assert (await client.get("/charts/current")).json()["status"] == "empty"
        assert len(runtime.context.create_calls) == 1
        assert len(runtime.context.load_calls) == 1
        runtime.assert_no_calculation()


async def test_assets_do_not_create_business_request_events(app_client, runtime, caplog) -> None:
    caplog.set_level(logging.INFO, logger="exact_orb.http_api")
    async with app_client(runtime) as client:
        for name in UI_RESOURCES:
            assert (await client.get("/" if name == "index.html" else "/ui/" + name)).status_code == 200
        assert not any(record.getMessage().startswith("http_request_") for record in caplog.records)
        control = await client.post("/session/bootstrap", json={})
        assert control.status_code == 200
    events = [record.getMessage() for record in caplog.records
              if record.getMessage().startswith(("http_request_started ", "http_request_finished "))]
    assert len(events) == 2
    assert all(f"request_id={control.headers['X-Request-ID']}" in event for event in events)


@pytest.mark.parametrize("path", ("/ui/missing.mjs", "/ui/%2e%2e/app.py", "/not-a-route"))
async def test_asset_mount_preserves_safe_404_and_blocks_parent_traversal(path, app_client, runtime) -> None:
    async with app_client(runtime) as client:
        response = await client.get(path)
        assert response.status_code == 404
        assert response.json()["code"] == "NOT_FOUND"
        assert response.headers["cache-control"] == "no-store"
        assert (await client.get("/ui/styles.css")).status_code == 200
    assert runtime.context.create_calls == []
    assert runtime.context.load_calls == []
    runtime.assert_no_calculation()


async def test_ui_methods_do_not_intercept_business_or_health_routes(app_client, runtime) -> None:
    async with app_client(runtime) as client:
        for path in ("/", "/ui/styles.css"):
            wrong_method = await client.post(path, json={})
            assert wrong_method.status_code == 405
            assert wrong_method.json()["code"] == "METHOD_NOT_ALLOWED"
        asset_head = await client.head("/ui/styles.css")
        assert asset_head.status_code == 200
        assert asset_head.headers.get("cache-control") == "no-cache"
        assert asset_head.content == b""
        current = await client.get("/charts/current")
        assert current.status_code == 409
        assert current.json()["code"] == "SESSION_REQUIRED"
        assert (await client.get("/health/ready")).status_code == 200
        assert (await client.get("/health/live")).status_code == 200
    assert runtime.context.create_calls == []
    assert runtime.context.load_calls == []
    runtime.assert_no_calculation()


def test_installed_wheel_serves_assets_without_source_checkout(tmp_path: Path) -> None:
    """DEV-UI-01/04: весь UI, включая reader, доставляется из wheel вне checkout."""
    repository = Path(__file__).resolve().parents[2]
    project = tmp_path / "project"
    project.mkdir()
    shutil.copy2(repository / "pyproject.toml", project / "pyproject.toml")
    shutil.copytree(repository / "src", project / "src",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    wheels = tmp_path / "wheels"
    installed = tmp_path / "installed"
    commands = (
        [sys.executable, "-B", "-m", "pip", "wheel", "--no-deps", "--no-index",
         "--no-build-isolation", "--wheel-dir", str(wheels), str(project)],
    )
    for command in commands:
        built = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True, timeout=120)
        assert built.returncode == 0, built.stdout + built.stderr
    wheel, = wheels.glob("exact_orb-*.whl")
    installed_result = subprocess.run(
        [sys.executable, "-B", "-m", "pip", "install", "--no-deps", "--no-index",
         "--target", str(installed), str(wheel)],
        cwd=tmp_path, capture_output=True, text=True, timeout=120,
    )
    assert installed_result.returncode == 0, installed_result.stdout + installed_result.stderr
    # Новый процесс вне исходников: реальные маршруты и ресурсы, запрещён вызов фабрик.
    probe = '''
import asyncio
from datetime import datetime, timezone
from importlib.resources import files
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import httpx
import exact_orb.http_api.app as module

assert Path(module.__file__).resolve().is_relative_to(Path(sys.argv[1]).resolve())
resource = files("exact_orb.http_api").joinpath("ui")
names = json.loads(sys.argv[3])
for name in names:
    assert resource.joinpath(name).read_bytes()
settings = SimpleNamespace(**json.loads(sys.argv[2]))
settings.allowed_origins = tuple(settings.allowed_origins)
settings.trusted_proxy_cidrs = tuple(settings.trusted_proxy_cidrs)
def forbidden(*args):
    raise AssertionError("asset delivery must not open runtime/catalog")
app = module.create_app(settings=settings, runtime_factory=forbidden, catalog_factory=forbidden,
                        utc_clock=lambda: datetime.now(timezone.utc), scheduler=module.MonotonicScheduler())
async def check():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="https://testserver") as client:
        for name in names:
            path = "/" if name == "index.html" else "/ui/" + name
            response = await client.get(path)
            assert response.status_code == 200, (path, response.status_code)
            assert response.content == resource.joinpath(name).read_bytes()
            if name.endswith((".mjs", ".css")):
                assert response.headers.get("cache-control") == "no-cache"
                cached = await client.get(path, headers={"If-None-Match": response.headers["etag"]})
                assert cached.status_code == 304
                assert cached.headers.get("cache-control") == "no-cache"
                assert cached.content == b""
            assert "Set-Cookie" not in response.headers
asyncio.run(check())
print(f"installed wheel: {len(names)} UI resources delivered without checkout")
'''
    env = dict(os.environ, PYTHONPATH=str(installed), PYTHONDONTWRITEBYTECODE="1")
    checked = subprocess.run(
        [sys.executable, "-B", "-c", probe, str(installed), json.dumps(vars(http_settings())),
         json.dumps(UI_RESOURCES)],
        cwd=tmp_path, env=env, capture_output=True, text=True, timeout=30,
    )
    assert checked.returncode == 0, checked.stdout + checked.stderr
    assert f"installed wheel: {len(UI_RESOURCES)} UI resources delivered without checkout" in checked.stdout
