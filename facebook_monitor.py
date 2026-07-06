"""
Facebook Monitor - Search, Analyze, and Notify
Updated with detailed debug output
"""

import time
import json
import re
import hashlib
import os
import random
import datetime
import config
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from telegram_notifier import send_telegram_alert, send_bulk_alerts
from ai_analyzer import AIAnalyzer

class FacebookMonitor:
    """Facebook Post Monitor with AI Analysis"""
    
    def __init__(self, driver, keywords=None, campaign="3d_printing"):
        """
        Initialize Facebook Monitor
        
        Args:
            driver: Selenium WebDriver instance
            keywords: List of keywords to search
            campaign: Selected marketing campaign
        """
        self.driver = driver
        self.keywords = keywords or []
        self.campaign = campaign
        self.analyzer = AIAnalyzer()
        self.found_posts = []
        self.processed_posts = []
        self.analyzed_posts = []
        self.seen_hashes = set()  # For duplicate detection
        self.processed_urls = set()  # For tracking processed posts
        
    def load_keywords(self, filepath="keywords.json"):
        """Load keywords from JSON file"""
        try:
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    if self.campaign in data:
                        self.keywords = data.get(self.campaign, [])
                    else:
                        self.keywords = data.get('keywords', [])
                else:
                    self.keywords = []
                print(f"✅ Loaded {len(self.keywords)} keywords for campaign '{self.campaign}' from {filepath}")
                print("\n📋 Keywords:")
                for i, kw in enumerate(self.keywords, 1):
                    print(f"  {i}. {kw}")
                return self.keywords
        except Exception as e:
            print(f"❌ Error loading keywords: {e}")
            return []
    
    def _get_post_hash(self, post_data):
        """Generate hash for post to detect duplicates"""
        content = post_data.get('text', '')[:200]  # Use first 200 chars
        author = post_data.get('author', '')
        hash_str = f"{author}:{content}"
        return hashlib.md5(hash_str.encode('utf-8')).hexdigest()
    
    def _is_duplicate(self, post_data):
        """Check if post is duplicate"""
        post_hash = self._get_post_hash(post_data)
        if post_hash in self.seen_hashes:
            return True
        self.seen_hashes.add(post_hash)
        return False
    
    def _debug_page(self):
        """Debug current page to find correct selectors"""
        print("\n🔍 DEBUG: Finding page elements...")
        print("="*60)
        
        # Find all divs with text
        all_divs = self.driver.find_elements(By.XPATH, "//div")
        print(f"📊 Total divs: {len(all_divs)}")
        
        # Find posts-like elements
        possible_selectors = [
            "//div[@role='article']",
            "//div[contains(@class, 'x1yztbdb')]",
            "//div[@data-ad-comet-preview]",
            "//div[contains(@class, 'x1n2onr6')]",
            "//div[contains(@class, 'x1jx94hy')]"
        ]
        
        print("\n📌 Testing selectors:")
        for selector in possible_selectors:
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                print(f"  ✅ '{selector}': {len(elements)} elements found")
                if elements:
                    # Get first element's text snippet
                    try:
                        text = elements[0].text[:100]
                        print(f"    📝 Sample: {text}...")
                    except:
                        pass
            except Exception as e:
                print(f"  ❌ '{selector}': Error - {e}")
        
        print("="*60)
    
    def _print_post_debug(self, post_data, index, total):
        """
        Print detailed debug info for a post
        """
        print(f"\n{'='*60}")
        print(f"📌 POST #{index}/{total}")
        print(f"{'='*60}")
        print(f"👤 Author: {post_data.get('author', 'Unknown')}")
        print(f"📝 Title/Content:")
        print(f"{post_data.get('text', '')[:300]}")
        if len(post_data.get('text', '')) > 300:
            print("... (truncated)")
        print(f"🔗 URL: {post_data.get('url', 'N/A')}")
        print(f"🕐 Time: {post_data.get('timestamp', 'N/A')}")
        print(f"🆔 ID: {post_data.get('id', 'N/A')}")
        print(f"🔑 Matched Keyword: {post_data.get('matched_keyword', 'N/A')}")
        print(f"{'='*60}")
    
    def search(self, max_scroll=3, min_score=0.6, inline_comment=True):
        """
        Search Facebook for posts with keywords
        
        Args:
            max_scroll: Number of scrolls to load more results
            min_score: Minimum relevance score to trigger comment
            inline_comment: Whether to analyze and comment immediately upon finding a post
        
        Returns:
            List of post dictionaries
        """
        if not self.keywords:
            print("❌ No keywords to search")
            return []
        
        print("\n" + "="*60)
        print("🔍 GIAI ĐOẠN 1: TÌM KIẾM VÀ CÀO BÀI VIẾT (SEARCH PHASE)")
        print("📢 TOOL ĐANG LƯỚT BÀI VIẾT, CHỤP ẢNH MINH CHỨNG VÀ TRÍCH XUẤT THÔNG TIN.")
        print("⚠️ CHƯA BÌNH LUẬN Ở BƯỚC NÀY. SAU KHI CÀO XONG HẾT CÁC TỪ KHÓA,")
        print("   TOOL SẼ TỰ ĐỘNG CHUYỂN SANG BƯỚC BÌNH LUẬN!")
        print("="*60)
        
        self.found_posts = []
        self.seen_hashes = set()  # Reset duplicates
        total_posts_found = 0
        
        # Create crawled directory named by DDMMYYYY
        date_str = datetime.datetime.now().strftime("%d%m%Y")
        crawled_dir = os.path.join(".", "crawled", date_str)
        os.makedirs(crawled_dir, exist_ok=True)
        
        for keyword_idx, keyword in enumerate(self.keywords, 1):
            print(f"\n{'='*60}")
            print(f"🔎 Keyword #{keyword_idx}/{len(self.keywords)}: '{keyword}'")
            print(f"{'='*60}")
            
            try:
                # Search URL
                search_url = f"https://www.facebook.com/search/posts/?q={keyword.replace(' ', '%20')}"
                print(f"🌐 URL: {search_url}")
                self.driver.get(search_url)
                time.sleep(5)
                
                # Debug page
                self._debug_page()
                
                # Wait for results - try different selectors
                post_found = False
                selectors_to_try = [
                    "//div[contains(@class, 'x1yztbdb')]",
                    "//div[@data-ad-comet-preview]",
                    "//div[@role='article']"
                ]
                
                used_selector = None
                for selector in selectors_to_try:
                    try:
                        WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.XPATH, selector))
                        )
                        post_found = True
                        used_selector = selector
                        print(f"✅ Found posts with selector: {selector}")
                        break
                    except TimeoutException:
                        continue
                
                if not post_found:
                    print(f"⚠️ No posts found for '{keyword}'")
                    continue
                
                # Scroll and collect
                scroll_count = 0
                posts_found_this_keyword = 0
                all_posts_elements = []
                
                while scroll_count < max_scroll:
                    print(f"\n📜 Scroll {scroll_count + 1}/{max_scroll}...")
                    
                    # Try multiple ways to find posts, prioritizing the class 'x1yztbdb'
                    posts = []
                    
                    # Method 1: By class
                    try:
                        posts = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'x1yztbdb')]")
                        if posts:
                            print(f"  ✅ Found {len(posts)} posts by class 'x1yztbdb'")
                    except:
                        pass
                    
                    # Method 2: By data-ad-comet-preview
                    if not posts:
                        try:
                            posts = self.driver.find_elements(By.XPATH, "//div[@data-ad-comet-preview]")
                            if posts:
                                print(f"  ✅ Found {len(posts)} posts by data-ad-comet-preview")
                        except:
                            pass
                    
                    # Method 3: By role (filtered to ensure they are real post elements)
                    if not posts:
                        try:
                            candidate_posts = self.driver.find_elements(By.CSS_SELECTOR, "[role='article']")
                            for p in candidate_posts:
                                try:
                                    if p.text and len(p.text.strip()) > 30:
                                        posts.append(p)
                                except:
                                    continue
                            if posts:
                                print(f"  ✅ Found {len(posts)} valid posts by [role='article']")
                        except:
                            pass
                    
                    print(f"  📊 Total post elements on this scroll: {len(posts)}")
                    
                    # Process each post
                    for idx, post in enumerate(posts, 1):
                        try:
                            post_data = self._extract_post_data_v2(post)
                            
                            # Print debug for each post found
                            if post_data and post_data.get('text'):
                                print(f"\n  📝 Post #{idx} found:")
                                print(f"    Author: {post_data.get('author', 'Unknown')}")
                                print(f"    Content: {post_data.get('text', '')[:100]}...")
                                
                                # Check duplicate
                                if not self._is_duplicate(post_data):
                                
                                    # Check Sponsored/Quảng cáo
                                    try:
                                        full_text = post.text.lower() if post.text else post_data['text'].lower()
                                    except:
                                        full_text = post_data.get('text', '').lower()
                                        
                                    if "được tài trợ" in full_text or "sponsored" in full_text:
                                        print("    ⏭️ Bỏ qua bài viết Quảng cáo (Sponsored).")
                                        continue
                                        
                                    # Basic keyword check to avoid completely unrelated posts
                                    # Since Facebook search can be fuzzy, we check if at least one part of the keyword is in the text
                                    kw_lower = keyword.lower()
                                    kw_parts = kw_lower.split()
                                    has_kw = kw_lower in full_text
                                    if not has_kw and len(kw_parts) > 1:
                                        for p in kw_parts:
                                            if len(p) >= 4 and p in full_text:
                                                has_kw = True
                                                break
                                                
                                    if not has_kw:
                                        print(f"    ⏭️ Bỏ qua bài viết không chứa từ khóa '{keyword}'. Snippet: {full_text[:100].replace(chr(10), ' ')}...")
                                        continue
                                
                                    # Check if already liked (to skip previously interacted posts)
                                    try:
                                        already_liked = False
                                        like_btn = self._find_like_button(post)
                                        if like_btn:
                                            label = like_btn.get_attribute("aria-label")
                                            if label:
                                                label_lower = label.lower()
                                                if "remove" in label_lower or "bỏ" in label_lower or "gỡ" in label_lower:
                                                    already_liked = True
                                                    
                                        if already_liked:
                                            print(f"    ⏭️ Bài viết này đã được thả Like từ trước -> Bỏ qua không comment.")
                                            continue
                                    except Exception as e:
                                        print(f"    ⚠️ Lỗi khi kiểm tra trạng thái Like: {e}")
                                
                                    post_data['matched_keyword'] = keyword
                                    self.found_posts.append(post_data)
                                    posts_found_this_keyword += 1
                                    total_posts_found += 1
                                    
                                    # Crop screenshot of the post element
                                    screenshot_filename = f"post_{total_posts_found}.png"
                                    screenshot_path = os.path.join(crawled_dir, screenshot_filename)
                                    try:
                                        # Scroll element into center of screen before taking screenshot
                                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", post)
                                        time.sleep(1)
                                        post.screenshot(screenshot_path)
                                        post_data['screenshot'] = screenshot_path
                                        print(f"    📸 Saved cropped screenshot: {screenshot_path}")
                                    except Exception as screenshot_err:
                                        print(f"    ⚠️ Could not take screenshot: {screenshot_err}")
                                    
                                    # Print full debug for new post
                                    self._print_post_debug(post_data, total_posts_found, len(self.found_posts))
                                    
                                    if inline_comment:
                                        print(f"    🧠 Đang chấm điểm bài viết ngay lập tức...")
                                        analysis = self.analyzer.analyze_post(
                                            post_data.get('text', ''),
                                            post_data.get('author'),
                                            [post_data.get('matched_keyword')]
                                        )
                                        post_data['relevance_score'] = analysis.get('relevance_score', 0)
                                        post_data['recommendation'] = analysis.get('recommendation', 'review')
                                        score = post_data['relevance_score']
                                        
                                        print(f"    🎯 Điểm đánh giá (Score): {score:.2f}")
                                        if score >= min_score:
                                            print(f"    🚀 Đạt chuẩn (>= {min_score}). Tiến hành bình luận luôn...")
                                            lang = self.detect_language(post_data.get('text', ''))
                                            templates = self.load_comment_templates()
                                            comment_text = templates.get(lang, templates.get("default", ""))
                                            
                                            # Dùng tính năng share để lấy URL chính xác
                                            real_url = self._get_post_url_via_share(post)
                                            target_url = real_url if real_url else post_data['url']
                                            if real_url:
                                                print(f"    🔗 Lấy được URL chuẩn qua nút Share: {target_url}")
                                            else:
                                                print(f"    ⚠️ Không lấy được URL qua Share, dùng URL dự phòng: {target_url}")

                                            # Thử Like ngay tại trang Search trước khi mở tab mới
                                            print("    👉 Đang thả Like để đánh dấu bài viết...")
                                            try:
                                                like_btn = self._find_like_button(post)
                                                if like_btn:
                                                    label = like_btn.get_attribute("aria-label")
                                                    if label:
                                                        label_lower = label.lower()
                                                        if "remove" not in label_lower and "gỡ" not in label_lower and "bỏ" not in label_lower:
                                                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", like_btn)
                                                            time.sleep(1.0)
                                                            
                                                            click_success = False
                                                            try:
                                                                from selenium.webdriver.common.action_chains import ActionChains
                                                                ActionChains(self.driver).move_to_element(like_btn).click().perform()
                                                                click_success = True
                                                            except Exception as e:
                                                                pass
                                                            
                                                            if not click_success:
                                                                try:
                                                                    like_btn.click()
                                                                    click_success = True
                                                                except Exception as e:
                                                                    pass
                                                                    
                                                            if not click_success:
                                                                try:
                                                                    inner = like_btn.find_elements(By.XPATH, ".//div[@data-ad-rendering-role='like_button']")
                                                                    if inner:
                                                                        self.driver.execute_script("arguments[0].click();", inner[0])
                                                                    else:
                                                                        self.driver.execute_script("arguments[0].click();", like_btn)
                                                                    click_success = True
                                                                except Exception as e:
                                                                    pass
                                                                    
                                                            if click_success:
                                                                time.sleep(2)
                                                                try:
                                                                    new_label = like_btn.get_attribute("aria-label") or ""
                                                                    if "remove" in new_label.lower() or "bỏ" in new_label.lower() or "gỡ" in new_label.lower():
                                                                        print("    ✅ Đã thả Like thành công!")
                                                                    else:
                                                                        print(f"    ⚠️ Đã bấm Like nhưng trạng thái chưa đổi (Label hiện tại: {new_label}).")
                                                                except:
                                                                    print("    ✅ Đã thả Like thành công (không thể verify lại label)!")
                                                            else:
                                                                print("    ❌ Không thể click nút Like bằng bất kỳ cách nào.")
                                                            time.sleep(1)
                                                        else:
                                                            print("    ⚠️ Bài viết này đã được thả Like từ trước.")
                                            except Exception as e:
                                                print(f"    ⚠️ Lỗi khi thả Like: {e}")

                                            # Mở tab mới để comment mà không làm mất trang search hiện tại
                                            original_window = self.driver.current_window_handle
                                            self.driver.execute_script("window.open('', '_blank');")
                                            time.sleep(1)
                                            for window_handle in self.driver.window_handles:
                                                if window_handle != original_window:
                                                    self.driver.switch_to.window(window_handle)
                                                    break
                                            
                                            try:
                                                success = self._comment_on_single_post(target_url, comment_text)
                                                if success:
                                                    self.save_commented_post(post_data, comment_text)
                                                    print("    ✅ Đã bình luận xong! Đóng tab và quay lại cào tiếp...")
                                                else:
                                                    print("    ❌ Bình luận thất bại.")
                                            except Exception as comment_err:
                                                print(f"    ❌ Lỗi khi bình luận inline: {comment_err}")
                                            finally:
                                                self.driver.close()
                                                self.driver.switch_to.window(original_window)
                                                time.sleep(2)
                                        else:
                                            print(f"    ⏭️ Bỏ qua bình luận do điểm thấp ({score:.2f} < {min_score})")
                                else:
                                    print(f"    ⏭️ Duplicate detected - skipped")
                            else:
                                print(f"  ⚠️ Post #{idx} has no text content")
                                
                        except Exception as e:
                            print(f"  ❌ Error extracting post #{idx}: {e}")
                            continue
                    
                    # Scroll down
                    print(f"\n  ⬇️ Scrolling down...")
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(3)
                    scroll_count += 1
                
                print(f"\n📊 Found {posts_found_this_keyword} new posts for '{keyword}'")
                print(f"📊 Total posts so far: {len(self.found_posts)}")
                
            except Exception as e:
                print(f"❌ Error searching '{keyword}': {e}")
        
        print(f"\n{'='*60}")
        print(f"📊 SEARCH COMPLETE")
        print(f"{'='*60}")
        print(f"Total unique posts found: {len(self.found_posts)}")
        
        # Print summary of all posts found
        if self.found_posts:
            print("\n📋 SUMMARY OF ALL POSTS FOUND:")
            print("="*60)
            for i, post in enumerate(self.found_posts, 1):
                print(f"{i}. {post.get('author', 'Unknown')}: {post.get('text', '')[:80]}...")
                print(f"   🔑 Keyword: {post.get('matched_keyword', 'N/A')}")
                print(f"   🔗 {post.get('url', 'N/A')}")
                print("-"*40)
        else:
            print("\n❌ No posts found matching any keyword")
        
        # Save all found posts to posts.json in the crawled folder
        if self.found_posts:
            json_path = os.path.join(crawled_dir, "posts.json")
            try:
                with open(json_path, 'w', encoding='utf-8-sig') as f:
                    json.dump(self.found_posts, f, indent=4, ensure_ascii=False)
                print(f"\n💾 Saved all crawled posts data to {json_path}")
            except Exception as save_err:
                print(f"\n❌ Error saving posts.json: {save_err}")
        
        return self.found_posts
    
    def monitor_news_feed(self, max_scroll=10, min_score=0.6):
        """
        Scroll through the Facebook News Feed normally, detect keywords, and comment inline.
        """
        if not self.keywords:
            print("❌ No keywords loaded to monitor.")
            return []
            
        print("\n" + "="*60)
        print("📰 CHẾ ĐỘ LƯỚT BẢNG TIN (NEWS FEED)")
        print("📢 TOOL ĐANG LƯỚT FACEBOOK NHƯ NGƯỜI BÌNH THƯỜNG...")
        print("📢 NẾU THẤY BÀI VIẾT CÓ CHỨA TỪ KHÓA -> CHẤM ĐIỂM -> BÌNH LUẬN NGAY!")
        print("="*60)
        
        self.driver.get("https://www.facebook.com/")
        time.sleep(5)
        
        # Create crawled directory
        date_str = datetime.datetime.now().strftime("%d%m%Y")
        crawled_dir = os.path.join(".", "crawled", date_str)
        os.makedirs(crawled_dir, exist_ok=True)
        
        scroll_count = 0
        total_posts_found = 0
        
        while scroll_count < max_scroll:
            print(f"\n📜 Đang lướt News Feed lần {scroll_count + 1}/{max_scroll}...")
            
            # Find posts on news feed
            posts = []
            try:
                candidate_posts = self.driver.find_elements(By.CSS_SELECTOR, "[role='article']")
                for p in candidate_posts:
                    try:
                        if p.is_displayed() and p.text and len(p.text.strip()) > 30:
                            posts.append(p)
                    except:
                        pass
                        
                if not posts:
                    candidate_posts2 = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'x1yztbdb')] | //div[@data-ad-comet-preview]")
                    for p in candidate_posts2:
                        try:
                            if p.is_displayed() and p.text and len(p.text.strip()) > 30:
                                posts.append(p)
                        except:
                            pass
            except:
                pass
                
            print(f"  📊 Tìm thấy {len(posts)} bài viết trên màn hình hiện tại.")
            
            for idx, post in enumerate(posts, 1):
                try:
                    post_data = self._extract_post_data_v2(post)
                    if not post_data:
                        print(f"    ⚠️ Post #{idx}: _extract_post_data_v2 returned None")
                        try:
                            print(f"       [Debug] post.text = {post.text[:200].replace(chr(10), ' ')}")
                        except: pass
                        continue
                    if not post_data.get('text'):
                        print(f"    ⚠️ Post #{idx}: extracted text is empty")
                        continue
                        
                    # Check duplicate
                    if self._is_duplicate(post_data):
                        continue
                        
                    # Check if already liked (to skip previously interacted posts)
                    try:
                        already_liked = False
                        like_btn = self._find_like_button(post)
                        if like_btn:
                            label = like_btn.get_attribute("aria-label")
                            if label:
                                label = label.lower()
                                if "remove" in label or "gỡ" in label or "bỏ" in label:
                                    already_liked = True
                                    
                        if already_liked:
                            print(f"    ⏭️ Bỏ qua vì bài viết đã được thả Like (đánh dấu đã xử lý).")
                            continue
                    except Exception as e:
                        pass
                        
                    # Check entire post text (including group name, author, etc.)
                    try:
                        full_post_text = post.text.lower()
                    except:
                        full_post_text = post_data['text'].lower()
                        
                    matched_kw = None
                    for kw in self.keywords:
                        kw_lower = kw.lower()
                        # Khớp chính xác
                        if kw_lower in full_post_text:
                            matched_kw = kw
                            break
                        
                        # Khớp một phần từ khóa (nếu từ khóa dài hơn 1 từ)
                        parts = kw_lower.split()
                        if len(parts) > 1:
                            for p in parts:
                                if len(p) >= 4 and p in full_post_text:
                                    matched_kw = p
                                    break
                        
                        if matched_kw:
                            break
                            
                    if not matched_kw:
                        print(f"    ⏭️ Post #{idx}: No keyword matched. Snippet: {full_post_text[:100].replace(chr(10), ' ')}...")
                        continue
                        
                    post_data['matched_keyword'] = matched_kw
                    self.found_posts.append(post_data)
                    total_posts_found += 1
                    
                    print(f"\n  🎉 PHÁT HIỆN BÀI VIẾT CHỨA TỪ KHÓA '{matched_kw}'!")
                    print(f"    Author: {post_data.get('author', 'Unknown')}")
                    print(f"    Content: {post_data.get('text', '')[:100]}...")
                    
                    # Analyze and comment inline
                    print(f"    🧠 Đang chấm điểm bài viết...")
                    analysis = self.analyzer.analyze_post(
                        post_data.get('text', ''),
                        post_data.get('author'),
                        [matched_kw]
                    )
                    post_data['relevance_score'] = analysis.get('relevance_score', 0)
                    post_data['recommendation'] = analysis.get('recommendation', 'review')
                    score = post_data['relevance_score']
                    
                    print(f"    🎯 Điểm đánh giá (Score): {score:.2f}")
                    if score >= min_score:
                        print(f"    🚀 Đạt chuẩn (>= {min_score}). Tiến hành bình luận luôn...")
                        lang = self.detect_language(post_data.get('text', ''))
                        templates = self.load_comment_templates()
                        comment_text = templates.get(lang, templates.get("default", ""))
                        
                        # Dùng tính năng share để lấy URL chính xác
                        real_url = self._get_post_url_via_share(post)
                        target_url = real_url if real_url else post_data['url']
                        if real_url:
                            print(f"    🔗 Lấy được URL chuẩn qua nút Share: {target_url}")
                        else:
                            print(f"    ⚠️ Không lấy được URL qua Share, dùng URL dự phòng: {target_url}")
                            
                        # Thả Like ngay tại News Feed trước khi mở tab mới
                        print("    ❤️ Đang thả Like để đánh dấu bài viết...")
                        try:
                            like_btn = self._find_like_button(post)
                            if like_btn:
                                label = like_btn.get_attribute("aria-label")
                                if label:
                                    label_lower = label.lower()
                                    if "remove" not in label_lower and "gỡ" not in label_lower and "bỏ" not in label_lower:
                                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", like_btn)
                                        time.sleep(1.0) # Tăng thời gian chờ sau khi scroll
                                        
                                        # Thử 3 cách click: ActionChains -> Native -> JS
                                        click_success = False
                                        try:
                                            from selenium.webdriver.common.action_chains import ActionChains
                                            ActionChains(self.driver).move_to_element(like_btn).click().perform()
                                            click_success = True
                                        except Exception as e:
                                            print(f"    [Debug] ActionChains click failed: {e}")
                                            
                                        if not click_success:
                                            try:
                                                like_btn.click()
                                                click_success = True
                                            except Exception as e:
                                                print(f"    [Debug] Native click failed: {e}")
                                                
                                        if not click_success:
                                            try:
                                                # Cố gắng click vào phần tử lõi bên trong thay vì wrapper ngoài bằng JS
                                                inner = like_btn.find_elements(By.XPATH, ".//div[@data-ad-rendering-role='like_button']")
                                                if inner:
                                                    self.driver.execute_script("arguments[0].click();", inner[0])
                                                else:
                                                    self.driver.execute_script("arguments[0].click();", like_btn)
                                                click_success = True
                                            except Exception as e:
                                                print(f"    [Debug] JS click failed: {e}")
                                                
                                        if click_success:
                                            time.sleep(2) # Đợi Facebook update DOM
                                            try:
                                                new_label = like_btn.get_attribute("aria-label") or ""
                                                if "remove" in new_label.lower() or "bỏ" in new_label.lower() or "gỡ" in new_label.lower():
                                                    print("    ✅ Đã thả Like thành công!")
                                                else:
                                                    print(f"    ⚠️ Đã bấm Like nhưng trạng thái chưa đổi (Label hiện tại: {new_label}). Có thể bị Facebook chặn click.")
                                            except:
                                                print("    ✅ Đã thả Like thành công (không thể verify lại label)!")
                                        else:
                                            print("    ❌ Không thể click nút Like bằng bất kỳ cách nào.")
                                        time.sleep(1)
                                    else:
                                        print("    ⚠️ Bài viết này đã được thả Like từ trước.")
                                else:
                                    print("    ⚠️ Tìm thấy nút Like nhưng không đọc được trạng thái.")
                            else:
                                print("    ⚠️ Không tìm thấy nút Like để bấm.")
                        except Exception as like_err:
                            print(f"    ⚠️ Lỗi khi thả Like: {like_err}")

                        original_window = self.driver.current_window_handle
                        self.driver.execute_script("window.open('', '_blank');")
                        time.sleep(1)
                        for window_handle in self.driver.window_handles:
                            if window_handle != original_window:
                                self.driver.switch_to.window(window_handle)
                                break
                        
                        success = False
                        try:
                            success = self._comment_on_single_post(target_url, comment_text)
                            if success:
                                self.save_commented_post(post_data, comment_text)
                        except Exception as comment_err:
                            print(f"    ❌ Lỗi khi bình luận inline: {comment_err}")
                        finally:
                            self.driver.close()
                            self.driver.switch_to.window(original_window)
                            time.sleep(1)
                            
                        if success:
                            print("    ✅ Hoàn tất quy trình cho bài viết này!")
                        else:
                            print("    ❌ Bình luận thất bại.")
                    else:
                        print(f"    ⏭️ Bỏ qua bình luận do điểm thấp ({score:.2f} < {min_score})")
                        
                except Exception as e:
                    continue
                    
            print(f"\n  ⬇️ Tiếp tục cuộn trang xuống...")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(4)
            scroll_count += 1
            
        print(f"\n{'='*60}")
        print(f"📊 KẾT THÚC LƯỚT BẢNG TIN (Đã tìm thấy {total_posts_found} bài liên quan)")
        print(f"{'='*60}")
        return self.found_posts

    def _get_post_url_via_share(self, post_element):
        """
        Click the 'Share' button, then 'Copy link', and read from the Windows clipboard.
        """
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", post_element)
            time.sleep(1)
            
            # Find Share button
            share_buttons = post_element.find_elements(By.XPATH, ".//div[@role='button' and (contains(@aria-label, 'Chia sẻ') or contains(@aria-label, 'Share'))]")
            if not share_buttons:
                share_buttons = post_element.find_elements(By.XPATH, ".//div[contains(@class, 'x1i10hfl')]//*[contains(text(), 'Chia sẻ') or contains(text(), 'Share')]/ancestor::div[@role='button']")
                
            share_btn = None
            for btn in share_buttons:
                if btn.is_displayed():
                    share_btn = btn
                    break
                    
            if not share_btn:
                return None
                
            self.driver.execute_script("arguments[0].click();", share_btn)
            
            # Find Copy link button in popup (robust search with fast retry)
            copy_btn = None
            for attempt in range(5): # Thử tối đa 5 lần, mỗi lần 0.3s (tổng 1.5s)
                time.sleep(0.3)
                # 1. Search inside menuitems
                menuitems = self.driver.find_elements(By.XPATH, "//div[@role='menuitem']")
                for item in menuitems:
                    try:
                        if item.is_displayed():
                            text = item.text.lower().strip()
                            if text in ["copy link", "sao chép liên kết", "sao chép"]:
                                copy_btn = item
                                break
                            elif "copy link" in text or "sao chép" in text:
                                copy_btn = item
                                break
                    except:
                        continue
                        
                if copy_btn:
                    break
                        
                # 2. Aggressive fallback search (Optimized for speed using Browser-side XPath filtering)
                # Dùng translate() trong XPath để tìm kiếm không phân biệt hoa thường và tìm trực tiếp element chứa text
                elements = self.driver.find_elements(By.XPATH, "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'copy link') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'sao chép')]")
                for item in elements:
                    try:
                        if item.is_displayed():
                            copy_btn = item
                            # Cố gắng tìm thẻ cha là nút bấm thực sự để click cho chuẩn
                            try:
                                btn_parent = item.find_element(By.XPATH, "./ancestor::div[@role='button' or @role='menuitem']")
                                copy_btn = btn_parent
                            except:
                                pass
                            break
                    except:
                        continue
                        
                if copy_btn:
                    break
                        
            if not copy_btn:
                print("    ⚠️ Không tìm thấy nút Copy Link trong Menu Share")
                # Close popup
                from selenium.webdriver.common.action_chains import ActionChains
                ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
                return None
                
            # Must use native click to trigger clipboard permissions (JS click won't work)
            try:
                copy_btn.click()
            except:
                try:
                    from selenium.webdriver.common.action_chains import ActionChains
                    ActionChains(self.driver).move_to_element(copy_btn).click().perform()
                except:
                    self.driver.execute_script("arguments[0].click();", copy_btn)
                    
            time.sleep(0.5) # Chỉ cần đợi 0.5s là đủ để clipboard nhận dữ liệu
            
            # Read from Windows clipboard using powershell (safe from segfaults)
            import subprocess
            try:
                result = subprocess.run(['powershell', '-command', 'Get-Clipboard'], capture_output=True, text=True, timeout=5)
                url = result.stdout.strip()
            except Exception as clip_err:
                print(f"    ⚠️ Lỗi đọc clipboard: {clip_err}")
                url = ""
            
            if url and ("facebook.com" in url or "fb.watch" in url):
                return url
            return None
        except Exception as e:
            print(f"    ⚠️ Get link via share error: {e}")
            return None

    def _find_like_button(self, post_element):
        """
        Robustly find the Like button of a Facebook post.
        Uses data-ad-rendering-role if available, otherwise falls back to aria-label matching.
        """
        try:
            btns = post_element.find_elements(By.XPATH, ".//div[@role='button']")
            # print(f"    [Debug] Found {len(btns)} role='button' elements in post.")
            
            # Ưu tiên 1: Tìm bằng data-ad-rendering-role bên trong nút (chính xác 100%)
            for idx, btn in enumerate(btns):
                try:
                    if btn.find_elements(By.XPATH, ".//div[@data-ad-rendering-role='like_button']"):
                        lbl = btn.get_attribute("aria-label")
                        # print(f"    [Debug] Btn {idx} has like_button role. aria-label='{lbl}'")
                        if lbl:
                            return btn
                except:
                    pass
            
            # Ưu tiên 2: Tìm bằng aria-label chuẩn
            for idx, btn in enumerate(btns):
                label = btn.get_attribute("aria-label")
                if label:
                    label_lower = label.lower().strip()
                    if label_lower in ["like", "thích", "remove like", "gỡ thích", "bỏ thích"]:
                        # print(f"    [Debug] Found via exact label: {label_lower}")
                        return btn
            
            # Ưu tiên 3: Tìm bằng aria-label chứa từ khóa
            for idx, btn in enumerate(btns):
                label = btn.get_attribute("aria-label")
                if label:
                    label_lower = label.lower().strip()
                    if "remove like" in label_lower or "gỡ thích" in label_lower or "bỏ thích" in label_lower:
                        # print(f"    [Debug] Found via partial label: {label_lower}")
                        return btn
                        
        except Exception as e:
            print(f"    ⚠️ Lỗi khi tìm nút Like: {e}")
            pass
            
        return None

    def _extract_post_data_v2(self, post_element):
        """
        Extract data from a Facebook post element - Updated version
        
        Returns:
            dict: Post data or None
        """
        try:
            # 0. Try to click "See more" / "Xem thêm" to expand text
            try:
                see_more_elements = post_element.find_elements(By.XPATH, ".//*[(self::div or self::span or self::a) and (text()='Xem thêm' or text()='See more' or contains(text(), 'Xem thêm') or contains(text(), 'See more'))]")
                for elem in see_more_elements:
                    if elem.is_displayed() and elem.is_enabled():
                        txt = elem.text.strip()
                        if txt in ["Xem thêm", "See more", "Xem thêm...", "See more..."] or len(txt) < 15:
                            self.driver.execute_script("arguments[0].click();", elem)
                            print(f"    🖱️ Expanded 'See more' content.")
                            time.sleep(1.5)
                            break
            except:
                pass

            post_text = ""
            author = "Unknown"
            url = ""
            timestamp = ""
            
            # 1. Get text - prioritize the post preview
            try:
                preview_elements = post_element.find_elements(By.XPATH, ".//div[@data-ad-comet-preview]")
                if preview_elements:
                    post_text = preview_elements[0].text.strip()
            except:
                pass
                
            if not post_text:
                # Fallback to dir='auto' elements (usually the post content text containers)
                try:
                    dir_elements = post_element.find_elements(By.XPATH, ".//div[@dir='auto'] | .//span[@dir='auto']")
                    # Find the element with the maximum text length that isn't a header/link
                    candidate_text = ""
                    for elem in dir_elements:
                        text = elem.text.strip()
                        if text and len(text) > len(candidate_text):
                            candidate_text = text
                    if len(candidate_text) > 10:
                        post_text = candidate_text
                except:
                    pass
            
            # Fallback to general text methods if still empty
            if not post_text:
                text_methods = [
                    lambda: post_element.find_element(By.XPATH, ".//div[contains(@class, 'x1lliihq')]").text,
                    lambda: post_element.find_element(By.XPATH, ".//span[contains(@class, 'x1lliihq')]").text,
                    lambda: post_element.find_element(By.XPATH, ".//div[contains(@class, 'x1n2onr6')]").text,
                    lambda: post_element.find_element(By.XPATH, ".//div[contains(@class, 'x1yztbdb')]").text,
                ]
                for method in text_methods:
                    try:
                        text = method()
                        if text and len(text.strip()) > 10:
                            post_text = text.strip()
                            break
                    except:
                        continue
            
            if not post_text:
                try:
                    text = post_element.text.strip()
                    if text and len(text) > 10:
                        post_text = text
                except:
                    pass
                    
            if not post_text:
                return None
            
            # 2. Get URL & Timestamp
            links = []
            try:
                links = post_element.find_elements(By.XPATH, ".//a[@href]")
            except:
                pass
                
            best_url = ""
            fallback_url = ""
            best_link = None
            fallback_link = None
            
            for link in links:
                try:
                    href = link.get_attribute("href")
                    if not href:
                        continue
                        
                    # Check for permalinks or post URLs (strong matches)
                    if any(pattern in href for pattern in ['/posts/', '/permalink/', 'story_fbid', 'pfbid', '/photos/', '/videos/', '/photo/']):
                        best_url = href
                        best_link = link
                        # Try to get clean timestamp from the permalink link attributes
                        title = link.get_attribute("title")
                        aria_label = link.get_attribute("aria-label")
                        if title:
                            timestamp = title
                        elif aria_label:
                            timestamp = aria_label
                        break  # Found best URL, stop searching
                        
                    elif '/search/posts/' in href and '__cft__' in href and not fallback_url:
                        fallback_url = href
                        fallback_link = link
                        # Try to get clean timestamp from this link attributes
                        title = link.get_attribute("title")
                        aria_label = link.get_attribute("aria-label")
                        if title:
                            timestamp = title
                        elif aria_label:
                            timestamp = aria_label
                except:
                    continue
            
            url = best_url if best_url else fallback_url
            # The scrambled timestamp is always inside the fallback_link (the search URL link)
            time_link = fallback_link if fallback_link else best_link
            
            # If timestamp is still empty or looks scrambled, run JS de-scrambler on time_link
            if time_link and (not timestamp or len(timestamp) > 40 or '\n' in timestamp or 'Sponsored' in timestamp or 'g' in timestamp):
                try:
                    js_descramble = """
                    function getVisibleText(element) {
                        let text = "";
                        function traverse(node) {
                            if (node.nodeType === Node.TEXT_NODE) {
                                text += node.nodeValue;
                            } else if (node.nodeType === Node.ELEMENT_NODE) {
                                let style = window.getComputedStyle(node);
                                if (style.display === "none" || style.visibility === "hidden" || style.opacity === "0") {
                                    return;
                                }
                                if (style.position === "absolute" || parseFloat(style.width) <= 1 || parseFloat(style.height) <= 1) {
                                    return;
                                }
                                for (let child of node.childNodes) {
                                    traverse(child);
                                }
                            }
                        }
                        traverse(element);
                        return text.replace(/\\s+/g, ' ').trim();
                    }
                    return getVisibleText(arguments[0]);
                    """
                    descrambled = self.driver.execute_script(js_descramble, time_link)
                    if descrambled and len(descrambled) > 0 and len(descrambled) < 45:
                        # Only accept if it does not contain the word Sponsored or suggested
                        if "Sponsored" not in descrambled and "suggested" not in descrambled.lower():
                            timestamp = descrambled
                except Exception as js_err:
                    pass
            
            # 3. Get author
            for link in links:
                try:
                    href = link.get_attribute("href")
                    text = link.text.strip()
                    if href and text:
                        # Skip group links and permalinks
                        if '/groups/' in href and '/user/' in href:
                            author = text
                            break
                        elif ('/user/' in href or 'profile.php' in href) and '/groups/' not in href:
                            author = text
                            break
                except:
                    continue
            
            if author == "Unknown":
                try:
                    author_elements = post_element.find_elements(By.XPATH, ".//strong//a | .//h3//a | .//h2//a")
                    for elem in author_elements:
                        text = elem.text.strip()
                        if text:
                            author = text
                            break
                except:
                    pass
            
            # 4. Get timestamp fallback (via <time> tag)
            if not timestamp or len(timestamp) > 50: # If empty or contains scrambled text
                try:
                    time_elem = post_element.find_element(By.XPATH, ".//time")
                    if time_elem:
                        timestamp = time_elem.text or time_elem.get_attribute("datetime")
                except:
                    pass
            
            # If still empty or scrambled, try clean text representation
            if not timestamp:
                try:
                    time_elements = post_element.find_elements(By.XPATH, ".//span[contains(@class, 'x1rg5ohu')]")
                    if time_elements:
                        text = time_elements[0].text
                        # Clean if it doesn't contain a lot of newlines (scrambled)
                        if text and text.count('\n') < 3:
                            timestamp = text.strip()
                except:
                    pass
            
            if not timestamp:
                timestamp = "Vừa xong (Just now)"
            
            # 5. Get post ID
            post_id = None
            try:
                if url:
                    # Match from typical formats
                    match = re.search(r'/posts/(\d+)', url)
                    if match:
                        post_id = match.group(1)
                    else:
                        match = re.search(r'story_fbid=(\d+)', url)
                        if match:
                            post_id = match.group(1)
                        else:
                            match = re.search(r'/permalink/(\d+)', url)
                            if match:
                                post_id = match.group(1)
                            else:
                                match = re.search(r'set=pcb\.(\d+)', url)
                                if match:
                                    post_id = match.group(1)
                                else:
                                    match = re.search(r'fbid=(\d+)', url)
                                    if match:
                                        post_id = match.group(1)
                                        
                    # Fallback to CFT token hash if no numeric ID found in URL
                    if not post_id:
                        match = re.search(r'__cft__\[\d+\]=([^&]+)', url)
                        if match:
                            import hashlib
                            token = match.group(1)
                            post_id = hashlib.md5(token.encode('utf-8')).hexdigest()
            except:
                pass
            
            return {
                'text': post_text,
                'url': url,
                'author': author,
                'timestamp': timestamp,
                'id': post_id,
                'keyword_matched': [],
                'matched_keyword': ''
            }
            
        except Exception as e:
            return None
    
    def analyze_posts(self, posts=None):
        """
        Analyze posts using AI
        """
        if posts is None:
            posts = self.found_posts
        
        if not posts:
            print("❌ No posts to analyze")
            return []
        
        print("\n" + "="*60)
        print("🤖 ANALYZING POSTS WITH AI")
        print("="*60)
        
        # Filter by keywords first
        relevant_posts = []
        for post in posts:
            matched_keywords = []
            text = post.get('text', '').lower()
            
            for keyword in self.keywords:
                if keyword.lower() in text:
                    matched_keywords.append(keyword)
            
            # Fallback to the matched keyword during the search query if not directly present in post body
            if not matched_keywords and post.get('matched_keyword'):
                matched_keywords.append(post.get('matched_keyword'))
            
            if matched_keywords:
                post['keyword_matched'] = matched_keywords
                relevant_posts.append(post)
                print(f"✅ Matched: {post.get('author', 'Unknown')} - {post.get('text', '')[:50]}...")
                print(f"   🔑 Keywords: {', '.join(matched_keywords)}")
        
        print(f"\n📊 Found {len(relevant_posts)} posts matching keywords out of {len(posts)} total")
        
        if not relevant_posts:
            return []
        
        # AI Analysis
        print("\n🧠 Running AI analysis...")
        self.analyzed_posts = self.analyzer.analyze_batch(relevant_posts)
        
        # Print AI results
        print("\n📊 AI ANALYSIS RESULTS:")
        print("="*60)
        for post in self.analyzed_posts:
            score = post.get('relevance_score', 0)
            recommendation = post.get('recommendation', 'review')
            emoji = "🟢" if score >= 0.7 else "🟡" if score >= 0.4 else "🔴"
            print(f"{emoji} {post.get('author', 'Unknown')}: Score {score:.2f} - {recommendation.upper()}")
            print(f"   📝 {post.get('text', '')[:80]}...")
            print(f"   🤔 {post.get('reasoning', '')[:100]}...")
            print("-"*40)
        
        # Filter by AI relevance
        high_relevance_posts = [p for p in self.analyzed_posts if p.get('relevance_score', 0) >= 0.6]
        
        print(f"\n✅ {len(high_relevance_posts)} posts with high relevance (score >= 0.6)")
        
        return self.analyzed_posts
    
    def notify_posts(self, posts=None, min_score=0.6):
        """
        Send notifications for analyzed posts
        """
        if posts is None:
            posts = self.analyzed_posts
        
        if not posts:
            print("❌ No posts to notify")
            return 0
        
        print("\n" + "="*60)
        print("📨 SENDING NOTIFICATIONS")
        print("="*60)
        
        # Filter by relevance score
        notify_posts = [p for p in posts if p.get('relevance_score', 0) >= min_score]
        
        if not notify_posts:
            print("❌ No posts meet the relevance threshold")
            return 0
        
        # Remove duplicates by URL
        unique_posts = {}
        for post in notify_posts:
            url = post.get('url', '')
            if url and url not in self.processed_urls:
                unique_posts[url] = post
                self.processed_urls.add(url)
        
        notify_posts = list(unique_posts.values())
        
        print(f"✅ Notifying {len(notify_posts)} unique posts")
        
        # Print posts to be notified
        print("\n📋 POSTS TO BE NOTIFIED:")
        print("="*60)
        for i, post in enumerate(notify_posts, 1):
            print(f"{i}. {post.get('author', 'Unknown')} - Score: {post.get('relevance_score', 0):.2f}")
            print(f"   📝 {post.get('text', '')[:100]}...")
            print(f"   🎯 Recommendation: {post.get('recommendation', 'review').upper()}")
            print("-"*40)
        
        # Send each post as notification
        success_count = 0
        
        for post in notify_posts:
            # Build notification message
            title = f"📢 3D Print Lead by {post.get('author', 'Unknown')}"
            
            # AI analysis summary
            analysis = post.get('analysis', '')
            reasoning = post.get('reasoning', '')
            recommendation = post.get('recommendation', 'review')
            
            # Add AI insights
            if analysis or reasoning:
                ai_summary = f"AI Analysis: {analysis[:150]}\nReasoning: {reasoning[:150]}"
            else:
                ai_summary = "No AI analysis available"
            
            # Create detailed description
            description = f"🔑 Keywords: {', '.join(post.get('keyword_matched', []))}\n\n"
            description += f"📝 Post Content:\n{post.get('text', '')[:500]}\n\n"
            description += f"🤖 AI Assessment:\n{ai_summary}\n"
            description += f"📊 Score: {post.get('relevance_score', 0):.2f}\n"
            description += f"💡 Recommendation: {recommendation.upper()}"
            
            # Send notification
            success = send_telegram_alert(
                title=title,
                description=description,
                url=post.get('url', ''),
                author=post.get('author'),
                matched_keywords=post.get('keyword_matched', []),
                analysis=f"Score: {post.get('relevance_score', 0):.2f} | {recommendation}",
                post_id=post.get('id', None)
            )
            
            if success:
                success_count += 1
                post['notified'] = True
                print(f"✅ Notified: {post.get('author', 'Unknown')}")
            else:
                print(f"❌ Failed to notify: {post.get('author', 'Unknown')}")
            
            time.sleep(1)  # Avoid rate limit
        
        print(f"\n✅ Successfully notified {success_count}/{len(notify_posts)} posts")
        return success_count
    
    def detect_language(self, text):
        """
        Detect language of text. Returns 'vi', 'en', 'th', or 'default'.
        """
        if not text:
            return "default"
            
        text_lower = text.lower()
        
        # 1. Check for Thai script (Unicode range: U+0E00 - U+0E7F)
        thai_pattern = re.compile(r'[\u0e00-\u0e7f]')
        if thai_pattern.search(text):
            return "th"
            
        # 2. Check for Vietnamese-specific diacritics
        vietnamese_chars = set("àáảãạâầấẩẫậăằắẳẵặèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ")
        if any(char in vietnamese_chars for char in text_lower):
            return "vi"
            
        # 3. Check for common English words (excluding universal technical loanwords and cognates)
        english_words = {"the", "and", "you", "for", "with", "this", "have", "that", "looking", "need", "work", "anyone", "someone", "please", "about", "got", "help"}
        words = set(re.findall(r'\b\w+\b', text_lower))
        if words.intersection(english_words):
            return "en"
            
        return "default"

    def load_comment_templates(self, filepath="comment_templates.json"):
        """Load comment templates by language"""
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8-sig') as f:
                    data = json.load(f)
                    if isinstance(data, dict) and self.campaign in data:
                        templates = data[self.campaign]
                    else:
                        templates = data
                    print(f"✅ Loaded comment templates for campaign '{self.campaign}': {list(templates.keys())}")
                    return templates
            else:
                return {
                    "vi": config.DEFAULT_COMMENT,
                    "en": "Hi, we specialize in high-quality 3D printing and design services. Please check your message requests/inbox so we can discuss details!",
                    "default": config.DEFAULT_COMMENT
                }
        except Exception as e:
            print(f"❌ Error loading comment templates: {e}")
            return {}

    def load_commented_posts(self, filepath="commented_posts.json"):
        """Load already commented posts URLs"""
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8-sig') as f:
                    data = json.load(f)
                    urls = set()
                    for item in data:
                        if isinstance(item, dict) and 'url' in item:
                            urls.add(item['url'])
                        elif isinstance(item, str):
                            urls.add(item)
                    return urls
            return set()
        except Exception as e:
            print(f"❌ Error loading commented posts: {e}")
            return set()

    def save_commented_post(self, post_data, comment_text, filepath="commented_posts.json"):
        """Save commented post to persist across runs"""
        try:
            commented_list = []
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8-sig') as f:
                        commented_list = json.load(f)
                        if not isinstance(commented_list, list):
                            commented_list = []
                except:
                    commented_list = []
            
            commented_list.append({
                "url": post_data.get("url", ""),
                "author": post_data.get("author", "Unknown"),
                "text": post_data.get("text", "")[:100],
                "commented_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "comment_text": comment_text
            })
            
            with open(filepath, 'w', encoding='utf-8-sig') as f:
                json.dump(commented_list, f, indent=4, ensure_ascii=False)
            
            print(f"💾 Saved comment record to {filepath}")
            return True
        except Exception as e:
            print(f"❌ Error saving commented post: {e}")
            return False

    def _get_campaign_image_path(self):
        """
        Get the image path for the current campaign (e.g., meccha_chameleon or 3d_printing)
        """
        base_path = os.path.join(r"D:\LTD\dont_delete\facebook_commentor\resources", self.campaign, "pic1")
        if os.path.exists(base_path):
            if os.path.isdir(base_path):
                for f in os.listdir(base_path):
                    if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                        return os.path.join(base_path, f)
            else:
                return base_path
                
        for ext in ['.png', '.jpg', '.jpeg', '.webp']:
            alt_path = base_path + ext
            if os.path.exists(alt_path):
                return alt_path
                
        parent_dir = os.path.dirname(base_path)
        if os.path.exists(parent_dir) and os.path.isdir(parent_dir):
            for f in os.listdir(parent_dir):
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                    return os.path.join(parent_dir, f)
                    
        return None

    def _comment_on_single_post(self, post_url, comment_text):
        """
        Navigate to a post URL and comment on it using Selenium
        """
        try:
            print(f"\n🌐 Navigating to post: {post_url}")
            self.driver.get(post_url)
            time.sleep(5)
            
            # Scroll down to ensure comment box is visible/loaded
            self.driver.execute_script("window.scrollTo(0, 400);")
            time.sleep(2)
            
            # Selectors for main comment textbox
            comment_selectors = [
                "//div[@role='textbox' and contains(@aria-label, 'bình luận')]",
                "//div[@role='textbox' and contains(@aria-label, 'Bình luận')]",
                "//div[@role='textbox' and contains(@aria-label, 'comment')]",
                "//div[@role='textbox' and contains(@aria-label, 'Comment')]",
                "//div[@role='textbox' and @aria-label]",
                "//div[@role='textbox']",
                "//textarea[contains(@placeholder, 'comment')]",
                "//textarea[contains(@placeholder, 'bình luận')]"
            ]
            
            comment_input = None
            for selector in comment_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for elem in elements:
                        if elem.is_displayed() and elem.is_enabled():
                            aria_label = elem.get_attribute("aria-label") or ""
                            if "tìm kiếm" in aria_label.lower() or "search" in aria_label.lower():
                                continue
                            comment_input = elem
                            print(f"🎯 Found comment box with: {selector} (Aria-label: '{aria_label}')")
                            break
                    if comment_input:
                        break
                except:
                    continue
            
            if not comment_input:
                print("💬 Comment box not found immediately. Trying to click 'Comment' button first...")
                comment_buttons = [
                    "//div[@role='button' and (contains(@aria-label, 'Bình luận') or contains(@aria-label, 'Comment') or contains(@aria-label, 'bình luận') or contains(@aria-label, 'comment'))]",
                    "//span[text()='Bình luận' or text()='Comment']",
                    "//div[contains(text(), 'Bình luận') or contains(text(), 'Comment')]"
                ]
                for btn_sel in comment_buttons:
                    try:
                        btn = self.driver.find_element(By.XPATH, btn_sel)
                        if btn.is_displayed():
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                            time.sleep(1)
                            btn.click()
                            print(f"✅ Clicked Comment button using: {btn_sel}")
                            time.sleep(3) # Wait for comment input to load
                            break
                    except:
                        continue
                        
                # Try finding the comment box again after clicking
                for selector in comment_selectors:
                    try:
                        elements = self.driver.find_elements(By.XPATH, selector)
                        for elem in elements:
                            if elem.is_displayed() and elem.is_enabled():
                                aria_label = elem.get_attribute("aria-label") or ""
                                if "tìm kiếm" in aria_label.lower() or "search" in aria_label.lower():
                                    continue
                                comment_input = elem
                                print(f"🎯 Found comment box after click: {selector} (Aria-label: '{aria_label}')")
                                break
                        if comment_input:
                            break
                    except:
                        continue
            
            if not comment_input:
                print("❌ Could not find the comment box for this post.")
                try:
                    self.driver.save_screenshot("comment_failed.png")
                    print("📸 Saved debug screenshot to comment_failed.png")
                except:
                    pass
                return False
            
            print("⌨️ Focusing and typing comment...")
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", comment_input)
            time.sleep(1)
            
            try:
                comment_input.click()
            except:
                self.driver.execute_script("arguments[0].click();", comment_input)
            
            time.sleep(1)
            
            from selenium.webdriver.common.keys import Keys
            
            independent_comments = comment_text.split('\\n')
            
            for idx, ind_comment in enumerate(independent_comments):
                ind_comment = ind_comment.strip()
                if not ind_comment:
                    continue
                
                if idx > 0:
                    time.sleep(3)
                    try:
                        comment_input.click()
                        time.sleep(1)
                    except:
                        pass
                
                try:
                    comment_input.click()
                except:
                    self.driver.execute_script("arguments[0].focus();", comment_input)
                
                time.sleep(1)
                
                # 1. Inject text via JavaScript (bypasses Emoji crashes and OS clipboard focus issues)
                js_script = """
                    var el = arguments[0];
                    var text = arguments[1];
                    el.focus();
                    while (el.firstChild) { el.removeChild(el.firstChild); }
                    document.execCommand('insertText', false, text);
                """
                self.driver.execute_script(js_script, comment_input, ind_comment)
                time.sleep(1.5)
                
                # 2. The "Space Trick": Send a real keystroke to force React to read the DOM and enable the Post button
                try:
                    comment_input.send_keys(" ")
                    time.sleep(0.5)
                    comment_input.send_keys(Keys.BACKSPACE)
                except Exception as e:
                    print(f"    ⚠️ Lỗi khi trigger React bằng phím Space: {e}")
                
                time.sleep(1.5)
                
                # Upload picture ONLY for the FIRST independent comment
                if idx == 0:
                    image_path = self._get_campaign_image_path()
                    if image_path:
                        try:
                            print(f"📷 Attempting to attach image: {image_path}")
                            file_input = None
                            
                            # Find the hidden input file element inside the same comment container/form
                            try:
                                ancestor_form = comment_input.find_element(By.XPATH, "./ancestor::form")
                                file_input = ancestor_form.find_element(By.XPATH, ".//input[@type='file']")
                            except:
                                pass
                                
                            if not file_input:
                                try:
                                    # Look for file inputs nearby
                                    file_input = comment_input.find_element(By.XPATH, "../..//input[@type='file']")
                                except:
                                    pass
                                    
                            if not file_input:
                                try:
                                    file_inputs = self.driver.find_elements(By.XPATH, "//input[@type='file']")
                                    for inp in file_inputs:
                                        if inp.is_enabled():
                                            file_input = inp
                                            break
                                except:
                                    pass
                                    
                            if file_input:
                                file_input.send_keys(os.path.abspath(image_path))
                                print("✅ Attached image successfully! Waiting for upload to complete...")
                                time.sleep(5) # Wait for image to upload and display
                            else:
                                print("⚠️ Could not find file input element to attach image.")
                        except Exception as upload_err:
                            print(f"❌ Error uploading image: {upload_err}")

                # Nhấn Enter để gửi comment (nếu send_keys trên phần tử lỗi thì dùng ActionChains)
                try:
                    comment_input.send_keys(Keys.RETURN)
                except:
                    ActionChains(self.driver).send_keys(Keys.RETURN).perform()
                    
                print(f"🚀 Pressed Enter to post comment #{idx + 1}!")
                time.sleep(4)
            
            return True
            
        except Exception as e:
            print(f"❌ Error while commenting: {e}")
            return False

    def comment_on_posts(self, posts):
        """
        Iterate over found posts and post comments based on language templates
        """
        if not posts:
            print("❌ No posts to comment on.")
            return 0
            
        templates = self.load_comment_templates()
        commented_urls = self.load_commented_posts()
        
        success_count = 0
        
        print("\n" + "="*60)
        print("💬 GIAI ĐOẠN 2: BẮT ĐẦU TỰ ĐỘNG BÌNH LUẬN (COMMENTING PHASE)")
        print("📢 TOOL SẼ TỰ ĐỘNG DI CHUYỂN TỚI TỪNG BÀI VIẾT, MỞ KHUNG CHAT,")
        print("   ĐÍNH KÈM HÌNH ẢNH VÀ ĐĂNG BÌNH LUẬN!")
        print("="*60)
        print(f"Total posts to process: {len(posts)}")
        print(f"Already commented posts (loaded from file): {len(commented_urls)}")
        
        for idx, post in enumerate(posts, 1):
            url = post.get('url')
            if not url:
                print(f"⚠️ Post #{idx} has no URL, skipping.")
                continue
                
            if url in commented_urls:
                print(f"⏭️ Post #{idx} ({post.get('author', 'Unknown')}) already commented, skipping.")
                continue
                
            print(f"\n📋 Processing Post #{idx}/{len(posts)}:")
            print(f"  👤 Author: {post.get('author', 'Unknown')}")
            print(f"  📝 Content: {post.get('text', '')[:120]}...")
            print(f"  🔗 URL: {url}")
            
            # 1. Detect language
            lang = self.detect_language(post.get('text', ''))
            print(f"  🌐 Detected Language: {lang.upper()}")
            
            # 2. Select template
            comment_text = templates.get(lang, templates.get("default", ""))
            
            # Use AI suggestion if available
            ai_suggested = post.get('suggested_response')
            
            # 3. Determine comment mode (auto vs interactive)
            mode = config.COMMENT_MODE.lower()
            
            if mode == 'interactive':
                print(f"\n💡 Templates available:")
                print(f"   [1] Template ({lang}): {comment_text}")
                if ai_suggested:
                    print(f"   [2] AI Suggested: {ai_suggested}")
                print(f"   [3] Custom comment (type your own)")
                print(f"   [4] Skip this post")
                print(f"   [5] Abort commenting pipeline")
                
                choice = input("👉 Select action (1-5, default is 1): ").strip()
                
                if choice == '5':
                    print("🚪 Aborting commenting pipeline.")
                    break
                elif choice == '4':
                    print("⏭️ Skipped.")
                    continue
                elif choice == '2' and ai_suggested:
                    selected_comment = ai_suggested
                elif choice == '3':
                    selected_comment = input("💬 Type your comment: ").strip()
                    if not selected_comment:
                        print("⚠️ Empty comment, skipping.")
                        continue
                else:
                    selected_comment = comment_text
            else:
                selected_comment = comment_text
                print(f"Auto Mode: Using template for '{lang}': {selected_comment}")
                
            # 4. Comment on post
            success = self._comment_on_single_post(url, selected_comment)
            
            if success:
                success_count += 1
                self.save_commented_post(post, selected_comment)
                commented_urls.add(url)
                
                # Add delay if there are more posts and mode is auto
                if idx < len(posts) and mode == 'auto':
                    delay = random.randint(config.COMMENT_DELAY_MIN, config.COMMENT_DELAY_MAX)
                    print(f"⏳ Sleeping for {delay} seconds before next comment...")
                    time.sleep(delay)
            else:
                print("❌ Comment posting failed.")
                
        print(f"\n✅ Completed commenting. Successfully posted {success_count} comments.")
        return success_count

    def run(self, max_scroll=3, min_score=0.6):
        """Full pipeline: Search → Analyze → Notify → Comment"""
        # Search
        self.search(max_scroll)
        
        if not self.found_posts:
            print("❌ No posts found")
            return []
        
        # Analyze
        self.analyze_posts()
        
        if not self.analyzed_posts:
            print("❌ No posts analyzed")
            return []
        
        # Notify
        self.notify_posts(min_score=min_score)
        
        # Comment on highly relevant posts
        high_relevance_posts = [p for p in self.analyzed_posts if p.get('relevance_score', 0) >= min_score]
        if high_relevance_posts:
            print(f"\n💬 Triggering commenting pipeline for {len(high_relevance_posts)} high relevance posts...")
            self.comment_on_posts(high_relevance_posts)
        else:
            print("\n⏭️ No high relevance posts found for commenting.")
        
        return self.analyzed_posts

# For testing
if __name__ == "__main__":
    from fb_auth import FacebookAuth
    
    # Initialize auth
    auth = FacebookAuth()
    success, driver = auth.authenticate()
    
    if success:
        # Load keywords
        with open('keywords.json', 'r', encoding='utf-8-sig') as f:
            keywords = json.load(f).get('keywords', [])
        
        # Create monitor
        monitor = FacebookMonitor(driver, keywords)
        
        # Run full pipeline
        results = monitor.run(max_scroll=3, min_score=0.6)
        
        # Close
        auth.close()
    else:
        print("❌ Authentication failed")
