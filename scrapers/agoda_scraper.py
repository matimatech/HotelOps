import pandas as pd

from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright
from utils.util import apply_stealth_mode, scroll_and_navigate_all_results_agoda
today = datetime.today()
check_in_date  = (today + timedelta(days=7)).strftime("%Y-%m-%d")
check_out_date = (today + timedelta(days=8)).strftime("%Y-%m-%d")

current_datetime = datetime.today()
formatted_datetime = current_datetime.strftime("%Y-%m-%d")

def scrape_hotel(url, search_query, check_in_date, check_out_date):
    try:
        with sync_playwright() as p:

            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            apply_stealth_mode(context)
            page = context.new_page()
            page.goto(url)
            page.wait_for_timeout(1000)

            # searching the location
            search = page.locator('#textInput')
            search.fill(search_query)
            page.wait_for_timeout(1000)
        
            page.eval_on_selector(".Popup", "el => el.style.display = 'none'")
            page.wait_for_timeout(1000)

            page.locator('[data-selenium="checkInBox"]').click()
            page.wait_for_timeout(1000)

            page.locator(f'[data-selenium-date="{check_in_date}"]').click()
            
            page.wait_for_timeout(1000)

            page.locator(f'[data-selenium-date="{check_out_date}"]').click()
            page.eval_on_selector(".Popup__content_Occupancy", "el => el.style.display = 'none'")
            page.wait_for_timeout(1000)
            print(f"check in {check_in_date}, check out {check_out_date}")
            with context.expect_page() as new_page_info:
                page.click("xpath=//*[@id='Tabs-Container']/button//span[contains(text(),'CARI')]")

            new_page = new_page_info.value
                        
            new_page.wait_for_selector('#textInput')

            scraped_data = scroll_and_navigate_all_results_agoda(new_page)
            scraped_data = pd.DataFrame(scraped_data)

            scraped_data['platform']      = 'agoda'
            scraped_data['city_search']          = search_query
            scraped_data['check_in_date'] = check_in_date   # parameter dari fungsi
            scraped_data['check_out_date'] = check_out_date  # parameter dari fungsi

            scraped_data.to_csv(
                f'data/raw/{formatted_datetime}-agoda-{location}.csv',
                index=False  # ← tambahkan ini juga
            )
            context.close()
            browser.close()

    except Exception as e:
        print(f"Error during Agoda scraping: {e}")

# Jalankan script
if __name__ == "__main__":
    LOCATIONS = ["Bali", "Yogyakarta", "Jakarta"]
    for location in LOCATIONS:
        scrape_hotel("https://www.agoda.com/id-id/", location, check_in_date, check_out_date)