from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os

# Chrome setup
options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome(options=options)
driver.set_window_position(0, 0)
driver.set_window_size(1920, 1080)

# Replace with your IDN URL and login credentials
idn_url = os.environ["CI_ENVIRONMENT_URL"]
username = os.environ["IDN_USERNAME"]
password = os.environ["IDN_PASSWORD"] 
sources_page = os.environ["CI_ENVIRONMENT_URL"] + "/ui/a/admin/connections/sources-list/configured-sources"
roles_page = os.environ["CI_ENVIRONMENT_URL"] + "/ui/a/admin/access/roles/landing-page"
workflows_page = os.environ["CI_ENVIRONMENT_URL"] + "/ui/a/admin/workflows"
try:
    driver.get(idn_url)
    
    username_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "username")))
    password_field = driver.find_element(By.ID, "password")
    
    username_field.send_keys(username)
    password_field.send_keys(password + Keys.RETURN)
    time.sleep(3)
    
    driver.get(sources_page)
    time.sleep(3)

    driver.save_screenshot('sources_view.png')
    print("Source page screenshot saved")

    driver.get(roles_page)
    time.sleep(3)
    
    driver.save_screenshot('roles_view.png')
    print("Roles page screenshot saved")

    driver.get(workflows_page)
    time.sleep(3)
    
    driver.save_screenshot('workflows_view.png')
    print("Workflows page screenshot saved")



finally:
    driver.quit()