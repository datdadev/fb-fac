"""
Facebook Features Module - Search, Filter, Notify
"""

import time
import json
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Load keywords from JSON file
def load_keywords():
    """Load keywords from JSON file"""
    try:
        with open('keywords.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('keywords', [])
    except FileNotFoundError:
        print("⚠️ keywords.json not found, using default keywords")
        return ["cần in 3D", "cần tìm đơn vị thiết kế và in 3D", "dịch vụ in 3D"]
    except Exception as e:
        print(f"❌ Error loading keywords: {e}")
        return ["cần in 3D"]

def save_posts_to_file(posts, filename="found_posts.json"):
    """Save found posts to JSON file"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(posts, f, indent=4, ensure_ascii=False)
        print(f"✅ Saved {len(posts)} posts to {filename}")
        return True
    except Exception as e:
        print(f"❌ Error saving posts: {e}")
        return False

def search_facebook_posts(driver, keywords, max_scroll=5):
    """
    Search Facebook for posts containing keywords
    
    Args:
        driver: WebDriver instance
        keywords: List of keywords to search
        max_scroll: Number of scrolls to load more results
    
    Returns:
        List of post dictionaries
    """
    print("\n" + "="*60)
    print("🔍 SEARCHING FACEBOOK POSTS")
    print("="*60)
    
    found_posts = []
    seen_urls = set()
    
    for keyword in keywords:
        print(f"\n🔎 Searching for: '{keyword}'")
        
        try:
            # Navigate to Facebook search
            search_url = f"https://www.facebook.com/search/posts/?q={keyword.replace(' ', '%20')}"
            driver.get(search_url)
            time.sleep(5)
            
            # Wait for results to load
            try:
                # Wait for any post element
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'x1yztbdb')]"))
                )
            except TimeoutException:
                print(f"  ⚠️ No results found for '{keyword}' or page took too long")
                continue
            
            # Scroll to load more results
            for scroll_count in range(max_scroll):
                print(f"  Scroll {scroll_count + 1}/{max_scroll}...")
                
                # Find posts on current scroll
                posts = driver.find_elements(By.XPATH, "//div[contains(@class, 'x1yztbdb')]")
                
                for post in posts:
                    try:
                        # Extract post data
                        post_data = extract_post_data(driver, post)
                        
                        if post_data and post_data['url'] not in seen_urls:
                            seen_urls.add(post_data['url'])
                            found_posts.append(post_data)
                            print(f"  ✅ Found post: {post_data['text'][:50]}...")
                    except Exception as e:
                        continue
                
                # Scroll down
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
                
                # Check if we reached the end
                try:
                    load_more = driver.find_element(By.XPATH, "//div[contains(text(), 'See more') or contains(text(), 'Xem thêm')]")
                    if load_more:
                        load_more.click()
                        time.sleep(2)
                except:
                    pass
            
            print(f"  ✅ Found {len([p for p in found_posts if keyword in p.get('text', '')])} posts for '{keyword}'")
            
        except Exception as e:
            print(f"  ❌ Error searching '{keyword}': {e}")
    
    # Save results
    save_posts_to_file(found_posts)
    
    print(f"\n📊 Total posts found: {len(found_posts)}")
    return found_posts

def extract_post_data(driver, post_element):
    """
    Extract data from a Facebook post element
    
    Returns:
        dict: Post data or None
    """
    try:
        # Get post text
        try:
            text_element = post_element.find_element(By.XPATH, ".//div[contains(@class, 'x1lliihq')]")
            post_text = text_element.text
        except:
            post_text = ""
        
        # Get post URL
        try:
            url_element = post_element.find_element(By.XPATH, ".//a[contains(@href, '/posts/')]")
            post_url = url_element.get_attribute('href')
        except:
            post_url = None
        
        # Get author
        try:
            author_element = post_element.find_element(By.XPATH, ".//strong//a")
            author = author_element.text
            author_url = author_element.get_attribute('href')
        except:
            author = "Unknown"
            author_url = None
        
        # Get timestamp
        try:
            time_element = post_element.find_element(By.XPATH, ".//span[contains(@class, 'x1rg5ohu')]")
            timestamp = time_element.text
        except:
            timestamp = "Unknown"
        
        return {
            'text': post_text,
            'url': post_url,
            'author': author,
            'author_url': author_url,
            'timestamp': timestamp,
            'keyword_matched': []
        }
        
    except Exception as e:
        return None

def filter_posts_by_keywords(posts, keywords):
    """
    Filter posts that contain keywords in their text
    
    Returns:
        List of filtered posts with matched keywords
    """
    print("\n🔍 FILTERING POSTS BY KEYWORDS")
    print("="*60)
    
    filtered = []
    
    for post in posts:
        post_text = post.get('text', '').lower()
        matched_keywords = []
        
        for keyword in keywords:
            if keyword.lower() in post_text:
                matched_keywords.append(keyword)
        
        if matched_keywords:
            post['keyword_matched'] = matched_keywords
            filtered.append(post)
            print(f"✅ Matched: {post['text'][:50]}... (Keywords: {', '.join(matched_keywords)})")
    
    print(f"\n📊 Filtered posts: {len(filtered)}/{len(posts)}")
    save_posts_to_file(filtered, "filtered_posts.json")
    return filtered

def comment_on_post(driver, post_url, comment_text):
    """
    Comment on a Facebook post
    
    Returns:
        bool: Success or failure
    """
    try:
        print(f"\n💬 Commenting on: {post_url}")
        driver.get(post_url)
        time.sleep(3)
        
        # Scroll to comment section
        driver.execute_script("window.scrollTo(0, 600);")
        time.sleep(1)
        
        # Find comment input
        comment_selectors = [
            "//div[@aria-label='Viết bình luận...']",
            "//div[@aria-label='Write a comment...']",
            "//div[@role='textbox']",
            "//textarea[@placeholder='Write a comment...']",
            "//textarea[contains(@placeholder, 'comment')]"
        ]
        
        comment_input = None
        for selector in comment_selectors:
            try:
                comment_input = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                if comment_input:
                    break
            except:
                continue
        
        if comment_input:
            comment_input.click()
            time.sleep(0.5)
            comment_input.send_keys(comment_text)
            time.sleep(0.5)
            comment_input.send_keys(Keys.RETURN)
            print(f"✅ Commented: {comment_text[:30]}...")
            return True
        else:
            print("❌ Could not find comment box")
            return False
            
    except Exception as e:
        print(f"❌ Error commenting: {e}")
        return False

def send_notification_telegram(posts, bot_token, chat_id):
    """
    Send notifications to Telegram
    
    Returns:
        bool: Success or failure
    """
    try:
        import requests
        
        for post in posts:
            message = f"📢 **New Post Found!**\n\n"
            message += f"**Author:** {post.get('author', 'Unknown')}\n"
            message += f"**Keywords:** {', '.join(post.get('keyword_matched', []))}\n"
            message += f"**Post:** {post.get('text', '')[:200]}...\n"
            message += f"**URL:** {post.get('url', '')}\n"
            
            # Send to Telegram
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                print(f"✅ Telegram notification sent for post")
            else:
                print(f"❌ Telegram error: {response.text}")
                
        return True
        
    except ImportError:
        print("⚠️ requests module not found. Install: pip install requests")
        return False
    except Exception as e:
        print(f"❌ Telegram error: {e}")
        return False

def send_notification_discord(posts, webhook_url):
    """
    Send notifications to Discord
    
    Returns:
        bool: Success or failure
    """
    try:
        import requests
        
        for post in posts:
            embed = {
                "title": f"📢 New Post Found!",
                "fields": [
                    {"name": "Author", "value": post.get('author', 'Unknown'), "inline": True},
                    {"name": "Keywords", "value": ', '.join(post.get('keyword_matched', [])), "inline": True},
                    {"name": "Post", "value": post.get('text', '')[:500]},
                    {"name": "URL", "value": post.get('url', '')}
                ],
                "color": 0x00ff00
            }
            
            payload = {
                "embeds": [embed]
            }
            
            response = requests.post(webhook_url, json=payload)
            
            if response.status_code == 200:
                print(f"✅ Discord notification sent for post")
            else:
                print(f"❌ Discord error: {response.text}")
                
        return True
        
    except ImportError:
        print("⚠️ requests module not found. Install: pip install requests")
        return False
    except Exception as e:
        print(f"❌ Discord error: {e}")
        return False

def search_and_filter_main(driver, keywords=None, max_scroll=5):
    """
    Main function: Search, filter, and notify
    
    Args:
        driver: WebDriver instance
        keywords: List of keywords (uses JSON file if None)
        max_scroll: Number of scrolls
    
    Returns:
        List of filtered posts
    """
    if not keywords:
        keywords = load_keywords()
    
    # Search for posts
    all_posts = search_facebook_posts(driver, keywords, max_scroll)
    
    if not all_posts:
        print("❌ No posts found")
        return []
    
    # Filter posts by keywords
    filtered_posts = filter_posts_by_keywords(all_posts, keywords)
    
    if not filtered_posts:
        print("❌ No posts matched keywords")
        return []
    
    return filtered_posts

def interactive_commenting(driver, posts):
    """
    Interactive CLI for reviewing and commenting on posts
    """
    if not posts:
        print("❌ No posts to review")
        return
    
    print("\n" + "="*60)
    print("📝 REVIEW POSTS AND COMMENT")
    print("="*60)
    
    for i, post in enumerate(posts, 1):
        print(f"\n{'='*60}")
        print(f"📌 Post {i}/{len(posts)}")
        print(f"{'='*60}")
        print(f"👤 Author: {post.get('author', 'Unknown')}")
        print(f"📝 Keywords: {', '.join(post.get('keyword_matched', []))}")
        print(f"📄 Content: {post.get('text', '')[:200]}...")
        print(f"🔗 URL: {post.get('url', '')}")
        
        action = input("\nOptions: (c)omment | (v)iew full post | (s)kip | (q)uit: ").strip().lower()
        
        if action == 'q':
            break
        elif action == 'v':
            # Open post in browser
            driver.get(post.get('url', ''))
            time.sleep(3)
            action = input("\n(c)omment | (s)kip: ").strip().lower()
            if action == 'c':
                comment_text = input("💬 Enter comment: ")
                if comment_text:
                    comment_on_post(driver, post.get('url', ''), comment_text)
        elif action == 'c':
            comment_text = input("💬 Enter comment: ")
            if comment_text:
                comment_on_post(driver, post.get('url', ''), comment_text)
        elif action == 's':
            print("⏭️ Skipped")
            continue
        else:
            print("⏭️ Invalid option, skipping")
    
    print("\n✅ Done reviewing posts")