
import os
import sys
import random
from datetime import datetime
from pathlib import Path
# Add current dir to path
sys.path.append("/home/tetsuya/mini-twitter")

from autonomous_poster import load_mood, generate_comment_with_llm, create_post, render_and_deploy
from skills.rss_reader import get_random_rss_item


def main():
    print("🚀 Forcing RSS Post Generation...")
    
    # 1. Load Mood
    mood = load_mood()
    print(f"  Mood: {mood}")
    
    # 2. Get RSS Item
    print("  📡 Fetching RSS item...")
    rss_item = get_random_rss_item()
    if not rss_item:
        print("❌ Failed to get RSS item")
        return

    print(f"  ✅ Got item: {rss_item['title']}")
    
    # 3. Generate Comment
    print("  🧠 Generating comment...")
    raw_text = f"【技术雷达：订阅更新】\n来源：{rss_item['source']}\n标题：{rss_item['title']}\n摘要：{rss_item['summary'][:200]}\n任务：请作为技术观察者，分析这条更新的价值。如果是 AI 相关的，谈谈它的潜在影响；如果是工程相关的，谈谈它解决的问题。语气要专业、敏锐。"
    
    # Unpack the tuple return: (comment, model_name)
    llm_comment, model_name = generate_comment_with_llm(raw_text, "technology_startup")
    
    if not llm_comment:
        print("❌ All models failed to generate comment. Aborting to avoid fake content.")
        return
        
    quote = f"\n\n> **From {rss_item['source']}**:\n> [{rss_item['title']}]({rss_item['link']})"
    content = llm_comment + quote
    
    # 4. Create Post (MANUAL PATH HANDLING)
    timestamp = datetime.now()
    filename = timestamp.strftime("%Y-%m-%d-%H%M%S") + "-rss.md"
    
    # Manually construct path to ensure no logic errors
    year = timestamp.strftime("%Y")
    # Corrected month format from %02d to %m
    month = timestamp.strftime("%m")
    day = timestamp.strftime("%d")
    
    # Structure: posts/YYYY/MM/DD/filename
    posts_dir = Path("/home/tetsuya/mini-twitter/posts") / year / month / day
    try:
        os.makedirs(posts_dir, exist_ok=True)
    except Exception as e:
        print(f"❌ Error creating dir: {e}")
        return
    
    filepath = posts_dir / filename
    
    print(f"  📝 Writing directly to: {filepath}")
    
    md_content = f"""---
time: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}
tags: Repost, Tech
mood: happiness=80, stress=20, energy=80, autonomy=85
model: {model_name}
---

{content}
"""
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md_content)
    except Exception as e:
        print(f"❌ Write failed: {e}")
        return
    
    if os.path.exists(filepath):
        print(f"  ✅ File verified on disk: {filepath}")
        print(f"  📄 Content size: {os.path.getsize(filepath)} bytes")
        
        # 5. Push
        render_and_deploy()
    else:
        print("❌ File NOT found after write!")

if __name__ == "__main__":
    main()
