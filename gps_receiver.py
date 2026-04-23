import socket
import threading
import time
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

TCP_HOST = "149.81.112.139"
TCP_PORT = 7070

HTTP_HOST = "149.81.112.139"
HTTP_PORT = 8080

MAX_FRAMES = 200
frames = []
frames_lock = threading.Lock()


def safe_text(data: bytes) -> str:
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("latin-1", errors="replace")


def add_frame(remote_addr, data: bytes):
    item = {
        "receivedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "remoteAddress": f"{remote_addr[0]}:{remote_addr[1]}",
        "protocol": "tcp",
        "length": len(data),
        "text": safe_text(data),
        "hex": data.hex()
    }
    with frames_lock:
        frames.append(item)
        if len(frames) > MAX_FRAMES:
            del frames[0:len(frames) - MAX_FRAMES]
    print(json.dumps(item, ensure_ascii=False))


def handle_client(conn, addr):
    print(f"Connected: {addr[0]}:{addr[1]}")
    try:
        conn.settimeout(300)
        while True:
            data = conn.recv(4096)
            if not data:
                break
            add_frame(addr, data)

            # Optional ACK if your tracker requires it:
            # conn.sendall(b"OK\n")
    except Exception as e:
        print(f"Client error {addr}: {e}")
    finally:
        try:
            conn.close()
        except Exception:
            pass
        print(f"Disconnected: {addr[0]}:{addr[1]}")


def tcp_server():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((TCP_HOST, TCP_PORT))
    srv.listen(100)
    print(f"TCP server listening on {TCP_HOST}:{TCP_PORT}")

    while True:
        conn, addr = srv.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()


class ApiHandler(BaseHTTPRequestHandler):
    def _send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            self._send_json({"ok": True, "tcpPort": TCP_PORT, "httpPort": HTTP_PORT})
            return

        if self.path == "/latest-frame":
            with frames_lock:
                payload = frames[-1] if frames else {"message": "No frames received yet"}
            self._send_json(payload)
            return

        if self.path == "/frames":
            with frames_lock:
                payload = list(frames)
            self._send_json(payload)
            return

        self._send_json({"error": "Not found"}, status=404)

    def log_message(self, format, *args):
        return


def http_server():
    server = HTTPServer((HTTP_HOST, HTTP_PORT), ApiHandler)
    print(f"HTTP API listening on {HTTP_HOST}:{HTTP_PORT}")
    server.serve_forever()


if __name__ == "__main__":
    threading.Thread(target=tcp_server, daemon=True).start()
    http_server()
