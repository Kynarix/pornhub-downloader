
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus, urljoin

from curl_cffi import requests
from bs4 import BeautifulSoup
from yt_dlp import YoutubeDL

from core.models import FormatOption, VideoInfo
from providers.base import Provider

PH_HOSTS = (
    "pornhub.com",
    "www.pornhub.com",
    "pornhub.org",
    "www.pornhub.org",
    "pornhub.net",
    "www.pornhub.net",
    "pornhubpremium.com",
    "www.pornhubpremium.com",
)

BASE = "https://www.pornhub.com"
AGE_COOKIES = {
    "accessAgeDisclaimerPH": "1",
    "age_verified": "1",
    "platform": "pc",
}

# Göz at — popüler sıralamalar + kategori (Pornhub: /video?c=ID)
BROWSE_SECTIONS: list[dict[str, str]] = [
    {"id": "hot", "label": "Hot", "url": f"{BASE}/video?o=ht"},
    {"id": "most_viewed", "label": "Most Viewed", "url": f"{BASE}/video?o=mv"},
    {"id": "newest", "label": "Newest", "url": f"{BASE}/video?o=cm"},
    {"id": "recommended", "label": "Recommended", "url": f"{BASE}/recommended"},
]

# id = UI slug, c = Pornhub category id (/video?c=…)
CATEGORIES: list[dict[str, str]] = [
    {"id": "amateur", "label": "Amateur", "c": "3"},
    {"id": "anal", "label": "Anal", "c": "35"},
    {"id": "asian", "label": "Asian", "c": "1"},
    {"id": "big-ass", "label": "Big Ass", "c": "4"},
    {"id": "big-dick", "label": "Big Dick", "c": "7"},
    {"id": "big-tits", "label": "Big Tits", "c": "8"},
    {"id": "blonde", "label": "Blonde", "c": "9"},
    {"id": "blowjob", "label": "Blowjob", "c": "13"},
    {"id": "brunette", "label": "Brunette", "c": "11"},
    {"id": "creampie", "label": "Creampie", "c": "15"},
    {"id": "cumshot", "label": "Cumshot", "c": "16"},
    {"id": "ebony", "label": "Ebony", "c": "17"},
    {"id": "fetish", "label": "Fetish", "c": "18"},
    {"id": "hardcore", "label": "Hardcore", "c": "21"},
    {"id": "latina", "label": "Latina", "c": "26"},
    {"id": "lesbian", "label": "Lesbian", "c": "27"},
    {"id": "milf", "label": "MILF", "c": "29"},
    {"id": "pov", "label": "POV", "c": "41"},
    {"id": "public", "label": "Public", "c": "24"},
    {"id": "rough-sex", "label": "Rough Sex", "c": "67"},
    {"id": "small-tits", "label": "Small Tits", "c": "59"},
    {"id": "threesome", "label": "Threesome", "c": "65"},
]


