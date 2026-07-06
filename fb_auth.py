"""
Facebook Authentication Module
Handles login, cookies, 2FA, and session management
"""

import os
import time
import pickle
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from dotenv import load_dotenv

load_dotenv()

# Constants
COOKIE_FILE = "facebook_cookies.pkl"
SELECTOR_FILE = "facebook_selectors.json"


class FacebookAuth:
    """
    Facebook Authentication Handler
    Manages login, cookies, 2FA, and session
    """
    
    def __init__(self, email=None, password=None, headless=False):
        """
        Initialize FacebookAuth
        
        Args:
            email: Facebook email (optional, will load from .env if not provided)
            password: Facebook password (optional, will load from .env if not provided)
            headless: Run in headless mode (default: False)
        """
        self.email = email or os.getenv("FACEBOOK_EMAIL")
        self.password = password or os.getenv("FACEBOOK_PASSWORD")
        self.headless = headless
        self.driver = None
        self.cookies = []
        self.is_authenticated = False
        
        if not self.email or not self.password:
            raise ValueError("Email and password must be provided or set in .env file")
    
    def init_driver(self):
        """Initialize Chrome WebDriver with anti-detection options"""
        print("[Selenium] Khởi tạo Webdriver...")
        
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        if self.headless:
            options.add_argument("--headless")
        
        self.driver = webdriver.Chrome(options=options)
        return self.driver
    
    def _load_selectors(self):
        """Load selectors from JSON file"""
        if os.path.exists(SELECTOR_FILE) and os.path.getsize(SELECTOR_FILE) > 0:
            try:
                with open(SELECTOR_FILE, 'r', encoding='utf-8-sig') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_selectors(self, selectors):
        """Save selectors to JSON file"""
        try:
            with open(SELECTOR_FILE, 'w', encoding='utf-8-sig') as f:
                json.dump(selectors, f, indent=4, ensure_ascii=False)
            return True
        except:
            return False
    
    def _find_element_smart(self, element_name, default_selectors, wait_time=10):
        """
        Find element with multiple selector strategies and memory
        
        Args:
            element_name: Name/key for the element
            default_selectors: List of (by, value) tuples
            wait_time: Maximum wait time in seconds
        
        Returns:
            WebElement or None
        """
        if not self.driver:
            return None
            
        saved_selectors = self._load_selectors()
        selectors_to_try = []
        
        if element_name in saved_selectors:
            saved = saved_selectors[element_name]
            if isinstance(saved, list):
                selectors_to_try.extend(saved)
            else:
                selectors_to_try.append(saved)
        
        for selector in default_selectors:
            if selector not in selectors_to_try:
                selectors_to_try.append(selector)
        
        wait = WebDriverWait(self.driver, wait_time)
        
        for selector_type, selector_value in selectors_to_try:
            try:
                element = None
                if selector_type == "id":
                    element = wait.until(EC.presence_of_element_located((By.ID, selector_value)))
                elif selector_type == "name":
                    element = wait.until(EC.presence_of_element_located((By.NAME, selector_value)))
                elif selector_type == "xpath":
                    element = wait.until(EC.presence_of_element_located((By.XPATH, selector_value)))
                elif selector_type == "css":
                    element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector_value)))
                elif selector_type == "class":
                    element = wait.until(EC.presence_of_element_located((By.CLASS_NAME, selector_value)))
                elif selector_type == "placeholder":
                    element = wait.until(EC.presence_of_element_located((By.XPATH, f"//input[@placeholder='{selector_value}']")))
                elif selector_type == "text":
                    element = wait.until(EC.presence_of_element_located((By.XPATH, f"//button[contains(text(),'{selector_value}')]")))
                
                if element and element.is_enabled():
                    if element_name not in saved_selectors:
                        saved_selectors[element_name] = []
                    if (selector_type, selector_value) not in saved_selectors[element_name]:
                        saved_selectors[element_name].append((selector_type, selector_value))
                        self._save_selectors(saved_selectors)
                    return element
            except:
                continue
        
        return None
    
    def _handle_2fa(self):
        """
        Handle Facebook 2FA verification
        Returns True if 2FA passed, False otherwise
        """
        if not self.driver:
            return False
            
        current_url = self.driver.current_url.lower()
        
        if "checkpoint" not in current_url and "two_step" not in current_url and "authentication" not in current_url:
            return True  # No 2FA required
        
        print("\n" + "="*60)
        print("🔐 PHÁT HIỆN YÊU CẦU XÁC THỰC 2FA")
        print("="*60)
        print("\n📱 Facebook yêu cầu xác thực 2 bước!")
        print("👉 Vui lòng mở điện thoại để lấy mã xác thực.")
        print("👉 Hoặc kiểm tra email để lấy mã.")
        print("\n" + "="*60)
        
        try:
            # Try to find 2FA input
            code_input = None
            selectors = [
                (By.ID, "approvals_code"),
                (By.NAME, "approvals_code"),
                (By.XPATH, "//input[@type='text' and contains(@placeholder, 'code')]"),
                (By.XPATH, "//input[contains(@placeholder, 'mã')]"),
                (By.XPATH, "//input[contains(@aria-label, 'code')]"),
                (By.CSS_SELECTOR, "input[type='text']"),
            ]
            
            for by, value in selectors:
                try:
                    code_input = WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located((by, value))
                    )
                    if code_input:
                        break
                except:
                    continue
            
            if code_input:
                code = input("\n🔑 Mã 2FA: ").strip()
                if code:
                    code_input.clear()
                    time.sleep(0.5)
                    code_input.send_keys(code)
                    print("✅ Đã nhập mã xác thực")
                    
                    try:
                        confirm_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Tiếp tục') or contains(text(), 'Continue') or contains(text(), 'Xác nhận')]")
                        confirm_btn.click()
                        print("✅ Đã nhấn nút xác nhận")
                    except:
                        code_input.send_keys(Keys.RETURN)
                        print("✅ Đã nhấn Enter")
                    
                    time.sleep(5)
                    
                    if "checkpoint" not in self.driver.current_url.lower() and "two_step" not in self.driver.current_url.lower():
                        print("✅ Xác thực 2FA thành công!")
                        return True
                    else:
                        print("❌ Xác thực 2FA thất bại! Thử lại...")
                        return self._handle_2fa()
            else:
                print("\n⚠️ Không tìm thấy input nhập mã 2FA!")
                print("Vui lòng xác thực thủ công trên điện thoại hoặc email.")
                input("✅ Nhấn Enter sau khi đã xác thực xong...")
                
                self.driver.refresh()
                time.sleep(3)
                
                if "checkpoint" not in self.driver.current_url.lower() and "two_step" not in self.driver.current_url.lower():
                    print("✅ Xác thực 2FA thành công!")
                    return True
                else:
                    return self._handle_2fa()
                    
        except Exception as e:
            print(f"⚠️ Lỗi xử lý 2FA: {e}")
            return False
    
    def _login_with_credentials(self):
        """
        Login using email and password
        Returns True if successful, False otherwise
        """
        if not self.driver:
            return False
            
        try:
            time.sleep(2)
            
            # Find and fill email
            print("[Login] Đang tìm input email...")
            email_selectors = [
                ("id", "email"),
                ("name", "email"),
                ("xpath", "//input[@type='text' and @name='email']"),
                ("xpath", "//input[@name='email']"),
                ("xpath", "//input[contains(@placeholder, 'Email')]"),
                ("xpath", "//input[contains(@placeholder, 'Số điện thoại')]"),
            ]
            
            email_input = self._find_element_smart("email_input", email_selectors, wait_time=10)
            
            if email_input:
                email_input.clear()
                time.sleep(0.3)
                email_input.send_keys(self.email)
                print(f"[Login] ✅ Đã điền email: {self.email[:3]}...{self.email[-3:]}")
            else:
                print("[Login] ❌ Không tìm thấy input email!")
                return False
            
            # Find and fill password
            print("[Login] Đang tìm input password...")
            password_selectors = [
                ("id", "pass"),
                ("name", "pass"),
                ("xpath", "//input[@type='password']"),
                ("xpath", "//input[contains(@placeholder, 'Mật khẩu')]"),
            ]
            
            password_input = self._find_element_smart("password_input", password_selectors, wait_time=10)
            
            if password_input:
                password_input.clear()
                time.sleep(0.3)
                password_input.send_keys(self.password)
                print("[Login] ✅ Đã điền password")
            else:
                print("[Login] ❌ Không tìm thấy input password!")
                return False
            
            # Find and click login button
            print("[Login] Đang tìm nút đăng nhập...")
            login_selectors = [
                ("name", "login"),
                ("xpath", "//button[@type='submit']"),
                ("xpath", "//button[contains(text(), 'Đăng nhập')]"),
                ("xpath", "//button[contains(text(), 'Log In')]"),
            ]
            
            login_button = self._find_element_smart("login_button", login_selectors, wait_time=10)
            
            if login_button:
                try:
                    login_button.click()
                except:
                    self.driver.execute_script("arguments[0].click();", login_button)
                print("[Login] ✅ Đã nhấn nút đăng nhập")
            else:
                if password_input:
                    password_input.send_keys(Keys.RETURN)
                    print("[Login] ✅ Đã nhấn Enter để đăng nhập")
                else:
                    print("[Login] ❌ Không tìm thấy nút đăng nhập!")
                    return False
            
            # Wait for processing
            print("\n[Login] ⏳ Đang đợi đăng nhập...")
            time.sleep(5)
            
            # Check for 2FA
            current_url = self.driver.current_url.lower()
            
            if "checkpoint" in current_url or "two_step" in current_url or "authentication" in current_url:
                print("\n🔐 Phát hiện yêu cầu xác thực 2FA")
                if self._handle_2fa():
                    print("\n✅ Xác thực 2FA thành công!")
                    return True
                else:
                    print("\n❌ Xác thực 2FA thất bại!")
                    return False
            
            # Check login success
            if "login" not in current_url:
                print("\n[Login] ✅ ĐĂNG NHẬP THÀNH CÔNG!")
                return True
            else:
                print("\n[Login] ❌ Đăng nhập thất bại!")
                return False
                
        except Exception as e:
            print(f"[Login Error] {e}")
            return False
    
    def _load_cookies(self):
        """
        Load cookies from file and apply to driver
        Returns True if successful, False otherwise
        """
        if not self.driver:
            return False
            
        if os.path.exists(COOKIE_FILE) and os.path.getsize(COOKIE_FILE) > 0:
            try:
                self.driver.get("https://www.facebook.com")
                time.sleep(2)
                cookies = pickle.load(open(COOKIE_FILE, "rb"))
                for cookie in cookies:
                    if 'sameSite' in cookie:
                        cookie.pop('sameSite', None)
                    if 'expiry' in cookie:
                        cookie['expiry'] = int(cookie['expiry'])
                    try:
                        self.driver.add_cookie(cookie)
                    except:
                        pass
                print(f"[Cookie] Đã load {len(cookies)} cookies")
                self.driver.refresh()
                time.sleep(3)
                
                current_url = self.driver.current_url.lower()
                if "login" not in current_url and "checkpoint" not in current_url:
                    return True
                else:
                    print("[Cookie] Cookies không hiệu lực, cần đăng nhập lại")
                    return False
            except Exception as e:
                print(f"[Cookie] Lỗi: {e}")
                return False
        return False
    
    def _save_cookies(self):
        """
        Save current driver cookies to file
        Returns True if successful, False otherwise
        """
        if not self.driver:
            return False
            
        try:
            cookies = self.driver.get_cookies()
            with open(COOKIE_FILE, "wb") as f:
                pickle.dump(cookies, f)
            self.cookies = cookies
            print(f"[Cookie] Đã lưu {len(cookies)} cookies")
            return True
        except Exception as e:
            print(f"[Cookie] Lỗi: {e}")
            return False
    
    def authenticate(self, force_login=False):
        """
        Main authentication method
        Tries cookies first, then falls back to credentials + 2FA
        
        Args:
            force_login: Skip loading cookies and force credential/manual login if True
            
        Returns:
            tuple: (success: bool, driver: WebDriver)
        """
        if not self.driver:
            self.init_driver()
        
        print("\n" + "="*60)
        print("=== FACEBOOK AUTHENTICATION ===")
        print("="*60)
        
        try:
            print("\n[Process] Đang truy cập Facebook...")
            self.driver.get("https://www.facebook.com")
            time.sleep(3)
            
            # Try cookies first (unless forced to login)
            if not force_login and self._load_cookies():
                print("\n✅ ĐĂNG NHẬP BẰNG COOKIES THÀNH CÔNG!")
                self.is_authenticated = True
                return True, self.driver
            
            # Fallback to credentials
            print("\n=== ĐĂNG NHẬP BẰNG USERNAME/PASSWORD ===")
            if self._login_with_credentials():
                self._save_cookies()
                print("\n✅ ĐĂNG NHẬP THÀNH CÔNG!")
                self.is_authenticated = True
                self.driver.save_screenshot("facebook_logged_in.png")
                print("📸 Đã lưu screenshot: facebook_logged_in.png")
                return True, self.driver
            else:
                print("\n⚠️ Không thể đăng nhập tự động bằng thông tin từ .env")
                print("👉 Vui lòng đăng nhập thủ công trên trình duyệt Chrome vừa hiển thị...")
                print("👉 (Sau khi đăng nhập thành công và nhìn thấy trang chủ Facebook, hãy quay lại đây)")
                input("⌨️ Nhấn Enter tại đây để lưu Cookies mới...")
                
                # Check login success again
                if self.is_logged_in():
                    self._save_cookies()
                    print("\n✅ ĐĂNG NHẬP THÀNH CÔNG (THỦ CÔNG)!")
                    self.is_authenticated = True
                    return True, self.driver
                else:
                    print("\n❌ ĐĂNG NHẬP THẤT BẠI!")
                    self.is_authenticated = False
                    return False, self.driver
                
        except Exception as e:
            print(f"\n[Error] {e}")
            self.is_authenticated = False
            return False, self.driver
    
    def get_driver(self):
        """
        Get authenticated driver
        If not authenticated, authenticate first
        """
        if not self.is_authenticated or not self.driver:
            success, driver = self.authenticate()
            if not success:
                raise Exception("Failed to authenticate Facebook")
        return self.driver
    
    def close(self):
        """Close the driver and cleanup"""
        if self.driver:
            self.driver.quit()
            self.driver = None
            self.is_authenticated = False
    
    def refresh_session(self):
        """
        Refresh the current session
        Useful if cookies expire during long-running operations
        """
        if self.driver:
            self.driver.refresh()
            time.sleep(3)
            
            # Check if still logged in
            if "login" in self.driver.current_url.lower():
                print("[Session] Session expired, re-authenticating...")
                return self.authenticate()
            return True, self.driver
        return False, None
    
    def is_logged_in(self):
        """
        Check if currently logged in
        Returns True if logged in, False otherwise
        """
        if not self.driver:
            return False
        
        current_url = self.driver.current_url.lower()
        return "login" not in current_url and "checkpoint" not in current_url


# Convenience functions for backward compatibility
def get_authenticated_driver(email=None, password=None, headless=False):
    """
    Quick function to get authenticated driver
    
    Args:
        email: Facebook email
        password: Facebook password
        headless: Run in headless mode
    
    Returns:
        WebDriver: Authenticated driver
    """
    auth = FacebookAuth(email, password, headless)
    success, driver = auth.authenticate()
    if not success:
        raise Exception("Failed to authenticate")
    return driver


def quick_auth():
    """
    Quick authentication with .env credentials
    Returns driver
    """
    return get_authenticated_driver()


# Main for testing
if __name__ == "__main__":
    print("Testing Facebook Authentication Module...")
    auth = FacebookAuth()
    success, driver = auth.authenticate()
    
    if success:
        print("\n" + "="*60)
        print("📌 THÔNG TIN:")
        print(f"  - Tiêu đề: {driver.title}")
        print(f"  - URL: {driver.current_url}")
        print("="*60)
        
        input("\nPress Enter to close...")
        auth.close()
    else:
        print("Authentication failed!")
