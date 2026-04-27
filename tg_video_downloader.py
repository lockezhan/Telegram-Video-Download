# original imports
import os
import asyncio
import re
import time
import sys
import math
from telethon import TelegramClient
from telethon.tl.types import MessageMediaDocument, Document, Photo, InputDocumentFileLocation, InputPhotoFileLocation
from telethon.tl.functions.upload import GetFileRequest
from telethon.errors import FileMigrateError

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module='telethon.client.auth')


try:
    from tqdm.asyncio import tqdm
except ImportError:
    print("❌ Error: 'tqdm' is not installed. Please install it using 'pip install tqdm'.")
    sys.exit(1)

try:
    import cryptg
    HAS_CRYPTG = True
except ImportError:
    HAS_CRYPTG = False

# ================= SETTINGS =================

# 1. API_ID & API_HASH
# Get these by logging into https://my.telegram.org/, 
# navigating to "API development tools" and creating a new application.
API_ID = 123456  # Replace with your API_ID (integer without quotes)
API_HASH = 'xxxxxxxxxx'  # Replace with your API_HASH (string inside quotes)

# 2. Telegram Phone Number
# Your phone number in international format, including the plus sign.
PHONE = '+12345678'  # Replace with your phone number

# 3. Mode of Operation
# 'specific'  — download posts listed in POST_URLS
# 'scan_all'  — scan the entire channel and download all media
MODE = 'specific'  # change to 'specific' if you want to download exact URLs

# 4. Target Channel ID
# If your private channel URL is https://t.me/c/123456789/123, 
# the ID is usually formed by prefixing '-100' -> -100123456789
CHANNEL_ID = int('-1003665829879')  # Replace with the actual channel ID

# 5. Starting Message ID (Optional)
# If you want to start scanning from a specific post, put its ID here. 
# Or leave it as 0 to start from the very first post in the channel.
START_FROM_MSG_ID = 0

# 6. Specific Post URLs (Used only if MODE = 'specific')
POST_URLS = [
    'https://t.me/12134/4401',
]

# 7. Concurrent Downloads
# Increase this value carefully; Telegram/network stability is usually the limiting factor.
DOWNLOAD_CONCURRENCY = 4

# 8. Performance Tweaks
# Set False to skip thumbnail fetch for videos (usually faster overall).
DOWNLOAD_VIDEO_THUMBNAIL = False
# Live progress in terminal using tqdm
SHOW_LIVE_PROGRESS = True
# Refresh interval when SHOW_LIVE_PROGRESS is enabled.
PROGRESS_UPDATE_INTERVAL_SEC = 0.5
# Enable Parallel Chunk Downloading (bypasses non-premium limits)
FAST_DOWNLOAD_ENABLED = True
# Number of concurrent workers per file for parallel chunking
FAST_DOWNLOAD_WORKERS = 4

# Directory where files will be saved
DOWNLOAD_DIR = 'telegram_videos'
# ============================================


def sanitize_folder_name(text):
    if not text:
        return "Untitled"
    safe_text = re.sub(r'[\\/*?:"<>|\n\r]', ' ', text)
    safe_text = " ".join(safe_text.split())
    return safe_text[:40].strip()


def scan_already_downloaded(download_dir):
    """Scans the designated directory and returns a set of IDs for already downloaded videos."""
    downloaded_ids = set()
    if not os.path.exists(download_dir):
        return downloaded_ids
    for root, dirs, files in os.walk(download_dir):
        for fname in files:
            m = re.match(r'video_(\d+)\.mp4', fname)
            if m:
                downloaded_ids.add(int(m.group(1)))
    return downloaded_ids


def is_video(message):
    """Checks if the given message contains a video file."""
    if message.video:
        return True
    if message.media and isinstance(message.media, MessageMediaDocument):
        doc = message.media.document
        if doc:
            # Check mime type
            if doc.mime_type and doc.mime_type.startswith('video/'):
                return True
    return False


def has_media_to_download(message):
    """Helper to check if there is a video or a photo attached."""
    if message.video or message.photo:
        return True
    if message.media and isinstance(message.media, MessageMediaDocument):
        doc = message.media.document
        if doc and doc.mime_type and doc.mime_type.startswith('video/'):
            return True
    return False

