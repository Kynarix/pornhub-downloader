
from __future__ import annotations

import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import webview

from app.api import Api

UI_DIR = Path(__file__).resolve().parent.parent / "ui"
ICON_PATH = Path(__file__).resolve().parent.parent / "assets" / "icon.ico"


def _start_ui_server(ui_dir: Path) -> str:
    class QuietHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(ui_dir), **kwargs)

        def log_message(self, format: str, *args) -> None:  # noqa: A003
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), QuietHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return f"http://127.0.0.1:{port}/index.html"


def create_window(api: Api) -> webview.Window:
    url = _start_ui_server(UI_DIR)
    window = webview.create_window(
        title="Hub Downloader",
        url=url,
        js_api=api,
        width=1120,
        height=760,
        min_size=(880, 600),
        background_color="#f8f9fa",
        text_select=True,
    )
    return window


def icon_path() -> str | None:
    if ICON_PATH.exists():
        return str(ICON_PATH)
    png = ICON_PATH.with_suffix(".png")
    return str(png) if png.exists() else None
