"""Tester-only loopback HTTPS wire seam; production app runs unchanged on 8001.

REQ-UI-01..10 / AS-UI-01..23. Ordinary requests reach the real application.
POST http://127.0.0.1:9009/arm: {case, rules:[{method,path,query?,mode?,gate?,
status?,body?,text?,headers?}]}. Gates are threading.Event, never timed delays.
Modes: override, forward (default), abort, abort_after_forward, abort_then_forward.
GET /state records ordering and response filenames; POST /release {gate} releases
one barrier. Control listener is separate from HTTPS and bound to loopback only.
Synthetic data only; cookies are forwarded but never recorded. This is a manual
browser acceptance harness, not a replacement for server lifecycle tests.
"""
from __future__ import annotations

import argparse
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import socket
import ssl
import threading
import time
from urllib.parse import urlsplit, parse_qs


class State:
    def __init__(self, directory: Path):
        self.directory = directory
        directory.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        self.case = "startup"
        self.rules = []
        self.gates = {}
        self.records = []
        self.changed = threading.Condition(self.lock)
        wire = directory / "wire.jsonl"
        if wire.exists():
            latest = {}
            for line in wire.read_text(encoding="utf-8").splitlines():
                row = json.loads(line)
                latest[row["id"]] = row
            self.records = [latest[key] for key in sorted(latest)]

    def log(self, record, **changes):
        with self.changed:
            record.update(changes)
            with (self.directory / "wire.jsonl").open("a", encoding="utf-8") as out:
                out.write(json.dumps(record, ensure_ascii=False) + "\n")
            self.changed.notify_all()

    def enter(self, method, url, body, referer):
        parsed = urlsplit(url)
        with self.lock:
            rule = {}
            for index, candidate in enumerate(self.rules):
                if (candidate["path"] == parsed.path
                        and candidate.get("method", "GET") == method
                        and ("referer_contains" not in candidate or
                             candidate["referer_contains"] in referer)
                        and ("query" not in candidate or
                             parse_qs(parsed.query).get("query") == [candidate["query"]])):
                    rule = self.rules.pop(index)
                    break
            record = {"id": len(self.records) + 1, "case": self.case,
                      "method": method, "url": url, "phase": "entered",
                      "monotonic": time.monotonic(), "rule": rule, "referer": referer}
            if method == "POST" and parsed.path == "/charts/natal":
                try:
                    record["intent"] = json.loads(body)
                except ValueError:
                    record["invalid_json"] = True
            self.records.append(record)
        self.log(record)
        return record, rule

    def gate(self, name):
        if not name:
            return
        with self.lock:
            event = self.gates.setdefault(name, threading.Event())
        # Timeout protects a forgotten controller release; it proves no ordering.
        if not event.wait(120):
            raise TimeoutError(f"Unreleased acceptance gate {name}")


