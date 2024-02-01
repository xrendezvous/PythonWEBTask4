import mimetypes
import urllib.parse
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer
import socket
import threading
import json
from datetime import datetime
import os

BASE_DIR = Path()


class MyFramework(BaseHTTPRequestHandler):

    def do_GET(self):
        route = urllib.parse.urlparse(self.path)
        match route.path:
            case '/':
                self.send_html('index.html')
            case '/message':
                self.send_html('message.html')
            case _:
                file = BASE_DIR.joinpath(route.path[1:])
                if file.exists():
                    self.send_static(file)
                else:
                    self.send_html('error.html', 404)


    def do_POST(self):
        content_length = str(self.headers['Content-Length'])
        post_data = self.rfile.read(int(content_length))
        post_data = urllib.parse.parse_qs(post_data.decode('utf-8'))
        print("POST data received: ", post_data)
        json_data = json.dumps(post_data)

        udp_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_client.sendto(json_data.encode('utf-8'), ('localhost', 5000))
        udp_client.close()

        self.send_response(303)
        self.send_header('Location', '/')
        self.end_headers()

    def send_html(self, filename, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as f:
            self.wfile.write(f.read())

    def send_static(self, filename, status_code=200):
        self.send_response(status_code)
        mime_type, *_ = mimetypes.guess_type(filename)
        if mime_type:
            self.send_header('Content-Type', mime_type)
        else:
            self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        with open(filename, 'rb') as f:
            self.wfile.write(f.read())


def run_server():
    address = ('localhost', 3000)
    http_server = HTTPServer(address, MyFramework)
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        http_server.server_close()


def handle_udp_data(data, addr):
    print(f"Received data from {addr}")
    data_dict = json.loads(data.decode('utf-8'))
    print("Received data:", data_dict)

    storage_path = os.path.join('storage', 'data.json')
    if not os.path.exists('storage'):
        os.makedirs('storage')
    if not os.path.isfile(storage_path):
        with open(storage_path, 'w') as file:
            json.dump({}, file)
    with open(storage_path, 'r+') as file:
        data_json = json.load(file)
        data_json[str(datetime.now())] = data_dict
        file.seek(0)
        json.dump(data_json, file, indent=4)


def run_udp_server():
    udp_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_server.bind(('localhost', 5000))
    try:
        while True:
            data, addr = udp_server.recvfrom(1024)
            handle_udp_data(data, addr)
    except KeyboardInterrupt:
        udp_server.close()


if __name__ == '__main__':
    http_server_thread = threading.Thread(target=run_server)
    http_server_thread.start()

    run_udp_server()