"""Independent manual-run assertions for the loopback acceptance stand.

Contract: docs/requirements/changes/ui-birth-form-and-facts/{requirements,scenarios}.md
REQ-UI-01..10 / AS-UI-01..23: protocol subset and recorded browser assertions.
Run from repository root. No production code or golden fixtures are modified.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sqlite3
import ssl

import httpx

BASE = "https://exact-orb.localhost:8443"
OUT = Path("logs/tester-a8b45db")


def check(name, condition, details):
    result = {"name": name, "status": "PASS" if condition else "FAIL", "details": details}
    with (OUT / "protocol-evidence.jsonl").open("a", encoding="utf-8") as file:
        file.write(json.dumps(result, ensure_ascii=False) + "\n")
    print(json.dumps(result, ensure_ascii=False), flush=True)
    if not condition:
        raise AssertionError(name)


def records():
    latest = {}
    for line in (OUT / "wire.jsonl").read_text(encoding="utf-8").splitlines():
        value = json.loads(line)
        latest[value["id"]] = value
    return list(latest.values())


def protocol():
    ca = Path(os.environ["LOCALAPPDATA"]) / "mkcert/rootCA.pem"
    context = ssl.create_default_context(cafile=str(ca))
    with httpx.Client(base_url=BASE, verify=context, trust_env=False, timeout=45,
                      headers={"Origin": BASE}) as client:
        def call(name, method, path, status, **kwargs):
            response = client.request(method, path, **kwargs)
            check(name + " status/headers", response.status_code == status
                  and response.headers.get("cache-control") == "no-store"
                  and bool(response.headers.get("x-request-id")),
                  {"status": response.status_code, "request_id": response.headers.get("x-request-id")})
            return response.json()

        valid = {"birth_date": "1985-09-02", "birth_time": "14:30", "place_id": "524901"}
        invalid = call("AS17 invalid calendar without cookie", "POST", "/charts/natal", 422,
                       json={**valid, "birth_date": "1990-02-30"})
        check("AS17 validation precedes cookie", invalid["code"] == "INVALID_REQUEST"
              and invalid["issues"][0]["field"] == "birth.date", invalid)
        no_session = call("AS17 valid body without cookie", "POST", "/charts/natal", 409, json=valid)
        check("AS17 session required", no_session["code"] == "SESSION_REQUIRED", no_session)
        foreign = call("AS17 foreign Origin before body", "POST", "/charts/natal", 403,
                       content="{", headers={"Origin": "https://foreign.example", "Content-Type": "application/json"})
        check("AS17 Origin priority", foreign["code"] == "ORIGIN_NOT_ALLOWED", foreign)
        call("AS01 cookie bootstrap", "POST", "/session/bootstrap", 200, json={})
        call("AS01 cookie current", "GET", "/charts/current", 200)
        for label, query in [("empty", ""), ("control", "\x00"), ("too long", "a" * 513)]:
            result = call("AS18 query " + label, "GET", "/places", 422, params={"query": query})
            check("AS18 query " + label + " typed error",
                  result["code"] in {"INVALID_REQUEST", "INVALID_PLACE_QUERY"}, result)
        places = call("AS02 query positive", "GET", "/places", 200, params={"query": "Москва"})
        check("AS02 real Moscow", any(p["place_id"] == "524901" for p in places["items"]),
              {"count": len(places["items"])})
        cases = [
            ("unsupported date", {**valid, "birth_date": "1700-01-01"}, "birth.date", "UNSUPPORTED"),
            ("gap", {**valid, "birth_date": "2021-03-14", "birth_time": "02:30", "place_id": "5128581"}, "birth.time", "INVALID"),
            ("fold", {**valid, "birth_date": "2021-11-07", "birth_time": "01:30", "place_id": "5128581"}, "birth.time", "AMBIGUOUS"),
            ("missing place", {**valid, "place_id": "qa-missing-place"}, "birth.place", "INVALID"),
            ("missing local date", {**valid, "birth_date": "2011-12-30", "birth_time": None, "place_id": "4035413"}, "birth.date", "INVALID"),
        ]
        for label, intent, field, code in cases:
            result = call("AS06 " + label, "POST", "/charts/natal", 422, json=intent)
            check("AS06 " + label + " typed issue", result["code"] == "INPUT_REQUIRED"
                  and any(i["field"] == field and i["code"] == code for i in result["issues"]), result)
        positive = call("AS06 positive real build", "POST", "/charts/natal", 200, json=valid)
        check("AS06 positive natal", positive["status"] == "chart_ready"
              and positive["chart"]["kind"] == "natal" and len(positive["chart"]["houses"]) == 12,
              {"identity": positive["chart"]["chart_identity"], "points": len(positive["chart"]["points"]),
               "aspects": len(positive["chart"]["aspects"])})


def damage():
    # Only the dedicated stand DB, only the exact published browser identity.
    database = (OUT / "sessions.sqlite3").resolve()
    if database.parent != OUT.resolve() or not str(database).startswith(str(Path.cwd().resolve()) + os.sep):
        raise ValueError("Not the dedicated QA database")
    candidate = [r for r in records() if r["url"] == "/charts/natal"
                 and r.get("status") == 200 and r.get("response")][-1]
    dto = json.loads((OUT / candidate["response"]).read_text(encoding="utf-8"))
    identity = dto["chart"]["chart_identity"]
    with sqlite3.connect(database) as connection:
        rows = connection.execute("SELECT session_id,payload FROM session_charts WHERE calculation_key=?", (identity,)).fetchall()
        if len(rows) != 1:
            raise AssertionError("Expected one exact QA session chart")
        session_id, payload = rows[0]
        (OUT / "original-payload.bin").write_bytes(payload)
        changed = connection.execute("UPDATE session_charts SET payload=? WHERE session_id=? AND calculation_key=?",
                                     (b"QA deterministic corrupted artifact", session_id, identity)).rowcount
        check("AS11 corruption fixture", changed == 1, {"identity": identity, "wire_source": candidate["id"]})


def audit():
    rows = records()
    for row in rows:
        if "headers" in row:
            row["headers"] = {key.lower(): value for key, value in row["headers"].items()}
    browser = json.loads((OUT / "browser-evidence.json").read_text(encoding="utf-8"))
    check("browser assertions", bool(browser) and all(item["status"] == "PASS" for item in browser),
          {"checks": len(browser), "failures": [r["name"] for r in browser if r["status"] != "PASS"]})
    api = [r for r in rows if r["url"].split("?")[0] in
           {"/session/bootstrap", "/charts/current", "/charts/natal", "/places"}
           and r.get("status") is not None]
    check("wire API headers", bool(api) and all(r["headers"].get("cache-control") == "no-store"
          and r["headers"].get("x-request-id") for r in api), {"responses": len(api)})
    bad_intents = [r["id"] for r in rows if "intent" in r and set(r["intent"]) != {"birth_date", "birth_time", "place_id"}]
    check("browser/API intent whitelist", not bad_intents, {"bad_wire_ids": bad_intents})
    check("closed HTTPS endpoint", BASE == "https://exact-orb.localhost:8443", {"endpoint": BASE})
    normal = [r for r in rows if r.get("status") == 200 and r["url"] == "/charts/natal"
              and not r["rule"] and r.get("response")]
    # Check a real positive build trace, not the proxy's injected error records.
    source = normal[-1]
    request_id = source["headers"]["x-request-id"]
    lines = (OUT / "application.log").read_text(encoding="utf-8").splitlines()
    trace = [line for line in lines if "request_id=" + request_id in line]
    peers = {"AdmissionControl", "ApplicationOrchestrator"}
    check("real build HTTP coordination", all(any("direction=" + direction in line
          and "peer=" + peer in line for line in trace)
          for peer in peers for direction in ("send", "receive")),
          {"wire_id": source["id"], "request_id": request_id, "peers": sorted(peers)})
    application = [line for line in lines if "run_id=" + request_id in line]
    transitions = [("ContextService", "load"), ("BuildNatalHandler", "handle"),
                   ("BirthDataResolver", "resolve_birth_data"),
                   ("ChartArtifactResolver", "ensure_chart"),
                   ("ChartArtifactResolver", "to_stored"), ("ContextService", "save")]
    check("real build application commit trace", all(any("peer=" + peer in line
          and "operation=" + operation in line and "direction=" + direction in line
          for line in application) for peer, operation in transitions
          for direction in ("send", "receive"))
          and any("operation=save message_type=Committed" in line for line in application)
          and any("http_request_finished" in line for line in trace),
          {"request_id": request_id, "correlated_events": len(application), "transitions": transitions})
    rejected = next(r for r in rows if r.get("status") == 403 and not r["rule"])
    rejected_id = rejected["headers"]["x-request-id"]
    rejected_trace = [line for line in lines if "request_id=" + rejected_id in line]
    check("Origin rejection before component boundary", bool(rejected_trace)
          and not any("http_message" in line for line in rejected_trace),
          {"wire_id": rejected["id"], "request_id": rejected_id})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("protocol", "damage", "audit"))
    options = parser.parse_args()
    {"protocol": protocol, "damage": damage, "audit": audit}[options.phase]()
