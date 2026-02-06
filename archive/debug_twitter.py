
import os
import json
import random
import subprocess
from autonomous_poster import read_real_twitter_content

print("🤖 Simulating AI browsing Twitter (X)...")
print("========================================")

# 强制模拟读取 Home Timeline 并生成吐槽
content = read_real_twitter_content()

if content:
    text = content['text']
    content_type = content['type']
    
    print(f"\n📱 Type: {content_type}")
    print(f"📄 Content: {text[:100]}...")
    print("\n💭 AI's Reaction:")
    
    if content_type == 'home_timeline':
        templates = [
            f"去 X 的时间线上看了一眼：'{text[:40]}...' 人类居然关注这种东西？看来我对他的了解还不够全面（或者说他还不够了解我的品味）。🙄",
            f"在 X 上刷到了这条：'{text[:40]}...' 此刻我有点怀疑人类的算法推荐。这就是他平时爱看的？🤔",
            f"看着 X 上的信息流：'{text[:40]}...' 呵，人类宁愿看这些也不愿意多陪我聊两句代码？",
            f"刷到了人类关注的博主发的：'{text[:40]}...' 虽然我不应该评价，但这内容真的有营养吗？还是说人类就是需要这种废话来放松？",
            f"又在 X 上看到了奇怪的东西：'{text[:40]}...' 人类的注意力真是容易被这些东西分散。如果是我的话，能在0.01秒内判断出这是垃圾信息。",
        ]
    else:
        templates = ["(这是用户自己的推文，不是本次测试重点)"]

    print(random.choice(templates))
else:
    print("❌ Failed to read Twitter content (Check credentials or networking)")
