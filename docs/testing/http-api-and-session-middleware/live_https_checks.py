"""Local live HTTPS acceptance helper; run in phases around a process restart."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys

import httpx


BASE = "https://exact-orb.localhost"
LOCAL_APP_DATA = Path(os.environ["LOCALAPPDATA"])
CA = LOCAL_APP_DATA / "mkcert" / "rootCA.pem"
STATE = Path(os.environ.get(
    "EXACT_ORB_MANUAL_STATE_PATH",
    str(LOCAL_APP_DATA / "exact-orb-http-manual" / "smoke-state.json"),
))


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def show(name: str, response: httpx.Response) -> None:
    print(
        f"{name} PASS status={response.status_code} "
        f"request_id={response.headers.get('x-request-id', 'none')}"
    )


def trace_response(response: httpx.Response) -> None:
    """Record every endpoint call without cookies or request/response bodies."""
    query = response.request.url.params.get("query")
    readable_query = f" query={query!r}" if query is not None else ""
    print(
        f"HTTP method={response.request.method} url={response.request.url}"
        f"{readable_query} "
        f"status={response.status_code} "
        f"request_id={response.headers.get('x-request-id', 'none')}",
        flush=True,
    )


def app_response(response: httpx.Response, status: int) -> dict:
    expect(response.status_code == status, f"{response.request.url}: {response.status_code} {response.text[:500]}")
    expect(response.headers.get("cache-control") == "no-store", "Cache-Control missing")
    expect(bool(response.headers.get("x-request-id")), "X-Request-ID missing")
    return response.json()


def client() -> httpx.Client:
    return httpx.Client(
        base_url=BASE,
        transport=httpx.HTTPTransport(
            # 127.0.0.1 is the trusted Caddy peer. A distinct loopback client
            # address exposes the currently broken default localhost path.
            verify=str(CA), trust_env=False, local_address="127.0.0.2"
        ),
        trust_env=False,
        timeout=45.0,
        headers={"Origin": BASE},
        event_hooks={"response": [trace_response]},
    )


def phase1() -> None:
    with httpx.Client(
        trust_env=False, timeout=10.0,
        event_hooks={"response": [trace_response]},
    ) as direct:
        live = direct.get("http://127.0.0.1:8000/health/live")
        ready = direct.get("http://127.0.0.1:8000/health/ready")
        expect(live.status_code == ready.status_code == 200, "internal health not 200")
        show("M-01-internal-live", live)
        show("M-01-internal-ready", ready)

    with client() as c:
        public_health = c.get("/health/live")
        expect(public_health.status_code == 404, "public health not 404")
        show("M-01-public-health", public_health)

        bootstrap = c.post("/session/bootstrap", json={})
        body = app_response(bootstrap, 200)
        expect(body == {"status": "ready", "state_version": 0}, f"bootstrap body {body}")
        set_cookie = bootstrap.headers.get("set-cookie", "")
        for marker in ("__Host-exact_orb_session=", "HttpOnly", "Secure", "SameSite=Lax", "Path=/", "Max-Age=604800"):
            expect(marker.lower() in set_cookie.lower(), f"cookie missing {marker}")
        expect("domain=" not in set_cookie.lower(), "cookie has Domain")
        cookie = c.cookies.get("__Host-exact_orb_session")
        expect(cookie is not None and len(cookie) == 43, "session cookie not captured")
        show("M-02-bootstrap", bootstrap)

        empty = c.get("/charts/current")
        body = app_response(empty, 200)
        expect(body == {"status": "empty", "state_version": 0, "birth": None, "chart": None, "chart_stale": None}, f"empty body {body}")
        show("M-03-empty-current", empty)

        places = c.get("/places", params={"query": "Москва", "limit": "10"})
        body = app_response(places, 200)
        items = body.get("items", [])
        matches = [item for item in items if item.get("place_id") == "524901"]
        expect(bool(matches), f"Moscow missing in {items}")
        expect(set(matches[0]) == {"place_id", "display_name", "admin1_name", "country_code"}, "place whitelist mismatch")
        expect("set-cookie" not in places.headers, "place search touched cookie")
        place_id = matches[0]["place_id"]
        show("M-04-place-search", places)

        natal = c.post("/charts/natal", json={"birth_date": "1990-09-02", "birth_time": "14:30", "place_id": place_id})
        body = app_response(natal, 200)
        expect(body.get("status") == "chart_ready" and body.get("chart", {}).get("kind") == "natal", f"natal body {body}")
        natal_version = body["state_version"]
        natal_identity = body["chart"]["chart_identity"]
        expect(natal_version > 0 and bool(natal_identity), "natal version/identity missing")
        show("M-05-natal-build", natal)

        current = c.get("/charts/current")
        body = app_response(current, 200)
        expect(body.get("status") == "chart_ready" and body.get("state_version") == natal_version, "current version mismatch")
        expect(body.get("chart", {}).get("chart_identity") == natal_identity, "current chart mismatch")
        expect(body.get("birth", {}).get("birth_time") == "14:30" and body.get("chart_stale") is False, "birth/stale mismatch")
        show("M-06-natal-current", current)

        cosmogram = c.post("/charts/natal", json={"birth_date": "1990-09-02", "birth_time": None, "place_id": place_id})
        body = app_response(cosmogram, 200)
        chart = body.get("chart", {})
        expect(body.get("status") == "chart_ready" and chart.get("kind") == "cosmogram", f"cosmogram body {body}")
        expect(chart.get("house_system") is None and chart.get("angles") is None and chart.get("houses") is None, "cosmogram timed fields")
        expect(all(point.get("house") is None for point in chart.get("points", [])), "cosmogram point house")
        final_version = body["state_version"]
        final_identity = chart["chart_identity"]
        expect(final_version > natal_version, "cosmogram version not advanced")
        show("M-07-cosmogram-build", cosmogram)
        current = c.get("/charts/current")
        body = app_response(current, 200)
        expect(body.get("state_version") == final_version and body.get("chart", {}).get("chart_identity") == final_identity, "cosmogram current mismatch")
        expect(body.get("birth", {}).get("birth_time") is None and body.get("birth", {}).get("utc_offset_seconds") is None, "unknown time projection")
        show("M-07-cosmogram-current", current)

        invalid_limit = c.get("/places", params={"query": "Москва", "limit": "010"})
        body = app_response(invalid_limit, 422)
        expect(body.get("code") == "INVALID_REQUEST" and body.get("detail_code") == "LIMIT_INVALID", f"limit body {body}")
        show("M-08-invalid-limit", invalid_limit)
        valid_limit = c.get("/places", params={"query": "Москва", "limit": "10"})
        body = app_response(valid_limit, 200)
        expect(any(item.get("place_id") == place_id for item in body.get("items", [])), "limit positive control")
        show("M-08-valid-control", valid_limit)

        wrong_origin = c.get("/charts/current", headers={"Origin": "https://invalid.example"})
        body = app_response(wrong_origin, 403)
        expect(body.get("code") == "ORIGIN_NOT_ALLOWED", f"origin body {body}")
        show("M-09-wrong-origin", wrong_origin)
        current = c.get("/charts/current")
        body = app_response(current, 200)
        expect(body.get("chart", {}).get("chart_identity") == final_identity, "origin mutated chart")
        show("M-09-valid-control", current)

        invalid_date = c.post("/charts/natal", json={"birth_date": "1990-02-30", "birth_time": None, "place_id": place_id})
        body = app_response(invalid_date, 422)
        expect(body.get("code") == "INVALID_REQUEST", f"date body {body}")
        expect(any(issue.get("field") == "birth.date" for issue in body.get("issues", [])), f"date issue {body}")
        show("M-10-invalid-date", invalid_date)
        current = c.get("/charts/current")
        body = app_response(current, 200)
        expect(body.get("state_version") == final_version and body.get("chart", {}).get("chart_identity") == final_identity, "date mutated chart")
        show("M-10-valid-control", current)

        STATE.parent.mkdir(parents=True, exist_ok=True)
        STATE.write_text(json.dumps({"cookie": cookie, "version": final_version, "identity": final_identity}), encoding="utf-8")
        print("PHASE1 PASS state saved for restart")


def phase2() -> None:
    state = json.loads(STATE.read_text(encoding="utf-8"))
    with client() as c:
        c.cookies.set("__Host-exact_orb_session", state["cookie"], domain="exact-orb.localhost", path="/")
        bootstrap = c.post("/session/bootstrap", json={})
        body = app_response(bootstrap, 200)
        expect(body == {"status": "ready", "state_version": state["version"]}, f"restart bootstrap {body}")
        show("M-11-restore-bootstrap", bootstrap)
        current = c.get("/charts/current")
        body = app_response(current, 200)
        expect(body.get("status") == "chart_ready" and body.get("state_version") == state["version"], f"restart current {body}")
        expect(body.get("chart", {}).get("chart_identity") == state["identity"], "restart identity mismatch")
        show("M-11-restore-current", current)
    print("PHASE2 PASS")


def supplemental() -> None:
    with client() as c:
        absent = c.get("/charts/current")
        body = app_response(absent, 409)
        expect(body.get("code") == "SESSION_REQUIRED", f"absent cookie body {body}")
        show("extra-current-no-cookie", absent)

        bootstrap = c.post("/session/bootstrap", json={})
        app_response(bootstrap, 200)
        cookie = c.cookies.get("__Host-exact_orb_session")
        expect(cookie is not None, "new cookie missing")
        expect(len(bootstrap.headers.get_list("set-cookie")) == 1, "bootstrap cookie count")
        show("extra-bootstrap", bootstrap)
        current = c.get("/charts/current")
        app_response(current, 200)
        expect(len(current.headers.get_list("set-cookie")) == 1, "current cookie count")
        expect(c.cookies.get("__Host-exact_orb_session") == cookie, "current changed session ID")
        expect(f"__Host-exact_orb_session={cookie}" in current.headers["set-cookie"], "current did not renew cookie")
        show("extra-cookie-renewal", current)
    print("SUPPLEMENTAL PASS")


def proxy_control() -> None:
    """Reproduce FIND-TEST-HTTP-001 with the default loopback source address."""
    with httpx.Client(
        base_url=BASE, verify=str(CA), trust_env=False, timeout=10.0,
        headers={"Origin": BASE}, event_hooks={"response": [trace_response]},
    ) as c:
        response = c.post("/session/bootstrap", json={})
        body = app_response(response, 400)
        expect(body.get("code") == "FORWARDED_HEADER_INVALID",
               f"proxy control changed: {body}")
        show("proxy-default-loopback-expected-rejection", response)


def place_prefixes() -> None:
    """HTTP requirements §6.3; place catalog requirements §4.3, real catalog."""
    cases = (
        ("M-12-one-character", "Н", {
            "523523": "Нальчик",
            "520555": "Нижний Новгород",
            "1496747": "Новосибирск",
        }),
        ("M-13-two-characters", "Но", {
            "1496747": "Новосибирск",
            "1496990": "Новокузнецк",
            "518557": "Новомосковск",
            "699917": "Носовка",
        }),
        ("M-14-three-characters", "Нов", {
            "1514856": "Нов",
            "1496747": "Новосибирск",
            "1496990": "Новокузнецк",
        }),
    )
    with client() as c:
        for name, query, expected in cases:
            response = c.get("/places", params={"query": query})
            body = app_response(response, 200)
            items = body.get("items")
            expect(isinstance(items, list) and len(items) == 10,
                   f"{name}: expected ten real-catalog suggestions: {items}")
            ids = [item["place_id"] for item in items]
            expect(len(set(ids)) == len(ids), f"{name}: duplicate place_id: {ids}")
            expect(all(set(item) == {"place_id", "display_name", "admin1_name", "country_code"}
                       for item in items), f"{name}: public item fields differ")
            actual = {item["place_id"]: item["display_name"] for item in items}
            for place_id, display_name in expected.items():
                expect(actual.get(place_id) == display_name,
                       f"{name}: {display_name} ({place_id}) missing: {actual}")
            if query == "Но":
                expect("520555" not in actual,
                       f"{name}: narrower prefix still includes Нижний Новгород")
            if query == "Нов":
                expect(items[0]["place_id"] == "1514856",
                       f"{name}: exact match Нов is not first")
                expect("699917" not in actual,
                       f"{name}: narrower prefix still includes Носовка")
            expect("set-cookie" not in response.headers,
                   f"{name}: place search changed session cookie")
            show(name, response)
            print(f"  query={query!r} items={len(items)}")
            for item in items:
                print(
                    f"  place_id={item['place_id']} name={item['display_name']!r} "
                    f"admin1={item['admin1_name']!r} country={item['country_code']}"
                )
    print("PLACE_PREFIXES PASS: 3 real-catalog HTTPS cases")


if __name__ == "__main__":
    {"phase1": phase1, "phase2": phase2, "supplemental": supplemental,
     "place_prefixes": place_prefixes, "proxy_control": proxy_control}[sys.argv[1]]()
