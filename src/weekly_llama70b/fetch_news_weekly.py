# src/fetch_weekly_news_playwright.py

import os
import csv
import time
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path
from playwright.sync_api import sync_playwright

nifty_companies = [
    ("Adani Enterprises Ltd.", "ADANIENT"),
    ("Adani Ports and Special Economic Zone Ltd.", "ADANIPORTS"),
    ("Apollo Hospitals Enterprise Ltd.", "APOLLOHOSP"),
    # add rest as needed
]

output_base = Path("data/news/weekly")
output_base.mkdir(parents=True, exist_ok=True)

# Generate weekly date ranges (Monday to Sunday)
def get_week_ranges():
    sundays = []
    current = datetime(2024, 3, 3)
    end = datetime(2025, 6, 1)
    while current <= end:
        sunday = current
        monday = sunday - timedelta(days=6)
        sundays.append((monday.strftime("%Y-%m-%d"), sunday.strftime("%Y-%m-%d"), sunday.strftime("%Y-%m-%d")))
        current += timedelta(days=7)
    return sundays

def scrape_news_for_week(company_name, symbol, start_date, end_date, page):
    query = f"{company_name} financial news from {start_date} to {end_date}"
    encoded_query = urllib.parse.quote_plus(query)
    url = f"https://www.google.com/search?q={encoded_query}&tbm=nws"
    page.goto(url)
    time.sleep(3)

    articles = page.query_selector_all('div.SoAPf')
    results = []

    for article in articles:
        try:
            heading = article.query_selector('div.n0jPhd').inner_text()
            source = article.query_selector('div.MgUUmf span').inner_text()
            date = article.query_selector('div.OSrXXb').inner_text()
            results.append([heading, source, date, symbol])
        except:
            continue
    return results

def fetch_weekly_news():
    weeks = get_week_ranges()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        for company_name, symbol in nifty_companies:
            page = browser.new_page()
            for mon_date, sun_date, folder_date in weeks:
                print(f"[SCRAPE] {symbol} => {mon_date} to {sun_date}")
                try:
                    news = scrape_news_for_week(company_name, symbol, mon_date, sun_date, page)
                    if not news:
                        continue

                    out_dir = output_base / folder_date
                    out_dir.mkdir(parents=True, exist_ok=True)
                    out_file = out_dir / f"{symbol}.csv"

                    with open(out_file, mode='w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow(["Heading", "Source", "Date", "Symbol"])
                        writer.writerows(news)

                    print(f"[OK] {symbol} → {folder_date} | {len(news)} articles")
                except Exception as e:
                    print(f"[ERROR] {symbol} - {folder_date}: {e}")
                time.sleep(2)
            page.close()
        browser.close()

if __name__ == "__main__":
    fetch_weekly_news()
