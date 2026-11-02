"""Helper anti-deteksi — satu-satunya sumber helper stealth di proyek ini.

Dipindahkan apa adanya dari `scrapers/utils/util.py`.
"""

import random
import time

from playwright.sync_api import BrowserContext

# Daftar User-Agent agar terlihat seperti manusia
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
]


def apply_stealth_mode(context: BrowserContext):
    """Versi synchronous untuk menyembunyikan identitas bot."""
    ua = random.choice(USER_AGENTS)

    context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]});
        Object.defineProperty(navigator, 'languages', {get: () => ['id-ID', 'id', 'en-US']});
        Object.defineProperty(navigator, 'platform', {get: () => 'Win32'});
    """)

    context.set_extra_http_headers({
        "User-Agent": ua,
        "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
    })


def random_delay(min_sec=2, max_sec=4):
    """Sleep for a random duration between min_sec and max_sec."""
    time.sleep(random.uniform(min_sec, max_sec))


def simulate_human_mouse(page):
    """Simulate random human-like mouse movements."""
    viewport = page.viewport_size or {"width": 1366, "height": 768}
    width, height = viewport["width"], viewport["height"]
    for _ in range(random.randint(3, 4)):
        x, y = random.randint(0, width), random.randint(0, height)
        page.mouse.move(x, y, steps=random.randint(5, 10))
        time.sleep(random.uniform(0.2, 0.8))
