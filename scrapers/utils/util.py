import random
import time
from playwright.sync_api import BrowserContext

# Daftar User-Agent agar terlihat seperti manusia (Chrome 124-131, up-to-date)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]

# Pasangan WebGL vendor/renderer yang realistis
WEBGL_VENDORS = [
    ("Google Inc. (NVIDIA)", "ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (Intel)", "ANGLE (Intel, Intel(R) UHD Graphics 620 Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (AMD)", "ANGLE (AMD, AMD Radeon RX 580 Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (NVIDIA)", "ANGLE (NVIDIA, NVIDIA GeForce GTX 1650 Direct3D11 vs_5_0 ps_5_0, D3D11)"),
]

STEALTH_SCRIPT = """
// 1. Hapus flag webdriver
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });

// 2. Fake plugins (PluginArray-like)
const pluginData = [
    { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
    { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '' },
    { name: 'Native Client', filename: 'internal-nacl-plugin', description: '' },
];
Object.defineProperty(navigator, 'plugins', {
    get: () => {
        const arr = pluginData.map(p => {
            const plugin = Object.create(Plugin.prototype);
            Object.defineProperties(plugin, {
                name: { value: p.name },
                filename: { value: p.filename },
                description: { value: p.description },
                length: { value: 0 },
            });
            return plugin;
        });
        arr.item = i => arr[i];
        arr.namedItem = name => arr.find(p => p.name === name);
        arr.refresh = () => {};
        Object.defineProperty(arr, 'length', { value: arr.length });
        return arr;
    }
});

// 3. Bahasa & platform
Object.defineProperty(navigator, 'languages', { get: () => ['id-ID', 'id', 'en-US', 'en'] });
Object.defineProperty(navigator, 'platform', { get: () => 'Win32' });
Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });
Object.defineProperty(navigator, 'deviceMemory', { get: () => 8 });

// 4. Tambahkan objek chrome yang biasanya ada di browser asli
if (!window.chrome) {
    window.chrome = {
        app: { isInstalled: false, InstallState: { DISABLED: 'disabled', INSTALLED: 'installed', NOT_INSTALLED: 'not_installed' }, RunningState: { CANNOT_RUN: 'cannot_run', READY_TO_RUN: 'ready_to_run', RUNNING: 'running' } },
        runtime: {
            OnInstalledReason: { CHROME_UPDATE: 'chrome_update', INSTALL: 'install', SHARED_MODULE_UPDATE: 'shared_module_update', UPDATE: 'update' },
            OnRestartRequiredReason: { APP_UPDATE: 'app_update', GC: 'gc', OS_UPDATE: 'os_update' },
            PlatformArch: { ARM: 'arm', ARM64: 'arm64', MIPS: 'mips', MIPS64: 'mips64', X86_32: 'x86-32', X86_64: 'x86-64' },
            PlatformNaclArch: { ARM: 'arm', MIPS: 'mips', MIPS64: 'mips64', X86_32: 'x86-32', X86_64: 'x86-64' },
            PlatformOs: { ANDROID: 'android', CROS: 'cros', LINUX: 'linux', MAC: 'mac', OPENBSD: 'openbsd', WIN: 'win' },
            RequestUpdateCheckStatus: { NO_UPDATE: 'no_update', THROTTLED: 'throttled', UPDATE_AVAILABLE: 'update_available' },
        }
    };
}

// 5. Override Notification permission agar tidak terlihat seperti bot
const originalQuery = window.navigator.permissions.query;
window.navigator.permissions.query = (parameters) =>
    parameters.name === 'notifications'
        ? Promise.resolve({ state: Notification.permission })
        : originalQuery(parameters);

// 6. Spoof WebGL vendor & renderer (nilai di-inject via Python per-page)
(function() {
    const getParam = WebGLRenderingContext.prototype.getParameter;
    const getParam2 = WebGL2RenderingContext ? WebGL2RenderingContext.prototype.getParameter : null;
    const spoof = function(original) {
        return function(param) {
            if (param === 37445) return window.__tvk_webgl_vendor__ || 'Google Inc. (NVIDIA)';
            if (param === 37446) return window.__tvk_webgl_renderer__ || 'ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0, D3D11)';
            return original.call(this, param);
        }
    };
    WebGLRenderingContext.prototype.getParameter = spoof(getParam);
    if (getParam2) WebGL2RenderingContext.prototype.getParameter = spoof(getParam2);
})();

// 7. Canvas fingerprint noise
(function() {
    const toBlob = HTMLCanvasElement.prototype.toBlob;
    const toDataURL = HTMLCanvasElement.prototype.toDataURL;
    const getImageData = CanvasRenderingContext2D.prototype.getImageData;
    const noise = () => Math.floor(Math.random() * 10) - 5;
    CanvasRenderingContext2D.prototype.getImageData = function(x, y, w, h) {
        const data = getImageData.call(this, x, y, w, h);
        for (let i = 0; i < data.data.length; i += 100) { data.data[i] = Math.max(0, Math.min(255, data.data[i] + noise())); }
        return data;
    };
})();
"""

# Viewport yang realistis
VIEWPORTS = [
    {"width": 1920, "height": 1080},
    {"width": 1366, "height": 768},
    {"width": 1440, "height": 900},
    {"width": 1536, "height": 864},
    {"width": 1280, "height": 720},
]


def apply_stealth_mode(context: BrowserContext):
    """
    Menyembunyikan identitas bot dengan menginjeksi berbagai patch anti-deteksi.
    """
    # Injeksi stealth script ke setiap halaman yang dibuka oleh context ini
    context.add_init_script(STEALTH_SCRIPT)


def get_stealth_context_options() -> dict:
    """
    Mengembalikan opsi context browser yang menyerupai pengguna nyata.
    Digunakan saat membuat browser context.
    """
    ua = random.choice(USER_AGENTS)
    viewport = random.choice(VIEWPORTS)
    webgl_vendor, webgl_renderer = random.choice(WEBGL_VENDORS)
    return {
        "user_agent": ua,
        "viewport": viewport,
        "locale": "id-ID",
        "timezone_id": "Asia/Jakarta",
        "extra_http_headers": {
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "Upgrade-Insecure-Requests": "1",
        },
        "_webgl_vendor": webgl_vendor,
        "_webgl_renderer": webgl_renderer,
    }


def random_delay(min_sec=2, max_sec=4):
    """Sleep for a random duration between min_sec and max_sec."""
    time.sleep(random.uniform(min_sec, max_sec))


def simulate_human_mouse(page):
    """Simulate random human-like mouse movements."""
    width, height = page.viewport_size['width'], page.viewport_size['height']
    for _ in range(random.randint(4, 7)):
        x = random.randint(100, width - 100)
        y = random.randint(100, height - 100)
        page.mouse.move(x, y, steps=random.randint(10, 25))
        time.sleep(random.uniform(0.1, 0.6))


def human_type(page, selector: str, text: str):
    """
    Mengetik teks dengan jeda random antar karakter seperti manusia.
    """
    page.click(selector)
    for char in text:
        page.keyboard.type(char)
        time.sleep(random.uniform(0.05, 0.2))