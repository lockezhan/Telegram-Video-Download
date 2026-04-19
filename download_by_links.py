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
            print(f"⚠️  跳过无效链接: {link}")
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
            print(f"❌ 读取链接文件失败: {exc}")
            sys.exit(1)

    if not links and not args.no_prompt:
        print("请输入帖子链接（每行一个，输入空行结束）:")
        while True:
            line = input().strip()
            if not line:
                break
            links.append(line)

    links = normalize_links(links)

    if not links:
        print("❌ 没有可用的 Telegram 帖子链接。")
        print("示例: https://t.me/channel_name/1234")
        sys.exit(1)

    return links


def parse_args():
    parser = argparse.ArgumentParser(
        description="Telegram 指定帖子链接下载器（独立入口）"
    )
    parser.add_argument(
        "links",
        nargs="*",
        help="帖子链接，可传多个，例如: https://t.me/xxx/1 https://t.me/xxx/2",
    )
    parser.add_argument(
        "-f",
        "--file",
        help="从文本文件读取链接（每行一个）",
    )
    parser.add_argument(
        "--no-prompt",
        action="store_true",
        help="未传 links/file 时不进入交互输入，直接报错退出",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    links = collect_links(args)

    core.MODE = "specific"
    core.POST_URLS = links

    print("=" * 60)
    print("🚀 独立入口启动：指定链接下载模式")
    print(f"🔗 本次链接数量: {len(links)}")
    for index, link in enumerate(links, 1):
        print(f"  {index}. {link}")
    print("=" * 60)

    asyncio.run(core.main())


if __name__ == "__main__":
    main()
