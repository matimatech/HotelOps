import time
import random
import pandas as pd

from datetime import datetime

from playwright.sync_api import sync_playwright
from utils import apply_stealth_mode, scroll_and_navigate_all_results_agoda


current_datetime = datetime.now()

formatted_datetime = current_datetime.strftime("%Y-%m-%d")

def scrape_hotel(url, search_query):
    try:
        with sync_playwright() as p:

            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            # apply_stealth_mode(context)
            page = context.new_page()
            page.goto(url)
            page.wait_for_timeout(1000)

            # searching the location
            search = page.locator('#textInput')
            search.fill(search_query)
            page.wait_for_timeout(1000)
        
            page.eval_on_selector(".Popup", "el => el.style.display = 'none'")
            page.wait_for_timeout(1000)
            with context.expect_page() as new_page_info:
                page.click("xpath=//*[@id='Tabs-Container']/button//span[contains(text(),'CARI')]")

            new_page = new_page_info.value
                        
            new_page.wait_for_selector('#textInput')

            scraped_data = scroll_and_navigate_all_results_agoda(new_page)
            scraped_data = pd.DataFrame(scraped_data)
            scraped_data.to_csv(f'data/raw/{formatted_datetime}-agoda.csv')

            context.close()
            browser.close()

    except Exception as e:
        print(f"Error during Agoda scraping: {e}")

# Jalankan script
if __name__ == "__main__":
    scrape_hotel("https://www.agoda.com/id-id/", "Makassar")