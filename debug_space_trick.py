import time
from fb_auth import FacebookAuth
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

auth = FacebookAuth()
success, driver = auth.authenticate()
if success:
    driver.get("https://www.facebook.com/VietNamOvershare/posts/pfbid0251Vw7FjM6nHKnZ3223PzSgHjK9D6Uj1N5yQ9x5BqF7ZcM7T6k4rT2z9W2T4g2q7Ul")
    time.sleep(5)
    driver.execute_script("window.scrollTo(0, 500);")
    time.sleep(2)
    
    comment_input = None
    try:
        # Tương tự như trong _comment_on_single_post
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
        
        for selector in comment_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                for elem in elements:
                    if elem.is_displayed() and elem.is_enabled():
                        aria_label = elem.get_attribute("aria-label") or ""
                        if "tìm kiếm" in aria_label.lower() or "search" in aria_label.lower():
                            continue
                        comment_input = elem
                        break
                if comment_input:
                    break
            except:
                continue
                
        if comment_input:
            print("Found comment box!")
            try:
                comment_input.click()
            except:
                driver.execute_script("arguments[0].focus();", comment_input)
            time.sleep(1)
            
            text = "Test comment with emoji 👉\nSecond line"
            print("Injecting via JS...")
            driver.execute_script("""
                var el = arguments[0];
                el.focus();
                document.execCommand('insertText', false, arguments[1]);
            """, comment_input, text)
            
            time.sleep(1)
            print("Sending space and backspace...")
            comment_input.send_keys(" ")
            time.sleep(0.5)
            comment_input.send_keys(Keys.BACKSPACE)
            time.sleep(1)
            
            print("Hitting enter...")
            comment_input.send_keys(Keys.RETURN)
            time.sleep(5)
            driver.save_screenshot("step_final_trick.png")
        else:
            print("Could not find comment box.")
    except Exception as e:
        print("Error:", e)
    
    auth.close()
