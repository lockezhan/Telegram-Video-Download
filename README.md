# Telegram Video & Media Downloader

> 🇨🇳 [中文文档请点击这里 / Chinese README](README_CN.md)

A high-performance Telegram media downloader built with `telethon`, featuring parallel chunk downloading for maximum speed.

## Features ✨

*   **FastDownload Engine (Parallel Chunking):** Specifically optimized for non-premium accounts to bypass single-connection speed limits via multi-threaded chunking.
*   **Clean Terminal UI:** Integrated with `tqdm` for beautiful, non-flickering concurrent progress bars.
*   **Automatic Bottleneck Detection:** Notifies you if `cryptg` is missing or if your account status (Premium/Non-Premium) is affecting speeds.
*   **Album support:** Auto-detect grouped media and download all items.
*   **Smart resume:** Skip already-downloaded media automatically.
*   **Caption export:** Saves `post_text.txt` per post folder.
*   **Web gallery generator:** `generate_ui.py` creates `index.html` for browsing.

## Prerequisites 🛠

Before you begin, you need:
1. **Python 3.8+**
2. An active **Telegram Account**.

## 🚀 Getting Started

### 1. Gather your API Data
1. Log into your Telegram account: [https://my.telegram.org/](https://my.telegram.org/)
2. Go to **"API development tools"**.
3. Create a new App and copy the **`api_id`** and **`api_hash`**.

### 2. Download and Setup
Clone the repository and install dependencies:

```bash
git clone https://github.com/lockezhan/Telegram-Video-Download.git
cd Telegram-Video-Download

# Install requirements
pip3 install telethon tqdm cryptg
```

### 3. Configure the Script
Open `tg_video_downloader.py` and set your credentials:

```python
# ================= SETTINGS =================
API_ID = 1234567               
API_HASH = 'your_api_hash'     
PHONE = '+1234567890'          

# Speed & UI Settings
DOWNLOAD_CONCURRENCY = 4       # Concurrent files
FAST_DOWNLOAD_ENABLED = True   # Multi-chunk downloading (Highly Recommended)
FAST_DOWNLOAD_WORKERS = 4      # Workers per file
SHOW_LIVE_PROGRESS = True      # Clean tqdm bars
```

### 4. Performance Tips ⚡

If you want the absolute best speeds:
1. **Ensure `cryptg` is installed:** This provides hardware acceleration for Telegram's encryption.
2. **Enable `FAST_DOWNLOAD_ENABLED`:** This is the key to bypassing the ~1MB/s limit on non-premium accounts.
3. **Connection Count:** `DOWNLOAD_CONCURRENCY * FAST_DOWNLOAD_WORKERS` defines your total active TCP connections. Keep total connections around 16-32 for optimal stability.

## Usage Guide 📖

### Option 1: Direct Download (Standard)
Configure the `POST_URLS` or `MODE` inside `tg_video_downloader.py`, then run:
```bash
python3 tg_video_downloader.py
```

### Option 2: Flexible Link Entry (Recommended 🚀)
Use the `run_links.sh` wrapper (or `download_by_links.py` directly) to pass links without editing variables:

**1. Command Line Links:**
```bash
./run_links.sh "https://t.me/channel_name/101" "https://t.me/channel_name/102"
```

**2. From a Text File:**
Create a `links.txt` with one URL per line, then run:
```bash
./run_links.sh -f links.txt
```

**3. Interactive Mode:**
Just run the script, and it will prompt you to paste links:
```bash
./run_links.sh
```

---

*   **First Time Run:** The terminal will prompt you to enter a Telegram Login Code.
*   **Session Management:** A `telegram_session.session` file will be generated. Keep this safe to avoid re-logging.

### Generate a Web Gallery (Optional) 🖥️
To view your downloads in a beautiful web dashboard:
```bash
python3 generate_ui.py
```
Open `index.html` in your browser.

## Authors & Credits 👨‍💻

*   Original Idea: [telegram-channel-dowloader](https://github.com/cyberg1psy/telegram-channel-dowloader.git)
*   Optimization & UI: Antigravity AI
*   New Engine: FastTelethon-style parallel chunking implementation.

## License 📜

This project is licensed under the [MIT License](LICENSE).

---
*Disclaimer: This tool is provided for personal backup and educational purposes only. Respect Telegram's TOS.*
