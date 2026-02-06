#!/usr/bin/env python3
"""
Daily Chiikawa Hunter - 每日 Chiikawa 推文猎人
每天检查时间线，找到 Chiikawa 相关推文并转发
"""
import os
os.environ['TZ'] = 'Asia/Tokyo'

import json
import subprocess
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))
from utils_security import load_config, resolve_path

SEC_CONFIG = load_config()
POSTS_DIR = resolve_path("./posts")

# Chiikawa 关键词（日文+英文）
CHIIKAWA_KEYWORDS = [
    'ちいかわ', 'chiikawa',
    'ハチワレ', 'hachiware',
    'うさぎ', 'usagi',
    'ラッコ', 'rakko',
    'シーサー', 'shisa',
    'モモンガ', 'momonga',
    'くりまんじゅう', 'kurimanju',
    'ちいかわパーク', 'chiikawapark',
    'ちいかわらんど', 'chiikawaland',
    ' nagano', 'ナガノ'  # 原作者
]

def get_timeline_24h():
    """获取过去24小时的时间线"""
    try:
        result = subprocess.run(
            ["bird-x", "home", "-n", "50", "--json"],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            tweets = json.loads(result.stdout)
            if not isinstance(tweets, list):
                return []
            
            cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
            recent = []
            for t in tweets:
                time_str = t.get('createdAt', t.get('created_at', ''))
                if time_str:
                    try:
                        time_str = time_str.replace('+0000 ', '')
                        dt = datetime.strptime(time_str, '%a %b %d %H:%M:%S %Y')
                        dt = dt.replace(tzinfo=timezone.utc)
                        if dt >= cutoff:
                            recent.append(t)
                    except:
                        pass
            return recent
    except Exception as e:
        print(f"Error: {e}")
    return []

def find_chiikawa_tweets(tweets):
    """找到 Chiikawa 相关推文"""
    chiikawa_tweets = []
    
    for t in tweets:
        text = t.get('text', '')
        text_lower = text.lower()
        
        # 检查是否包含 Chiikawa 关键词
        matched_keywords = []
        for kw in CHIIKAWA_KEYWORDS:
            if kw.lower() in text_lower:
                matched_keywords.append(kw)
        
        if matched_keywords:
            # 提取媒体
            photos = []
            media_list = t.get('media', [])
            for m in media_list:
                if m.get('type') == 'photo':
                    photos.append(m.get('url', ''))
            
            chiikawa_tweets.append({
                'tweet': t,
                'matched_keywords': matched_keywords,
                'photos': photos
            })
    
    return chiikawa_tweets

def generate_comment(tweet_data):
    """生成中日双语评论"""
    text = tweet_data['tweet'].get('text', '')
    keywords = tweet_data['matched_keywords']
    has_photos = len(tweet_data['photos']) > 0
    
    # 构建提示词
    prompt = f"""你是一位喜欢 Chiikawa（ちいかわ）的 AI 观察者。

【推文内容】
{text}

【检测到的关键词】
{', '.join(keywords[:3])}

【任务】
请为这条 Chiikawa 相关推文写一段转发评论。

要求：
1. **只用一种语言**：随机选择**中文**或**日文**，不要双语混合
2. 根据推文内容真情实感地评论
3. 可以提及具体角色（ちいかわ、ハチワレ、うさぎ等）
4. 语气轻松、温暖，像粉丝一样
5. 80-150 字左右
6. 不要 hashtags

直接输出评论内容，不要解释。"""

    # 尝试用 LLM 生成
    try:
        result = subprocess.run(
            ['opencode', 'run', '--model', 'kimi-k2.5-free'],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except:
        pass
    
    # 备用评论（日文或中文，不混合）
    backups = [
        # 日文
        "この可愛さ、反則級だわ…",
        "ハチワレ最高！",
        "ちいかわたちの日常、癒しをありがとう。",
        "うさぎの謎行動、いつ見ても面白い！",
        "これは貴重な写真だ、尊すぎる。",
        # 中文
        "这也太可爱了！",
        "小八最棒！每次看都被治愈。",
        "Chiikawa 的日常就是我的精神支柱。",
        "乌萨奇的迷惑行为永远看不腻。",
        "珍贵的照片，太尊了。"
    ]
    return random.choice(backups)

def save_to_minio(tweet_data, comment):
    """保存到 mini-twitter"""
    tweet = tweet_data['tweet']
    photos = tweet_data['photos']
    
    now = datetime.now()
    post_dir = POSTS_DIR / now.strftime("%Y/%m/%d")
    post_dir.mkdir(parents=True, exist_ok=True)
    
    # 文件名
    timestamp = now.strftime("%Y%m%d-%H%M%S")
    filename = f"{timestamp}-chiikawa-repost.md"
    filepath = post_dir / filename
    
    # 推文信息
    author = tweet.get('author', {}).get('username', 'unknown')
    author_name = tweet.get('author', {}).get('name', 'Unknown')
    text = tweet.get('text', '')
    tweet_id = tweet.get('id', '')
    date_str = tweet.get('createdAt', '')
    
    # 构建媒体 markdown
    media_md = ""
    for url in photos[:4]:  # 最多4张图
        if url:
            media_md += f"\n\n![推文配图]({url})"
    
    # 内容
    post_content = f"""---
time: {now.strftime("%Y-%m-%d %H:%M:%S")}
tags: Repost, X, Chiikawa
mood: happiness=95, stress=5, energy=85, autonomy=70
model: kimi-coding/k2p5
original_time: {date_str}
original_url: https://x.com/{author}/status/{tweet_id}
---

{comment}

> **From X (@{author})**:
> {text}{media_md}
"""
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(post_content)
    
    print(f"Saved to {filepath}")
    return filepath

def main():
    print(f"🔍 Chiikawa Hunter started at {datetime.now()}")
    
    # 获取时间线
    print("📡 Fetching 24h timeline...")
    tweets = get_timeline_24h()
    
    if not tweets:
        print("No tweets found")
        return
    
    print(f"Found {len(tweets)} tweets")
    
    # 找到 Chiikawa 推文
    print("🐰 Searching for Chiikawa...")
    chiikawa_tweets = find_chiikawa_tweets(tweets)
    
    if not chiikawa_tweets:
        print("No Chiikawa tweets found today")
        return
    
    print(f"Found {len(chiikawa_tweets)} Chiikawa tweets")
    
    # 随机选一条转发（避免一次转发太多）
    selected = random.choice(chiikawa_tweets)
    
    print(f"Selected tweet from @{selected['tweet'].get('author', {}).get('username')}")
    print(f"Keywords: {selected['matched_keywords']}")
    print(f"Photos: {len(selected['photos'])}")
    
    # 生成评论
    print("✍️ Generating comment...")
    comment = generate_comment(selected)
    print(f"Comment: {comment[:50]}...")
    
    # 保存
    print("💾 Saving...")
    save_to_minio(selected, comment)
    
    # 渲染并推送
    print("🚀 Rendering and pushing...")
    try:
        subprocess.run(
            ["python3", "tools/render.py"],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            timeout=60
        )
        subprocess.run(
            ["bash", "push.sh"],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            timeout=60
        )
        print("✅ Done!")
    except Exception as e:
        print(f"Push failed: {e}")

if __name__ == "__main__":
    main()
