
"""Hub Downloader — Pornhub desktop downloader (pywebview + yt-dlp)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import webview

from app.api import Api
from app.window import create_window, icon_path


def main() -> None:
    api = Api()
    create_window(api)
    # edgechromium = WebView2 on Windows
    kwargs = {"gui": "edgechromium", "debug": False}
    icon = icon_path()
    if icon:
        kwargs["icon"] = icon
    webview.start(**kwargs)


if __name__ == "__main__":
    main()
