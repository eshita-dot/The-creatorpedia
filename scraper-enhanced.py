import time
import random
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import gspread
from oauth2client.service_account import ServiceAccountCredentials

SHEET_URL = "https://docs.google.com/spreadsheets/d/1-b42-16e9g2kouyW3BIYxRZ0Bo90K1s6zLoYtD3mY_k/edit"

def setup_driver():
    """Set up Chrome with anti-detection"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def setup_google_sheets():
    """Connect to Google Sheets"""
    try:
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']
        
        gc = gspread.service_account(filename='credentials.json')
        sheet = gc.open_by_url(SHEET_URL).sheet1
        return sheet
    except Exception as e:
        print(f"Error connecting to sheets: {e}")
        return None

def extract_number(text):
    """Extract numeric value from text like '3.5M' or '125K'"""
    if not text:
        return 0
    
    text = text.replace(',', '').upper().strip()
    
    try:
        if 'M' in text:
            return int(float(text.replace('M', '')) * 1000000)
        elif 'K' in text:
            return int(float(text.replace('K', '')) * 1000)
        else:
            return int(float(text))
    except:
        return 0

def scrape_instagram_profile(driver, username):
    """Scrape Instagram profile"""
    try:
        url = f"https://www.instagram.com/{username}/"
        print(f"  Visiting {url}...")
        driver.get(url)
        time.sleep(random.uniform(5, 8))
        
        profile_data = {
            'name': username,
            'handle': f"@{username}",
            'followers': 0,
            'bio': '',
            'verified': 'No',
            'category': 'Entertainment',
            'location': 'India',
            'language': 'English'
        }
        
        # Try to get follower count from meta tags first (more reliable)
        try:
            meta_content = driver.find_element(By.XPATH, "//meta[@property='og:description']").get_attribute('content')
            if 'Followers' in meta_content:
                parts = meta_content.split('Followers')[0].strip().split()
                if parts:
                    profile_data['followers'] = extract_number(parts[-1])
                    print(f"  Found followers from meta: {profile_data['followers']}")
        except:
            pass
        
        # Fallback: try from page content
        if profile_data['followers'] == 0:
            try:
                # Look for follower count in various possible selectors
                possible_selectors = [
                    "//a[contains(@href, '/followers/')]/span/span",
                    "//a[contains(@href, '/followers/')]/span",
                    "//button[contains(text(), 'followers')]/span",
                    "//*[contains(text(), 'followers')]"
                ]
                
                for selector in possible_selectors:
                    try:
                        elem = driver.find_element(By.XPATH, selector)
                        text = elem.get_attribute('title') or elem.text
                        if text and text.strip():
                            profile_data['followers'] = extract_number(text)
                            if profile_data['followers'] > 0:
                                print(f"  Found followers from page: {profile_data['followers']}")
                                break
                    except:
                        continue
            except Exception as e:
                print(f"  Could not find followers: {e}")
        
        # Get name
        try:
            name_elem = driver.find_element(By.XPATH, "//span[@class='_ap3a _aaco _aacw _aacx _aad7 _aade']")
            if name_elem.text:
                profile_data['name'] = name_elem.text
        except:
            pass
        
        # Get bio
        try:
            bio_elem = driver.find_element(By.XPATH, "//h1[@class='_ap3a _aaco _aacu _aacx _aad6 _aade']")
            if bio_elem.text:
                profile_data['bio'] = bio_elem.text[:200]
        except:
            pass
        
        # Check verification
        try:
            driver.find_element(By.XPATH, "//svg[@aria-label='Verified']")
            profile_data['verified'] = 'Yes'
        except:
            profile_data['verified'] = 'No'
        
        print(f"  ✓ Scraped: {profile_data['name']} - {profile_data['followers']} followers")
        return profile_data
        
    except Exception as e:
        print(f"  Error scraping {username}: {e}")
        return None

def clear_old_scraped_data(sheet):
    """Delete rows with 0 followers (bad scrapes) but keep manual entries"""
    try:
        all_values = sheet.get_all_values()
        rows_to_delete = []
        
        for i, row in enumerate(all_values[1:], start=2):  # Skip header
            if len(row) > 2 and row[2] == '0':  # Follower count column
                rows_to_delete.append(i)
        
        # Delete in reverse order to maintain row numbers
        for row_num in sorted(rows_to_delete, reverse=True):
            sheet.delete_rows(row_num)
            print(f"Deleted row {row_num} (bad data)")
        
        print(f"Cleaned {len(rows_to_delete)} bad rows")
    except Exception as e:
        print(f"Error cleaning sheet: {e}")

def scrape_influencers(usernames):
    """Main scraping function"""
    sheet = setup_google_sheets()
    if not sheet:
        print("Failed to connect to Google Sheets")
        return
    
    print("Cleaning old failed scrapes...")
    clear_old_scraped_data(sheet)
    
    driver = setup_driver()
    print(f"\nStarting to scrape {len(usernames)} influencers...\n")
    
    for i, username in enumerate(usernames, 1):
        print(f"[{i}/{len(usernames)}] Scraping @{username}...")
        profile_data = scrape_instagram_profile(driver, username)
        
        if profile_data and profile_data['followers'] > 0:
            # Build row with correct 35 columns
            row = [
                profile_data['name'],                    # 1. Influencer Name
                profile_data['handle'],                  # 2. Instagram Handle
                profile_data['followers'],               # 3. Follower Count
                profile_data['category'],                # 4. Category
                profile_data['location'],                # 5. Location
                profile_data['language'],                # 6. Language
                '',                                       # 7. Brand Collaborations
                '', '', '',                              # 8-10. Recent Deals
                'Posts, Reels',                          # 11. Content Type
                '3-5%',                                  # 12. Engagement Rate
                f"https://instagram.com/{username}",     # 13. Profile Link
                datetime.now().strftime('%Y-%m-%d %H:%M'), # 14. Last Updated
                profile_data['bio'],                     # 15. Bio/Description
                profile_data['verified'],                # 16. Verified Status
                '', '', '',                              # 17-19. Avg Views/Likes/Comments
                '',                                      # 20. Posting Frequency
                'Instagram',                             # 21. Primary Platform
                '',                                      # 22. Secondary Platforms
                '', '', '',                              # 23-25. Reels/Posts/Stories %
                '', '', '',                              # 26-28. Audience Age/Gender/Location
                '', '',                                  # 29-30. Email/Agency
                '', '', '',                              # 31-33. Sponsored/Affiliate/Gifted Count
                '',                                      # 34. Total Collabs
                ''                                       # 35. First Collab Date
            ]
            
            try:
                sheet.append_row(row)
                print(f"  ✓ Added to sheet: {profile_data['name']}")
            except Exception as e:
                print(f"  ✗ Failed to add to sheet: {e}")
        else:
            print(f"  ✗ Skipped (no data)")
        
        if i < len(usernames):
            delay = random.randint(10, 15)
            print(f"  Waiting {delay}s...\n")
            time.sleep(delay)
    
    driver.quit()
    print("\n✓ Scraping Complete!")

# Test with 5 influencers
INFLUENCERS = ['beerbiceps', 'tanmaybhat', 'mostlysane', 'dollysingh', 'kushkapila']

if __name__ == "__main__":
    print("=" * 60)
    print("Creatorpedia Scraper v4.0 - FIXED")
    print("=" * 60)
    scrape_influencers(INFLUENCERS)
