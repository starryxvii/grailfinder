import spacy
from driver import newDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import StaleElementReferenceException
import time, logging, pandas as pd

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load the spaCy model
nlp = spacy.load('en_core_web_md')

def extract_important_text(text):
    doc = nlp(text.lower())
    keywords = ' '.join(token.text for token in doc if token.pos_ in ['NOUN', 'PROPN', 'NUM'])
    return keywords

def score_similarity(a, b):
    doc1 = nlp(extract_important_text(a))
    doc2 = nlp(extract_important_text(b))
    similarity = doc1.similarity(doc2)

    # Extract numbers to enforce model number accuracy
    numbers_a = set(token.text for token in doc1 if token.like_num)
    numbers_b = set(token.text for token in doc2 if token.like_num)
    if numbers_a != numbers_b:
        similarity -= 0.3  # Penalize if numbers do not match, significant in product model differentiation

    return max(0, similarity)  # Ensure similarity does not go negative

def query(q, headless=False):
    start_time = time.time()
    logging.info("Started Grailed job, initializing browser")
    driver = newDriver(headless)
    logging.info("Browser ready")
    listings = pd.DataFrame(columns=["title", "price", "size", "url"])
    
    def waitForElement(by, q):
        return WebDriverWait(driver, 30).until(EC.presence_of_element_located((by, q)))

    def scroll_down():
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)  # Wait for the page to load more items

    try:
        driver.get("https://grailed.com")
        logging.info("Opened Grailed website")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        searchButton = waitForElement(By.XPATH, '//*[@id="globalHeaderWrapper"]/div/div[1]/form/button')
        searchButton.click()
        logging.info("Clicked on the search button to prompt modal.")
        driver.execute_script("var modals = document.querySelectorAll('.ReactModal__Content--after-open, .modal, .Modal-module__authenticationModal___g7Ufu'); if (modals.length > 0) { modals.forEach(modal => { if (modal.style.display !== 'none') { modal.style.display = 'none'; console.log('Modal closed'); }});}")
        logging.info("Modals handled.")
        searchBox = waitForElement(By.XPATH, '//*[@id="header_search-input"]')
        searchBox.send_keys(q)
        searchBox.send_keys(Keys.ARROW_DOWN)
        correctedText = searchBox.get_attribute("value")
        searchBox.send_keys(Keys.ENTER)
        logging.info(f"Searched for: {correctedText}")

        while True:
            filter = Select(waitForElement(By.CLASS_NAME, 'ais-SortBy-select'))
            filter.select_by_value("Listing_by_low_price_production")
            logging.info("Set filter to sort by low price.")
            try:
                feed = WebDriverWait(driver, 30).until(EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@class, 'feed-item') and not(contains(@class, 'empty-item'))]")))
                logging.info(f"Indexing through {len(feed)} items of \"{correctedText}\".")

                for item in feed:
                    title = item.find_element(By.XPATH, f".//div[3]/div[2]/p").text
                    if score_similarity(title, correctedText) >= 0.85:
                        price = int(item.find_element(By.XPATH, ".//div/div/span[1]").text.lstrip("$").replace(',', ''))
                        size = item.find_element(By.XPATH, ".//div[3]/div[1]/p[2]").text
                        url = item.find_element(By.XPATH, ".//a").get_attribute('href')
                        listings = pd.concat([listings, pd.DataFrame([{"title": title, "price": price, "size": size, "url": url}])], ignore_index=True)
                        if len(listings) >= 5:
                            break

                if len(listings) < 5:
                    scroll_down()
                else:
                    break
            except StaleElementReferenceException:
                logging.warning("Detected stale element reference, refreshing the page.")
                continue

    finally:
        driver.quit()
        elapsed_time = time.time() - start_time
        logging.info(f"Finished Grailed job in {elapsed_time:.2f}s.")
        return listings if not listings.empty else pd.DataFrame(columns=["title", "price", "size", "url"])

# Example usage
df = query("yeezy slides", True)
df.to_csv('results.csv', index=False)
logging.info("Results saved to CSV file.")
