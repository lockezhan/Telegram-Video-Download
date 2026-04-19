# Telegram Video & Media Downloader

A practical Telegram media downloader built with `telethon`, focused on downloading by direct post links (`t.me/...`).

## Features ✨

* **Link-first workflow:** download by specific post links quickly.
* **Minimal entry script:** `run_links.sh` for one-command usage.
* **Album support:** auto-detect grouped media and download all items.
* **Smart resume:** skip already-downloaded media automatically.
* **Caption export:** saves `post_text.txt` per post folder.
* **Web gallery generator:** `generate_ui.py` creates `index.html` for browsing.

## Prerequisites 🛠

Before you begin, you need:
1. **Python 3.7+** installed on your system.
2. An active **Telegram Account**.

## 🚀 Getting Started

### 1. Gather your API Data
You must obtain authorization keys to interact with Telegram as an application.
1. Log into your Telegram core account: [https://my.telegram.org/](https://my.telegram.org/)
2. Go to **"API development tools"**.
3. Create a new App (the details like app name don't matter much) and copy the **`App api_id`** and **`App api_hash`**.

### 2. Download and Setup
Clone the repository and install dependencies:

```bash
git clone https://github.com/yourusername/telegram-video-downloader.git
cd telegram-video-downloader

# Install the required library
pip3 install telethon
```

### 3. Configure the Script
Open `tg_video_downloader.py` and set your credentials in the `SETTINGS` block:

```python
# ================= SETTINGS =================

API_ID = 1234567               # Replace 1234567 with your Integer App api_id
API_HASH = 'your_api_hash'     # Replace with your App api_hash string
PHONE = '+1234567890'          # Replace with your international phone number

MODE = 'specific'              # recommended for link-first workflow
CHANNEL_ID = int('-100123456789') # Replace with your Target Channel ID.
# ...
```

#### How to find your Private Channel ID:
If the URL to a post is: `https://t.me/c/123049182/42`
Your base ID sequence is `123049182`. To convert this to an API Channel ID, prefix it with `-100`. So it becomes `-100123049182`.

### 4. Use the Minimal Link Entry (Recommended)

Use the standalone launcher:

```bash
cd TG-channel-dowloader
./run_links.sh "https://t.me/channel_name/1234"
```

Multiple links:

```bash
./run_links.sh "https://t.me/a/1" "https://t.me/b/2"
```

From file (one link per line):

```bash
./run_links.sh -f links.txt
```

### 5. Alternative Run Modes

Run core script directly:

```bash
python3 tg_video_downloader.py
```

Run standalone Python link entry directly:

```bash
python3 download_by_links.py "https://t.me/channel_name/1234"
```

* **First Time Run:** The terminal will prompt you to enter a Telegram Login Code (sent to your Telegram App via the main Telegram service chat account). Type it in and hit enter. 
* A `telegram_session.session` file will be generated in your folder. Keep this safe, as it prevents you from having to log in again.

### 6. Check out your files!
By default, the script will create a folder called `telegram_videos` where all fetched posts will be organized neatly into named sub-directories. 

### 7. Generate a Web Gallery (Optional) 🖥️
To comfortably view all the downloaded media in your browser instead of digging through folders, we've included a UI generator script.
Simply run:
```bash
python3 generate_ui.py
```
This will scan your `telegram_videos` folder and instantly create an `index.html` file. Open `index.html` in any web browser to enjoy a beautiful, responsive dashboard to view all your posts, read captions, and watch videos seamlessly!

## GitHub Upload Checklist ✅

Before pushing publicly:

1. Replace real credentials in `tg_video_downloader.py`:
    - `API_ID`
    - `API_HASH`
    - `PHONE`
2. Keep session/media artifacts untracked (already covered in `.gitignore`):
    - `telegram_session.session*`
    - `telegram_videos/`
    - `index.html`
3. If any sensitive files were already tracked, untrack them once:

```bash
git rm --cached telegram_session.session telegram_session.session-journal 2>/dev/null || true
git rm -r --cached telegram_videos 2>/dev/null || true
git rm --cached index.html 2>/dev/null || true
```

## Folder Structure Example
```
telegram_videos/
├── Amazing Python tutorial video... (ID 142)/
│   ├── video_142.mp4
│   ├── thumb_142.jpg
│   └── post_text.txt
└── Great photo array from... (ID 188)/
    ├── photo_188.jpg
    ├── photo_189.jpg
    └── post_text.txt
```

## Authors & Credits 👨‍💻

* **cyberg1psy* - Idea, architecture, and testing.
* **Claude 3 Opus** - AI Assistant.
* **Gemini (Antigravity)** - AI Assistant.

## License 📜

This project is licensed under the [MIT License](LICENSE) - see the LICENSE file for details.

---
*Disclaimer: Make sure you have the rights to download and distribute the content you are scraping. This tool is provided for personal backup and educational purposes only.*
