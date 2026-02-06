
from autonomous_poster import generate_tweet_content, create_post, render_and_deploy, load_mood
import os

def force_post_integrated():
    print("🔄 Forcing a post using integrated logic...")
    mood = load_mood()
    content = generate_tweet_content(mood)
    
    if content:
        print(f"✅ Generated content: {content[:100]}...")
        # Use a distinctive suffix to identify this run
        create_post(content, mood, suffix="img-fix-final-v1")
        render_and_deploy()
        os.system("./push")
    else:
        print("❌ Failed to generate content.")

if __name__ == "__main__":
    force_post_integrated()
