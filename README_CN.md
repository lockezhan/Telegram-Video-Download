# Telegram 视频与媒体下载器

一款基于 `telethon` 构建的高性能 Telegram 媒体下载工具，通过并行分块下载实现极速传输。

## 功能特性 ✨

*   **FastDownload 引擎（并行分块）：** 专为非高级账户优化，通过多线程分块突破单连接限速。
*   **简洁终端界面：** 集成 `tqdm`，提供美观、无闪烁的并发进度条。
*   **自动瓶颈检测：** 若缺少 `cryptg` 或账户状态（高级/普通）影响速度时自动提示。
*   **相册支持：** 自动检测分组媒体并批量下载。
*   **断点续传：** 自动跳过已下载的媒体文件。
*   **字幕导出：** 每个帖子文件夹自动保存 `post_text.txt`。
*   **网页画廊生成器：** `generate_ui.py` 生成 `index.html`，方便浏览下载内容。

## 前置要求 🛠

开始前，请确保具备：
1. **Python 3.8+**
2. 一个有效的 **Telegram 账号**

## 🚀 快速开始

### 1. 获取 API 信息

1. 登录 Telegram 账号：[https://my.telegram.org/](https://my.telegram.org/)
2. 前往 **"API development tools"**。
3. 创建一个新 App，复制 **`api_id`** 和 **`api_hash`**。

### 2. 下载与安装

克隆仓库并安装依赖：

```bash
git clone https://github.com/lockezhan/Telegram-Video-Download.git
cd Telegram-Video-Download

# 安装依赖
pip3 install telethon tqdm cryptg
```

### 3. 配置脚本

打开 `tg_video_downloader.py`，填写你的账号信息：

```python
# ================= 配置项 =================
API_ID = 1234567               # 你的 API ID
API_HASH = 'your_api_hash'     # 你的 API Hash
PHONE = '+1234567890'          # 你的手机号（含国家代码）

# 速度与界面设置
DOWNLOAD_CONCURRENCY = 4       # 同时下载文件数
FAST_DOWNLOAD_ENABLED = True   # 多分块下载（强烈推荐）
FAST_DOWNLOAD_WORKERS = 4      # 每个文件的工作线程数
SHOW_LIVE_PROGRESS = True      # 显示 tqdm 进度条
```

### 4. 性能优化技巧 ⚡

若想获得最佳下载速度：
1. **确保已安装 `cryptg`：** 为 Telegram 加密提供硬件加速。
2. **开启 `FAST_DOWNLOAD_ENABLED`：** 这是突破非高级账户约 1MB/s 限速的关键。
3. **连接数建议：** `DOWNLOAD_CONCURRENCY × FAST_DOWNLOAD_WORKERS` 即总 TCP 连接数，建议保持在 16~32 之间以获得最佳稳定性。

## 使用说明 📖

### 方式一：直接下载（标准模式）

在 `tg_video_downloader.py` 中配置 `POST_URLS` 或 `MODE`，然后运行：
```bash
python3 tg_video_downloader.py
```

### 方式二：灵活链接输入（推荐 🚀）

使用 `run_links.sh` 包装脚本（或直接使用 `download_by_links.py`），无需修改变量即可传入链接：

**1. 命令行直接传入链接：**
```bash
./run_links.sh "https://t.me/channel_name/101" "https://t.me/channel_name/102"
```

**2. 从文本文件读取：**
创建一个 `links.txt`，每行一个 URL，然后运行：
```bash
./run_links.sh -f links.txt
```

**3. 交互式模式：**
直接运行脚本，按提示粘贴链接：
```bash
./run_links.sh
```

---

*   **首次运行：** 终端会提示输入 Telegram 登录验证码。
*   **会话管理：** 运行后会生成 `telegram_session.session` 文件，请妥善保管，避免重复登录。

### 生成网页画廊（可选）🖥️

在浏览器中以美观的网页界面浏览已下载内容：
```bash
python3 generate_ui.py
```
用浏览器打开生成的 `index.html` 即可。

## 作者与致谢 👨‍💻

*   原始灵感：[telegram-channel-dowloader](https://github.com/cyberg1psy/telegram-channel-dowloader.git)
*   优化与界面：Antigravity AI
*   新引擎：FastTelethon 风格并行分块下载实现

## 许可证 📜

本项目基于 [MIT 许可证](LICENSE) 开源。

---
*免责声明：本工具仅供个人备份与学习研究之用，请遵守 Telegram 服务条款。*
