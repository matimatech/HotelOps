import random
import locale

import pandas as pd

from tqdm import tqdm
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright
from utils.util import apply_stealth_mode, random_delay, simulate_human_mouse
from playwright_stealth import Stealth

today = datetime.today()
check_in_date  = (today + timedelta(days=7)).strftime("%-d %B %Y %A")
check_out_date = (today + timedelta(days=8)).strftime("%-d %B %Y %A")
print(check_in_date)
current_datetime = datetime.today()
formatted_datetime = current_datetime.strftime("%Y-%m-%d")


# today = datetime.today()
# check_in_date  = (today + timedelta(days=7)).strftime("%Y-%m-%d")
# check_out_date = (today + timedelta(days=8)).strftime("%Y-%m-%d")

current_datetime = datetime.today()
print(current_datetime)
formatted_datetime = current_datetime.strftime("%Y-%m-%d")


def extract_hotel_info_agoda(item: any) -> object:
    """
    Mengambil informasi terkait hotel dari tiap element item.
    Args:
        item: The hotel item element.
        
    Returns:
        dict/None: A dictionary with hotel details if the hotel matches the criteria, otherwise None.
    """
    try:
        card_element = item.query_selector("[data-element-name='property-card-content']")
        if card_element:
            # Ambil dari ScreenReaderOnly span yang berisi nama hotel
            sr_element = item.query_selector(".ScreenReaderOnly__ScreenReaderOnlyStyled-sc-szxtre-0")
            if sr_element:
                raw_text = sr_element.text_content().strip()
                # Hapus suffix " buka di tab baru"
                hotel_name = raw_text.replace(" buka di tab baru", "").strip()

        address_element = item.query_selector("[data-selenium='area-city-text']")
        if address_element:
            address = item.query_selector(".sc-aXZVg.Typographystyled__TypographyStyled-sc-1uoovui-0.ifcRDN.jUTNZD.TextLink__TextStyled-sc-upxc4y-0.cTuyyX").text_content().strip()
        else:
            address = "N/A"
       
        full_address = address.split(" - ")[0]  # Hasil: "Legian, Bali"

        splited = full_address.split(", ")
        subdistrict = splited[0] if len(splited) > 0 else "N/A"
        regency = splited[1] if len(splited) > 1 else "N/A"   

        # Extract hotel id
        hotel_id_element = item.query_selector("[data-element-name='property-card-content']")
        hotel_id = hotel_id_element.get_attribute("property-id") if hotel_id_element else "N/A"

        # Extract hotel rating
        rating_elements = item.query_selector_all("span")
        rating_text = "N/A"
        for element in rating_elements:
            if "bintang dari 5" in element.text_content():
                rating_text = element.inner_text()
                break
        
        hotel_rating = "N/A"
        if rating_text != "N/A":
            try:
                hotel_rating = rating_text.split(" ")[0]
            except Exception:
                pass
        
        # Extract review count
        review_element = item.query_selector("[data-element-name='property-card-review'] p:last-child")
        review_text = review_element.text_content().strip() if review_element else "N/A"
        # Hasil: "227 ulasan" → ambil angkanya saja
        review_count = ''.join(filter(str.isdigit, review_text)) if review_text != "N/A" else "N/A"
        
        # Extract guest score
        guest_score_element = item.query_selector("[data-element-name='property-card-review'] span.iiiJNz")
        guest_score = guest_score_element.text_content().strip().replace(",", ".") if guest_score_element else "N/A"


        # Extract hotel price
        price_element = item.query_selector("div[data-element-name='final-price'] span[data-selenium='display-price']")
        price_text = price_element.inner_text() if price_element else "N/A"
        hotel_price = "N/A"
        if price_text != "N/A":
            try:
                hotel_price = int(''.join(c for c in price_text if c.isdigit() or c != '.'))
            except Exception:
                pass
        # Extract booking URL
        booking_url_element = item.query_selector("a[data-selenium='hotel-name']")
        booking_url = booking_url_element.get_attribute("href") if booking_url_element else "N/A"
        if booking_url == "N/A":
            booking_url_element = item.query_selector("a[class='PropertyCard__Link']")
            booking_url = booking_url_element.get_attribute("href") if booking_url_element else "N/A"

        # Extract main image URL
        main_image_element = item.query_selector("img[data-element-name='ssrweb-mosaicphotos']")
        main_image_url = main_image_element.get_attribute("src") if main_image_element else "N/A"
        

        if hotel_id == 'N/A' or hotel_name == 'N/A' or hotel_price == 'N/A' or hotel_rating == 'N/A' \
            or subdistrict == 'N/A' or regency == 'N/A' or review_count == 'N/A' or guest_score == 'N/A' \
            or booking_url == 'N/A' or main_image_url == 'NA':
            return None

        return {
            'hotel_id': int(hotel_id),
            'hotel_name': hotel_name,
            'hotel_price': hotel_price,
            'hotel_rating': float(hotel_rating),
            'subdistrict': subdistrict,
            'regency': regency,
            'review_count': int(review_count),
            'guest_score': float(guest_score),
            'booking_url': 'https://www.agoda.com'+ booking_url,
            'image_url': 'https:'+ main_image_url,
            'scraped_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    except Exception as e:
        print(f"Error extracting hotel information: {e}")


def scroll_and_navigate_all_results_tiket(page) -> list:
    """
    Scroll untuk merender seluruh konten tiket.com
    
    Args:
        page: The Playwright page object
        
    Returns:
        list: List of dictionaries containing hotel information
    """   
    hotel_info = [] 
    page_num = 1
    
    while True:
        # Wait for the content container to load
        page.wait_for_selector('[data-testid="srp-main-wrapper"]', timeout=10000)
        print(f"Page {page_num} loaded. Scrolling through results...")

        # Check if search results are empty after setting price filters
        no_results_xpath = "//*[@id='contentContainer']//p[contains(text(), \"We couldn't find any results that match your search criteria\")]"
        if page.is_visible(no_results_xpath, timeout=5000):
            print("No results found anymore")
            break        
        # Scroll down gradually to load all hotels on current page
        last_height = page.evaluate("document.body.scrollHeight")
        current_position = 0
        
        while current_position < last_height:
            # Calculate scroll amount as a percentage of the remaining page
            remaining_height = last_height - current_position
            # Scroll between 15-25% of the remaining height
            scroll_percentage = random.uniform(0.15, 0.20)
            scroll_amount = int(remaining_height * scroll_percentage)
            
            # Ensure we scroll at least a little bit
            scroll_amount = max(scroll_amount, 200)
            
            # Perform the scroll
            page.evaluate(f"window.scrollBy(0, {scroll_amount})")
            current_position += scroll_amount
            
            random_delay(0.5, 1.5)  # Small pause between scrolls
            
            # Check if content has dynamically loaded and increased page height
            new_height = page.evaluate("document.body.scrollHeight")
            if new_height > last_height:
                last_height = new_height
        
        print("Extracting hotel details from current page...")
        hotel_items = page.query_selector_all("//*[@id='contentContainer']//ol[@class='hotel-list-container']//li[@data-selenium='hotel-item']")
        
        for item in tqdm(hotel_items, desc=f"Processing page {page_num}"):
            # ✅ Scroll item ke viewport dulu sebelum extract
            item.scroll_into_view_if_needed()
            page.wait_for_timeout(500)  # tunggu lazy load triggered

            hotel_data = extract_hotel_info_agoda(item)
            if hotel_data:
                hotel_info.append(hotel_data)
                print(f"Added hotel: {hotel_data['hotel_name']} (Rp.{hotel_data['hotel_price']}, {hotel_data['hotel_rating']} stars)")

        print(f"Extracted {len(hotel_info)} matching hotels so far.")

        # Check if "Next" button exists
        next_button_visible = page.is_visible('//*[@id="paginationNext"]')
        if not next_button_visible:
            print("No 'Next' button found. Reached the last page of listings.")
            break
        
        # Click the Next button to go to the next page
        simulate_human_mouse(page)  # Simulate human mouse movement
        print(f"Clicking 'Next' to navigate to page {page_num + 1}...")
        page.click('//*[@id="paginationNext"]')
        
        random_delay(4, 5)  # Wait for the next page to load
        page_num += 1
    
    print(f"Finished navigating through all {page_num} pages of hotel listings.")
    print(f"Total hotels extracted: {len(hotel_info)}")
    random_delay(1, 3)
    
    return hotel_info


def scrape_hotel(url, search_query, check_in_date, check_out_date):
    try:
        with sync_playwright() as p:

            browser = p.chromium.launch(headless=False)
            context = browser.new_context(
                viewport={"width": 1366, "height": 768},
                locale="id-ID",
                timezone_id="Asia/Makassar",
            )
            
            page = context.new_page()
            Stealth().apply_stealth_sync(page)
            
            page.goto(url)
            page.wait_for_timeout(1000)

            # searching the location
            page.locator('[data-testid="destination-input"]').click()
            page.wait_for_timeout(1000)
            page.locator('.SearchBox_input_box__NIaen').click()
            search = page.locator('[data-testid="destination-search-box"]')
            search.fill(search_query)
            page.wait_for_timeout(1000)
            
            first_recom = page.locator('[data-testid="hotel-list-item"]').first
            first_recom.click()
          
            page.locator('[data-testid="date-picker"]').click()
            page.wait_for_timeout(1000)
            

            page.locator(f'[aria-label="{check_in_date}"]').click()
            
            page.wait_for_timeout(1000)

            page.locator(f'[aria-label="{check_out_date}"]').click()
            page.wait_for_timeout(1000)

            page.locator(f'[aria-label="search"]').click()
            scraped_data = scroll_and_navigate_all_results_tiket(page)
            scraped_data = pd.DataFrame(scraped_data)

            scraped_data['platform'] = 'tiket'
            scraped_data['city_search'] = search_query
            scraped_data['check_in_date'] = check_in_date   
            scraped_data['check_out_date'] = check_out_date  

            scraped_data.to_csv(
                f'data/raw/{formatted_datetime}-agoda-{location}.csv',
                index=False  
            )
            context.close()
            browser.close()

    except Exception as e:
        print(f"Error during Agoda scraping: {e}")

# Jalankan script
if __name__ == "__main__":
    LOCATIONS = ["Bali", "Yogyakarta", "Jakarta"]
    for location in LOCATIONS:
        scrape_hotel("https://www.tiket.com/en-id/hotel", location, check_in_date, check_out_date)