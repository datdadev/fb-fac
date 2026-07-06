import time
from fb_auth import FacebookAuth
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import pyperclip

auth = FacebookAuth()
success, driver = auth.authenticate()
if success:
    driver.get("data:text/html,<div id='test' contenteditable='true' style='border:1px solid black; width:100px; height:100px;'></div>")
    time.sleep(2)
    elem = driver.find_element(By.ID, "test")
    
    print("Trying send_keys with ctrl+v on contenteditable...")
    try:
        pyperclip.copy("👉 test from pyperclip")
        elem.send_keys(Keys.CONTROL, 'v')
        print("Success! Value is now:", driver.execute_script("return arguments[0].innerText;", elem))
    except Exception as e:
        print("Fail:", e)
        
    time.sleep(2)
    auth.close()
