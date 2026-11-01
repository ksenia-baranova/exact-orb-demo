"""TASK-D-04 browser fixture: unchanged package assets, golden HTTP leaf only.

Run from repository: python docs/project_management/changes/terms-of-use/plans/evidence/server.py
This is not a production server or a calculation acceptance test.
"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import hashlib
import json
from urllib.parse import urlsplit, parse_qs

ROOT = Path(__file__).resolve().parents[6]
ASSETS = ROOT / 'src/exact_orb/http_api/ui'
HERE = Path(__file__).resolve().parent
VIEWS = json.loads((ROOT / 'tests/http_api/golden/session_view.json').read_text())
CHARTS = json.loads((ROOT / 'tests/http_api/golden/chart_dto.json').read_text())
PLACE = json.loads((ROOT / 'tests/fixtures/places.jsonl').read_text(encoding='utf-8').splitlines()[0])
REQUESTS = []


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def send(self, data, mime='application/json', cookie=None):
        if not isinstance(data, bytes):
            data = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(200)
        self.send_header('Content-Type', mime + '; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        if cookie:
            self.send_header('Set-Cookie', cookie)
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        route = urlsplit(self.path)
        if route.path == '/':
            saved = parse_qs(route.query).get('saved', ['0'])[0]
            html = (ASSETS / 'index.html').read_bytes()
            # Test-only instrumentation runs before the unchanged production module.
            html = html.replace(b'<head>', b'<head><script src="/evidence.js"></script>')
            self.send(html, 'text/html', 'fixture_saved=' + saved + '; Path=/; SameSite=Lax')
        elif route.path == '/evidence.js':
            self.send((HERE / 'fixture.js').read_bytes(), 'text/javascript')
        elif route.path.startswith('/ui/') and '/' not in route.path[4:]:
            name = route.path[4:]
            mime = 'text/css' if name.endswith('.css') else 'text/javascript'
            self.send((ASSETS / name).read_bytes(), mime)
        elif route.path == '/charts/current':
            view = dict(VIEWS['known_ready'] if 'fixture_saved=1' in self.headers.get('Cookie', '') else VIEWS['empty'])
            if view['chart']:
                view['chart'] = CHARTS['natal']
            self.send(view)
        elif route.path == '/places':
            self.send({'items': [{'place_id': PLACE['place_id'], 'display_name': PLACE['name'],
                                  'admin1_name': PLACE['admin1'], 'country_code': PLACE['country']}]})
        elif route.path == '/requests':
            self.send(REQUESTS)
        else:
            self.send_error(404)

    def do_POST(self):
        data = self.rfile.read(int(self.headers.get('Content-Length', 0)))
        REQUESTS.append({'path': self.path, 'body': json.loads(data)})
        if self.path == '/session/bootstrap':
            self.send({'status': 'ready', 'state_version': 1})
        elif self.path == '/charts/natal':
            self.send({'status': 'chart_ready', 'state_version': 2, 'chart': CHARTS['natal']})
        else:
            self.send_error(404)


if __name__ == '__main__':
    print(json.dumps({'url': 'http://127.0.0.1:8874', 'assets': {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in ASSETS.iterdir() if p.is_file()
    }}, ensure_ascii=False), flush=True)
    ThreadingHTTPServer(('127.0.0.1', 8874), Handler).serve_forever()
