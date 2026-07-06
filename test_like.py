from fb_auth import FacebookAuth
from facebook_monitor import FacebookMonitor
from selenium.webdriver.common.by import By
import time
import sys
import io

if sys.platform.startswith('win'):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', write_through=True)
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', write_through=True)
    except Exception:
        pass

def test_like():
    auth = FacebookAuth(headless=False); driver = auth.init_driver(); auth.authenticate(); monitor = FacebookMonitor(driver)
    
    
    print("Looking for real posts...")
    
    # Scroll a bit to load real posts
    for _ in range(3):
        monitor.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(2)
        
    posts = monitor.driver.find_elements(By.XPATH, "//div[contains(@class, 'x1yztbdb')]")
    if not posts:
        posts = monitor.driver.find_elements(By.XPATH, "//div[@data-ad-comet-preview]")
    if not posts:
        posts = monitor.driver.find_elements(By.CSS_SELECTOR, "[role='article']")
    
    real_posts = []
    for p in posts:
        data = monitor._extract_post_data_v2(p)
        if data and data.get('text'):
            real_posts.append((p, data))

    if not real_posts:
        print("No real posts found.")
        monitor.driver.quit()
        return
        
    print(f"Found {len(real_posts)} real posts.")
    
    for p_idx, (post, data) in enumerate(real_posts[:2]):
        print(f"\n--- Post {p_idx} ---")
        print(f"Text snippet: {data['text'][:100].replace(chr(10), ' ')}...")
            
        like_btn = monitor._find_like_button(post)

        if like_btn:
            print("  Attempting to click Like button...")
            try:
                monitor.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", like_btn)
                time.sleep(1)
                
                # Check state before
                label_before = like_btn.get_attribute("aria-label")
                print(f"  State before click: {label_before}")
                
                try:
                    from selenium.webdriver.common.action_chains import ActionChains
                    ActionChains(monitor.driver).move_to_element(like_btn).click().perform()
                    print("  ActionChains click executed!")
                except Exception as e:
                    print(f"  ActionChains failed: {e}")
                    monitor.driver.execute_script("arguments[0].click();", like_btn)
                    print("  JS click executed!")
                    
                time.sleep(3)
                label_after = like_btn.get_attribute("aria-label")
                print(f"  State after click: {label_after}")
            except Exception as e:
                print(f"  Error interacting: {e}")
        else:
            print("  Like button not found in this post.")
            btns = post.find_elements(By.XPATH, ".//div[@role='button']")
            for idx, b in enumerate(btns):
                try:
                    lbl = b.get_attribute('aria-label')
                    has_like = bool(b.find_elements(By.XPATH, ".//div[@data-ad-rendering-role='like_button']"))
                    if lbl or has_like:
                        print(f"    Btn {idx} label: {lbl}, has_like: {has_like}")
                except:
                    pass

    monitor.driver.quit()

if __name__ == "__main__":
    test_like()