def handler(state: State, upstream_port: int, *, control=False):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *_):
            pass

        def json_reply(self, body):
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def abort(self):
            self.close_connection = True
            try:
                self.connection.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            self.connection.close()

        def do_GET(self):
            self.dispatch()

        def do_POST(self):
            self.dispatch()

        def do_HEAD(self):
            self.dispatch()

        def dispatch(self):
            body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
            if control:
                value = json.loads(body) if body else {}
                if self.path == "/arm":
                    with state.lock:
                        state.case = value["case"]
                        state.rules = value.get("rules", [])
                    self.json_reply({"armed": value["case"]})
                elif self.path == "/release":
                    with state.lock:
                        state.gates.setdefault(value["gate"], threading.Event()).set()
                    self.json_reply({"released": value["gate"]})
                elif self.path == "/state":
                    with state.lock:
                        result = json.loads(json.dumps(state.records))
                    self.json_reply(result)
                elif self.path == "/wait":
                    with state.changed:
                        reached = state.changed.wait_for(lambda: any(
                            row["id"] == value["id"] and row["phase"] == value["phase"]
                            for row in state.records), timeout=45)
                    self.json_reply({"reached": reached, "id": value["id"], "phase": value["phase"]})
                else:
                    self.send_error(404)
                return
            if self.path.startswith("/health/"):
                self.send_error(404)
                return
            record, rule = state.enter(self.command, self.path, body, self.headers.get("Referer", ""))
            state.log(record, user_agent=self.headers.get("User-Agent", ""))
            mode = rule.get("mode", "forward")
            if mode in {"abort", "abort_then_forward"}:
                self.abort()
                state.log(record, phase="wire_aborted")
                if mode == "abort":
                    return
            state.log(record, phase="waiting" if rule.get("gate") else "forwarding")
            state.gate(rule.get("gate"))
            if mode == "override":
                status = rule.get("status", 200)
                data = (rule["text"].encode("utf-8") if "text" in rule else
                        json.dumps(rule.get("body"), ensure_ascii=False).encode("utf-8"))
                headers = [("Content-Type", "application/json; charset=utf-8"),
                           ("X-Request-ID", f"qa-wire-{record['id']}"),
                           ("Cache-Control", "no-store")]
            else:
                headers_up = dict(self.headers.items())
                for key in list(headers_up):
                    if key.lower() in {"connection", "accept-encoding", "x-forwarded-for", "x-forwarded-proto"}:
                        headers_up.pop(key)
                headers_up.update({"X-Forwarded-For": self.client_address[0],
                                   "X-Forwarded-Proto": "https", "Accept-Encoding": "identity"})
                connection = http.client.HTTPConnection("127.0.0.1", upstream_port,
                    timeout=45, source_address=("127.0.0.2", 0))
                try:
                    connection.request(self.command, self.path, body, headers_up)
                    response = connection.getresponse()
                    status, headers, data = response.status, response.getheaders(), response.read()
                finally:
                    connection.close()
            if "replace_body" in rule:
                status = rule["replace_status"]
                data = json.dumps(rule["replace_body"], ensure_ascii=False).encode("utf-8")
            extra_headers = rule.get("headers", {})
            headers = [(key, value) for key, value in headers if key.lower() not in
                       {"content-length", "connection", "transfer-encoding"}
                       and key.lower() not in {item.lower() for item in extra_headers}]
            headers.extend(extra_headers.items())
            filename = f"response-{record['id']:04d}.json"
            try:
                decoded = json.loads(data)
                (state.directory / filename).write_text(
                    json.dumps(decoded, ensure_ascii=False, indent=2), encoding="utf-8")
            except (ValueError, UnicodeDecodeError):
                filename = None
            state.log(record, phase="upstream_complete", status=status,
                      response=filename,
                      headers={key: value for key, value in headers if key.lower() != "set-cookie"},
                      cookie_attributes=[value.split(";", 1)[1] if ";" in value else ""
                                         for key, value in headers if key.lower() == "set-cookie"])
            if mode in {"abort_then_forward", "abort_after_forward"}:
                self.abort()
                state.log(record, phase="complete_without_response")
                return
            self.send_response(status)
            for key, value in headers:
                self.send_header(key, value)
            self.send_header("Content-Length", str(len(data)))
            # Avoid a stale pooled socket causing a native browser wire retry.
            # This keeps injected no-status failures on a fresh TLS connection.
            self.send_header("Connection", "close")
            self.end_headers()
            try:
                if self.command != "HEAD":
                    self.wfile.write(data)
                state.log(record, phase="delivered")
            except (BrokenPipeError, ConnectionResetError, ssl.SSLError):
                state.log(record, phase="client_disconnected")
    return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cert", required=True)
    parser.add_argument("--key", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--upstream-port", type=int, default=8001)
    args = parser.parse_args()
    state = State(args.output)
    controls = ThreadingHTTPServer(("127.0.0.1", 9009), handler(state, args.upstream_port, control=True))
    threading.Thread(target=controls.serve_forever, daemon=True).start()
    server = ThreadingHTTPServer(("127.0.0.1", 8443), handler(state, args.upstream_port))
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(args.cert, args.key)
    server.socket = context.wrap_socket(server.socket, server_side=True)
    print("QA HTTPS 127.0.0.1:8443 -> 127.0.0.1:8001; controls 127.0.0.1:9009", flush=True)
    try:
        server.serve_forever()
    finally:
        controls.shutdown()
        controls.server_close()
        server.server_close()


if __name__ == "__main__":
    main()
