"""
take_screenshots.py
-------------------
Uses Playwright to capture screenshots of every tab in the
GridPulse AI dashboard and saves them to demo/screenshots/.
"""

import time
import os
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:8502"
OUT_DIR  = "demo/screenshots"
os.makedirs(OUT_DIR, exist_ok=True)

TABS = [
    ("Overview",           "01_overview.png"),
    ("Forecast",           "02_forecast.png"),
    ("Asset Health",       "03_asset_health.png"),
    ("Optimization",       "04_optimization.png"),
    ("Before vs After",    "05_before_vs_after.png"),
    ("AI Operator Brief",  "06_operator_brief.png"),
]

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page    = browser.new_page(viewport={"width": 1440, "height": 900})

        print(f"Opening {BASE_URL} ...")
        page.goto(BASE_URL, wait_until="networkidle", timeout=30000)
        time.sleep(4)   # let Streamlit fully render

        # --- normal tabs ---
        for tab_name, fname in TABS:
            try:
                page.get_by_role("tab", name=tab_name).click()
                time.sleep(2)
                path = os.path.join(OUT_DIR, fname)
                page.screenshot(path=path, full_page=True)
                print(f"  saved {path}")
            except Exception as e:
                print(f"  WARN: could not capture '{tab_name}': {e}")

        # --- manual entry (sidebar button) ---
        try:
            page.get_by_role("tab", name="Overview").click()
            time.sleep(1)
            page.get_by_role("button", name="Enter Data Manually").click()
            time.sleep(2)
            path = os.path.join(OUT_DIR, "07_manual_entry.png")
            page.screenshot(path=path, full_page=True)
            print(f"  saved {path}")
        except Exception as e:
            print(f"  WARN: could not capture Manual Entry: {e}")

        # --- adverse counterfactual scenario ---
        try:
            page.get_by_role("tab", name="Overview").click()
            time.sleep(1)
            page.get_by_label("Demo C: Adverse Counterfactual").click()
            time.sleep(3)
            page.get_by_role("tab", name="Before vs After").click()
            time.sleep(2)
            path = os.path.join(OUT_DIR, "08_adverse_counterfactual.png")
            page.screenshot(path=path, full_page=True)
            print(f"  saved {path}")
        except Exception as e:
            print(f"  WARN: could not capture Adverse Counterfactual: {e}")

        # --- run pipeline live log (sidebar) ---
        try:
            page.get_by_role("tab", name="Overview").click()
            page.get_by_label("Live / Latest").click()
            time.sleep(1)
            page.get_by_role("button", name="Run Full Pipeline").click()
            time.sleep(6)   # let some steps complete for a good live-log shot
            path = os.path.join(OUT_DIR, "09_pipeline_live_log.png")
            page.screenshot(path=path, full_page=True)
            print(f"  saved {path}")
        except Exception as e:
            print(f"  WARN: could not capture Pipeline Live Log: {e}")

        browser.close()
        print("Done.")

run()
