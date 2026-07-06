import time
from fb_auth import FacebookAuth
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

auth = FacebookAuth()
success, driver = auth.authenticate()
if success:
    print("Navigating to public post to find a comment box...")
    driver.get("https://www.facebook.com/VietNamOvershare/posts/pfbid0251Vw7FjM6nHKnZ3223PzSgHjK9D6Uj1N5yQ9x5BqF7ZcM7T6k4rT2z9W2T4g2q7Ul")
    time.sleep(5)
    
    # Try to find comment box
    comment_input = None
    try:
        comment_input = driver.find_element(By.XPATH, "//div[@role='textbox' and @contenteditable='true']")
        print("Found comment box!")
    except:
        print("Could not find comment box.")
    
    if comment_input:
        text = "Test comment with emoji 👉\nSecond line"
        print("Injecting via JS...")
        driver.execute_script("""
            var el = arguments[0];
            el.focus();
            document.execCommand('insertText', false, arguments[1]);
            el.dispatchEvent(new Event('input', { bubbles: true }));
        """, comment_input, text)
        print("Injected! Waiting to see if it worked...")
        time.sleep(3)
        comment_input.send_keys(Keys.RETURN)
        print("Hit return!")
        time.sleep(5)
    
    auth.close()
