import os
import sys
import io
from dotenv import load_dotenv
from selenium.webdriver.common.by import By
import time
from fb_auth import FacebookAuth

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_share():
    load_dotenv()
    auth = FacebookAuth()
    driver = auth.init_driver()
    
    if not auth.authenticate(driver):
        print("Login failed")
        driver.quit()
        return

    print("Navigating to Facebook...")
    driver.get("https://www.facebook.com/")
    time.sleep(5)
    
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)

    print("Looking for Share buttons...")
    share_buttons = driver.find_elements(By.XPATH, "//div[@role='button' and (contains(@aria-label, 'Chia sẻ') or contains(@aria-label, 'Share'))]")
    if not share_buttons:
        share_buttons = driver.find_elements(By.XPATH, "//div[contains(@class, 'x1i10hfl')]//*[contains(text(), 'Chia sẻ') or contains(text(), 'Share')]/ancestor::div[@role='button']")

    print(f"Found {len(share_buttons)} Share buttons.")
    
    if share_buttons:
        btn = share_buttons[0]
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
        time.sleep(1)
        
        print("Clicking first Share button...")
        driver.execute_script("arguments[0].click();", btn)
        time.sleep(3)
        
        print("Dumping all menuitems and buttons...")
        with open("share_dump.txt", "w", encoding="utf-8") as f:
            f.write("=== MENU ITEMS ===\n")
            items = driver.find_elements(By.XPATH, "//div[@role='menuitem']")
            for item in items:
                if item.is_displayed():
                    f.write(f"TEXT: {item.text}\n")
                    f.write(f"HTML: {item.get_attribute('outerHTML')}\n")
                    f.write("-" * 40 + "\n")
                    
            f.write("\n=== ALL VISIBLE SPANS ===\n")
            spans = driver.find_elements(By.XPATH, "//span")
            for span in spans:
                if span.is_displayed() and span.text.strip():
                    f.write(f"SPAN TEXT: {span.text}\n")
        
        print("Dump saved to share_dump.txt. Please share the contents!")
        
    driver.quit()

if __name__ == "__main__":
    test_share()
