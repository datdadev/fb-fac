import time
from fb_auth import FacebookAuth
from facebook_monitor import FacebookMonitor
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import pyperclip

auth = FacebookAuth()
success, driver = auth.authenticate()
if success:
    monitor = FacebookMonitor(driver, ["test"])
    post_url = "https://www.facebook.com/VietNamOvershare/posts/pfbid0251Vw7FjM6nHKnZ3223PzSgHjK9D6Uj1N5yQ9x5BqF7ZcM7T6k4rT2z9W2T4g2q7Ul"
    
    print(f"Navigating to {post_url}")
    driver.get(post_url)
    time.sleep(5)
    driver.save_screenshot("step1_loaded.png")
    
    driver.execute_script("window.scrollTo(0, 500);")
    time.sleep(2)
    driver.save_screenshot("step2_scrolled.png")
    
    # Check if comment box is visible and interactable before running full function
    print("Testing manual comment injection first to debug visual state...")
    try:
        comment_input = driver.find_element(By.XPATH, "//div[@role='textbox' and @contenteditable='true']")
        comment_input.click()
        time.sleep(1)
        driver.save_screenshot("step3_focused.png")
        
        # Test copy paste
        pyperclip.copy("Test comment 👉\nNewLine")
        comment_input.send_keys(Keys.CONTROL, 'v')
        time.sleep(2)
        driver.save_screenshot("step4_typed.png")
        
        # We will not submit to avoid spamming the public page, but we want to see if the text is there
    except Exception as e:
        print(f"Manual debug failed: {e}")
    
    auth.close()
