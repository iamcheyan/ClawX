
import feedparser
import sys
import threading
import time

feeds = {
    # 中文
    "少数派": "https://sspai.com/feed",
    "爱范儿": "https://www.ifanr.com/feed",
    "腾讯科技": "https://rsshub.app/qqtech", # 可能会失败，RSSHub代理
    "V2EX": "https://www.v2ex.com/feed/tab/tech.xml",
    "钛媒体": "https://www.tmtpost.com/feed",
    "机核 GCORES": "https://www.gcores.com/rss", #修正为官方
    
    # 日文
    "ITmedia News": "https://rss.itmedia.co.jp/rss/2.0/news_bursts.xml",
    "PC Watch": "https://pc.watch.impress.co.jp/data/rss/1.0/pcw/feed.rdf", # Impress Watch Example
    "GIZMODO Japan": "https://www.gizmodo.jp/index.xml",
    
    # 英文
    "TechCrunch": "https://techcrunch.com/feed/",
    "The Verge": "https://www.theverge.com/rss/tech/index.xml",
    "Ars Technica": "https://feeds.arstechnica.com/arstechnica/technology-lab",
    "Slashdot": "http://rss.slashdot.org/Slashdot/slashdotMain",
    "Hacker News": "https://news.ycombinator.com/rss",
    "Wired": "https://www.wired.com/feed/rss",
}

def check_feed(name, url):
    try:
        # Some servers block python-requests/feedparser user agents
        feed = feedparser.parse(url)
        if feed.entries and len(feed.entries) > 0:
            print(f"✅ [VALID] {name}: {url} ({len(feed.entries)} entries)")
            return True, name, url
        else:
             # Try with raw requests first if feedparser fails (sometimes headers needed)
             import requests
             headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
             try:
                 r = requests.get(url, headers=headers, timeout=5)
                 if r.status_code == 200:
                     feed = feedparser.parse(r.content)
                     if feed.entries:
                        print(f"✅ [VALID-REQ] {name}: {url} ({len(feed.entries)} entries)")
                        return True, name, url
             except:
                 pass
             
             print(f"❌ [EMPTY/FAIL] {name}: {url}")
             if hasattr(feed, 'status'):
                 print(f"   Status: {feed.status}")
             return False, name, url
    except Exception as e:
        print(f"❌ [ERROR] {name}: {e}")
        return False, name, url

def main():
    print("🔍 Validating RSS Feeds...")
    
    threads = []
    
    for name, url in feeds.items():
        t = threading.Thread(target=check_feed, args=(name, url))
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()

if __name__ == "__main__":
    main()
