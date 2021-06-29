import http.server
import os
import shutil
import socketserver
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urlparse


class MirrorHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
      url = urlparse(self.path)
      mpath = Path(os.getcwd() + "/" + url.netloc + url.path)
      if not os.path.exists(mpath):
        print("MISS", mpath)
        mpath.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(self.path)
        for h in self.headers:
          if h not in ["Host"]:
            req.add_header(h, self.headers[h])
        res = urllib.request.urlopen(req)
        buf = res.read(10240)
        self.send_response(200)
        for h in res.headers:
          if h in ["Content-Length"]: # Content-Length is required by some apps e.g. apt-get
            self.send_header(h, res.headers[h])
        self.end_headers()
        with open(mpath.with_suffix(".tmp"), "wb") as mfile:
          while buf:
            mfile.write(buf)
            self.wfile.write(buf)
            buf = res.read(10240)
        os.rename(mpath.with_suffix(".tmp"), mpath)
      else:
        print("HIT ", mpath)
        with open(mpath, "rb") as mfile:
          self.send_response(200)
          self.send_header("Content-Length",os.path.getsize(mpath)) # Content-Length is required by some apps e.g. apt-get
          self.end_headers()
          shutil.copyfileobj(mfile, self.wfile)


if __name__ == '__main__':
  #socketserver.TCPServer.allow_reuse_address = True # FIXME If enabled, port cannot be accessed from docker container?
  with socketserver.TCPServer(("0.0.0.0", 8000), MirrorHandler) as httpd:
      try:
          httpd.serve_forever()
      except KeyboardInterrupt:
          sys.exit(0)
