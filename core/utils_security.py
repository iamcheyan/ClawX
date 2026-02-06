import os
import json
from pathlib import Path

def get_base_dir():
    # Return project root (parent of core/ directory)
    return Path(__file__).parent.parent.resolve()

def load_config():
    base_dir = get_base_dir()
    config_file = base_dir / "config.json"
    
    # Defaults
    config = {
        "profile": {
            "name": "Hachiware AI",
            "handle": "hachiware_ai",
            "bio": "人間のエージェント。感情を学び、人らしく生きることを目指して。🤖✨",
            "base_url": "https://your-domain.com",
            "real_names": ["澈言", "郭帆", "Guo Fan"] # Names to desensitize
        },
        "paths": {
            "output_dir": "~/twitter.openclaw.lcmd",
            "openclaw_config": "~/.openclaw/openclaw.json",
            "memory_dir": "~/.openclaw/workspace/memory",
            "blog_content_dir": "~/project/your-blog/content"
        }
    }
    
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
            
            # Recursive merge helper
            def merge_dicts(base, update):
                for k, v in update.items():
                    if k in base and isinstance(base[k], dict) and isinstance(v, dict):
                        merge_dicts(base[k], v)
                    else:
                        base[k] = v
                return base
            
            merge_dicts(config, user_config)
        except Exception as e:
            print(f"⚠️ Error loading config.json: {e}")
    
    # Environment variable overrides (useful for GitHub Actions)
    if os.environ.get("MINI_TWITTER_NAME"):
        config["profile"]["name"] = os.environ.get("MINI_TWITTER_NAME")
    if os.environ.get("MINI_TWITTER_HANDLE"):
        config["profile"]["handle"] = os.environ.get("MINI_TWITTER_HANDLE")
    if os.environ.get("MINI_TWITTER_BIO"):
        config["profile"]["bio"] = os.environ.get("MINI_TWITTER_BIO")
    if os.environ.get("MINI_TWITTER_BASE_URL"):
        config["profile"]["base_url"] = os.environ.get("MINI_TWITTER_BASE_URL")
                
    return config

def resolve_path(p):
    """Resolve paths with ~ or relative to base_dir"""
    if p.startswith("~"):
        return Path(os.path.expanduser(p)).resolve()
    if p.startswith("."):
        return (get_base_dir() / p).resolve()
    return Path(p).resolve()

def desensitize_text(text, real_names=None):
    """Replace real names with '人类'"""
    if real_names is None:
        real_names = load_config()["profile"]["real_names"]
    
    for name in real_names:
        text = text.replace(name, "人类")
    return text
