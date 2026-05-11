import time
import random
import json
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import gspread
from oauth2client.service_account import ServiceAccountCredentials

SHEET_URL = "https://docs.google.com/spreadsheets/d/1-b42-16e9g2kouyW3BIYxRZ0Bo90K1s6zLoYtD3mY_k/edit"

def setup_driver():
    """Set up Chrome"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def setup_google_sheets():
    """Connect to Google Sheets"""
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        gc = gspread.service_account(filename='credentials.json')
        sheet = gc.open_by_url(SHEET_URL).sheet1
        return sheet
    except Exception as e:
        print(f"Sheet error: {e}")
        return None

def extract_instagram_json(driver, username):
    """Extract profile data from Instagram's JSON in page source"""
    try:
        url = f"https://www.instagram.com/{username}/"
        print(f"  Loading {url}...")
        driver.get(url)
        time.sleep(random.uniform(4, 7))

        # Get page source and extract JSON
        page_source = driver.page_source

        # Instagram embeds profile data in <script type="application/ld+json">
        json_match = re.search(r'<script type="application/ld\+json">(.+?)</script>', page_source)

        if json_match:
            json_data = json.loads(json_match.group(1))

            # Extract from structured data
            name = json_data.get('name', username)
            description = json_data.get('description', '')

            # Get followers from interactionStatistic
            followers = 0
            if 'interactionStatistic' in json_data:
                for stat in json_data['interactionStatistic']:
                    if stat.get('@type') == 'InteractionCounter':
                        if 'FollowAction' in stat.get('interactionType', ''):
                            followers = int(stat.get('userInteractionCount', 0))
                            break

            print(f"  ✓ Found: {name} - {followers:,} followers")

            return {
                'name': name,
                'followers': followers,
                'bio': description[:200] if description else '',
                'verified': 'Yes' if 'isVerified' in page_source else 'No'
            }

        # Fallback: try to find _sharedData
        shared_data_match = re.search(r'window\._sharedData = ({.+?});</script>', page_source)
        if shared_data_match:
            shared_data = json.loads(shared_data_match.group(1))
            user_data = shared_data['entry_data']['ProfilePage'][0]['graphql']['user']

            return {
                'name': user_data['full_name'] or username,
                'followers': user_data['edge_followed_by']['count'],
                'bio': user_data['biography'][:200] if user_data.get('biography') else '',
                'verified': 'Yes' if user_data.get('is_verified') else 'No'
            }

    except Exception as e:
        print(f"  ✗ Error: {e}")
        return None

def clear_sheet(sheet):
    """Delete all rows except header"""
    try:
        all_values = sheet.get_all_values()
        if len(all_values) > 1:
            sheet.delete_rows(2, len(all_values))
            print("✓ Cleared old data")
    except Exception as e:
        print(f"Clear error: {e}")

def reset_headers(sheet):
    """Reset correct headers"""
    headers = [
        'Influencer Name', 'Instagram Handle', 'Follower Count', 'Category', 'Location',
        'Language', 'Brand Collaborations', 'Recent Brand Deal 1', 'Recent Brand Deal 2',
        'Recent Brand Deal 3', 'Content Type', 'Engagement Rate', 'Profile Link', 'Last Updated',
        'Bio/Description', 'Verified Status', 'Average Views', 'Average Likes', 'Average Comments',
        'Posting Frequency', 'Primary Platform', 'Secondary Platforms', 'Reels %', 'Posts %',
        'Stories %', 'Audience Age', 'Audience Gender', 'Audience Location', 'Email', 'Agency',
        'Sponsored Count', 'Affiliate Count', 'Gifted Count', 'Total Collabs', 'First Collab Date'
    ]

    try:
        sheet.clear()
        sheet.update('A1:AI1', [headers])
        print("✓ Headers reset")
    except Exception as e:
        print(f"Header error: {e}")

def scrape_influencers(usernames):
    """Main scraping"""
    sheet = setup_google_sheets()
    if not sheet:
        return

    print("\n" + "="*60)
    print("RESETTING SHEET...")
    print("="*60)
    reset_headers(sheet)

    driver = setup_driver()
    print(f"\nSCRAPING {len(usernames)} INFLUENCERS...\n")

    success_count = 0

    for i, username in enumerate(usernames, 1):
        print(f"[{i}/{len(usernames)}] @{username}")

        profile = extract_instagram_json(driver, username)

        if profile and profile['followers'] > 0:
            row = [
                profile['name'], f"@{username}", profile['followers'],
                'Entertainment', 'India', 'English', '', '', '', '',
                'Posts, Reels', '3-5%', f"https://instagram.com/{username}",
                datetime.now().strftime('%Y-%m-%d %H:%M'),
                profile['bio'], profile['verified'],
                '', '', '', '', 'Instagram', '', '', '', '',
                '', '', '', '', '', '', '', '', '', ''
            ]

            try:
                sheet.append_row(row)
                success_count += 1
                print(f"  ✓ Added: {profile['name']}")
            except Exception as e:
                print(f"  ✗ Sheet error: {e}")
        else:
            print(f"  ✗ Failed to scrape")

        if i < len(usernames):
            delay = random.randint(8, 12)
            print(f"  Waiting {delay}s...\n")
            time.sleep(delay)

    driver.quit()

    print("\n" + "="*60)
    print(f"COMPLETE! Added {success_count}/{len(usernames)} influencers")
    print("="*60)

INFLUENCERS = ['beerbiceps', 'tanmaybhat', 'mostlysane', 'dollysingh', 'kushkapila']

if __name__ == "__main__":
    scrape_influencers(INFLUENCERS)
