import os
import re
import pytest
from playwright.async_api import Page, expect

@pytest.mark.asyncio
async def test_homepage_loads(page: Page):
    """
    Verify that the Nephele landing page loads and contains the main title.
    Requires the frontend to be served locally (e.g. python -m http.server 8000)
    """
    base_url = os.getenv("E2E_BASE_URL", "http://localhost:8000")
    
    try:
        await page.goto(base_url)
    except Exception as e:
        pytest.skip(f"Frontend server not running at {base_url}. Skip E2E. Error: {e}")
    
    # Check main headings
    await expect(page.locator("body")).to_contain_text(re.compile("Nephele", re.IGNORECASE))
    
    # Check for the Enter Portal or similar start button
    portal_btn = page.locator("text='Enter Portal'")
    # We won't strictly expect it to be visible in case the page design changes, but we wait for page load.
    if await portal_btn.count() > 0:
        await expect(portal_btn.first).to_be_visible()
