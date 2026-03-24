import random
import time

from tqdm import tqdm
from datetime import datetime, timedelta
from playwright.sync_api import BrowserContext

# Daftar User-Agent agar terlihat seperti manusia
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15"
]


def apply_stealth_mode(context: BrowserContext):
    """
    Versi Synchronous untuk menyembunyikan identitas bot.
    """
    ua = random.choice(USER_AGENTS)

    # Injeksi skrip untuk menghapus jejak 'webdriver'
    context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    """)

    # Atur header agar bahasa dan user-agent sesuai
    context.set_extra_http_headers({
        "User-Agent": ua,
        "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7"
    })



def random_delay(min_sec=2, max_sec=4):
    """Sleep for a random duration between min_sec and max_sec."""
    time.sleep(random.uniform(min_sec, max_sec))

def simulate_human_mouse(page):
    """Simulate random human-like mouse movements."""
    width, height = page.viewport_size['width'], page.viewport_size['height']
    for _ in range(random.randint(3, 4)):  # Perform random moves
        x, y = random.randint(0, width), random.randint(0, height)
        page.mouse.move(x, y, steps=random.randint(5, 10))
        time.sleep(random.uniform(0.2, 0.8))  # Random pauses


def extract_hotel_info_agoda(item: any) -> object:
    """
    Mengambil informasi terkait hotel dari tiap element item.
    Args:
        item: The hotel item element.
        star_rating: The target star rating to match.
        min_price: Minimum price filter.
        max_price: Maximum price filter.
        
    Returns:
        dict/None: A dictionary with hotel details if the hotel matches the criteria, otherwise None.
    """
    try:
        hotel_name_element = item.query_selector("a[data-selenium='hotel-name']")
        hotel_name = hotel_name_element.text_content() if hotel_name_element else "N/A"

        if hotel_name == "N/A":
            hotel_name_element = item.query_selector("h3.sc-aXZVg.Typographystyled__TypographyStyled-sc-1uoovui-0.ifcRDN.bCMrPR")
            hotel_name = hotel_name_element.text_content() if hotel_name_element else "N/A"
        
        # extract address

        #TODO: Still Error in address
        address = item.query_selector("span.sc-aXZVg.Typographystyled__TypographyStyled-sc-1uoovui-0.ifcRDN.jUTNZD.TextLink__TextStyled-sc-upxc4y-0.cTuyyX").get_attribute('label')
        print(address)
        full_address = address.split(" - ")[0]  # Hasil: "Legian, Bali"

        splited = full_address.split(", ")

        subdistrict = splited[0]
        regency = splited[1]


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
        
        if hotel_name == 'N/A' or hotel_price == 'N/A' or hotel_rating == 'N/A' or booking_url == 'N/A' or main_image_url == 'NA':
            return None
        
        return {
            'hotel_name': hotel_name,
            'hotel_price': hotel_price,
            'hotel_rating': hotel_rating,
            'subdistrict': subdistrict,
            'regency': regency,
            'booking_url': 'https://www.agoda.com'+ booking_url,
            'image_url': 'https:'+ main_image_url
        }
    
    except Exception as e:
        print(f"Error extracting hotel information: {e}")
 

def scroll_and_navigate_all_results_agoda(page) -> object:
    """
    Continuously scrolls down the page and clicks 'Next' when available
    to load all hotel listings across multiple pages. Extracts hotel information
    that matches the specified criteria.
    
    Args:
        page: The Playwright page object
        city_name: The city being searched
        star_rating: The target star rating to filter by (e.g., "5", "4", "3")
        min_price: The minimum price to filter by (optional)
        max_price: The maximum price to filter by (optional)
        
    Returns:
        list: List of dictionaries containing hotel information
    """   
    hotel_info = [] 
    page_num = 1
    
    while True:
        # Wait for the content container to load
        page.wait_for_selector('//div[@class="container-agoda"]', timeout=10000)
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
            hotel_data = extract_hotel_info_agoda(item)
            if hotel_data:
                hotel_info.append(hotel_data)
                print(f"Added hotel: {hotel_data['hotel_name']} (${hotel_data['hotel_price']}, {hotel_data['hotel_rating']} stars)")
        
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

