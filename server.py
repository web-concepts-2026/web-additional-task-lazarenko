import json
import socket



HOST = "localhost"
PORT = 8080


def handle(conn):
    request = conn.recv(4096)
    if not request:
        return None

    head, body = request.split(b"\r\n\r\n", 1)
    lines = head.decode().split("\r\n")
    method, full_path, version = lines[0].split(" ")

    headers = {}
    for line in lines[1:]:
        name, value = line.split(":", 1)
        headers[name.strip().lower()] = value.strip()

    length = int(headers.get("content-length", 0))
    while len(body) < length:
        chunk = conn.recv(4096)
        if not chunk:
            break
        body += chunk

    path, _, query_string = full_path.partition("?")
    query = {}
    for pair in query_string.split("&"):
        if "=" in pair:
            key, value = pair.split("=", 1)
            query[key] = value

    print(method, path, query)

    if method == "GET" and path == "/":
        with open("static/index.html", encoding="utf-8") as f:
            return "200 OK", "text/html", f.read()
    if method == "GET" and path == "/page":
        page_id = query.get("id", "none").replace("<", "&lt;")
        return "200 OK", "text/html", f"<h1>Page {page_id}</h1>"
    if method == "GET" and path == "/headers":
        return "200 OK", "application/json", json.dumps(headers, indent=2)
    if method == "POST" and path == "/api/data":
        try:
            data = json.loads(body)
        except ValueError:
            return "400 Bad Request", "application/json", '{"error": "invalid JSON"}'
        return "200 OK", "application/json", json.dumps({"status": "ok", "received": data})
    return "404 Not Found", "text/html", "<h1>404 Not Found</h1>"


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()
server.settimeout(1)
print(f"Server started on http://{HOST}:{PORT}")

try:
    while True:
        try:
            conn, addr = server.accept()
        except socket.timeout:
            continue
        try:
            conn.settimeout(5)
            result = handle(conn)
            if result:
                status, content_type, answer = result
                answer = answer.encode()
                head = f"HTTP/1.1 {status}\r\nContent-Type: {content_type}; charset=utf-8\r\n"
                head += f"Content-Length: {len(answer)}\r\nConnection: close\r\n\r\n"
                conn.sendall(head.encode() + answer)
        except Exception as error:
            print("Error:", error)
        conn.close()
except KeyboardInterrupt:
    print("Server stopped")
