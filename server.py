#! /usr/bin/env python3
import http.server
import socketserver
import subprocess
import socket
import re
import pprint

def inspect(verbose=False):
    res = []
    out = subprocess.run(["powermetrics", "--samplers", "smc,disk,cpu_power", "-n", "1"], capture_output=True)
    text = out.stdout.decode('utf-8')
    if verbose:
        print(text)
    for r in re.finditer('CPU (\d+).*?CPU Average frequency as fraction of nominal: ([\d.]+)% \(([\d.]+) Mhz\)', text, re.DOTALL):
        #res.append('cpu_')
        res.append(f'cpu_clock{{cpu="{r.group(1)}"}} {r.group(3)}');
    for pattern, label in [
        ('CPU die temperature: ([\d.]+) C', 'temperature{point="cpu"}'),
        ('CPU Thermal level: (\d+)', 'thermal_level{point="cpu"}'),
        ('GPU die temperature: ([\d.]+) C', 'temperature{point="gpu"}'),
        ('GPU Thermal level: (\d+)', 'thermal_level{point="gpu"}'),        
        ('Fan: (\d+) rpm', 'fan{point="system"}'),
        ('read: ([\d.]+) ops/s', 'disk_iops{mode="read"}'),
        ('write: ([\d.]+) ops/s', 'disk_iops{mode="read"}'),
        ('read: [\d.]+ ops/s ([\d.]) KBytes/s', 'disk_bandwidth{mode="read"}'),
        ('write: [\d.]+ ops/s ([\d.]) KBytes/s', 'disk_bandwidth{mode="read"}'),
    ]:
        m = re.search(pattern, text)
        if m:
            res.append(f'{label} {m.group(1)}')
    if verbose:
        pprint.pprint(res)
        print('end')
    return res

class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        res = inspect()
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()

        self.wfile.write(bytes('\n'.join(res)+'\n', 'utf8'));

class MyServer(socketserver.TCPServer):
    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)
        ('read: [\d.]+ ops/s ([\d.]) KBytes/s', 'disk_bandwidth{mode="read"}'),

# Create an object of the above class
handler_object = MyHttpRequestHandler

PORT = 9997
my_server = MyServer(("", PORT), handler_object)
print('SERVING on port', PORT)
# Star the server
my_server.serve_forever()
