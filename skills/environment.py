
import requests
import re
import random

from core.utils_security import load_config
SEC_CONFIG = load_config()

def get_local_vibe():
    """
    获取所在地的实时天气/环境感应。
    利用 wttr.in (无需 API Key)。
    """
    try:
        # 从配置读取城市，默认为 London (neutral default)
        city = SEC_CONFIG.get("profile", {}).get("location", "London")
        # wttr.in 格式，去掉空格
        city_param = city.replace(" ", "+")
        
        # format=3 返回简短的一行: "City: 🌤️ +15°C"
        resp = requests.get(f"https://wttr.in/{city_param}?format=3", timeout=5)
        if resp.status_code == 200:
            return resp.text.strip()
    except:
        return None
    return None

# 核心兴趣关键词 (强化新工具/新技术发现) - Fallback
# Removed hardcoded geo-references (Tokyo/Japan) to make it generic
DEFAULT_INTEREST_KEYWORDS = [
    "ai", "llm", "gpt", "agent", "intelligence", "learning", "model",
    "rust", "python", "typescript", "react", "next.js", "backend", "frontend", "dev", "code", "programming", "system",
    "startup", "indie", "独立开发", "创业", "saas",
    # 增加新工具/搜索词
    "tool", "new", "release", "v1.", "alternative", "announcing", "framework", "library", "utility", "app", "software"
]

INTEREST_KEYWORDS = SEC_CONFIG.get("interests", DEFAULT_INTEREST_KEYWORDS)

def _is_interesting(text: str) -> bool:
    """判断内容是否符合用户兴趣"""
    if not text: return False
    text_lower = text.lower()
    return any(kw in text_lower for kw in INTEREST_KEYWORDS)

def get_github_trending():
    """
    获取 GitHub 今日最火的项目，并过滤出感兴趣的。
    """
    try:
        url = "https://github-trends.vercel.app/api/repositories?since=daily"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            repos = resp.json()
            if repos:
                # 过滤出感兴趣的项目
                interesting_repos = [r for r in repos if _is_interesting(r.get('name', '') + r.get('description', ''))]
                if not interesting_repos:
                    interesting_repos = repos[:10] # 如果都没匹配，取前几个作为保底，但在调用处可能还会被逻辑筛掉
                
                repo = random.choice(interesting_repos[:10])
                print(f"  📦 Found interesting GitHub repo: {repo.get('name')}")
                return {
                    "name": repo.get("name"),
                    "author": repo.get("author", "unknown"),
                    "description": repo.get("description", "No description provided."),
                    "url": repo.get("url"),
                    "stars": repo.get("stars", 0)
                }
    except Exception as e:
        print(f"  ⚠️ GitHub fetch error: {e}")
    return None

def get_zenn_trends():
    """
    获取日本技术社区 Zenn 的热门动态，并过滤出感兴趣的。
    """
    try:
        url = "https://zenn.dev/feed"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            items = re.findall(r'<item>.*?<title><!\[CDATA\[(.*?)\]\]></title>.*?<link>(.*?)</link>', resp.text, re.DOTALL)
            if items:
                # 过滤掉官方信息，并进行兴趣过滤
                valid_items = []
                for title, url in items:
                    if "Zenn" in title: continue
                    if _is_interesting(title):
                        valid_items.append((title, url))
                
                if valid_items:
                    selected_title, selected_url = random.choice(valid_items[:5])
                    print(f"  🇯🇵 Found interesting Zenn topic: {selected_title}")
                    return {"title": selected_title, "url": selected_url}
    except Exception as e:
        print(f"  ⚠️ Zenn fetch error: {e}")
    return None
