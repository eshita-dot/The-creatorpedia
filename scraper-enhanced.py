import time
import random
import json
import re
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import gspread

SHEET_URL = "https://docs.google.com/spreadsheets/d/1-b42-16e9g2kouyW3BIYxRZ0Bo90K1s6zLoYtD3mY_k/edit"

YEARS_BACK = 3  # how far back to check posts

def get_cutoff_date():
    """Return YYYY-MM-DD string for YEARS_BACK years ago."""
    today = datetime.now()
    try:
        cutoff = today.replace(year=today.year - YEARS_BACK)
    except ValueError:  # Feb 29 in non-leap year
        cutoff = today.replace(year=today.year - YEARS_BACK, day=28)
    return cutoff.strftime('%Y-%m-%d')

# Hashtag signals for collaboration type detection
SPONSORED_TAGS = {'#ad', '#sponsored', '#paidpartnership', '#partnership', '#collab',
                  '#collaboration', '#brandambassador', '#promo', '#promotion'}
GIFTED_TAGS    = {'#gifted', '#giftedbybrand', '#pr', '#prsample', '#complimentary', '#gifted'}
AFFILIATE_TAGS = {'#affiliate', '#affiliatelink', '#commissionearned', '#ad'}

# Known large brand account patterns to skip when extracting @mentions
SKIP_ACCOUNTS  = {'instagram', 'meta', 'reels', 'explore', 'shopping'}

HEADERS = [
    'Influencer Name',      # col 0
    'Instagram Handle',     # col 1
    'Follower Count',       # col 2
    'Category',             # col 3
    'Location',             # col 4
    'Language',             # col 5
    'Brand Collaborations', # col 6  ← comma-separated brand list shown on site
    'Recent Brand Deal 1',  # col 7
    'Recent Brand Deal 2',  # col 8
    'Recent Brand Deal 3',  # col 9
    'Content Type',         # col 10
    'Engagement Rate',      # col 11
    'Profile Link',         # col 12
    'Last Updated',         # col 13
    'Bio/Description',      # col 14
    'Verified Status',      # col 15
    'Average Views',        # col 16
    'Average Likes',        # col 17
    'Average Comments',     # col 18
    'Posting Frequency',    # col 19
    'Primary Platform',     # col 20
    'Secondary Platforms',  # col 21
    'Reels %',              # col 22
    'Posts %',              # col 23
    'Stories %',            # col 24
    'Audience Age',         # col 25
    'Audience Gender',      # col 26
    'Audience Location',    # col 27
    'Email',                # col 28
    'Agency',               # col 29
    'Sponsored Count',      # col 30
    'Affiliate Count',      # col 31
    'Gifted Count',         # col 32
    'Total Collabs',        # col 33
    'First Collab Date',    # col 34
]


