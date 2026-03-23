import asyncio
from playwright.async_api import async_playwright

async def test_playwright():
    try:
        print("Starting Playwright...")
        async with async_playwright() as p:
            print("Launching browser...")
            browser = await p.chromium.launch(headless=True) # Use headless for CI/test environment
            print("Browser launched successfully")
            await browser.close()
    except Exception as e:
        print(f"Playwright Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_playwright())
