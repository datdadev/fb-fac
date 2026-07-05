import os
import sys
import io
import time
import pickle
import subprocess
from selenium import webdriver

# Force UTF-8 encoding for stdout/stderr on Windows to support emojis
if sys.platform.startswith('win'):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', write_through=True)
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', write_through=True)
    except Exception:
        pass


def main():
    print("="*60)
    print("🚀 LAUNCHING CHROME IN REMOTE DEBUGGING MODE")
    print("="*60)
    print("This will open a Chrome window on your screen.")
    print("We will control it together: you can log in, enter 2FA,")
    print("and as soon as you are logged in, we will capture the cookies!")
    print("="*60)
    
    # Define profile directory
    profile_dir = os.path.abspath("./chrome_profile")
    os.makedirs(profile_dir, exist_ok=True)
    
    # Launch Chrome via subprocess
    chrome_cmd = f'start chrome --remote-debugging-port=9222 --user-data-dir="{profile_dir}"'
    print(f"Executing: {chrome_cmd}")
    subprocess.Popen(chrome_cmd, shell=True)
    
    print("\n⏳ Waiting 5 seconds for Chrome to launch...")
    time.sleep(5)
    
    # Connect Selenium to the debugging port
    print("🔌 Connecting Selenium to Chrome on port 9222...")
    options = webdriver.ChromeOptions()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    
    try:
        driver = webdriver.Chrome(options=options)
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\nPlease make sure all other Chrome instances using the profile directory are closed.")
        print("Alternatively, you can manually run this command in your command prompt/terminal:")
        print(f'start chrome --remote-debugging-port=9222 --user-data-dir="{profile_dir}"')
        return
        
    print("✅ Connected to Chrome!")
    
    # Navigate to Facebook if not already there
    try:
        current_url = driver.current_url or ""
    except Exception:
        current_url = ""
        
    if not current_url or "facebook.com" not in current_url:
        print("🌐 Navigating to Facebook login page...")
        driver.get("https://www.facebook.com")

        
    print("\n" + "="*60)
    print("👉 ACTION REQUIRED:")
    print("1. In the Chrome browser window that just opened, log in to Facebook.")
    print("2. Enter your 2FA code / verify if prompted.")
    print("3. Keep this terminal open. We will automatically detect when you are logged in!")
    print("="*60)
    
    # Loop to detect login
    try:
        while True:
            try:
                cookies = driver.get_cookies()
                cookie_names = [c['name'] for c in cookies]
                
                # 'c_user' cookie signifies a successful Facebook login session
                if 'c_user' in cookie_names:
                    print("\n🎉 SUCCESSFUL LOGIN DETECTED!")
                    print(f"Captured {len(cookies)} cookies.")
                    
                    # Save cookies to facebook_cookies.pkl
                    with open("facebook_cookies.pkl", "wb") as f:
                        pickle.dump(cookies, f)
                    print("💾 Saved cookies to facebook_cookies.pkl")
                    
                    # Take success screenshot
                    driver.save_screenshot("cookies_success.png")
                    print("📸 Saved screenshot to cookies_success.png")
                    break
            except Exception as loop_err:
                # Handle temporary browser communication disconnects
                pass
                
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n👋 Monitoring cancelled by user.")
    finally:
        print("\n✅ Setup complete. You can close this script now.")

if __name__ == "__main__":
    main()
