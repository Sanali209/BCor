from playwright.async_api import ProxySettings
from playwright.sync_api import sync_playwright
import time


url = "https://rule34.xxx/"
with sync_playwright() as p:
    proxy_settings = ProxySettings(
        server="socks4://127.0.0.1:9050"
    )
    browser = p.chromium.launch(
        headless=False,
        proxy= proxy_settings,

    )
    page = browser.new_page()
    page.goto(url)
    time.sleep(5)