"""A small, single-user todo app using only Python's standard library."""
import argparse
import json
import os
import sqlite3
import sys
import threading
import webbrowser
from contextlib import contextmanager
from functools import partial
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_ROOT = (Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'SimpleTodo'
             if getattr(sys, 'frozen', False) else ROOT / 'data')


@contextmanager
def connect(database):
    db = sqlite3.connect(database)
    try:
        db.row_factory = sqlite3.Row
        with db:
            db.execute('CREATE TABLE IF NOT EXISTS todos (id INTEGER PRIMARY KEY, title TEXT NOT NULL, completed INTEGER NOT NULL DEFAULT 0)')
            yield db
    finally:
        db.close()


class Handler(BaseHTTPRequestHandler):
    def __init__(self, *args, database, **kwargs):
        self.database = database
        super().__init__(*args, **kwargs)

    def send(self, status, data, content_type='application/json; charset=utf-8'):
        body = json.dumps(data, ensure_ascii=False).encode() if 'json' in content_type else data
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == '/':
            return self.send(200, (ROOT / 'static/index.html').read_bytes(), 'text/html; charset=utf-8')
        if self.path != '/api/todos':
            return self.send(404, {'error': '페이지를 찾을 수 없습니다.'})
        with connect(self.database) as db:
            rows = [dict(row) for row in db.execute('SELECT * FROM todos ORDER BY id DESC')]
        self.send(200, rows)

    def mutate(self):
        # JSON requests only: browser cross-origin form submissions cannot mutate data.
        if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
            return self.send(415, {'error': 'JSON 요청이 필요합니다.'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 8192:
                raise ValueError()
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict):
                raise ValueError()
            with connect(self.database) as db:
                if self.command == 'POST' and self.path == '/api/todos':
                    title = data.get('title')
                    if not isinstance(title, str) or not 1 <= len(title.strip()) <= 200:
                        return self.send(400, {'error': '할 일을 1~200자로 입력하세요.'})
                    cursor = db.execute('INSERT INTO todos(title) VALUES (?)', (title.strip(),))
                    result = {'id': cursor.lastrowid}
                    status = 201
                else:
                    parts = self.path.split('/')
                    if len(parts) != 4 or parts[1:3] != ['api', 'todos'] or not parts[3].isdigit():
                        return self.send(404, {'error': '항목을 찾을 수 없습니다.'})
                    todo_id = int(parts[3])
                    if self.command == 'PATCH':
                        if type(data.get('completed')) is not bool:
                            raise ValueError()
                        cursor = db.execute('UPDATE todos SET completed=? WHERE id=?', (data['completed'], todo_id))
                    elif self.command == 'DELETE':
                        cursor = db.execute('DELETE FROM todos WHERE id=?', (todo_id,))
                    else:
                        return self.send(404, {'error': '페이지를 찾을 수 없습니다.'})
                    if not cursor.rowcount:
                        return self.send(404, {'error': '항목을 찾을 수 없습니다.'})
                    result, status = {'ok': True}, 200
            self.send(status, result)
        except (ValueError, UnicodeDecodeError):
            self.send(400, {'error': '올바른 요청을 보내주세요.'})

    do_POST = mutate
    do_PATCH = mutate
    do_DELETE = mutate


def create_server(host='127.0.0.1', port=8000, database=None):
    database = Path(database) if database else DATA_ROOT / 'todos.db'
    database.parent.mkdir(parents=True, exist_ok=True)
    with connect(database):
        pass
    return ThreadingHTTPServer((host, port), partial(Handler, database=database))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=0 if getattr(sys, 'frozen', False) else 8000)
    parser.add_argument('--db', type=Path)
    args = parser.parse_args()
    server = create_server(args.host, args.port, args.db)
    print(f'할 일 앱 실행: http://{args.host}:{server.server_port}', flush=True)
    if getattr(sys, 'frozen', False):
        threading.Timer(0.5, webbrowser.open, args=(f'http://127.0.0.1:{server.server_port}',)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