class PornhubProvider(Provider):
    id = "pornhub"
    name = "Pornhub"

    def can_handle(self, url: str) -> bool:
        u = url.lower()
        return any(h in u for h in PH_HOSTS) or "pornhub" in u

    def resolve(self, url: str) -> VideoInfo:
        opts: dict[str, Any] = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "noplaylist": True,
        }
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)

        if not info:
            raise ValueError("Video bilgisi alınamadı.")

        formats = self._pick_formats(info.get("formats") or [])
        thumb = ""
        if info.get("thumbnail"):
            thumb = info["thumbnail"]
        elif info.get("thumbnails"):
            thumb = info["thumbnails"][-1].get("url", "")

        return VideoInfo(
            id=str(info.get("id") or ""),
            title=str(info.get("title") or "Untitled"),
            url=url,
            thumbnail=thumb,
            duration=info.get("duration"),
            uploader=str(info.get("uploader") or info.get("channel") or ""),
            formats=formats,
            webpage_url=str(info.get("webpage_url") or url),
        )

    def search(self, query: str, page: int = 1) -> dict[str, Any]:
        query = (query or "").strip()
        if not query:
            return {"ok": False, "error": "empty_query", "message": "Arama boş.", "items": []}
        page = max(1, int(page or 1))
        url = f"{BASE}/video/search?search={quote_plus(query)}&page={page}"
        try:
            items = self._scrape_list(url)
            return {
                "ok": True,
                "query": query,
                "page": page,
                "items": items,
                "has_more": len(items) >= 20,
            }
        except Exception as e:
            return {"ok": False, "error": str(e), "message": str(e), "items": [], "page": page}

    def browse(self, category: str = "", page: int = 1) -> dict[str, Any]:
        page = max(1, int(page or 1))
        category = (category or "hot").strip().lower()

        section = next((s for s in BROWSE_SECTIONS if s["id"] == category), None)
        if section:
            url = section["url"]
            if page > 1:
                sep = "&" if "?" in url else "?"
                url = f"{url}{sep}page={page}"
            label = section["label"]
        else:
            cat = next((c for c in CATEGORIES if c["id"] == category), None)
            # eski slug / sayısal c= desteği
            c_id = (cat or {}).get("c") or (category if category.isdigit() else "")
            if not c_id:
                return {
                    "ok": False,
                    "error": "unknown_category",
                    "message": f"Bilinmeyen kategori: {category}",
                    "items": [],
                    "page": page,
                    "category": category,
                    "sections": BROWSE_SECTIONS,
                    "categories": CATEGORIES,
                }
            url = f"{BASE}/video?c={c_id}"
            if page > 1:
                url = f"{url}&page={page}"
            label = cat["label"] if cat else f"c={c_id}"

        try:
            items = self._scrape_list(url)
            return {
                "ok": True,
                "category": category,
                "label": label,
                "page": page,
                "items": items,
                "has_more": len(items) >= 20,
                "sections": BROWSE_SECTIONS,
                "categories": CATEGORIES,
            }
        except Exception as e:
            return {
                "ok": False,
                "error": str(e),
                "message": str(e),
                "items": [],
                "page": page,
                "category": category,
                "sections": BROWSE_SECTIONS,
                "categories": CATEGORIES,
            }

    def list_catalog(self) -> dict[str, Any]:
        return {"ok": True, "sections": BROWSE_SECTIONS, "categories": CATEGORIES}

    def _scrape_list(self, url: str) -> list[dict[str, Any]]:
        html = self._fetch(url)
        soup = BeautifulSoup(html, "lxml")
        items: list[dict[str, Any]] = []
        seen: set[str] = set()

        for li in soup.select("li.pcVideoListItem, li.videoBox"):
            a = li.select_one('a[href*="view_video.php"]')
            if not a:
                continue
            href = a.get("href") or ""
            full = urljoin(BASE, href)
            if "viewkey=" not in full:
                continue
            viewkey = full.split("viewkey=")[-1].split("&")[0]
            if viewkey in seen:
                continue
            seen.add(viewkey)

            img = li.select_one("img")
            title = (
                (a.get("title") or "").strip()
                or (img.get("alt") if img else "")
                or a.get_text(" ", strip=True)
            )
            title = _clean_html_entities(title)
            thumb = ""
            if img:
                thumb = (
                    img.get("data-image")
                    or img.get("data-mediumthumb")
                    or img.get("data-src")
                    or img.get("src")
                    or ""
                )
            dur_el = li.select_one(".duration, var.duration")
            duration_text = dur_el.get_text(strip=True) if dur_el else ""
            video_id = ""
            if img and img.get("data-video-id"):
                video_id = str(img.get("data-video-id"))

            items.append(
                {
                    "id": viewkey,
                    "video_id": video_id,
                    "title": title,
                    "url": full.replace("http://", "https://"),
                    "thumbnail": thumb,
                    "duration_text": duration_text,
                    "duration": _parse_duration(duration_text),
                    "uploader": "",
                }
            )
        return items

    def _fetch(self, url: str) -> str:
        last_err: Exception | None = None
        for _ in range(3):
            try:
                r = requests.get(
                    url,
                    impersonate="chrome131",
                    cookies=AGE_COOKIES,
                    timeout=45,
                    headers={
                        "accept-language": "en-US,en;q=0.9",
                        "referer": BASE + "/",
                    },
                )
                if r.status_code >= 400:
                    raise RuntimeError(f"HTTP {r.status_code}")
                return r.text
            except Exception as e:
                last_err = e
                time.sleep(0.6)
        raise RuntimeError(f"Sayfa alınamadı: {last_err}")

    def _pick_formats(self, raw: list[dict[str, Any]]) -> list[FormatOption]:
        options: list[FormatOption] = []
        seen: set[str] = set()

        progressive = [
            f
            for f in raw
            if f.get("vcodec") not in (None, "none")
            and f.get("acodec") not in (None, "none")
            and (f.get("ext") or "").lower() in ("mp4", "webm", "mov")
        ]
        progressive.sort(key=lambda f: f.get("height") or 0, reverse=True)

        for f in progressive:
            fid = str(f.get("format_id"))
            if fid in seen:
                continue
            seen.add(fid)
            height = f.get("height")
            label = f"{height}p" if height else (f.get("format_note") or fid)
            options.append(
                FormatOption(
                    format_id=fid,
                    label=str(label),
                    ext=str(f.get("ext") or "mp4"),
                    height=height,
                    filesize=f.get("filesize") or f.get("filesize_approx"),
                    note=str(f.get("format_note") or "progressive"),
                )
            )

        heights = sorted(
            {
                f.get("height")
                for f in raw
                if f.get("vcodec") not in (None, "none") and f.get("height")
            },
            reverse=True,
        )
        for h in heights[:6]:
            fid = f"bv*[height<={h}]+ba/b[height<={h}]"
            if fid in seen:
                continue
            seen.add(fid)
            options.append(
                FormatOption(
                    format_id=fid,
                    label=f"{h}p (best)",
                    ext="mp4",
                    height=h,
                    note="merged",
                )
            )

        if not options:
            options.append(
                FormatOption(
                    format_id="bv*+ba/b",
                    label="En iyi kalite",
                    ext="mp4",
                    note="best",
                )
            )

        uniq: list[FormatOption] = []
        labels: set[str] = set()
        for opt in options:
            key = opt.label.lower()
            if key in labels:
                continue
            labels.add(key)
            uniq.append(opt)
        return uniq[:12]


def _parse_duration(text: str) -> int | None:
    text = (text or "").strip()
    if not text:
        return None
    parts = text.split(":")
    try:
        nums = [int(p) for p in parts]
    except ValueError:
        return None
    if len(nums) == 3:
        return nums[0] * 3600 + nums[1] * 60 + nums[2]
    if len(nums) == 2:
        return nums[0] * 60 + nums[1]
    if len(nums) == 1:
        return nums[0]
    return None


def _clean_html_entities(s: str) -> str:
    return (
        s.replace("&#039;", "'")
        .replace("&amp;", "&")
        .replace("&quot;", '"')
        .replace("&lt;", "<")
        .replace("&gt;", ">")
    )
