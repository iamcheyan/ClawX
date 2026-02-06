
import os
import re

def clean():
    posts_dir = "posts/"
    base_url = "https://iamcheyan.github.io/blog/assets/"
    
    for filename in os.listdir(posts_dir):
        if not filename.endswith(".md"):
            continue
            
        filepath = os.path.join(posts_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 核心逻辑：激进修复
        # 只要在这个模式里：![alt](...assets/...) 
        # 我们就假定它是博客图片，并且强制重写为标准 URL
        
        def rewrite_url(match):
            alt = match.group(1)
            # group(2) 是 assets/ 之后的部分 (path/to/img.jpg)
            suffix = match.group(2)
            # 修正：有些时候 suffix 可能已经被多次编码或包含杂质，但这里假设正则贪婪匹配到了最后的 assets/
            return f'![{alt}]({base_url}{suffix})'

        # 正则解释：
        # !\[(.*?)\]  -> 匹配 ![alt]
        # \(          -> 匹配 (
        # .*?         -> 匹配中间任意垃圾字符 (非贪婪)
        # assets\/    -> 匹配最后的 assets/
        # (.*?)       -> 匹配剩下的路径 (group 2)
        # \)          -> 匹配 )
        # 注意：为了防止一行内有多个图片出问题（虽然 markdown 图片通常一行一个），这种正则最好小心。
        # 但 re.sub 默认是非重叠的。
        
        # 我们先处理一种最常见的情况，确保 assets/ 是 URL 的一部分
        content = re.sub(r'!\[(.*?)\]\(.*?assets\/(.*?)\)', rewrite_url, content)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
            
    print("✅ All posts cleaned and localized to GitHub Assets.")

if __name__ == "__main__":
    clean()
