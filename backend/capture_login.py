import asyncio
import subprocess
import sys
import time
from pathlib import Path

DJANGO_DIR = Path(__file__).parent
SCREENSHOTS_DIR = Path(r"C:\Users\Петя\.local\share\opencode\tool-output\screenshots")

async def main():
    print("Starting Django server...")
    proc = subprocess.Popen(
        [sys.executable, "manage.py", "runserver", "8000", "--noreload"],
        cwd=DJANGO_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    time.sleep(3)
    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(viewport={"width": 1280, "height": 900}, locale="ru-RU")
            
            await page.goto("http://localhost:8000/login/", timeout=15000)
            await page.wait_for_load_state("networkidle")
            await page.wait_for_timeout(1000)
            await page.screenshot(path=str(SCREENSHOTS_DIR / "login.png"), full_page=True)
            print("  login captured")
            
            await browser.close()
            print("Done!")
    finally:
        proc.terminate()
        proc.wait()

asyncio.run(main())
