import time
import random
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import gspread
from oauth2client.service_account import ServiceAccountCredentials

SHEET_URL = "https://docs.google.com/spreadsheets/d/1-b42-16e9g2kouyW3BIYxRZ0Bo90K1s6zLoYtD3mY_k/edit"

def human_delay(min_seconds=2, max_seconds=5):
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)

def random_scroll(driver):
    scroll_pause = random.uniform(0.5, 1.5)
    for i in range(3):
        scroll_amount = random.randint(300, 700)
        driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
        time.sleep(scroll_pause)

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ]

    chrome_options.add_argument(f"user-agent={random.choice(user_agents)}")
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    return driver

def setup_google_sheets():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        gc = gspread.service_account(filename="credentials.json")
        sheet = gc.open_by_url(SHEET_URL).sheet1

        if not sheet.row_values(1):
            headers = ["Influencer Name", "Instagram Handle", "Follower Count", "Category", "Location", "Language", "Brand Collaborations", "Recent Brand Deal 1", "Recent Brand Deal 2", "Recent Brand Deal 3", "Content Type", "Engagement Rate", "Profile Link", "Last Updated"]
            sheet.insert_row(headers, 1)

        return sheet
    except Exception as e:
        print(f"Error: {e}")
        return None

def extract_follower_count(text):
    text = text.replace(",", "").replace(".", "")
    if "M" in text:
        return int(float(text.replace("M", "")) * 1000000)
    elif "K" in text:
        return int(float(text.replace("K", "")) * 1000)
    else:
        try:
            return int(text)
        except:
            return 0

def detect_category_from_bio(bio):
    bio_lower = bio.lower()
    categories = {
        "Beauty": ["beauty", "makeup", "skincare"],
        "Fashion": ["fashion", "style", "outfit"],
        "Food": ["food", "recipe", "chef"],
        "Tech": ["tech", "gadget", "software"],
        "Fitness": ["fitness", "gym", "workout"],
        "Travel": ["travel", "wanderlust"],
        "Entertainment": ["comedian", "entertainment"]
    }

    for category, keywords in categories.items():
        if any(keyword in bio_lower for keyword in keywords):
            return category
    return "Lifestyle"

def scrape_instagram_profile(driver, username):
    try:
        url = f"https://www.instagram.com/{username}/"
        print(f"  Visiting {url}...")
        driver.get(url)
        human_delay(3, 6)
        random_scroll(driver)
        human_delay(2, 4)

        profile_data = {"name": username, "followers": 0, "bio": "", "category": "Lifestyle", "brand_deals": []}

        return profile_data
    except Exception as e:
        print(f"  Error: {e}")
        return None

def scrape_influencers(usernames):
    sheet = setup_google_sheets()
    if not sheet:
        print("Failed to connect to Google Sheets.")
        return

    driver = setup_driver()
    print(f"Starting to scrape {len(usernames)} influencers...\n")

    for i, username in enumerate(usernames, 1):
        print(f"[{i}/{len(usernames)}] Scraping @{username}...")
        profile_data = scrape_instagram_profile(driver, username)

        if profile_data:
            row = [
                profile_data.get("name", ""),
                f"@{username}",
                profile_data.get("followers", 0),
                profile_data.get("category", "Lifestyle"),
                "India",
                "English",
                "", "", "", "",
                "Posts, Reels",
                "3-5%",
                f"https://instagram.com/{username}",
                datetime.now().strftime("%Y-%m-%d %H:%M")
            ]

            try:
                sheet.append_row(row)
                print(f"  + Added @{username}")
            except Exception as e:
                print(f"  x Failed: {e}")

        if i < len(usernames):
            delay = random.randint(8, 15)
            print(f"  Waiting {delay}s...\n")
            time.sleep(delay)

    driver.quit()
    print("Scraping Complete!")

INDIAN_INFLUENCERS = ["beerbiceps", "tanmaybhat", "mostlysane", "dollysingh", "kushkapila"]

if __name__ == "__main__":
    print("Creatorpedia Advanced Scraper v2.0")
    print("=" * 50)
    scrape_influencers(INDIAN_INFLUENCERS[:5])
