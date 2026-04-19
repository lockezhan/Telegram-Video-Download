import os
import asyncio
import re
from telethon import TelegramClient
from telethon.tl.types import MessageMediaDocument

# ================= SETTINGS =================

# 1. API_ID & API_HASH
# Get these by logging into https://my.telegram.org/, 
# navigating to "API development tools" and creating a new application.
API_ID = 123456  # Replace with your API_ID (integer without quotes)
API_HASH = 'xxxxxxxxxxxxxxxxx'  # Replace with your API_HASH (string inside quotes)

# 2. Telegram Phone Number
# Your phone number in international format, including the plus sign.
PHONE = '+12356789'  # Replace with your phone number

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


async def download_video(m, client, post_dir, idx, total, downloaded_ids):
    """Downloads media (video or photo) and its thumbnail."""
    is_vid = is_video(m) or m.video
    is_pic = m.photo

    if is_pic:
        file_name = f"photo_{m.id}.jpg"
    else:
        file_name = f"video_{m.id}.mp4"

    file_path = os.path.join(post_dir, file_name)
    
    print(f"  [{idx}/{total}] 处理文件: {file_name}")
    print(f"      类型: {'视频' if is_vid and not is_pic else '图片' if is_pic else '未知'}")

    # Attempt to grab the thumbnail first if it's a video
    if is_vid and not is_pic:
        try:
            thumb_path = os.path.join(post_dir, f"thumb_{m.id}.jpg")
            if not os.path.exists(thumb_path):
                await client.download_media(m, thumb=-1, file=thumb_path)
        except Exception as e:
            print(f"      ⚠️  缩略图下载失败: {e}")

    if m.id in downloaded_ids:
        print(f"  [{idx}/{total}] ⏭️  {file_name} — 已下载，跳过")
        return False

    if os.path.exists(file_path):
        print(f"  [{idx}/{total}] ⏭️  {file_name} — 本地已存在，跳过")
        downloaded_ids.add(m.id)
        return False

    print(f"  [{idx}/{total}] ⬇️  开始下载 {file_name}...")

    def progress(current, total_bytes):
        percent = current * 100 / total_bytes if total_bytes else 0
        bar_len = 24
        filled = int(bar_len * percent / 100)
        bar = '█' * filled + '░' * (bar_len - filled)
        current_mb = current / (1024 * 1024)
        total_mb = total_bytes / (1024 * 1024) if total_bytes else 0
        print(f"    [{bar}] {percent:6.2f}%  {current_mb:8.2f}MB/{total_mb:8.2f}MB", end='\r')

    try:
        await client.download_media(m, file=file_path, progress_callback=progress)
        print()
        downloaded_ids.add(m.id)
        print(f"  ✅ 下载完成: {file_name}")
        return True
    except Exception as e:
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
        print(f"🎬 Album detected (group ID: {message.grouped_id})")
        try:
            # Search nearby messages to find the rest of the album parts
            # Use a wider range and timeout to ensure we find all album items
            album_items = []
            async for m in client.iter_messages(entity, min_id=msg_id - 100, max_id=msg_id + 100, limit=100):
                if m.grouped_id == message.grouped_id:
                    if has_media_to_download(m):
                        album_items.append(m)
                    # Save the longest text piece just in case caption is attached to a different item
                    if m.text and len(m.text) > len(post_text):
                        post_text = m.text
            
            messages_to_download = sorted(album_items, key=lambda x: x.id)
            print(f"   Found {len(messages_to_download)} media items in album")
        except Exception as e:
            print(f"   ⚠️  Error scanning album: {e}")
            # Fallback: at least download the current message if it has media
            if has_media_to_download(message):
                messages_to_download.append(message)
    else:
        print(f"📄 Single message (not an album)")
        if has_media_to_download(message):
            messages_to_download.append(message)

    if not messages_to_download:
        print("⚠️  No downloadable media found.")
        return 0

    # Create folder for saving
    folder_prefix = sanitize_folder_name(post_text)
    post_folder_name = f"{folder_prefix} (ID {msg_id})"
    post_dir = os.path.join(DOWNLOAD_DIR, post_folder_name)
    os.makedirs(post_dir, exist_ok=True)
    print(f"📁 Saving to: {post_dir}")

    # Save original caption
    if post_text:
        with open(os.path.join(post_dir, "post_text.txt"), "w", encoding="utf-8") as f:
            f.write(post_text)

    # Iterate and download media files
    downloaded_count = 0
    total = len(messages_to_download)
    for idx, m in enumerate(messages_to_download, 1):
        ok = await download_video(m, client, post_dir, idx, total, downloaded_ids)
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
            print(f"📨 Message found (ID: {message.id})")
            print(f"   Has media: {message.media is not None}")
            print(f"   Has photo: {message.photo}")
            print(f"   Has video: {message.video}")
            print(f"   Has text: {bool(message.text)}")
            if message.media:
                print(f"   Media type: {type(message.media).__name__}")
                # Check for access restrictions
                if message.restriction_reason:
                    print(f"\n⚠️  ACCESS RESTRICTION DETECTED:")
                    for reason in message.restriction_reason:
                        print(f"   Platform: {reason.platform}")
                        print(f"   Reason: {reason.reason}")
                        print(f"   Message: {reason.text}")
                    print("   Note: this is Telegram metadata (often for official app stores).")
                    print("   Downloader will still attempt to fetch media.")
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
    print("✅ Authorization successful!\n")

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
