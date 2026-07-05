import os
import time
import pickle
import sys
import io
from selenium import webdriver

# Force UTF-8
if sys.platform.startswith('win'):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', write_through=True)
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', write_through=True)
    except Exception:
        pass

def main():
    print("="*60)
    print("🔌 CONNECTING TO RUNNING CHROME...")
    print("="*60)
    
    options = webdriver.ChromeOptions()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    
    try:
        driver = webdriver.Chrome(options=options)
        print("✅ Successfully connected to Chrome!")
    except Exception as e:
        print(f"❌ Failed to connect to Chrome on port 9222: {e}")
        print("Please ensure the Chrome window I opened is active and not blocked.")
        return
        
    print("\n" + "="*60)
    print("👉 ACTION REQUIRED:")
    print("1. Log in to Facebook in the Chrome browser window on your screen.")
    print("2. Enter your 2FA code / verify if prompted.")
    print("3. Keep this process running. I am monitoring the window...")
    print("="*60)
    
    try:
        while True:
            try:
                cookies = driver.get_cookies()
                cookie_names = [c['name'] for c in cookies]
                
                if 'c_user' in cookie_names:
                    print("\n🎉 SUCCESSFUL LOGIN DETECTED!")
                    print(f"Captured {len(cookies)} cookies.")
                    
                    with open("facebook_cookies.pkl", "wb") as f:
                        pickle.dump(cookies, f)
                    print("💾 Saved cookies to facebook_cookies.pkl")
                    
                    driver.save_screenshot("cookies_success.png")
                    print("📸 Saved success screenshot to cookies_success.png")
                    break
            except Exception:
                pass
            time.sleep(2)
    except KeyboardInterrupt:
        print("\n👋 Cancelled.")
    print("✅ Done!")

if __name__ == "__main__":
    main()
