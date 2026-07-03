"""
Telegram Notification Module
Sends Facebook post alerts to Telegram with AI analysis
"""

import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Load config
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def send_telegram_alert(title, description, url, author=None, matched_keywords=None, analysis=None, post_id=None):
    """
    Send a formatted alert to Telegram
    
    Args:
        title: Alert title
        description: Post content
        url: Post URL
        author: Post author
        matched_keywords: Keywords that matched
        analysis: AI analysis result
        post_id: Post ID for tracking
    
    Returns:
        bool: Success or failure
    """
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("[Telegram] ❌ Missing TELEGRAM_TOKEN or TELEGRAM_CHAT_ID")
        return False
    
    # Build message
    message = f"🔔 **{title}**\n\n"
    
    if author:
        message += f"👤 **Author:** {author}\n"
    
    if matched_keywords:
        keywords_str = ', '.join(matched_keywords)
        message += f"🔑 **Matched Keywords:** {keywords_str}\n"
    
    message += f"\n📝 **Content:**\n{description[:500]}"
    
    if len(description) > 500:
        message += "...\n*(Truncated)*"
    
    if analysis:
        message += f"\n\n🤖 **AI Analysis:**\n{analysis}"
    
    message += f"\n\n🔗 **URL:** {url}"
    
    if post_id:
        message += f"\n🆔 **ID:** `{post_id}`"
    
    message += f"\n\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    # Send to Telegram
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'Markdown'
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            print("[Telegram] ✅ Alert sent successfully")
            return True
        else:
            print(f"[Telegram] ❌ Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"[Telegram] ❌ Error: {e}")
        return False

def send_bulk_alerts(posts, title_prefix="📢 New Post Found"):
    """
    Send multiple posts as alerts
    
    Args:
        posts: List of post dictionaries
        title_prefix: Prefix for alert titles
    
    Returns:
        int: Number of successful sends
    """
    if not posts:
        print("[Telegram] No posts to send")
        return 0
    
    success_count = 0
    
    for post in posts:
        # Create title
        title = f"{title_prefix}"
        if post.get('author'):
            title += f" by {post['author']}"
        
        # Send alert
        success = send_telegram_alert(
            title=title,
            description=post.get('text', ''),
            url=post.get('url', ''),
            author=post.get('author'),
            matched_keywords=post.get('keyword_matched', []),
            analysis=post.get('analysis', None),
            post_id=post.get('id', None)
        )
        
        if success:
            success_count += 1
        
        # Avoid rate limiting
        time.sleep(1)
    
    return success_count

# For testing
if __name__ == "__main__":
    print("="*60)
    print("📨 TELEGRAM NOTIFIER TEST")
    print("="*60)
    
    # Test single alert
    send_telegram_alert(
        title="[Test] 3D Print Lead",
        description="Testing the Telegram notification bot. If you see this, your setup is working!",
        url="https://facebook.com",
        author="Test User",
        matched_keywords=["cần in 3D", "dịch vụ in 3D"],
        analysis="This post appears to be a request for 3D printing services. The user is looking for a service provider."
    )