import json
import time
import sys
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# ------------------ UTF-8 SAFE OUTPUT ------------------
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
except:
    pass

# ------------------ DRIVER SETUP ------------------
options = Options()
options.add_argument("--window-size=1920,1080")
options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
)
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

# Bypass webdriver detection
driver.execute_cdp_cmd(
    "Page.addScriptToEvaluateOnNewDocument",
    {"source": 'Object.defineProperty(navigator,"webdriver",{get:()=>undefined})'}
)

# ------------------ MANUAL LOGIN ------------------
print("\n========================================")
print("LOGIN REQUIRED")
print("Login to Zomato in the opened browser.")
print("========================================\n")

driver.get("https://www.zomato.com/")
input("Press ENTER after successful login...")

# ------------------ LOAD URL LIST ------------------
script_dir = os.path.dirname(os.path.abspath(__file__))
input_path = os.path.join(script_dir, "tir_hotels.txt")

with open(input_path, "r", encoding="utf-8") as f:
    urls = [line.strip() for line in f if line.strip()]
print(f"DEBUG: Loaded {len(urls)} URLs from file.")
if urls:
    print(f"DEBUG: First URL: {urls[0]}")

all_restaurants = []

# ------------------ SCRAPER FUNCTION ------------------
def scrape_restaurant(order_url):
    print(f"\nScraping → {order_url}")
    driver.get(order_url)
    time.sleep(10)

    data = {
        "url": order_url,
        "name": "",
        "address": "",
        "rating": "",
        "rating_count": "",
        "menu": [],
        "reviews": []
    }

    # ---------------- BASIC INFO ----------------
    try:
        data["name"] = driver.find_element(By.TAG_NAME, "h1").text
    except:
        pass

    try:
        data["address"] = driver.find_element(
            By.XPATH,
            '//section[contains(@class,"sc-fQejPQ")]//div[contains(@class,"sc-clNaTc")]'
        ).text
    except:
        pass

    try:
        # Attempt to find rating with class consistent with rating_count
        val = driver.find_element(
            By.XPATH,
            '//*[contains(@class,"sc-1q7bklc-1")]'
        ).text.strip()
        data["rating"] = val
    except:
        try:
            # Fallback to previous selector
            data["rating"] = driver.find_element(
                By.XPATH,
                '//*[contains(@class,"sc-1q722ms-0")]'
            ).text.strip()
        except:
            pass

    try:
        data["rating_count"] = driver.find_element(
            By.XPATH,
            '//*[contains(@class,"sc-1q7bklc-8") and contains(@class,"kEgyiI")]'
        ).text
    except:
        pass

    # ---------------- MENU ----------------
    for _ in range(8):
        driver.execute_script("window.scrollBy(0,800)")
        time.sleep(1)

    menu_cards = driver.find_elements(By.CSS_SELECTOR, "div.sc-jjgyjb")

    for card in menu_cards:
        try:
            name = card.find_element(By.TAG_NAME, "h4").text.strip()
            price = ""
            for span in card.find_elements(By.TAG_NAME, "span"):
                if "₹" in span.text:
                    price = span.text.strip()
                    break

            desc = ""
            ps = card.find_elements(By.TAG_NAME, "p")
            if ps:
                desc = ps[0].text.strip()

            if name:
                data["menu"].append({
                    "food_item_name": name,
                    "food_item_description": desc,
                    "food_price": price
                })
        except:
            continue

    # ---------------- REVIEWS WITH PAGINATION ----------------
    review_url = order_url.replace("/order", "/reviews")
    driver.get(review_url)
    time.sleep(5)

    seen_reviews = set()

    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        reviewer_elements = driver.find_elements(By.CSS_SELECTOR, "p.sc-lenlpJ")

        for name_el in reviewer_elements:
            try:
                card = name_el.find_element(
                    By.XPATH, "./ancestor::div[contains(@class,'sc-nUItV')]"
                )

                reviewer = name_el.text.strip()

                rating = ""
                try:
                    rating = card.find_element(
                        By.CSS_SELECTOR, "div.sc-1q7bklc-10"
                    ).text
                except:
                    pass

                comment = ""
                try:
                    comment = card.find_element(
                        By.CSS_SELECTOR, "p.sc-hfLElm"
                    ).text
                except:
                    pass

                key = (reviewer, comment)
                if key in seen_reviews:
                    continue
                seen_reviews.add(key)

                data["reviews"].append({
                    "reviewer_name": reviewer,
                    "review_rating_star": rating,
                    "reviewer_comment": comment
                })
            except:
                continue

        # ---------- PAGINATION USING YOUR SVG XPATH ----------
        try:
            next_svg_xpath = "//*[name()='svg' and .//*[name()='title' and text()='chevron-right']]"
            next_svg = driver.find_elements(By.XPATH, next_svg_xpath)

            if not next_svg:
                print("    → Review pagination completed.")
                break

            next_btn = next_svg[0].find_element(
                By.XPATH, "ancestor::a | ancestor::button"
            )

            driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});", next_btn
            )
            time.sleep(1)
            driver.execute_script("arguments[0].click();", next_btn)
            time.sleep(4)

        except Exception as e:
            print(f"    → Pagination stopped: {e}")
            break

    print(f"  → Menu: {len(data['menu'])}, Reviews: {len(data['reviews'])}")
    return data

# ------------------ MAIN LOOP ------------------
for i, url in enumerate(urls, 1):
    print(f"\n[{i}/{len(urls)}]")
    try:
        result = scrape_restaurant(url)
        all_restaurants.append(result)

        output_path = os.path.join(script_dir, "tir_multi.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(all_restaurants, f, indent=4, ensure_ascii=False)

    except Exception as e:
        print(f"FAILED → {url} | {e}")

driver.quit()

print("\n========================================")
print("SCRAPING COMPLETED")
print(f"Total restaurants: {len(all_restaurants)}")
print("Saved to: tir_multi.json")
print("========================================")
