import argparse
import asyncio
import re
import sys

import tg_video_downloader as core


def normalize_links(raw_links):
    normalized = []
    seen = set()

    for item in raw_links:
        if not item:
            continue
        link = item.strip()
        if not link:
            continue

        if not re.search(r"t\.me/(?:c/)?[^/]+/\d+", link):
            print(f"⚠️  skip invalid link: {link}")
            continue

        if link not in seen:
            seen.add(link)
            normalized.append(link)

    return normalized


def collect_links(args):
    links = []

    if args.links:
        links.extend(args.links)

    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as file_obj:
                for line in file_obj:
                    line = line.strip()
                    if line:
                        links.append(line)
        except Exception as exc:
            print(f"❌ read link file error: {exc}")
            sys.exit(1)

    if not links and not args.no_prompt:
        print("please input links(one per line, empty line to end):")
        while True:
            line = input().strip()
            if not line:
                break
            links.append(line)

    links = normalize_links(links)

    if not links:
        print("❌ No valid Telegram post links found.")
        print("Example: https://t.me/channel_name/1234")
        sys.exit(1)

    return links


def parse_args():
    parser = argparse.ArgumentParser(
        description="Telegram specific post links downloader"
    )
    parser.add_argument(
        "links",
        nargs="*",
        help="post links, e.g.: https://t.me/xxx/1 https://t.me/xxx/2",
    )
    parser.add_argument(
        "-f",
        "--file",
        help="read links from file(one per line)",
    )
    parser.add_argument(
        "--no-prompt",
        action="store_true",
        help="without links/file, no interactive input, exit directly",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    links = collect_links(args)

    core.MODE = "specific"
    core.POST_URLS = links

    print("=" * 60)
    print("🚀 Specific links download mode")
    print(f"🔗 Number of links: {len(links)}")
    for index, link in enumerate(links, 1):
        print(f"  {index}. {link}")
    print("=" * 60)

    asyncio.run(core.main())


if __name__ == "__main__":
    main()
