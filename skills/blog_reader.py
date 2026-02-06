
import os
import random
import re
from pathlib import Path

BLOG_CONTENT_DIR = Path("/home/tetsuya/project/your-blog/content")
SITE_URL_BASE = "https://blog.your-domain.com"

def _strip_markdown(text: str) -> str:
    # 去除代码块
    text = re.sub(r"```[\s\S]*?```", "", text)
    # 去除行内代码
    text = re.sub(r"`[^`]*`", "", text)
    # 链接和图片：保留可读文字
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", text)
    # 去除 HTML 标签
    text = re.sub(r"<[^>]+>", "", text)
    # 去除标题/引用/列表等前缀
    text = re.sub(r"^\s*#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*>\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
    # 去除强调标记
    text = re.sub(r"(\*{1,3}|_{1,3})", "", text)
    # 压缩空白
    text = re.sub(r"\s+", " ", text).strip()
    return text

def get_on_this_day_post():
    """
    寻找往年今日发布的博文。
    """
    from datetime import datetime
    now = datetime.now()
    month_day = now.strftime("-%m-%d") # 例如 -02-03
    
    if not BLOG_CONTENT_DIR.exists():
        return None

    candidates = []
    # 递归查找所有 .md 文件
    for root, dirs, files in os.walk(BLOG_CONTENT_DIR):
        for file in files:
            if file.endswith(".md"):
                filepath = os.path.join(root, file)
                try:
                    # 快速检查：如果文件名包含日期，直接匹配加速
                    if month_day in file:
                        candidates.append(filepath)
                        continue
                    
                    # 否则读取前 20 行检查 date:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        for _ in range(20):
                            line = f.readline()
                            if not line: break
                            if line.startswith("date:"):
                                # 检查是否包含相同的月日，且年份不是今年
                                if month_day in line and str(now.year) not in line:
                                    candidates.append(filepath)
                                    break
                except:
                    continue
    
    if not candidates:
        return None
        
    # 随机选一个并解析
    target_file = random.choice(candidates)
    return parse_blog_file(target_file)

def _fix_assets_urls(text: str) -> str:
    """将博客源码中的相对资产路径修改为 GitHub Pages 的绝对路径"""
    if not text: return text
    # 更加激进的匹配：
    # 1. 匹配 (../)assets/ 
    # 2. 或是直接在引号/括号后的 assets/
    base_assets_url = "https://your-username.github.io/blog/assets/"
    
    # 匹配所有包含 assets/ 的相对路径片段，统一替换
    # 这个正则会找非 http 开头的，且带有 assets/ 的路径
    fixed = re.sub(r'(?<!http[s]:\/\/)([\.\/]*?)assets\/', base_assets_url, text)
    return fixed

def parse_blog_file(filepath):
    """通用的解析博文文件逻辑"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            raw_content = f.read()
            
        title = "Untitled"
        slug = ""
        
        title_match = re.search(r'^title:\s*(.+)$', raw_content, re.MULTILINE)
        if title_match: title = title_match.group(1).strip()
        
        slug_match = re.search(r'^slug:\s*(.+)$', raw_content, re.MULTILINE)
        if slug_match: 
            slug = slug_match.group(1).strip()
        else:
            slug = Path(filepath).stem
            
        date_match = re.search(r'^date:\s*(.+)$', raw_content, re.MULTILINE)
        post_date = ""
        if date_match: post_date = date_match.group(1).strip()
        
        parts = raw_content.split('---', 2)
        body = parts[2].strip() if len(parts) >= 3 else raw_content
        
        # 修复图片/资产路径
        body = _fix_assets_urls(body)
        
        plain_text = _strip_markdown(body)
        
        return {
            "title": title,
            "date": post_date,
            "url": f"{SITE_URL_BASE}/{slug}.html",
            "content": body,
            "text_length": len(plain_text),
            "source": "User Blog"
        }
    except:
        return None

def get_random_blog_post(min_len: int = 200):
    """
    从用户的 Hexo/Pelican 博客中随机读取一篇文章（至少200字）。
    """
    if not BLOG_CONTENT_DIR.exists():
        return None

    all_files = []
    for root, dirs, files in os.walk(BLOG_CONTENT_DIR):
        for file in files:
            if file.endswith(".md"):
                all_files.append(os.path.join(root, file))
    
    if not all_files:
        return None
        
    for _ in range(10):
        target_file = random.choice(all_files)
        post = parse_blog_file(target_file)
        if post and post['text_length'] >= min_len:
            return post
            
    return None
