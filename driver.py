from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import os, json

with open('config.json', 'r') as file:
    config = json.load(file)

os.environ['FFMPEG_LOG_LEVEL'] = 'quiet'

def newDriver(headless=True):
    options = Options()

    #options.binary_location = config['path']['chrome']

    if headless:
        options.add_argument("--headless")
        options.add_argument("--window-size=1920,1080")
    
    #options.add_argument("--start-maximized")
    options.add_argument("--remote-debugging-pipe")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.9999.99 Safari/537.36")
    
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--enable-javascript")

    options.add_argument("--no-sandbox")  # Bypass OS security model, speeds up the setup on Linux
    options.add_argument("--disable-gpu")  # Disable GPU hardware acceleration
    options.add_argument("--disable-extensions")  # Disable extensions
    options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
    
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    
    # Suppress console logs
    options.add_argument("--log-level=3")
    options.add_argument("--silent")

    options.add_experimental_option("detach", True)

    # Ignore SSL errors
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--ignore-ssl-errors")

    driver = webdriver.Chrome(service=Service(config['path']['chromedriver'], log_output="chromedriver.log"), options=options)
    #driver = webdriver.Chrome(service=Service(ChromeDriverManager().install(), log_output="chromedriver.log"), options=options)
    return driver

