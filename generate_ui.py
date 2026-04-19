import os
import json
import re

DOWNLOAD_DIR = 'telegram_videos'
OUTPUT_FILE = 'index.html'
LANGUAGE = 'zh'  # 可选: 'zh' 或 'en'

I18N = {
    'zh': {
        'lang': 'zh-CN',
        'title': 'Telegram 媒体浏览',
        'logo': '媒体浏览',
        'empty_title': '暂无已下载内容',
        'empty_desc': '请先运行下载脚本，随后重新生成页面。',
        'fallback_media_title': '媒体文件',
        'post_prefix': '帖子 #',
        'img_alt': '图片预览',
        'no_media': '该帖子暂无媒体文件',
        'no_text': '该帖子没有文本内容。',
        'default_title': '媒体内容',
        'catalog': '目录',
        'open_folder': '打开目录',
        'success': '✅ 成功！已生成/更新',
        'processed': '👉 已处理帖子数',
    },
    'en': {
        'lang': 'en',
        'title': 'Telegram Media Viewer',
        'logo': 'Media Viewer',
        'empty_title': 'No downloaded content yet',
        'empty_desc': 'Run the downloader first, then regenerate this page.',
        'fallback_media_title': 'Media file',
        'post_prefix': 'Post #',
        'img_alt': 'Image preview',
        'no_media': 'No media found for this post',
        'no_text': 'No text for this post.',
        'default_title': 'Media Content',
        'catalog': 'Directory',
        'open_folder': 'Open folder',
        'success': '✅ Success! Generated/updated',
        'processed': '👉 Processed posts',
    },
}


def safe_join_under_download_dir(folder_name, file_name=None):
    base_abs = os.path.abspath(DOWNLOAD_DIR)
    candidate = os.path.join(DOWNLOAD_DIR, folder_name)
    if file_name:
        candidate = os.path.join(candidate, file_name)
    candidate_abs = os.path.abspath(candidate)
    if os.path.commonpath([base_abs, candidate_abs]) != base_abs:
        return None
    return candidate


def to_web_path(path):
    return path.replace('\\', '/')

