import sys
import io
import time
from fb_auth import FacebookAuth
from facebook_monitor import FacebookMonitor

if sys.platform.startswith('win'):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', write_through=True)
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', write_through=True)
    except Exception:
        pass

def debug_like():
    print("Starting debug_like.py...")
    auth = FacebookAuth(headless=False); driver = auth.init_driver(); monitor = FacebookMonitor(driver)
    if not auth.authenticate():
        print("Login failed!")
        return

    # Use just one keyword
    monitor.keywords = ["meccha chameleon"]
    
    # We will override _find_like_button in this instance to take screenshots
    original_find = monitor._find_like_button
    
    def hooked_find(post_element):
        print("\n--- HOOK: monitor_news_feeding for Like button ---")
        btn = original_find(post_element)
        if btn:
            print(f"Hook found button! aria-label: {btn.get_attribute('aria-label')}")
            # Take screenshot of the post
            try:
                monitor.driver.save_screenshot("post_before_like.png")
                print("Screenshot saved to post_before_like.png")
            except Exception as e:
                print(f"Screenshot failed: {e}")
        else:
            print("Hook DID NOT find button!")
            try:
                monitor.driver.save_screenshot("post_no_like_found.png")
            except: pass
        return btn
        
    monitor._find_like_button = hooked_find
    
    print("Running monitor_news_feed with 1 scroll...")
    try:
        monitor.monitor_news_feed(max_scroll=3, min_score=0)
    except Exception as e:
        print(f"Exception during monitor_news_feed: {e}")
        
    # Take a final screenshot
    try:
        monitor.driver.save_screenshot("final_state.png")
    except: pass
    
    print("Finished debug_like.py")
    monitor.driver.quit()

if __name__ == "__main__":
    debug_like()
