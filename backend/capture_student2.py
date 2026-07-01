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
            
            # Login as student
            await page.goto("http://localhost:8000/login/", timeout=15000)
            await page.wait_for_load_state("networkidle")
            await page.fill("input[name='username']", "алексеев")
            await page.fill("input[name='password']", "student123")
            async with page.expect_navigation():
                await page.click("button[type='submit']")
            await page.wait_for_load_state("networkidle")
            
            # Student schedule
            await page.goto("http://localhost:8000/student/schedule/", timeout=15000)
            await page.wait_for_load_state("networkidle")
            await page.wait_for_timeout(1000)
            await page.screenshot(path=str(SCREENSHOTS_DIR / "student_schedule.png"), full_page=True)
            print("  student_schedule captured")
            
            # Student grades
            await page.goto("http://localhost:8000/student/grades/", timeout=15000)
            await page.wait_for_load_state("networkidle")
            await page.wait_for_timeout(1000)
            await page.screenshot(path=str(SCREENSHOTS_DIR / "student_grades.png"), full_page=True)
            print("  student_grades captured")
            
            await browser.close()
            print("Done!")
    finally:
        proc.terminate()
        proc.wait()

asyncio.run(main())