def generate_html():
    i18n = I18N.get(LANGUAGE, I18N['zh'])
    posts = []
    
    if os.path.exists(DOWNLOAD_DIR):
        for item in os.listdir(DOWNLOAD_DIR):
            folder_path = os.path.join(DOWNLOAD_DIR, item)
            if not os.path.isdir(folder_path):
                continue
                
            # 查找形如 "(ID 123)" 的消息 ID
            m = re.search(r'\(ID (\d+)\)$', item)
            post_id = int(m.group(1)) if m else 0
            
            text = ""
            text_path = os.path.join(folder_path, "post_text.txt")
            if os.path.exists(text_path):
                with open(text_path, "r", encoding="utf-8") as f:
                    text = f.read()
                    
            video = None
            photo = None
            for f in os.listdir(folder_path):
                if f.startswith('thumb_') or f.startswith('photo_'):
                    safe_media = safe_join_under_download_dir(item, f)
                    if safe_media:
                        photo = safe_media
                elif f.startswith('video_'):
                    safe_media = safe_join_under_download_dir(item, f)
                    if safe_media:
                        video = safe_media
                    
            if not text and not video and not photo:
                continue
                
            # 安全处理文本并保留换行
            clean_text = text.replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br>')
            safe_folder = safe_join_under_download_dir(item)
            if not safe_folder:
                continue
            folder_web_path = to_web_path(safe_folder)
            
            posts.append({
                'id': post_id,
                'title': item,
                'text': clean_text,
                'media': photo or video,
                'media_type': 'image' if photo else ('video' if video else None),
                'folder_path': folder_web_path
            })
            
    posts.sort(key=lambda x: x['id'])
    
    # 生成 HTML
    posts_json = json.dumps(posts, ensure_ascii=False)
    
    html_content = f"""<!DOCTYPE html>
<html lang="{i18n['lang']}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{i18n['title']}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-color: #0b0d10;
            --surface-color: #161920;
            --surface-hover: #1e222b;
            --primary-color: #8b5cf6;
            --primary-glow: rgba(139, 92, 246, 0.4);
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --border-color: rgba(255, 255, 255, 0.08);
            --glass-bg: rgba(22, 25, 32, 0.7);
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-color);
            color: var(--text-primary);
            min-height: 100vh;
            background-image: 
                radial-gradient(circle at 0% 10%, rgba(139, 92, 246, 0.05) 0%, transparent 40%),
                radial-gradient(circle at 100% 90%, rgba(99, 102, 241, 0.05) 0%, transparent 40%);
            background-attachment: fixed;
            display: flex;
        }}

        /* Sidebar */
        .sidebar {{
            width: 320px;
            background: var(--glass-bg);
            backdrop-filter: blur(16px);
            border-right: 1px solid var(--border-color);
            padding: 2rem 1.5rem;
            display: flex;
            flex-direction: column;
            gap: 2rem;
            position: fixed;
            height: 100vh;
            overflow-y: auto;
            z-index: 10;
        }}

        .logo {{
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            background: linear-gradient(135deg, #c084fc, #818cf8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .nav-list {{
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
            flex: 1;
            overflow-y: auto;
        }}
        
        /* 滚动条 */
        .nav-list::-webkit-scrollbar {{
            width: 4px;
        }}
        .nav-list::-webkit-scrollbar-thumb {{
            background: var(--border-color);
            border-radius: 4px;
        }}

        .nav-item {{
            display: flex;
            flex-direction: column;
            padding: 0.75rem 1rem;
            border-radius: 12px;
            color: var(--text-secondary);
            text-decoration: none;
            transition: all 0.2s;
            cursor: pointer;
            border: 1px solid transparent;
        }}

        .nav-item:hover {{
            background: var(--surface-hover);
            color: var(--text-primary);
        }}

        .nav-item.active {{
            background: rgba(139, 92, 246, 0.1);
            color: white;
            border-color: rgba(139, 92, 246, 0.3);
            box-shadow: inset 4px 0 0 var(--primary-color);
        }}

        .nav-item-title {{
            font-weight: 600;
            font-size: 0.9rem;
            margin-bottom: 0.25rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        .nav-item-id {{
            font-size: 0.7rem;
            color: var(--primary-color);
            opacity: 0.8;
            font-weight: 700;
        }}

        /* Main Content */
        .main-content {{
            margin-left: 320px;
            flex: 1;
            padding: 3rem;
            display: flex;
            justify-content: center;
        }}

        .post-container {{
            width: 100%;
            max-width: 800px;
            background: var(--surface-color);
            border: 1px solid var(--border-color);
            border-radius: 20px;
            overflow: hidden;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            display: none;
            animation: fadeIn 0.4s ease;
        }}

        .post-container.active {{
            display: flex;
            flex-direction: column;
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        .post-media {{
            width: 100%;
            max-height: 500px;
            background: #000;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
            position: relative;
        }}

        .post-media img, .post-media video {{
            max-width: 100%;
            max-height: 500px;
            object-fit: contain;
        }}

        .post-content {{
            padding: 2.5rem;
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }}

        .post-meta {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 1rem;
        }}
        
        .post-title-text {{
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--text-primary);
        }}

        .post-id-badge {{
            background: rgba(139, 92, 246, 0.15);
            color: #a78bfa;
            padding: 6px 12px;
            border-radius: 8px;
            font-size: 0.8rem;
            font-weight: 700;
        }}

        .post-text {{
            line-height: 1.7;
            color: #cbd5e1;
            font-size: 1.05rem;
            white-space: pre-wrap;
        }}

        .post-footer {{
            margin-top: 1rem;
            padding-top: 1.5rem;
            border-top: 1px solid var(--border-color);
            display: flex;
            justify-content: space-between;
            color: var(--text-secondary);
            font-size: 0.85rem;
        }}

        .btn-folder {{
            background: var(--surface-hover);
            color: var(--text-primary);
            border: 1px solid var(--border-color);
            padding: 8px 16px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 500;
            transition: all 0.2s;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }}

        .btn-folder:hover {{
            background: var(--primary-color);
            border-color: var(--primary-color);
            box-shadow: 0 0 15px var(--primary-glow);
        }}

        /* Responsive */
        @media (max-width: 1024px) {{
            .sidebar {{ width: 280px; }}
            .main-content {{ margin-left: 280px; padding: 2rem; }}
        }}

        @media (max-width: 768px) {{
            body {{ flex-direction: column; }}
            .sidebar {{ 
                width: 100%; 
                height: 35vh; 
                position: relative; 
                border-right: none; 
                border-bottom: 1px solid var(--border-color); 
            }}
            .main-content {{ margin-left: 0; padding: 1.5rem; }}
        }}
    </style>
</head>
<body>

    <aside class="sidebar">
        <div class="logo">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"></path>
            </svg>
            {i18n['logo']}
        </div>

        <div class="nav-list" id="nav-list">
            <!-- Sidebar items will be generated by JS -->
        </div>
    </aside>

    <main class="main-content">
        <div id="post-view" style="width: 100%; display: flex; justify-content: center;">
            <!-- Post content will be shown here -->
        </div>
    </main>

    <script>
        const postsData = {posts_json};

        const navList = document.getElementById('nav-list');
        const postView = document.getElementById('post-view');

        function initNavigation() {{
            if (postsData.length === 0) {{
                postView.innerHTML = `<div style="color: var(--text-secondary); text-align: center; margin-top: 5rem;">
                    <h2>{i18n['empty_title']}</h2>
                    <p style="margin-top: 1rem;">{i18n['empty_desc']}</p>
                </div>`;
                return;
            }}

            // 渲染左侧导航
            postsData.forEach((post, index) => {{
                // 菜单标题：优先文本前缀，否则使用目录名
                const previewTitle = post.text 
                    ? post.text.replace(/<br>/g, ' ').substring(0, 40) + '...'
                    : post.title.replace(/\\(ID \\d+\\)/, '').trim() || '{i18n['fallback_media_title']}';

                const navItemHTML = `
                    <div class="nav-item ${{index === 0 ? 'active' : ''}}" id="nav-${{post.id}}" onclick="openPost(${{post.id}})">
                        <span class="nav-item-title">${{previewTitle}}</span>
                        <span class="nav-item-id">{i18n['post_prefix']}${{post.id}}</span>
                    </div>
                `;
                navList.innerHTML += navItemHTML;
            }});

            // 默认打开第一个帖子
            openPost(postsData[0].id);
        }}

        function openPost(id) {{
            const post = postsData.find(p => p.id === id);
            if (!post) return;

            // 更新激活态
            document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
            document.getElementById(`nav-${{id}}`).classList.add('active');

            // 构造媒体元素
            let mediaHTML = '';
            if (post.media) {{
                // 仅允许项目内相对路径
                const path = encodeURI(post.media.replace(/\\\\/g, '/'));
                if (post.media_type === 'image') {{
                    mediaHTML = `<img src="${{path}}" alt="{i18n['img_alt']}">`;
                }} else if (post.media_type === 'video') {{
                    mediaHTML = `<video src="${{path}}" controls poster="${{path}}"></video>`;
                }}
            }} else {{
                 mediaHTML = `<div style="height: 150px; display:flex; align-items:center; color: var(--text-secondary);">{i18n['no_media']}</div>`;
            }}

            const rawText = post.text || '{i18n['no_text']}';

            // 渲染帖子内容
            postView.innerHTML = `
                <div class="post-container active">
                    <div class="post-media">
                        ${{mediaHTML}}
                    </div>
                    <div class="post-content">
                        <div class="post-meta">
                            <h2 class="post-title-text">${{post.title.replace(/\\(ID \\d+\\)/, '').trim() || '{i18n['default_title']}'}}</h2>
                            <span class="post-id-badge">ID: ${{post.id}}</span>
                        </div>
                        <div class="post-text">${{rawText}}</div>
                        
                        <div class="post-footer">
                            <span>{i18n['catalog']}: /telegram_videos/</span>
                            <a href="${{encodeURI(post.folder_path)}}" target="_blank" class="btn-folder">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
                                </svg>
                                {i18n['open_folder']}
                            </a>
                        </div>
                    </div>
                </div>
            `;
            
            // 切换时回到顶部
            window.scrollTo(0, 0);
        }}

        // 初始化
        initNavigation();
    </script>
</body>
</html>"""
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html_content)
    print("=========================================")
    print(f"{i18n['success']} {OUTPUT_FILE}")
    print(f"{i18n['processed']}: {len(posts)}")
    print("=========================================")

if __name__ == '__main__':
    generate_html()
