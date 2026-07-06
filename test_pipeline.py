import json
import time
from fb_auth import FacebookAuth
from facebook_monitor import FacebookMonitor
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

auth = FacebookAuth()
success, driver = auth.authenticate()
if success:
    monitor = FacebookMonitor(driver, ["meccha chameleon"])
    with open("crawled/03072026/posts.json", "r", encoding="utf-8") as f:
        posts = json.load(f)
    
    test_url = posts[0]['url']
    print(f"Navigating to {test_url}")
    
    res = monitor._comment_on_single_post(test_url, "Shopee 3DBro có đủ 20 dáng pose, chỉ 16k/1 con mô hình ạ :)) \nSưu tầm nhiều đc giảm thêm á ạ\n👉 Đặt mua tại VN: https://vn.shp.ee/iZNy9Qn3")
    print(f"Result: {res}")
    driver.save_screenshot("step2_comment_done.png")
    auth.close()
