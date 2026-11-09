"""Serve this archive on loopback so browsers can load bundled reader files."""

from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
import webbrowser


ROOT = Path(__file__).resolve().parent
HOST = "127.0.0.1"
PORT_RANGE = range(8000, 8011)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-browser", action="store_true", help="serve without opening a browser tab")
    args = parser.parse_args()
    handler = partial(SimpleHTTPRequestHandler, directory=str(ROOT))
    server = None
    for port in PORT_RANGE:
        try:
            server = ThreadingHTTPServer((HOST, port), handler)
            break
        except OSError:
            continue
    if server is None:
        print("Could not start the local reader: ports 8000–8010 are all in use.")
        return 1

    address = f"http://{HOST}:{server.server_port}/"
    print(f"Serving this project on this computer only: {address}")
    print("Keep this window open while reading. Press Ctrl+C here to stop the local server.")
    if not args.no_browser:
        timer = threading.Timer(0.8, webbrowser.open_new_tab, args=(address,))
        timer.daemon = True
        timer.start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nLocal reader server stopped.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
