import time
from fb_auth import FacebookAuth
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

auth = FacebookAuth()
success, driver = auth.authenticate()
if success:
    driver.get("data:text/html,<div id='test' contenteditable='true' style='border:1px solid black; width:100px; height:100px;'></div>")
    time.sleep(2)
    elem = driver.find_element(By.ID, "test")
    
    print("Trying send_keys with emoji on contenteditable...")
    try:
        elem.send_keys("👉 test")
        print("Success!")
    except Exception as e:
        print("Fail:", e)
        
    time.sleep(2)
    auth.close()
