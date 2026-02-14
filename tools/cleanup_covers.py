import os
import re

def cleanup_broken_covers(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.md'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Regex to match cover metadata in YAML frontmatter
                # We target pollination links which are often broken/meaningless as per user
                new_content = re.sub(r'^cover: https://image\.pollinations\.ai.*?\n', '', content, flags=re.MULTILINE)
                
                if new_content != content:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"Cleaned cover from {filepath}")

if __name__ == "__main__":
    cleanup_broken_covers('/home/tetsuya/mini-twitter/posts/2026/02/')
