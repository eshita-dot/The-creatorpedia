import requests
import json
import time
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

SHEET_URL = "https://docs.google.com/spreadsheets/d/1-b42-16e9g2kouyW3BIYxRZ0Bo90K1s6zLoYtD3mY_k/edit"

def setup_google_sheets():
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']

    gc = gspread.service_account(filename='credentials.json')
    sheet = gc.open_by_url(SHEET_URL).sheet1

    if not sheet.row_values(1):
        headers = [
            'Influencer Name', 'Instagram Handle', 'Follower Count',
            'Category', 'Location', 'Language', 'Brand Collaborations',
            'Recent Brand Deal 1', 'Recent Brand Deal 2', 'Recent Brand Deal 3',
            'Content Type', 'Engagement Rate', 'Profile Link', 'Last Updated'
        ]
        sheet.insert_row(headers, 1)

    return sheet

INDIAN_INFLUENCERS = [
    'malvikasitlani', 'dollysingh', 'prajakta', 'tanmaybhat',
    'kushkapila', 'mostlysane', 'sejal.kumar', 'komalపandey'
]

if __name__ == "__main__":
    print("Creatorpedia Scraper - Manual mode")
    print("Add influencer data to your Google Sheet manually for now")
    sheet = setup_google_sheets()
    print("Google Sheet connected successfully!")
