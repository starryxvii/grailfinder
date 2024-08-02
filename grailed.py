from driver import newDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import StaleElementReferenceException
from fuzzywuzzy import fuzz
import time, logging, pandas as pd  

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def scoreSimilarity(a, b):
    # Use token sort ratio and partial ratio to get a comprehensive similarity score
    token_sort_score = fuzz.token_sort_ratio(a, b)  
    partial_ratio_score = fuzz.partial_ratio(a, b)  
    return max(token_sort_score, partial_ratio_score)

def query(q, headless=False):
    start_time = time.time()  # Record the start time
    logging.info("Started Grailed job, initializing browser")
    driver = newDriver(headless)
    logging.info("Browser ready")

    # Initialize an empty DataFrame with defined columns
    listings_df = pd.DataFrame(columns=["title", "price", "size", "url"])

    def waitForElement(by, q):
        return WebDriverWait(driver, 30).until(EC.presence_of_element_located((by, q)))

    try:
        driver.get("https://grailed.com")
        logging.info("Opened Grailed website")
        
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        
        # "Bait" signup modal prompt by clicking on search button
        searchButton = waitForElement(By.XPATH, '//*[@id="globalHeaderWrapper"]/div/div[1]/form/button')
        searchButton.click()
        logging.info("Clicked on the search button to prompt modal.")

        # Close signup modal using JavaScript
        driver.execute_script(
            """
            var modals = document.querySelectorAll('.ReactModal__Content--after-open, .modal, .Modal-module__authenticationModal___g7Ufu');
            if (modals.length > 0) {
                modals.forEach(modal => {
                    if (modal.style.display !== 'none') {
                        modal.style.display = 'none';
                        console.log('Modal closed');
                    }
                });
            }
            """
        )
        logging.info("Modals handled.")

        # Search        
        searchBox = waitForElement(By.XPATH, '//*[@id="header_search-input"]')
        searchBox.send_keys(q)
        searchBox.send_keys(Keys.ARROW_DOWN)
        correctedText = searchBox.get_attribute("value")
        searchBox.send_keys(Keys.ENTER)
        logging.info(f"Searched for: {correctedText}")

        # Handling dynamic changes by re-fetching the items list
        while True:
            try:
                filter = Select(waitForElement(By.CLASS_NAME, 'ais-SortBy-select'))
                filter.select_by_value("Listing_by_low_price_production")
                logging.info("Set filter to sort by low price.")

                feed = WebDriverWait(driver, 30).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@class, 'feed-item') and not(contains(@class, 'empty-item'))]"))
                )
                logging.info(f"Indexing through {len(feed)} items of \"{correctedText}\".")
                for index, _ in enumerate(feed, 1):
                    item = feed[index-1]  # Re-fetch each item to avoid staleness
                    title = item.find_element(By.XPATH, f".//div[3]/div[2]/p").text
                    if scoreSimilarity(title, correctedText) >= 85:
                        price = int(item.find_element(By.XPATH, ".//div/div/span[1]").text.lstrip("$").replace(',', ''))
                        size = item.find_element(By.XPATH, ".//div[3]/div[1]/p[2]").text
                        url = item.find_element(By.XPATH, ".//a").get_attribute('href')
                        listings_df = pd.concat([listings_df, pd.DataFrame([{"title": title, "price": price, "size": size, "url": url}])], ignore_index=True)
                break  # Exit loop if no errors
            except StaleElementReferenceException:
                logging.warning("Detected stale element reference, refreshing the feed list.")
                continue  # Refresh the feed list

    finally:
        driver.quit()
        elapsed_time = time.time() - start_time  # Calculate elapsed time
        logging.info(f"Finished Grailed job in {elapsed_time:.2f}s.")
        return listings_df if not listings_df.empty else pd.DataFrame(columns=["title", "price", "size", "url"])  # Return an empty DataFrame if no listings found

# Example usage
df = query("Jordan 4 Retro Off White Sail", True)
df.to_csv('results.csv', index=False)
logging.info("Results saved to CSV file.")
