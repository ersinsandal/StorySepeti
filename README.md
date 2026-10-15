# ⚡ StoryVault

<div align="center">

![StoryVault Banner](assets/icon.ico)

# StoryVault — Maximum Fidelity Instagram Story & Highlight Downloader
**Preserve Instagram stories and highlights at their true original resolution (1080p+, original photo dimensions, 60fps MP4/MKV) with zero technical hassle.**

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%20%7C%2011%20(x64)-0078D6.svg)]()
[![Quality](https://img.shields.io/badge/quality-True%201080p%2B%20%7C%20Original%20HQ-purple.svg)]()
[![Release](https://img.shields.io/badge/release-v1.0.0-orange.svg)](https://github.com/ersinsandal/StoryVault/releases)

[🇹🇷 **Türkçe Dokümantasyon için tıklayın (README_TR.md)**](README_TR.md) • [📖 **English Documentation**](#overview)

</div>

---

## 📑 Table of Contents
1. [Overview](#overview)
2. [Why StoryVault? (The 720p Limitation Solved)](#why-storyvault-the-720p-limitation-solved)
3. [Key Features](#key-features)
4. [Architecture & Pipeline](#architecture--pipeline)
5. [Quality Engine Deep Dive](#quality-engine-deep-dive)
6. [Security & Privacy](#security--privacy)
7. [Getting Started](#getting-started)
   - [Method 1: Standalone Windows Executable (Recommended)](#method-1-standalone-windows-executable-recommended)
   - [Method 2: Run from Source Code](#method-2-run-from-source-code)
   - [Method 3: Build Your Own Executable](#method-3-build-your-own-executable)
8. [Session & Cookie Management](#session--cookie-management)
9. [Project Structure](#project-structure)
10. [Troubleshooting & FAQ](#troubleshooting--faq)
11. [Legal Disclaimer & License](#legal-disclaimer--license)

---

<a name="overview"></a>
## 💡 Overview

**StoryVault** is a standalone, enterprise-grade Windows desktop application built with Python and CustomTkinter, designed to download and archive Instagram Stories (24-hour temporary media) and Story Highlights at their absolute highest available fidelity.

Unlike conventional web scrapers or online downloading portals that rely on unauthenticated endpoints, return heavily compressed 720p/480p preview streams, or break whenever Instagram updates its API, StoryVault combines:
- **Direct High-Speed Instagram Web API** with `curl_cffi` (Chrome 124 TLS fingerprint impersonation).
- **Multi-Source Fallback System** powered by `yt-dlp` and `gallery-dl`.
- **DASH Lossless Stream Muxing** to merge separated 1080p video and master audio into MKV/MP4 containers without re-encoding loss.
- **FFprobe Hardware Inspection** to physically verify codecs, dimensions, and bitrate for every saved file.
- **Enterprise-Grade Security** storing session tokens exclusively in Windows DPAPI-encrypted vaults (`AES-256-GCM`).

---

<a name="why-storyvault-the-720p-limitation-solved"></a>
## 🔬 Why StoryVault? (The 720p Limitation Solved)

Almost all popular online Instagram downloaders suffer from the **"720p Cap"** problem:

| Characteristic | Standard Web Tools / Basic Scrapers | StoryVault |
| :--- | :--- | :--- |
| **Authentication** | None (Anonymous or burnt proxy pools) | Authenticated user session (`X-IG-App-ID` + DPAPI session store) |
| **Endpoint Queried** | Unauthenticated HTML scrapers or deprecated `reels_media` API | Modern Web API endpoints + full DASH stream manifest resolution |
| **Max Video Quality** | Capped at **720x1280 (Progressive MP4)** to save Instagram server bandwidth | **True 1080p+ (DASH separate video + best audio merged losslessly)** |
| **Photo Quality** | Downscaled 640x640 or 1080x1080 thumbnails | Full uncompressed original canvas (e.g., **1206x2144**) |
| **Verification** | None (silent failure or partial download) | Automated physical stream analysis via **FFprobe** |
| **Data Privacy** | Plaintext cookie uploads to third-party web servers | **100% Local processing**; zero telemetry; encrypted with Windows DPAPI |

### The Technical Reason:
Instagram serves 1080p videos by splitting video and audio tracks via Dynamic Adaptive Streaming over HTTP (DASH). Standard web tools cannot download or merge separate tracks, so they fall back to the low-bitrate progressive 720p MP4 preview intended for mobile web browsers. StoryVault captures the complete representation stream, selects the highest bitrate video and pristine audio, and multiplexes them losslessly.

---

<a name="key-features"></a>
## ✨ Key Features

### 1. 🎯 4 Specialized Download Modes
- **Single Story:** Paste any individual story link (e.g. `https://www.instagram.com/stories/username/123456789/`) to immediately fetch that specific item.
- **All Active Stories:** Enter a profile username or story feed URL to archive all active 24-hour stories of that user into a timestamped directory.
- **Single Highlight:** Download an entire highlight album via direct URL or `/s/` base64 short link.
- **All Profile Highlights:** Scan any user profile to display all highlight albums with covers, titles, and item counts, allowing selective or bulk batch downloads.

### 2. 📁 Built-In Downloads Manager
- Integrated in-app panel to browse all archived media.
- Filter by: **All**, **Stories**, **Highlights**, **Videos**, and **Photos**.
- Interactive media cards displaying resolution, file size, creation date, and file path.
- 1-Click action buttons: **Open in Default Player**, **Show in File Explorer**, or **Delete**.

### 3. ⚡ In-App Engine Updater
- Automatically checks for upstream updates without requiring terminal commands or Python knowledge.
- In-app notification banner alerts you when engine updates are available.
- **[Update Now]** button downloads and applies the latest dependencies on the fly.

### 4. 🔒 Triple-Method Login Wizard
- **Live Interactive Browser Login:** Launches a safe Chrome/Edge window for manual login, automatically extracting session cookies upon successful authentication.
- **1-Click Browser Extraction:** Directly pulls active Instagram session cookies from installed Chrome, Edge, Firefox, Brave, or Opera browsers.
- **Manual Cookie File Import:** Supports standard Netscape/cookie.txt files with validation and automatic encryption.

### 5. 🖥️ Windows Integration & Ergonomics
- **System Tray Support:** Minimizes cleanly to the Windows taskbar notification area with a custom tray menu.
- **Native Desktop Notifications:** Dispatches balloon notifications on download completion or errors.
- **Smart Drag-and-Drop & Clipboard Auto-Paste:** Automatically extracts and classifies Instagram URLs from the Windows clipboard.
- **Dark & Light Themes:** Modern CustomTkinter interface with full Turkish and English localization.

---

<a name="architecture--pipeline"></a>
## 🏗️ Architecture & Pipeline

```
  ┌────────────────────────────────────────────────────────┐
  │                   StoryVault UI                        │
  │    (CustomTkinter Modern Windows GUI / System Tray)    │
  └──────────────────────────┬─────────────────────────────┘
                             │
                  [Input URL or Username]
                             │
                             ▼
  ┌────────────────────────────────────────────────────────┐
  │                 URL & Intent Parser                    │
  │        (Detects: Story, Highlight, Short Link)         │
  └──────────────────────────┬─────────────────────────────┘
                             │
                             ▼
  ┌────────────────────────────────────────────────────────┐
  │                   Cookie Manager                       │
  │   (Windows DPAPI AES-256-GCM Decrypted Memory Session)  │
  └──────────────────────────┬─────────────────────────────┘
                             │
            ┌────────────────┴────────────────┐
            ▼                                 ▼
┌───────────────────────────────┐ ┌───────────────────────────────┐
│     Primary Engine (Fast)     │ │    Secondary Safety Net       │
│  Instagram Web API (Native)   │ │  yt-dlp + gallery-dl Engine   │
│  - curl_cffi Chrome 124 TLS   │ │  - Multi-fragment DASH mux    │
│  - Full JSON Manifest Parser  │ │  - Formats: res,br sorting    │
│  - Max Resolution Stream DL   │ │  - Fallback album scraper     │
└───────────────┬───────────────┘ └───────────────┬───────────────┘
                │                                 │
                └────────────────┬────────────────┘
                                 │
                                 ▼
  ┌────────────────────────────────────────────────────────┐
  │              Physical Verifier (FFprobe)               │
  │  Checks: Codec (h264/hevc), Dimensions, Valid Stream   │
  └──────────────────────────┬─────────────────────────────┘
                             │
                             ▼
  ┌────────────────────────────────────────────────────────┐
  │           Output Archive & Downloads Panel             │
  │   - Sanitized Windows Paths (Turkish char translit)    │
  │   - Structured Directory: /user/stories/YYYYMMDD/...   │
  └────────────────────────────────────────────────────────┘
```

---

<a name="quality-engine-deep-dive"></a>
## 📊 Quality Engine Deep Dive

### Video Selection Strategy
1. **Short-Side Rule (`min(width, height) >= 1080`):** Instagram stories are vertically oriented ($1080 \times 1920$). The algorithm prioritizes the short side rather than pure width.
2. **DASH Stream Multiplexing:** When Instagram serves separate video (`vcodec != none`) and audio (`acodec != none`) tracks, StoryVault merges them into an **MKV** or **MP4** container without transcode degradation.
3. **Bitrate Maximization (`-S res,br`):** If multiple 1080p or 720p streams are offered, the stream with the highest bitrate (least compression) is selected.
4. **Physical Verification:** Downloaded video streams are evaluated with `ffprobe -show_entries stream=width,height,codec_name,bit_rate`. If a stream is corrupt, zero-byte, or unplayable, an error is logged immediately.

### Photo Selection Strategy
1. Queries the full `image_versions2.candidates` array from Instagram CDN.
2. Calculates pixel area ($width \times height$) for every candidate.
3. Downloads candidate 0 (unscaled original up to $1206 \times 2144$) directly from Facebook CDN (`fbcdn.net`).

---

<a name="security--privacy"></a>
## 🔐 Security & Privacy

StoryVault is built with a **Zero-Trust, Zero-Telemetry** architecture:

- **Windows DPAPI Vault:** Your Instagram session cookies are never written to disk as plain text. They are encrypted using `CryptProtectData` (Windows Data Protection API tied to your Windows user account credentials) and saved to `session.enc`. Even if another user copies `session.enc`, it cannot be decrypted on a different machine or user profile.
- **No Third-Party Servers:** All network connections occur directly between your computer and official Instagram/Facebook servers (`instagram.com`, `fbcdn.net`).
- **No Firewall Triggers:** StoryVault does not open listening ports (`bind()` sockets). All network activity consists of standard outbound HTTPS connections (port 443), ensuring complete Windows Firewall and antivirus compatibility.
- **Embedded Manifest:** Built with a Windows `asInvoker` security manifest to avoid administrator elevation prompts.

---

<a name="getting-started"></a>
## 🚀 Getting Started

### Method 1: Standalone Windows Executable (Recommended)

No Python, terminal, or compiler required:
1. Download the latest release from the [Releases](https://github.com/ersinsandal/StoryVault/releases) tab (or navigate to `dist/StoryVault/`).
2. Double-click **`StoryVault.exe`** to launch.
3. Open **Settings** or the **Login Wizard** to log in to your Instagram account.
4. Paste any link and click **Download**!

---

### Method 2: Run from Source Code

#### Prerequisites:
- Windows 10 or 11 (64-bit)
- Python 3.10, 3.11, 3.12, or 3.13
- FFmpeg installed in system `PATH` (optional, for stream verification)

#### Installation:
```powershell
# 1. Clone repository
git clone https://github.com/ersinsandal/StoryVault.git
cd StoryVault

# 2. Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Launch StoryVault
python StoryVaultPro.py
```

---

### Method 3: Build Your Own Executable

You can compile a standalone bundle matching our official release:

```cmd
build.bat
```

The compiled standalone application will be generated in `dist\StoryVault\StoryVault.exe`.

---

<a name="session--cookie-management"></a>
## 🔑 Session & Cookie Management

Instagram requires authentication to view active stories and user highlights. StoryVault provides three methods to log in safely:

1. **Option A: Live Interactive Browser (Easiest)**
   - Click `Giriş Sihirbazı` (Login Wizard).
   - Click `🌐 Tarayıcıda Instagram'ı Aç`.
   - Log in using your normal credentials. StoryVault detects successful authentication and captures the session automatically.
2. **Option B: Import from Default Browser**
   - Click `⚡ Oturumu Aktar` to import directly from Chrome, Edge, Firefox, Brave, or Opera.
3. **Option C: Netscape cookies.txt Import**
   - Export cookies using any standard browser extension (e.g. *Get cookies.txt LOCALLY*) and import the `.txt` file into StoryVault.

---

<a name="project-structure"></a>
## 📁 Project Structure

```
StoryVault/
├── StoryVaultPro.py              # Main application entry point
├── build.bat                     # Windows PyInstaller build script
├── storyvault.manifest           # Windows application manifest (asInvoker, dpiAware)
├── version_info.txt              # Windows PE executable version metadata
├── requirements.txt              # Python library dependencies
├── assets/                       # Icons, branding assets, and themes
│   └── icon.ico
├── storyvault/                   # Core application package
│   ├── app.py                    # Root application controller
│   ├── config/                   # Persistent JSON settings engine
│   │   └── settings.py
│   ├── cookies/                  # Security and authentication layer
│   │   ├── browser_extractor.py  # Local browser cookie extraction
│   │   ├── live_browser_login.py # Selenium interactive login helper
│   │   ├── manager.py            # Unified cookie manager
│   │   ├── manual_importer.py    # Netscape file parser & validator
│   │   └── secure_store.py       # Windows DPAPI encryption engine
│   ├── core/                     # Download and verification pipeline
│   │   ├── downloader.py         # Multi-threaded task execution queue
│   │   ├── engine_updater.py     # In-app background engine updater
│   │   ├── highlight.py          # Highlight album inspection and fetcher
│   │   ├── quality.py            # Resolution, bitrate and DASH selector
│   │   ├── story.py              # Native Web API story downloader + fallback
│   │   └── verifier.py           # FFprobe media stream integrity analyzer
│   ├── gui/                      # CustomTkinter interface components
│   │   ├── download_panel.py     # Main URL input & download panel
│   │   ├── downloads_panel.py    # Saved media explorer & playback panel
│   │   ├── log_panel.py          # Real-time console activity log
│   │   ├── login_wizard.py       # Interactive authentication dialog
│   │   ├── main_window.py        # Root application frame & sidebar
│   │   ├── mode_selector.py      # Download mode navigation
│   │   ├── progress_widget.py    # Live progress bar and transfer speed
│   │   ├── queue_panel.py        # Task queue and status monitor
│   │   ├── settings_panel.py     # Quality, path, and language preferences
│   │   └── tray.py               # Windows system tray integration
│   ├── i18n/                     # Internationalization (TR & EN)
│   └── utils/                    # Common utilities
│       ├── dep_checker.py        # Dependency and binary availability checker
│       ├── file_namer.py         # Windows path sanitizer & collision handler
│       ├── notifier.py           # Native Windows toast notification dispatcher
│       └── url_parser.py         # Instagram URL & short-token parser
└── tests/                        # Automated unit tests
    └── test_storyvault.py
```

---

<a name="troubleshooting--faq"></a>
## ❓ Troubleshooting & FAQ

#### Q: Does StoryVault work on private accounts?
**A:** Yes! As long as your logged-in Instagram account follows the private user, StoryVault can access and download their active stories and highlights.

#### Q: Why does Instagram say my cookies are expired?
**A:** Instagram sessions naturally expire or get invalidated if you log out on the web browser. Simply open the **Login Wizard** in StoryVault and refresh your session.

#### Q: Is my Instagram password stored anywhere?
**A:** **No.** StoryVault never asks for, handles, or stores your password. It only uses encrypted session cookies (`sessionid`), identical to how your web browser stays logged in.

#### Q: Does StoryVault send any data to external servers?
**A:** **Zero.** StoryVault has no telemetry, no tracking analytics, and no external databases. All requests are strictly direct between your PC and Instagram's official servers.

---

<a name="legal-disclaimer--license"></a>
## ⚖️ Legal Disclaimer & License

### Disclaimer
This software is intended for **personal archiving and fair use only**. Users are responsible for complying with Instagram's Terms of Service and respecting the intellectual property and privacy rights of content creators. The author and contributors assume no liability for misuse of this utility.

### License
Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for details.

---

<div align="center">
Developed with ❤️ by <b><a href="https://github.com/ersinsandal">Ersin Sandal</a></b>
</div>