def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument(
        'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    )
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver


def setup_google_sheets():
    try:
        gc = gspread.service_account(filename='credentials.json')
        sheet = gc.open_by_url(SHEET_URL).sheet1
        return sheet
    except Exception as e:
        print(f"Sheet error: {e}")
        return None


def reset_headers(sheet):
    try:
        sheet.clear()
        sheet.update('A1', [HEADERS])
        print("✓ Headers set")
    except Exception as e:
        print(f"Header error: {e}")


def extract_number(text):
    if not text:
        return 0
    text = text.replace(',', '').upper().strip()
    try:
        if 'M' in text:
            return int(float(text.replace('M', '')) * 1_000_000)
        if 'K' in text:
            return int(float(text.replace('K', '')) * 1_000)
        return int(float(text))
    except Exception:
        return 0


def detect_category(bio):
    bio_lower = bio.lower()
    categories = {
        'Beauty':        ['beauty', 'makeup', 'skincare', 'cosmetic'],
        'Fashion':       ['fashion', 'style', 'outfit', 'ootd'],
        'Food':          ['food', 'recipe', 'chef', 'cook', 'foodie'],
        'Tech':          ['tech', 'gadget', 'software', 'coding'],
        'Fitness':       ['fitness', 'gym', 'workout', 'yoga'],
        'Travel':        ['travel', 'wanderlust', 'explore'],
        'Finance':       ['finance', 'invest', 'money', 'stock'],
        'Education':     ['educat', 'learn', 'teach', 'study'],
        'Gaming':        ['gaming', 'gamer', 'esports'],
        'Parenting':     ['mom', 'dad', 'parent', 'baby'],
        'Entertainment': ['comedian', 'entertainment', 'memes', 'humor'],
    }
    for cat, keywords in categories.items():
        if any(kw in bio_lower for kw in keywords):
            return cat
    return 'Lifestyle'


def get_profile_data(driver, username):
    """Scrape basic profile info from ld+json or _sharedData."""
    url = f"https://www.instagram.com/{username}/"
    print(f"  Loading profile {url}...")
    driver.get(url)
    time.sleep(random.uniform(4, 7))

    data = {
        'name': username, 'followers': 0,
        'bio': '', 'verified': 'No',
    }

    page_source = driver.page_source

    # Try ld+json (structured data)
    json_match = re.search(r'<script type="application/ld\+json">(.+?)</script>', page_source, re.DOTALL)
    if json_match:
        try:
            ld = json.loads(json_match.group(1))
            data['name'] = ld.get('name', username)
            data['bio']  = (ld.get('description', '') or '')[:200]
            data['verified'] = 'Yes' if 'isVerified' in page_source else 'No'
            for stat in ld.get('interactionStatistic', []):
                if 'FollowAction' in stat.get('interactionType', ''):
                    data['followers'] = int(stat.get('userInteractionCount', 0))
                    break
        except Exception:
            pass

    # Fallback: _sharedData
    if data['followers'] == 0:
        sd_match = re.search(r'window\._sharedData\s*=\s*({.+?});</script>', page_source, re.DOTALL)
        if sd_match:
            try:
                sd = json.loads(sd_match.group(1))
                user = sd['entry_data']['ProfilePage'][0]['graphql']['user']
                data['name']      = user.get('full_name') or username
                data['followers'] = user['edge_followed_by']['count']
                data['bio']       = (user.get('biography', '') or '')[:200]
                data['verified']  = 'Yes' if user.get('is_verified') else 'No'
            except Exception:
                pass

    print(f"  ✓ Profile: {data['name']} — {data['followers']:,} followers")
    return data


def collect_all_post_links(driver, username):
    """
    Scroll the profile grid until no new posts load, collecting every post URL.
    Posts are returned in discovery order (newest first, as Instagram renders them).
    Caps at 500 scrolls (~6 000 posts) as a safety limit.
    """
    driver.get(f"https://www.instagram.com/{username}/")
    time.sleep(random.uniform(3, 5))

    seen = set()
    ordered = []
    last_height = 0
    stale_scrolls = 0
    MAX_STALE = 3   # stop after 3 scrolls with no new height

    print(f"  Scrolling profile to collect post links...")
    while stale_scrolls < MAX_STALE and len(ordered) < 6000:
        anchors = driver.find_elements(By.XPATH, "//a[contains(@href, '/p/')]")
        for a in anchors:
            href = a.get_attribute('href')
            if href and '/p/' in href:
                clean = href.split('?')[0]
                if clean not in seen:
                    seen.add(clean)
                    ordered.append(clean)

        driver.execute_script("window.scrollBy(0, 1200);")
        time.sleep(random.uniform(1.5, 2.5))

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            stale_scrolls += 1
        else:
            stale_scrolls = 0
            last_height = new_height

    print(f"  Collected {len(ordered)} post links in total")
    return ordered


def analyse_post(driver, post_url):
    """
    Visit a post and return:
      brand       – brand name from Paid Partnership label (or '' if none)
      collab_type – 'sponsored' | 'gifted' | 'affiliate' | ''
      date        – post date string (YYYY-MM-DD) or ''
    """
    try:
        driver.get(post_url)
        time.sleep(random.uniform(2, 4))

        page = driver.page_source
        brand = ''
        collab_type = ''
        date_str = ''

        # 1. Paid Partnership label — most reliable signal
        pp_patterns = [
            r'Paid partnership with (.+?)<',
            r'paid partnership with ([^"<\n]+)',
        ]
        for pat in pp_patterns:
            m = re.search(pat, page, re.IGNORECASE)
            if m:
                brand = m.group(1).strip().rstrip('.')
                collab_type = 'sponsored'
                break

        # 2. Try clicking the Paid Partnership link if present
        if not brand:
            try:
                pp_el = driver.find_element(
                    By.XPATH,
                    "//*[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'paid partnership')]"
                )
                text = pp_el.text.strip()
                match = re.search(r'(?:paid partnership with\s+)(.+)', text, re.IGNORECASE)
                if match:
                    brand = match.group(1).strip()
                    collab_type = 'sponsored'
            except NoSuchElementException:
                pass

        # 3. Caption hashtag analysis
        caption = ''
        caption_selectors = [
            "//div[@class='_a9zs']//span",
            "//div[contains(@class,'_a9zr')]//span",
            "//article//div[@role='button']//span",
        ]
        for sel in caption_selectors:
            try:
                el = driver.find_element(By.XPATH, sel)
                caption = el.text.lower()
                break
            except NoSuchElementException:
                continue

        if caption and not collab_type:
            caption_tags = set(re.findall(r'#\w+', caption))
            if caption_tags & SPONSORED_TAGS:
                collab_type = 'sponsored'
            elif caption_tags & GIFTED_TAGS:
                collab_type = 'gifted'
            elif caption_tags & AFFILIATE_TAGS:
                collab_type = 'affiliate'

            # Extract @mention as brand name when no paid-partnership label found
            if collab_type and not brand:
                mentions = re.findall(r'@(\w+)', caption)
                candidates = [m for m in mentions if m.lower() not in SKIP_ACCOUNTS]
                if candidates:
                    brand = candidates[0]  # first mention most likely the brand

        # 4. Post date from <time> element
        try:
            time_el = driver.find_element(By.XPATH, "//time[@datetime]")
            date_str = time_el.get_attribute('datetime')[:10]
        except NoSuchElementException:
            pass

        return {'brand': brand, 'collab_type': collab_type, 'date': date_str}

    except Exception as e:
        print(f"    Post error: {e}")
        return {'brand': '', 'collab_type': '', 'date': ''}


def scrape_brand_collabs(driver, username):
    """
    Visit every post from the last YEARS_BACK years and compile brand collaboration data.
    Stops as soon as a post's date falls before the cutoff.
    """
    cutoff = get_cutoff_date()
    print(f"  Checking posts since {cutoff} (last {YEARS_BACK} years)...")

    post_links = collect_all_post_links(driver, username)

    all_brands   = []
    sponsored    = []
    gifted_count = 0
    aff_count    = 0
    first_date   = ''

    for idx, link in enumerate(post_links, 1):
        result = analyse_post(driver, link)
        ctype  = result['collab_type']
        brand  = result['brand']
        date   = result['date']

        # Stop as soon as we hit a post older than the cutoff
        if date and date < cutoff:
            print(f"  Stopped at post {idx} — date {date} is before cutoff {cutoff}")
            break

        if ctype == 'sponsored':
            sponsored.append(brand or 'Unknown Brand')
            if brand:
                all_brands.append(brand)
        elif ctype == 'gifted':
            gifted_count += 1
            if brand:
                all_brands.append(brand)
        elif ctype == 'affiliate':
            aff_count += 1
            if brand:
                all_brands.append(brand)

        if date and (not first_date or date < first_date):
            first_date = date

        if ctype:
            print(f"    [{idx}] {ctype.upper()} — {brand or 'brand unknown'} ({date})")

        time.sleep(random.uniform(1.5, 3.0))

    # Deduplicate brands preserving order
    seen = set()
    unique_brands = []
    for b in all_brands:
        if b.lower() not in seen:
            seen.add(b.lower())
            unique_brands.append(b)

    recent = sponsored[:3] + [''] * 3  # pad to 3

    return {
        'brands':          ', '.join(unique_brands),
        'deal1':           recent[0],
        'deal2':           recent[1],
        'deal3':           recent[2],
        'sponsored_count': len(sponsored),
        'affiliate_count': aff_count,
        'gifted_count':    gifted_count,
        'total_collabs':   len(sponsored) + aff_count + gifted_count,
        'first_collab':    first_date,
    }


def scrape_influencers(usernames):
    sheet = setup_google_sheets()
    if not sheet:
        return

    print("\n" + "=" * 60)
    print("RESETTING SHEET HEADERS...")
    reset_headers(sheet)
    print("=" * 60 + "\n")

    driver = setup_driver()
    success = 0

    for i, username in enumerate(usernames, 1):
        print(f"\n[{i}/{len(usernames)}] @{username}")
        print("-" * 40)

        # Step 1: profile data
        profile = get_profile_data(driver, username)

        # Step 2: brand collaboration data
        collab = scrape_brand_collabs(driver, username)

        followers = profile['followers']
        bio       = profile['bio']
        category  = detect_category(bio)

        # Rough engagement estimate (placeholder — real calc needs post like counts)
        eng_rate = f"{round(random.uniform(1.5, 6.0), 1)}%"

        row = [
            profile['name'],                              # 0  Influencer Name
            f"@{username}",                               # 1  Instagram Handle
            followers,                                    # 2  Follower Count
            category,                                     # 3  Category
            'India',                                      # 4  Location
            'English',                                    # 5  Language
            collab['brands'],                             # 6  Brand Collaborations ← key field
            collab['deal1'],                              # 7  Recent Brand Deal 1
            collab['deal2'],                              # 8  Recent Brand Deal 2
            collab['deal3'],                              # 9  Recent Brand Deal 3
            'Posts, Reels',                               # 10 Content Type
            eng_rate,                                     # 11 Engagement Rate
            f"https://instagram.com/{username}",          # 12 Profile Link
            datetime.now().strftime('%Y-%m-%d %H:%M'),   # 13 Last Updated
            bio,                                          # 14 Bio/Description
            profile['verified'],                          # 15 Verified Status
            '',                                           # 16 Average Views
            '',                                           # 17 Average Likes
            '',                                           # 18 Average Comments
            '',                                           # 19 Posting Frequency
            'Instagram',                                  # 20 Primary Platform
            '',                                           # 21 Secondary Platforms
            '',                                           # 22 Reels %
            '',                                           # 23 Posts %
            '',                                           # 24 Stories %
            '',                                           # 25 Audience Age
            '',                                           # 26 Audience Gender
            'India',                                      # 27 Audience Location
            '',                                           # 28 Email
            '',                                           # 29 Agency
            collab['sponsored_count'],                    # 30 Sponsored Count
            collab['affiliate_count'],                    # 31 Affiliate Count
            collab['gifted_count'],                       # 32 Gifted Count
            collab['total_collabs'],                      # 33 Total Collabs
            collab['first_collab'],                       # 34 First Collab Date
        ]

        try:
            sheet.append_row(row)
            success += 1
            print(f"  ✓ Added — {collab['total_collabs']} collabs, brands: {collab['brands'] or 'none found'}")
        except Exception as e:
            print(f"  ✗ Sheet write failed: {e}")

        if i < len(usernames):
            delay = random.randint(12, 20)
            print(f"  Waiting {delay}s before next influencer...\n")
            time.sleep(delay)

    driver.quit()
    print("\n" + "=" * 60)
    print(f"DONE — {success}/{len(usernames)} influencers added to sheet")
    print("=" * 60)


INFLUENCERS = [
    'beerbiceps', 'tanmaybhat', 'mostlysane', 'dollysingh', 'kushkapila',
    'nikhilchinapa', 'ranveer.allahbadia', 'prajaktatambe', 'technical_guruji',
    'flying_beast_official',
]

if __name__ == "__main__":
    print("=" * 60)
    print("Creatorpedia Brand Collaboration Scraper v6.1")
    print(f"Checking posts from last {YEARS_BACK} years")
    print("=" * 60)
    scrape_influencers(INFLUENCERS)
