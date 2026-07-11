# Pornhub Downloader — Hub Downloader

**Pornhub video downloader for Windows** · free · open source · GitHub

Search terms this project targets: **pornhub downloader**, **pornhub downloader github**, **pornhub video download**, **pornhub desktop downloader**, **yt-dlp pornhub gui**.

A modern **Pornhub Downloader** desktop app with a clean Google-style UI. Paste a Pornhub URL, search Pornhub, browse categories, queue downloads, and save favorites — powered by **yt-dlp** + **WebView2**.

![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-0078D4?style=flat-square)
![Python](https://img.shields.io/badge/python-3.10%2B-3776AB?style=flat-square)
![Pornhub](https://img.shields.io/badge/site-Pornhub-FF9000?style=flat-square)
![yt-dlp](https://img.shields.io/badge/engine-yt--dlp-FF6D00?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)

> Discord: **ashtwix** · by Twixx

---

## Why this Pornhub Downloader?

Most “Pornhub downloader” tools are shady websites or broken scripts. **Hub Downloader** is a real Windows desktop app:

- Native window (Edge **WebView2**)
- Official-quality extraction via **yt-dlp**
- Search & category browse on **Pornhub.com**
- Download queue, history, favorites, themes

If you Googled **pornhub downloader github**, you’re in the right place.

---

## Features

| Feature | Description |
| --- | --- |
| **Pornhub URL download** | Paste `pornhub.com/view_video.php?…` → pick quality → queue |
| **Pornhub search** | Search Pornhub from the app, thumbnail grid |
| **Browse Pornhub** | Hot, Most Viewed, Newest + categories (Amateur, Anal, MILF, …) |
| **Favorites** | Save videos, one-click download |
| **Queue** | Progress, cancel, clear finished |
| **History** | Completed downloads |
| **Themes** | Pornhub orange, Crimson, Azure, Mint, Violet, Sand · light/dark |
| **Best quality** | One-click best format from the grid |

---

## Requirements

- Windows 10 / 11
- Python 3.10+
- [Microsoft Edge WebView2 Runtime](https://developer.microsoft.com/microsoft-edge/webview2/) (usually preinstalled on Windows 11)

---

## Install

```bash
git clone https://github.com/Kynarix/pornhub-downloader.git
cd pornhub-downloader

python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt
```

---

## Run

```bash
python main.py
```

---

## Usage

1. **Download** — paste a Pornhub video URL → **Getir** → choose quality → **Kuyruğa ekle**
2. **Search / Browse** — find videos on Pornhub → download or favorite
3. **Settings** — folder, theme, concurrent downloads

Default folder:

```text
%USERPROFILE%\Downloads\HubDownloader
```

---

## Keywords

`pornhub downloader` · `pornhub downloader github` · `pornhub video downloader` · `pornhub download windows` · `yt-dlp pornhub` · `pornhub gui` · `adult video downloader` · `hub downloader`

---

## Architecture

```text
pornhub-downloader/
├── main.py
├── app/           # WebView2 window + Python↔JS API
├── core/          # queue, yt-dlp downloader, history, favorites, settings
├── providers/     # Pornhub provider (resolve / search / browse)
├── ui/            # HTML / CSS / JS
├── assets/        # app icon
└── data/          # local only (gitignored)
```

Add more sites later by implementing `providers.base.Provider` and registering it.

---

## Stack

| Package | Role |
| --- | --- |
| `pywebview` | Desktop UI (WebView2) |
| `yt-dlp` | Pornhub video resolve & download |
| `curl_cffi` | Resilient HTTP (TLS fingerprint) |
| `beautifulsoup4` + `lxml` | Pornhub search / category scrape |

---

## Disclaimer

For **personal / educational** use only. Respect Pornhub’s terms of service and copyright laws in your country. The authors are not responsible for misuse.

---

## Roadmap

- [ ] More sites (XVideos, XNXX, …)
- [ ] Playlist / channel bulk download
- [ ] Cookie / login support
- [ ] Creator watchlist
- [ ] One-click `.exe` build

---

## License

MIT © Twixx · Discord **ashtwix**

---

## Türkçe özet

**Pornhub Downloader (Hub Downloader)** — Windows için masaüstü Pornhub video indirme uygulaması. URL yapıştır, Pornhub’da ara, kategorilere göz at, kuyrukla indir. `yt-dlp` + WebView2.

```bash
git clone https://github.com/Kynarix/pornhub-downloader.git
cd pornhub-downloader
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```
