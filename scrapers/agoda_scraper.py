from playwright.sync_api import sync_playwright

def scrape_hotel(url, search_query):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(url)
        page.wait_for_timeout(1000)

        # searching the location
        search = page.locator('#textInput')
        search.fill(search_query)
        
        page.wait_for_timeout(1000)
        page.eval_on_selector(".Popup", "el => el.style.display = 'none'")
        page.wait_for_timeout(10000)
        page.locator('button[data-element-name="search-button"]').click()

        page.wait_for_timeout(1000000)

        browser.close()


# Jalankan script
if __name__ == "__main__":
    scrape_hotel("https://www.agoda.com/id-id/", "Bali")