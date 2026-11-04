import http.client
import json
import tempfile
import threading
import unittest
from pathlib import Path
from app import create_server


class AppTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.database = Path(self.temp.name) / 'todos.db'
        self.start()

    def start(self):
        self.server = create_server(port=0, database=self.database)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def stop(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def tearDown(self):
        self.stop()
        self.temp.cleanup()

    def request(self, method, path='/api/todos', data=None):
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port)
        connection.request(method, path, body=json.dumps(data) if data is not None else None,
                           headers={'Content-Type': 'application/json'})
        response = connection.getresponse()
        body = response.read()
        status = response.status
        connection.close()
        return status, json.loads(body) if path != '/' else body.decode()

    def test_lifecycle_and_persistence(self):
        self.assertEqual(self.request('GET')[1], [])
        status, result = self.request('POST', data={'title': '  파이썬 공부  '})
        self.assertEqual(status, 201)
        path = f"/api/todos/{result['id']}"
        self.assertEqual(self.request('PATCH', path, {'completed': True})[0], 200)
        self.stop()
        self.start()
        todo = self.request('GET')[1][0]
        self.assertEqual((todo['title'], todo['completed']), ('파이썬 공부', 1))
        self.assertEqual(self.request('PATCH', path, {'completed': False})[0], 200)
        self.assertEqual(self.request('DELETE', path, {})[0], 200)
        self.assertEqual(self.request('GET')[1], [])
        self.assertEqual(self.request('DELETE', path, {})[0], 404)

    def test_validation(self):
        for title in ['', '  ', 'a' * 201, None]:
            self.assertEqual(self.request('POST', data={'title': title})[0], 400)
        self.assertEqual(self.request('PATCH', '/api/todos/1', {'completed': 'false'})[0], 400)
        self.assertEqual(self.request('GET', '/missing')[0], 404)

    def test_page(self):
        status, html = self.request('GET', '/')
        self.assertEqual(status, 200)
        self.assertIn('오늘의 할 일', html)
        self.assertIn('data-filter="active"', html)
