from driver import new_driver
from similarity import score_similarity
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import StaleElementReferenceException
import logging
import time
import pandas as pd

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def query(q, headless=False):
    start_time = time.time()
    logging.info("Started Grailed job, initializing browser")
    driver = new_driver(headless)
    logging.debug("Browser ready")
    listings = pd.DataFrame(columns=["title", "brand", "price", "size", "url"])

    def waitForElement(by, q):
        return WebDriverWait(driver, 30).until(EC.presence_of_element_located((by, q)))

    def scroll_down():
        last_height = driver.execute_script("return document.body.scrollHeight")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        WebDriverWait(driver, 10).until(lambda d: d.execute_script("return document.body.scrollHeight") > last_height)

    try:
        driver.get("https://grailed.com")
        logging.info("Opened Grailed website")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        searchButton = waitForElement(By.XPATH, '//*[@id="globalHeaderWrapper"]/div/div[1]/form/button')
        searchButton.click()
        logging.debug("Clicked on the search button to prompt modal.")
        driver.execute_script("var modals = document.querySelectorAll('.ReactModal__Content--after-open, .modal, .Modal-module__authenticationModal___g7Ufu'); if (modals.length > 0) { modals.forEach(modal => { if (modal.style.display != 'none') { modal.style.display = 'none'; console.debug('Modal closed'); }});}")
        logging.debug("Modals handled.")
        searchBox = waitForElement(By.XPATH, '//*[@id="header_search-input"]')
        searchBox.send_keys(q)
        searchBox.send_keys(Keys.ARROW_DOWN)
        correctedText = searchBox.get_attribute("value")
        searchBox.send_keys(Keys.ENTER)
        logging.debug(f"Searched for: {correctedText}")

        while True:
            filter = Select(waitForElement(By.CLASS_NAME, 'ais-SortBy-select'))
            filter.select_by_value("Listing_by_low_price_production")
            logging.debug("Set filter to sort by low price.")
            try:
                feed = WebDriverWait(driver, 30).until(EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@class, 'feed-item') and not(contains(@class, 'empty-item'))]")))
                logging.debug(f"Indexing through {len(feed)} items of \"{correctedText}\".")
                initial_len = len(listings)

                for item in feed:
                    title = item.find_element(By.XPATH, f".//div[3]/div[2]/p").text
                    try:
                        brand = item.find_element(By.XPATH, f".//div[3]/div[2]/p[2]").text
                    except:
                        brand = ""  # In case brand is not available

                    full_text = title + " " + brand  # Combine title and brand for similarity checking
                    if score_similarity(full_text, correctedText) >= 0.85:  # Adjusting the threshold to be less strict
                        price = int(item.find_element(By.XPATH, ".//div/div/span[1]").text.lstrip("$").replace(',', ''))
                        size = item.find_element(By.XPATH, ".//div[3]/div[1]/p[2]").text
                        url = item.find_element(By.XPATH, ".//a").get_attribute('href')
                        listings = pd.concat([listings, pd.DataFrame([{"title": title, "price": price, "size": size, "url": url}])], ignore_index=True)

                if len(listings) < 5 and len(feed) > 0:
                    scroll_down()
                elif len(listings) >= 5 or len(listings) == initial_len:
                    break
            except StaleElementReferenceException:
                logging.warning("Detected stale element reference, refreshing the page.")
                driver.refresh()
                time.sleep(2)  # Give time for the page to reload

    finally:
        driver.quit()
        elapsed_time = time.time() - start_time
        logging.info(f"Finished Grailed job in {elapsed_time:.2f}s.")
        return listings if not listings.empty else pd.DataFrame(columns=["title", "price", "size", "url"])

# Example usage
df = query("rick owens geobasket", True)
df.to_csv('results.csv', index=False)
logging.info("Results saved to CSV file.")