def get_input_file_location(message):
    """Extracts InputFileLocation and Size from a message for MTProto GetFileRequest."""
    if message.document:
        doc = message.document
        return InputDocumentFileLocation(
            id=doc.id,
            access_hash=doc.access_hash,
            file_reference=doc.file_reference,
            thumb_size=''
        ), doc.size
    elif message.photo:
        photo = message.photo
        # Get largest size
        largest = max(photo.sizes, key=lambda s: s.size if hasattr(s, 'size') else 0)
        return InputPhotoFileLocation(
            id=photo.id,
            access_hash=photo.access_hash,
            file_reference=photo.file_reference,
            thumb_size=largest.type
        ), largest.size if hasattr(largest, 'size') else 0
    return None, 0

async def fast_download_file(client, location, file_size, out_file, progress_callback=None, workers=4):
    """Parallel Chunk Downloader using multiple workers per file."""
    chunk_size = 1024 * 1024  # 1MB chunk size
    chunks = math.ceil(file_size / chunk_size)
    queue = asyncio.Queue()
    # Check if we are on the correct DC, if not, switch the client
    sender = client._sender
    exported = False
    try:
        # Try a tiny request to trigger DC migration if needed
        await client(GetFileRequest(location, offset=0, limit=4096))
    except FileMigrateError as e:
        # Transfer the client to the correct DC
        sender = await client._borrow_exported_sender(e.new_dc)
        exported = True
    except Exception:
        # Other errors will be handled in the workers
        pass

    for i in range(chunks):
        queue.put_nowait((i, i * chunk_size))

    # Pre-allocate file
    with open(out_file, 'wb') as f:
        if file_size > 0:
            f.seek(file_size - 1)
            f.write(b'\0')

    lock = asyncio.Lock()
    downloaded = 0

    async def worker():
        nonlocal downloaded
        while not queue.empty():
            try:
                i, offset = queue.get_nowait()
            except asyncio.QueueEmpty:
                break

            # Add retry mechanism for each chunk
            for attempt in range(3):
                try:
                    req = GetFileRequest(
                        location=location,
                        offset=offset,
                        limit=chunk_size
                    )
                    result = await client._call(sender, req)
                    
                    async with lock:
                        with open(out_file, 'rb+') as f:
                            f.seek(offset)
                            f.write(result.bytes)
                        downloaded += len(result.bytes)
                        if progress_callback:
                            progress_callback(downloaded, file_size)
                    break
                except Exception as e:
                    if attempt == 2:
                        raise e
                    await asyncio.sleep(1)
            
            queue.task_done()

    worker_tasks = [asyncio.create_task(worker()) for _ in range(workers)]
    try:
        await asyncio.gather(*worker_tasks)
    finally:
        if exported and sender:
            await client._return_exported_sender(sender)


