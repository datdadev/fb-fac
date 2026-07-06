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
    # Get the URL of post_1 from crawled posts
    with open("crawled/03072026/posts.json", "r", encoding="utf-8") as f:
        posts = json.load(f)
    
    test_url = 'https://www.facebook.com/zuck/posts/10114028525049901'
    print(f"Testing comment on: {test_url}")
    
    # Run _comment_on_single_post
    result = monitor._comment_on_single_post(test_url, "This is a test comment\nSecond line test")
    print(f"Result: {result}")
    
    time.sleep(5)
    auth.close()
