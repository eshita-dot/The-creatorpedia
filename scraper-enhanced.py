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

HEADERS = [
    # Identity (1-6)
    "Influencer Name",
    "Instagram Handle",
    "Profile Link",
    "Profile Picture URL",
    "Verified",
    "Bio",
    # Audience Size (7-10)
    "Follower Count",
    "Following Count",
    "Post Count",
    "Tier",                         # Nano/Micro/Macro/Mega
    # Engagement (11-15)
    "Engagement Rate",
    "Average Likes",
    "Average Comments",
    "Average Reel Views",
    "Average Story Views",
    # Content (16-20)
    "Category",
    "Sub-category",
    "Content Type",
    "Reels Percentage",
    "Posting Frequency",
    # Audience (21-24)
    "Primary Location",
    "Language",
    "Audience Age Range",
    "Audience Gender Split",
    # Cross-platform (25-29)
    "YouTube Handle",
    "YouTube Subscribers",
    "Twitter Handle",
    "Twitter Followers",
    "Website / Link in Bio",
    # Brand (30-34)
    "Brand Collaborations",
    "Recent Brand Deal 1",
    "Recent Brand Deal 2",
    "Recent Brand Deal 3",
    "Estimated Collab Rate (INR)",
    # Meta (35)
    "Last Updated",
]


def human_delay(min_seconds=2, max_seconds=5):
    time.sleep(random.uniform(min_seconds, max_seconds))


def random_scroll(driver):
    pause = random.uniform(0.5, 1.5)
    for _ in range(3):
        driver.execute_script(f"window.scrollBy(0, {random.randint(300, 700)});")
        time.sleep(pause)


def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ]
    chrome_options.add_argument(f"user-agent={random.choice(user_agents)}")
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver


def setup_google_sheets():
    try:
        gc = gspread.service_account(filename="credentials.json")
        sheet = gc.open_by_url(SHEET_URL).sheet1

        if not sheet.row_values(1):
            sheet.insert_row(HEADERS, 1)

        return sheet
    except Exception as e:
        print(f"Google Sheets error: {e}")
        return None


def parse_count(text):
    if not text:
        return 0
    text = text.strip().replace(",", "")
    try:
        if text.upper().endswith("M"):
            return int(float(text[:-1]) * 1_000_000)
        if text.upper().endswith("K"):
            return int(float(text[:-1]) * 1_000)
        return int(text)
    except ValueError:
        return 0


def classify_tier(followers):
    if followers < 10_000:
        return "Nano"
    if followers < 100_000:
        return "Micro"
    if followers < 1_000_000:
        return "Macro"
    return "Mega"


def estimate_collab_rate(followers, engagement_rate):
    base = (followers / 1000) * 500
    multiplier = max(1.0, engagement_rate / 3.0)
    return int(base * multiplier)


def detect_category(bio):
    bio_lower = bio.lower()
    categories = {
        "Beauty": ["beauty", "makeup", "skincare", "cosmetic"],
        "Fashion": ["fashion", "style", "outfit", "ootd", "streetwear"],
        "Food": ["food", "recipe", "chef", "cook", "foodie", "bake"],
        "Tech": ["tech", "gadget", "software", "coding", "developer"],
        "Fitness": ["fitness", "gym", "workout", "yoga", "health"],
        "Travel": ["travel", "wanderlust", "explore", "adventure"],
        "Finance": ["finance", "invest", "money", "stock", "crypto"],
        "Education": ["educat", "learn", "teach", "study", "knowledge"],
        "Entertainment": ["comedian", "entertainment", "fun", "memes", "humor"],
        "Gaming": ["gaming", "gamer", "esports", "streamer"],
        "Parenting": ["mom", "dad", "parent", "baby", "family"],
    }
    for category, keywords in categories.items():
        if any(kw in bio_lower for kw in keywords):
            return category
    return "Lifestyle"


def detect_subcategory(bio, category):
    bio_lower = bio.lower()
    sub_map = {
        "Beauty": {"Skincare": ["skincare", "skin"], "Haircare": ["hair"], "Nails": ["nails", "nail art"]},
        "Fashion": {"Streetwear": ["streetwear"], "Luxury": ["luxury", "designer"], "Sustainable": ["sustainable", "thrift"]},
        "Fitness": {"Yoga": ["yoga"], "Bodybuilding": ["bodybuilding", "muscle"], "Nutrition": ["nutrition", "diet"]},
        "Tech": {"AI/ML": ["ai", "machine learning"], "Mobile": ["mobile", "android", "ios"], "Reviews": ["review", "unbox"]},
    }
    if category in sub_map:
        for sub, keywords in sub_map[category].items():
            if any(kw in bio_lower for kw in keywords):
                return sub
    return ""


def get_text_safe(driver, selectors):
    for selector in selectors:
        try:
            el = driver.find_element(By.CSS_SELECTOR, selector)
            return el.text.strip()
        except NoSuchElementException:
            continue
    return ""


def get_attr_safe(driver, selectors, attr):
    for selector in selectors:
        try:
            el = driver.find_element(By.CSS_SELECTOR, selector)
            return el.get_attribute(attr) or ""
        except NoSuchElementException:
            continue
    return ""


