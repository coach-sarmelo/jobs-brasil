import http.server
import socketserver
import os

PORT = 3015
DIRECTORY = os.path.join(os.path.dirname(__file__), "site")

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
        print(f"Serving Jobs BR on http://0.0.0.0:{PORT}")
        httpd.serve_forever()