async def download_video(m, client, post_dir, idx, total, downloaded_ids, semaphore):
    """Downloads media (video or photo) and its thumbnail."""
    is_vid = is_video(m) or m.video
    is_pic = m.photo

    if is_pic:
        file_name = f"photo_{m.id}.jpg"
    else:
        file_name = f"video_{m.id}.mp4"

    file_path = os.path.join(post_dir, file_name)
    
    # Attempt to grab the thumbnail first if it's a video
    if DOWNLOAD_VIDEO_THUMBNAIL and is_vid and not is_pic:
        try:
            thumb_path = os.path.join(post_dir, f"thumb_{m.id}.jpg")
            if not os.path.exists(thumb_path):
                async with semaphore:
                    await client.download_media(m, thumb=-1, file=thumb_path)
        except Exception as e:
            tqdm.write(f"      ⚠️  缩略图下载失败: {e}")

    if m.id in downloaded_ids:
        return False

    if os.path.exists(file_path):
        downloaded_ids.add(m.id)
        return False

    progress_callback = None
    if SHOW_LIVE_PROGRESS:
        last_update = 0.0
        bar = tqdm(
            desc=file_name[:20],
            total=0,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
            leave=False,
            position=idx % max(1, DOWNLOAD_CONCURRENCY)
        )

        def progress(current, total_bytes):
            nonlocal last_update
            
            if bar.total == 0 and total_bytes:
                bar.total = total_bytes
                
            now = time.monotonic()
            is_finished = bool(total_bytes) and current >= total_bytes
            
            # small optimization so we don't spam terminal
            if not is_finished and (now - last_update) < PROGRESS_UPDATE_INTERVAL_SEC:
                return

            last_update = now
            bar.n = current
            bar.refresh()

        progress_callback = progress

    try:
        async with semaphore:
            if FAST_DOWNLOAD_ENABLED:
                location, size = get_input_file_location(m)
                if location and size:
                    await fast_download_file(client, location, size, file_path, progress_callback=progress_callback, workers=FAST_DOWNLOAD_WORKERS)
                else:
                    # Fallback to standard if no location found
                     await client.download_media(m, file=file_path, progress_callback=progress_callback)
            else:
                await client.download_media(m, file=file_path, progress_callback=progress_callback)
        downloaded_ids.add(m.id)
        if SHOW_LIVE_PROGRESS:
            bar.close()
            tqdm.write(f"  ✅ 下载完成: {file_name}")
        else:
            print(f"  ✅ 下载完成: {file_name}")
        return True
    except Exception as e:
        if SHOW_LIVE_PROGRESS:
            bar.close()
            tqdm.write(f"\n  ❌ 下载失败: {type(e).__name__}: {e}")
        else:
            print(f"\n  ❌ 下载失败: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


async def process_message(client, entity, message, downloaded_ids):
    """Processes a single message, handles albums, extracts caption, and downloads."""
    msg_id = message.id

    # Gather all related messages/media for albums
    messages_to_download = []
    post_text = message.text or ""

    if message.grouped_id:
        try:
            album_items = []
            async for m in client.iter_messages(entity, min_id=msg_id - 100, max_id=msg_id + 100, limit=100):
                if m.grouped_id == message.grouped_id:
                    if has_media_to_download(m):
                        album_items.append(m)
                    if m.text and len(m.text) > len(post_text):
                        post_text = m.text
            
            messages_to_download = sorted(album_items, key=lambda x: x.id)
        except Exception as e:
            if has_media_to_download(message):
                messages_to_download.append(message)
    else:
        if has_media_to_download(message):
            messages_to_download.append(message)

    if not messages_to_download:
        tqdm.write("⚠️  No downloadable media found.")
        return 0

    # Create folder for saving
    folder_prefix = sanitize_folder_name(post_text)
    post_folder_name = f"{folder_prefix} (ID {msg_id})"
    post_dir = os.path.join(DOWNLOAD_DIR, post_folder_name)
    os.makedirs(post_dir, exist_ok=True)
    tqdm.write(f"📁 Saving to: {post_dir}")

    # Save original caption
    if post_text:
        with open(os.path.join(post_dir, "post_text.txt"), "w", encoding="utf-8") as f:
            f.write(post_text)

    # Iterate and download media files
    downloaded_count = 0
    total = len(messages_to_download)
    semaphore = asyncio.Semaphore(max(1, DOWNLOAD_CONCURRENCY))

    tasks = [
        asyncio.create_task(
            download_video(m, client, post_dir, idx, total, downloaded_ids, semaphore)
        )
        for idx, m in enumerate(messages_to_download, 1)
    ]

    for ok in await asyncio.gather(*tasks):
        if ok:
            downloaded_count += 1

    return downloaded_count


async def run_specific(client, downloaded_ids):
    """Mode: Specific Posts"""
    total_new = 0

    for url in POST_URLS:
        print(f"\n{'='*55}")
        print(f"Targeting URL: {url}")

        match = re.search(r't\.me/(?:c/)?([^/]+)/(\d+)', url)
        if not match:
            print("❌ Invalid link format.")
            continue

        channel_identifier = match.group(1)
        msg_id = int(match.group(2))
        
        # Determine the channel entity
        # For private channels: c/123456789 -> -100123456789
        # For public channels: @channel_name or channel_name
        if channel_identifier.isdigit():
            channel_id = int(f"-100{channel_identifier}")
        else:
            # For public channels, use the username directly
            channel_id = channel_identifier if channel_identifier.startswith('@') else f"@{channel_identifier}"

        try:
            entity = await client.get_entity(channel_id)
            print(f"✅ Channel accessed: {entity.title if hasattr(entity, 'title') else entity.username}")
        except Exception as e:
            print(f"❌ Channel access error: {e}")
            continue

        try:
            message = await client.get_messages(entity, ids=msg_id)
            if not message:
                print("❌ Target message not found.")
                continue
            print(f"📨 Target acquired (ID: {message.id}) - Media processing...")
        except Exception as e:
            print(f"❌ Error fetching message: {e}")
            import traceback
            traceback.print_exc()
            continue

        if not has_media_to_download(message):
            print("❌ No downloadable media found in this message.")
            continue

        count = await process_message(client, entity, message, downloaded_ids)
        total_new += count

    return total_new


async def run_scan_all(client, downloaded_ids):
    """Mode: Scan Entire Channel"""
    total_new = 0
    processed = 0
    seen_groups = set()

    print(f"\n🔍 Scanning entire channel (ID: {CHANNEL_ID})...")
    print("   This may take a while depending on the channel size...\n")

    try:
        entity = await client.get_entity(CHANNEL_ID)
    except Exception as e:
        print(f"❌ Channel access error: {e}")
        return 0

    # Iterate through all messages starting from the most recent backward to older
    # Alternatively you can set reverse=False to start from oldest
    async for message in client.iter_messages(entity, reverse=True):
        if message and message.id < START_FROM_MSG_ID:
            continue
            
        processed += 1

        # Skip empty/service messages
        if not message or not hasattr(message, 'media'):
            continue

        # Prevent duplicate handling of the same album
        if message.grouped_id:
            if message.grouped_id in seen_groups:
                continue
            seen_groups.add(message.grouped_id)

        # Confirm at least one video exists
        has_video = is_video(message) or message.video
        if message.grouped_id and not has_video:
            pass # Album might contain a video in the grouping
        elif not has_video and not message.grouped_id:
            continue

        count = await process_message(client, entity, message, downloaded_ids)
        total_new += count

        if processed % 100 == 0:
            print(f"  📊 Processed items: {processed}, New videos found: {total_new}")

    print(f"\n  📊 Total messages reviewed: {processed}")
    return total_new


async def main():
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    # Cache previously downloaded files to optimize performance
    downloaded_ids = scan_already_downloaded(DOWNLOAD_DIR)
    if downloaded_ids:
        print(f"ℹ️  Found {len(downloaded_ids)} local media items. Duplicates will be skipped.")

    client = TelegramClient('telegram_session', API_ID, API_HASH)
    
    # Telethon will automatically prompt for the authentication code 
    # if no valid session file is found.
    await client.start(phone=PHONE)
    
    me = await client.get_me()
    print(f"✅ Authorization successful! User logged in: {me.username or me.first_name}")

    if not getattr(me, 'premium', False):
        print("\n⚠️  NOTICE: This account does NOT have Telegram Premium.")
    else:
        print("\n💎 Telegram Premium account detected! Download speeds should be fully unlocked.")

    if not HAS_CRYPTG:
        print("\n⚠️  CRITICAL WARNING: 'cryptg' library is missing in your environment.")
        print("   To massively boost download speed, please run: pip install cryptg")

    print("")

    if MODE == 'specific':
        print("📋 Active Mode: Specific URLs Mode")
        total_new = await run_specific(client, downloaded_ids)
    elif MODE == 'scan_all':
        print("🌐 Active Mode: Full Channel Scan")
        total_new = await run_scan_all(client, downloaded_ids)
    else:
        print(f"❌ Unknown mode selected: {MODE}")
        return

    print(f"\n🎉 OPERATION COMPLETE! Total new files downloaded: {total_new}")


if __name__ == '__main__':
    asyncio.run(main())
