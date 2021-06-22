import http.server
import socketserver
import urllib.request
import shutil
import os
import hashlib
import sys

from urllib.parse import urlparse
from pathlib import Path

class CacheHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
      o = urlparse(self.path)
      cache_filename = Path(os.getcwd() + "/" + o.netloc + o.path)
      
      if not os.path.exists(cache_filename):
        print("MISS", cache_filename)
        cache_filename.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(self.path)
        for k in self.headers:
          if k not in ["Host"]:
            req.add_header(k, self.headers[k])
        try:
          resp = urllib.request.urlopen(req)
          with open(cache_filename.with_suffix(".tmp"), "wb") as output:
            buf = resp.read(10240)
            self.send_response(200)
            for k in resp.headers:
              if k in ["Content-Length"]: # Content-Length required by apt update?
                self.send_header(k,resp.headers[k])
            self.end_headers()
            while buf:
              output.write(buf)
              self.wfile.write(buf)
              buf = resp.read(10240)
          os.rename(cache_filename.with_suffix(".tmp"), cache_filename)
        except urllib.error.HTTPError as err:
          self.send_response(err.code)
          self.end_headers()
          return
      else:
        print("HIT", cache_filename)
        with open(cache_filename, "rb") as cached:
          self.send_response(200)
          self.send_header("Content-Length",os.path.getsize(cache_filename))
          self.end_headers()
          shutil.copyfileobj(cached, self.wfile)

#socketserver.TCPServer.allow_reuse_address = True # If enabled, port cannot be accessed from inside docker container?

with socketserver.TCPServer(("0.0.0.0", 8000), CacheHandler) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        sys.exit(0)