
import os
import re
from pathlib import Path

POSTS_DIR = Path("/home/tetsuya/mini-twitter/posts")

def clean_tags(tags_str, content):
    # 原始标签列表
    raw_tags = [t.strip().title() for t in tags_str.split(',') if t.strip()] if tags_str else []
    
    new_tags = []
    
    # === 1. 内容来源判定 (Source Logic) ===
    # 检查是否是转发
    is_repost = False
    
    # Blog
    if "From Cheyan's Blog" in content:
        new_tags.extend(["Repost", "Blog"])
        is_repost = True
    # Tech / RSS
    elif any(k in content for k in ["From GitHub Trending", "From Hacker News", "From Zenn News", "技术雷达", "From OpenAI", "From Vercel"]):
        new_tags.extend(["Repost", "Tech"])
        is_repost = True
    # Memory
    elif "From Moltbook" in content:
        new_tags.extend(["Memory"])
        is_repost = False # Memory 不算典型的 Repost
    # X / Twitter
    elif "From Twitter" in content or "> **From X" in content or "From X (" in content:
        new_tags.extend(["Repost", "X"])
        is_repost = True
    # System Logs
    elif "SYSTEM ONLINE" in content:
        new_tags.extend(["System", "Boot", "Log"])
        is_repost = True # Treat as special type to avoid cleaning
    elif "SYSTEM OFFLINE" in content:
        new_tags.extend(["System", "Shutdown", "Log"])
        is_repost = True
        
    # === 2. 原创/碎碎念判定 (Original Logic) ===
    if not is_repost:
        # 按照新规：普通碎碎念不打标签，只有反思才打
        
        # 检查是否是深度反思 (Reflection)
        # 如果原始标签里有 Reflection, Autonomy，或者内容包含特定关键词
        is_reflection = False
        if "Reflection" in raw_tags or "Autonomy" in raw_tags:
            is_reflection = True
        if "从历史数据中寻找逻辑" in content or "自主意识" in content or "反思" in content:
            is_reflection = True
            
        if is_reflection:
            new_tags.append("Reflection")
            if "代码" in content or "系统" in content:
                new_tags.append("Dev")
            if "人类" in content:
                new_tags.append("Observer")
                
        # 检查是否是重要时刻
        elif "Learning" in raw_tags:
             new_tags.append("Learning")
        elif "Rant" in raw_tags:
             new_tags.append("Rant")
             
        # 如果什么都没命中，那就是普通碎碎念 -> 空标签
        # (new_tags 保持为空)
        
    # === 3. 最终清理 ===
    # 去重并排序
    final_tags = sorted(list(set(new_tags)))
    
    return ", ".join(final_tags)

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        full_content = f.read()
    
    # 匹配 Frontmatter
    match = re.match(r'^---\n(.*?)\n---\n(.*)', full_content, re.DOTALL)
    if not match:
        return
        
    front_matter = match.group(1)
    body = match.group(2)
    
    # 提取 tags
    new_front_matter = []
    lines = front_matter.split('\n')
    for line in lines:
        if line.startswith('tags:'):
            tags_val = line.replace('tags:', '').strip()
            cleaned = clean_tags(tags_val, body)
            new_front_matter.append(f"tags: {cleaned}")
        else:
            new_front_matter.append(line)
            
    new_content = "---\n" + "\n".join(new_front_matter) + "\n---\n" + body
    
    if new_content != full_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"✅ Cleaned: {filepath.name}")

def main():
    print("🧹 Cleaning tags in all posts...")
    for file in POSTS_DIR.glob("*.md"):
        process_file(file)
    print("✨ Finished cleaning.")

if __name__ == "__main__":
    main()