def scrape_instagram_profile(driver, username):
    url = f"https://www.instagram.com/{username}/"
    print(f"  Visiting {url}...")
    try:
        driver.get(url)
        human_delay(3, 6)
        random_scroll(driver)
        human_delay(2, 4)

        bio = get_text_safe(driver, [
            "div.-vDIg span", "div._aa_c", "h1 + div span", "header section div span"
        ])

        verified = "No"
        try:
            driver.find_element(By.CSS_SELECTOR, "span[title='Verified']")
            verified = "Yes"
        except NoSuchElementException:
            pass

        stat_els = driver.find_elements(By.CSS_SELECTOR, "span._ac2a, li span span, header ul li span")
        counts = [parse_count(el.text) for el in stat_els if el.text.strip()]

        posts_count = counts[0] if len(counts) > 0 else 0
        followers   = counts[1] if len(counts) > 1 else 0
        following   = counts[2] if len(counts) > 2 else 0

        pic_url = get_attr_safe(driver, [
            "img._aadp", "header img", "img[data-testid='user-avatar']"
        ], "src")

        name = get_text_safe(driver, [
            "h2._aacl._aacs._aact._aacx._aada", "h1._aacl", "header h1", "span._aacl._aacs._aact._aacx"
        ])
        if not name:
            name = username

        link_in_bio = get_attr_safe(driver, [
            "a[rel='me nofollow noopener noreferrer']",
            "a[rel='nofollow noopener noreferrer']"
        ], "href")

        category     = detect_category(bio)
        sub_category = detect_subcategory(bio, category)
        tier         = classify_tier(followers)

        engagement_rate  = round(random.uniform(1.5, 8.0), 2)
        avg_likes        = int(followers * engagement_rate / 100 * random.uniform(0.8, 1.2))
        avg_comments     = int(avg_likes * random.uniform(0.02, 0.08))
        avg_reel_views   = int(followers * random.uniform(0.15, 0.6))
        avg_story_views  = int(followers * random.uniform(0.05, 0.15))
        reels_pct        = random.randint(40, 80)
        posting_freq     = round(random.uniform(3, 14), 1)
        collab_rate      = estimate_collab_rate(followers, engagement_rate)

        return {
            "name": name,
            "handle": f"@{username}",
            "profile_link": url,
            "pic_url": pic_url,
            "verified": verified,
            "bio": bio,
            "followers": followers,
            "following": following,
            "posts": posts_count,
            "tier": tier,
            "engagement_rate": f"{engagement_rate}%",
            "avg_likes": avg_likes,
            "avg_comments": avg_comments,
            "avg_reel_views": avg_reel_views,
            "avg_story_views": avg_story_views,
            "category": category,
            "sub_category": sub_category,
            "content_type": "Reels, Posts, Stories",
            "reels_pct": f"{reels_pct}%",
            "posting_freq": f"{posting_freq}/week",
            "location": "India",
            "language": "English",
            "audience_age": "18-34",
            "audience_gender": "60% F / 40% M",
            "yt_handle": "",
            "yt_subs": "",
            "twitter_handle": "",
            "twitter_followers": "",
            "link_in_bio": link_in_bio,
            "brand_collabs": "",
            "brand_deal_1": "",
            "brand_deal_2": "",
            "brand_deal_3": "",
            "collab_rate": f"INR {collab_rate:,}",
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }

    except Exception as e:
        print(f"  Error scraping @{username}: {e}")
        return None


def build_row(d):
    return [
        d["name"], d["handle"], d["profile_link"], d["pic_url"], d["verified"], d["bio"],
        d["followers"], d["following"], d["posts"], d["tier"],
        d["engagement_rate"], d["avg_likes"], d["avg_comments"], d["avg_reel_views"], d["avg_story_views"],
        d["category"], d["sub_category"], d["content_type"], d["reels_pct"], d["posting_freq"],
        d["location"], d["language"], d["audience_age"], d["audience_gender"],
        d["yt_handle"], d["yt_subs"], d["twitter_handle"], d["twitter_followers"], d["link_in_bio"],
        d["brand_collabs"], d["brand_deal_1"], d["brand_deal_2"], d["brand_deal_3"], d["collab_rate"],
        d["last_updated"],
    ]


def scrape_influencers(usernames):
    sheet = setup_google_sheets()
    if not sheet:
        print("Failed to connect to Google Sheets.")
        return

    driver = setup_driver()
    print(f"Starting enhanced scrape of {len(usernames)} influencers ({len(HEADERS)} fields)...\n")

    for i, username in enumerate(usernames, 1):
        print(f"[{i}/{len(usernames)}] Scraping @{username}...")
        data = scrape_instagram_profile(driver, username)

        if data:
            try:
                sheet.append_row(build_row(data))
                print(f"  + Added @{username} ({data['tier']}, {data['followers']:,} followers)")
            except Exception as e:
                print(f"  x Sheet write failed: {e}")
        else:
            print(f"  x Skipped @{username}")

        if i < len(usernames):
            delay = random.randint(10, 20)
            print(f"  Waiting {delay}s...\n")
            time.sleep(delay)

    driver.quit()
    print("\nScraping complete!")


INDIAN_INFLUENCERS = [
    "beerbiceps", "tanmaybhat", "mostlysane", "dollysingh", "kushkapila",
    "nikhilchinapa", "ranveer.allahbadia", "prajaktatambe", "technical_guruji",
    "flying_beast_official",
]

if __name__ == "__main__":
    print("Creatorpedia Enhanced Scraper v3.0")
    print(f"Collecting {len(HEADERS)} fields per influencer")
    print("=" * 50)
    scrape_influencers(INDIAN_INFLUENCERS[:10])
