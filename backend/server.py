"""Local read-only dashboard server. No mutation or trading endpoints."""
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
import argparse,json
ROOT=Path(__file__).resolve().parent.parent
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ROOT/'web'),**kwargs)
 def do_GET(self):
  if self.path.split('?')[0]=='/api/status':
   raw=(ROOT/'web/app-data.json').read_bytes();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(raw);return
  super().do_GET()
 def do_POST(self):self.send_error(405,'Read-only service; no action or trading endpoints')
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--port',type=int,default=8000);a.add_argument('--host',default='127.0.0.1');x=a.parse_args();ThreadingHTTPServer((x.host,x.port),Handler).serve_forever()
