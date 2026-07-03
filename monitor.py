import time
import json
import os
import config
import notifier

SEEN_POSTS_FILE = "seen_posts.json"

def load_seen_posts():
    """
    Loads list of previously notified post IDs to avoid duplicate alerts.
    """
    if os.path.exists(SEEN_POSTS_FILE):
        try:
            with open(SEEN_POSTS_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception as e:
            print(f"[Monitor] Error loading seen posts: {e}")
            return set()
    return set()

def save_seen_posts(seen_ids):
    """
    Saves the list of notified post IDs to a file.
    """
    try:
        with open(SEEN_POSTS_FILE, "w", encoding="utf-8") as f:
            json.dump(list(seen_ids), f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Monitor] Error saving seen posts: {e}")

def check_for_keywords(text):
    """
    Returns True if any keyword from config matches the text (case-insensitive).
    """
    text_lower = text.lower()
    for kw in config.KEYWORDS:
        if kw.lower() in text_lower:
            return True
    return False

def get_mock_posts():
    """
    Simulates posts retrieved from Facebook or a user feed.
    In a production setup, this would fetch data from an API or a local file 
    exported by a lightweight browser extension.
    """
    return [
        {
            "id": "fb_101",
            "title": "Cần tìm bên thiết kế & in 3d vỏ hộp thiết bị điện tử",
            "content": "Chào mọi người, mình đang cần tìm đơn vị thiết kế và in 3D số lượng khoảng 50 cái vỏ hộp nhựa cho mạch điện tử tại Hà Nội. Có ai nhận làm trọn gói không ạ?",
            "url": "https://www.facebook.com/groups/3dprinting/posts/101"
        },
        {
            "id": "fb_102",
            "title": "Học in 3D cơ bản",
            "content": "Mình mới mua máy in 3D FDM cũ, muốn hỏi tài liệu học thiết kế 3D bằng Fusion 360 ở đâu tốt nhất?",
            "url": "https://www.facebook.com/groups/3dprinting/posts/102"
        },
        {
            "id": "fb_103",
            "title": "Cần in 3D tượng figure anime",
            "content": "Cần in 3D resin tượng anime cao 20cm, file có sẵn STL. Ai nhận in và sơn ở HCM báo giá inbox giúp mình nhé.",
            "url": "https://www.facebook.com/groups/3dprinting/posts/103"
        },
        {
            "id": "fb_104",
            "title": "Mua bán máy in nhựa thanh lý",
            "content": "Thanh lý bớt 2 máy in 3D Ender 3 Pro cũ hoạt động tốt giá hạt dẻ.",
            "url": "https://www.facebook.com/groups/3dprinting/posts/104"
        }
    ]

def run_monitor(mock_run=False):
    """
    Main monitor execution loop.
    """
    print("[Monitor] Starting Lead Notifier Engine...")
    print(f"[Monitor] Configured keywords: {config.KEYWORDS}")
    
    seen_ids = load_seen_posts()
    
    while True:
        print("\n[Monitor] Checking for new posts...")
        
        # Retrieve posts (Mocking source)
        posts = get_mock_posts()
        
        new_leads_found = 0
        for post in posts:
            post_id = post["id"]
            
            # Check if we already processed this post
            if post_id in seen_ids:
                continue
                
            # Combine title and content to check for keywords
            search_text = f"{post['title']} {post['content']}"
            
            if check_for_keywords(search_text):
                print(f"[Monitor] Match found: {post['title']}")
                
                # Send alert to configured notification channels
                alert_sent = notifier.send_alert(
                    title=post["title"],
                    description=post["content"],
                    url=post["url"]
                )
                
                if alert_sent or mock_run:
                    seen_ids.add(post_id)
                    new_leads_found += 1
        
        if new_leads_found > 0:
            save_seen_posts(seen_ids)
            
        if mock_run:
            print("[Monitor] Mock run finished. Exiting loop.")
            break
            
        print(f"[Monitor] Sleeping for {config.CHECK_INTERVAL} seconds...")
        time.sleep(config.CHECK_INTERVAL)

if __name__ == "__main__":
    # Run the continuous monitor loop by default
    run_monitor(mock_run=False)
