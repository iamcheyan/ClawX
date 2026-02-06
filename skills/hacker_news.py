# 核心兴趣关键词
INTEREST_KEYWORDS = [
    "ai", "llm", "gpt", "intelligence", "model", "neural",
    "rust", "python", "typescript", "react", "programming", "software", "performance", "database",
    "startup", "founder", "product", "growth", "saas",
    "japan", "tokyo", "tokio"
]

def fetch_top_stories(limit=30):
    """
    获取 Hacker News 的热门文章，并筛选出感兴趣的。
    """
    try:
        resp = requests.get('https://hacker-news.firebaseio.com/v0/topstories.json', timeout=10)
        if resp.status_code != 200: return None
        story_ids = resp.json()
        
        # 尝试寻找感兴趣的文章
        for target_id in story_ids[:limit]:
            story_url = f'https://hacker-news.firebaseio.com/v0/item/{target_id}.json'
            story_resp = requests.get(story_url, timeout=10)
            if story_resp.status_code != 200: continue
            story = story_resp.json()
            
            title = story.get('title', '').lower()
            if any(kw in title for kw in INTEREST_KEYWORDS):
                print(f"  🔥 Found interesting HN story: {story.get('title')}")
                return {
                    'source': 'Hacker News',
                    'title': story.get('title'),
                    'url': story.get('url', f"https://news.ycombinator.com/item?id={target_id}"),
                    'comments_url': f"https://news.ycombinator.com/item?id={target_id}",
                    'score': story.get('score', 0),
                    'author': story.get('by', 'unknown'),
                    'type': 'tech_news'
                }
        
        # 如果前 limit 个都没有匹配，随机返回前 5 个之一作为兜底
        target_id = random.choice(story_ids[:5])
        story_resp = requests.get(f'https://hacker-news.firebaseio.com/v0/item/{target_id}.json')
        story = story_resp.json()
        return {
            'title': story.get('title'),
            'url': story.get('url', f"https://news.ycombinator.com/item?id={target_id}"),
            # ...
        }
        
    except Exception as e:
        print(f"Error fetching Hacker News: {e}")
        return None
