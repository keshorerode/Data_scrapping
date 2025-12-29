import json
import time
import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Ensure output handles unicode
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

def scrape_zomato_paginated():
    order_url = "https://www.zomato.com/erode/kongu-parota-stall-asokapuram/order"
    reviews_url = "https://www.zomato.com/erode/kongu-parota-stall-asokapuram/reviews"
    
    options = Options()
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    # Bypass webdriver detection
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
    })
    
    final_data = {}
    
    try:
        # --- PART 1: ORDER PAGE (Menu Items) ---
        print(f"Navigating to Order Page: {order_url}")
        driver.get(order_url)
        time.sleep(8)
        
        # Clear overlays
        driver.execute_script("document.querySelectorAll('[class*=\"modal\"], [class*=\"overlay\"]').forEach(el => el.remove());")
        
        print("Scrolling to load menu...")
        for _ in range(10):
            driver.execute_script("window.scrollTo(0, window.scrollY + 800);")
            time.sleep(1.2)
        
        # Restaurant Info
        info = {}
        try:
            info["name"] = driver.find_element(By.XPATH, "//h1").text.strip()
            info["address"] = driver.find_element(By.XPATH, "//section//div[contains(@id,\"address\")] | //section//div[contains(@class,\"sc-\") and contains(text(), \"erode\")] | //h1/../following-sibling::div").text.split("\n")[0].strip()
        except:
            pass
        final_data["restaurant_info"] = info
        
        # Menu items
        menu_items = []
        name_els = driver.find_elements(By.XPATH, "//h4")
        print(f"Found {len(name_els)} potential food items.")
        
        for name_el in name_els:
            try:
                name = name_el.get_attribute("textContent").strip()
                if not name or len(name) < 2: continue
                
                item = {"food_item_name": name, "food_description": "", "food_price": ""}
                
                # Find price and description in proximity
                parent = name_el.find_element(By.XPATH, "./ancestor::div[contains(@class,'sc-')][1]")
                
                # Price search (look for rupee symbol)
                price_els = parent.find_elements(By.XPATH, ".//*[contains(text(), '₹')]")
                if price_els:
                    item["food_price"] = price_els[0].get_attribute("textContent").strip()
                
                # Description (usually a sibling p tag)
                desc_els = parent.find_elements(By.XPATH, ".//p")
                for d in desc_els:
                    d_txt = d.get_attribute("textContent").strip()
                    if d_txt and d_txt != name and "₹" not in d_txt:
                        item["food_description"] = d_txt
                        break
                
                menu_items.append(item)
                print(f"  Captured: {name[:30]} | {item['food_price']}")
            except:
                continue
        
        final_data["food_items"] = menu_items
        
        # --- PART 2: REVIEWS PAGINATION ---
        print(f"\nNavigating to Reviews: {reviews_url}")
        driver.get(reviews_url)
        time.sleep(8)
        
        all_reviews = []
        page = 1
        
        while True:
            print(f"\nScraping Page {page}...")
            
            # Scroll slowly to load reviews
            for s in range(5):
                driver.execute_script(f"window.scrollTo(0, {s * 1000});")
                time.sleep(1)
            
            # Extract reviews
            names = driver.find_elements(By.XPATH, "//p[contains(@class, 'dCAQIv')]")
            comments = driver.find_elements(By.XPATH, "//p[contains(@class, 'hreYiP')] | //p[contains(@class, 'sc-')]")
            ratings = driver.find_elements(By.XPATH, "//div[contains(@class, 'XPLrh')]")
            
            # Narrow down comments - Zomato comments usually follow the reviewer name section
            # For simplicity, we'll use a count-based match or proximity if needed.
            # But let's filter comments that are actually review text (length > 0)
            valid_comments = [c for c in comments if len(c.text.strip()) > 5]
            
            count = min(len(names), len(ratings))
            page_captured = 0
            for i in range(count):
                try:
                    r_name = names[i].text.strip()
                    r_rate = ratings[i].text.split("\n")[0].strip()
                    # Find corresponding comment (simplistic index match for now)
                    r_comm = ""
                    if i < len(valid_comments):
                        r_comm = valid_comments[i].text.strip()
                    
                    rev = {
                        "reviewer_name": r_name,
                        "reviewer_command": r_comm,
                        "review_rating_star": r_rate
                    }
                    
                    if not any(r['reviewer_name'] == r_name and r['reviewer_command'] == r_comm for r in all_reviews):
                        all_reviews.append(rev)
                        page_captured += 1
                except:
                    continue
            
            print(f"  Added {page_captured} new reviews. Total: {len(all_reviews)}")
            
            # Pagination logic per USER request
            print("  Checking for 'Next' button (<a> with SVG title 'chevron-right')...")
            # Force scroll to bottom to reveal pagination
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            
            try:
                # Target: <a> element containing SVG with <title> equal to chevron-right
                next_button_xpath = '//a[.//svg/title[text()="chevron-right"] or .//svg/title[contains(text(),"chevron-right")]]'
                next_buttons = driver.find_elements(By.XPATH, next_button_xpath)
                
                if next_buttons:
                    next_btn = next_buttons[0]
                    if next_btn.is_displayed() and next_btn.is_enabled():
                        print(f"  Next button found. Clicking to page {page + 1}...")
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_btn)
                        time.sleep(1)
                        
                        current_url = driver.current_url
                        try:
                            next_btn.click()
                        except:
                            driver.execute_script("arguments[0].click();", next_btn)
                        
                        # Wait for page content to change
                        page += 1
                        time.sleep(8) # Long wait for next page
                    else:
                        print("  Next button found but not visible/clickable. Terminating.")
                        break
                else:
                    print("  'chevron-right' Next button not present in DOM. Terminating.")
                    break
            except Exception as e:
                print(f"  Pagination check failed: {e}. Terminating.")
                break
        
        final_data["reviews"] = all_reviews
        
        # Final Save
        with open("zomato_data.json", "w", encoding="utf-8") as f:
            json.dump(final_data, f, indent=4, ensure_ascii=False)
        
        print("\n" + "="*40)
        print("EXTRACTION COMPLETE")
        print(f"Captured {len(menu_items)} items and {len(all_reviews)} reviews.")
        print("="*40)
        
    except Exception as e:
        print(f"\nCRITICAL ERROR: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    scrape_zomato_paginated()
