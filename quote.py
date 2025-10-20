#!/usr/bin/env python3
# quote_server.py
import http.server
import socketserver
import random
import json

QUOTES = [
    "Be the change you wish to see. — Gandhi",
    "Simplicity is the ultimate sophistication. — Leonardo da Vinci",
    "Code is like humor. When you have to explain it, it’s bad. — Cory House",
    "First, solve the problem. Then, write the code. — John Johnson",
]

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/quote"):
            q = random.choice(QUOTES)
            payload = {"quote": q}
            data = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        else:
            super().do_GET()

if __name__ == "__main__":
    PORT = 8000
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Serving on http://localhost:{PORT}/quote")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("Stopping server.")
