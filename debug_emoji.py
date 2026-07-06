import time
from fb_auth import FacebookAuth
from selenium.webdriver.common.action_chains import ActionChains

auth = FacebookAuth()
success, driver = auth.authenticate()
if success:
    driver.get("https://www.google.com")
    time.sleep(2)
    elem = driver.switch_to.active_element
    
    print("Trying element.send_keys with emoji...")
    try:
        elem.send_keys("👉 test")
        print("Success 1")
    except Exception as e:
        print("Fail 1:", e)
        
    print("Trying ActionChains with emoji...")
    try:
        ActionChains(driver).send_keys("👉 test").perform()
        print("Success 2")
    except Exception as e:
        print("Fail 2:", e)
        
    auth.close()
