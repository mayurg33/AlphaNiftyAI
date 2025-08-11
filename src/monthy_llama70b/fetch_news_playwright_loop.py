# src/fetch_news_playwright_loop.py
import os
import csv
import time
from datetime import datetime
from playwright.sync_api import sync_playwright
import urllib.parse

nifty_companies = [
    ("Adani Enterprises Ltd.", "ADANIENT"),
    ("Adani Ports and Special Economic Zone Ltd.", "ADANIPORTS"),
    ("Apollo Hospitals Enterprise Ltd.", "APOLLOHOSP"),
    ("Asian Paints Ltd.", "ASIANPAINT"),
    ("Axis Bank Ltd.", "AXISBANK"),
    ("Bajaj Auto Ltd.", "BAJAJ-AUTO"),
    ("Bajaj Finance Ltd.", "BAJFINANCE"),
    ("Bajaj Finserv Ltd.", "BAJAJFINSV"),
    ("Bharat Petroleum Corporation Ltd.", "BPCL"),
    ("Bharti Airtel Ltd.", "BHARTIARTL"),
    ("Britannia Industries Ltd.", "BRITANNIA"),
    ("Cipla Ltd.", "CIPLA"),
    ("Coal India Ltd.", "COALINDIA"),
    ("Divi's Laboratories Ltd.", "DIVISLAB"),
    ("Dr. Reddy's Laboratories Ltd.", "DRREDDY"),
    ("Eicher Motors Ltd.", "EICHERMOT"),
    ("Grasim Industries Ltd.", "GRASIM"),
    ("HCL Technologies Ltd.", "HCLTECH"),
    ("HDFC Bank Ltd.", "HDFCBANK"),
    ("HDFC Life Insurance Company Ltd.", "HDFCLIFE"),
    ("Hero MotoCorp Ltd.", "HEROMOTOCO"),
    ("Hindalco Industries Ltd.", "HINDALCO"),
    ("Hindustan Unilever Ltd.", "HINDUNILVR"),
    ("ICICI Bank Ltd.", "ICICIBANK"),
    ("ITC Ltd.", "ITC"),
    ("IndusInd Bank Ltd.", "INDUSINDBK"),
    ("Infosys Ltd.", "INFY"),
    ("JSW Steel Ltd.", "JSWSTEEL"),
    ("Kotak Mahindra Bank Ltd.", "KOTAKBANK"),
    ("LTIMindtree Ltd.", "LTIM"),
    ("Larsen & Toubro Ltd.", "LT"),
    ("Mahindra & Mahindra Ltd.", "M&M"),
    ("Maruti Suzuki India Ltd.", "MARUTI"),
    ("NTPC Ltd.", "NTPC"),
    ("Nestle India Ltd.", "NESTLEIND"),
    ("Oil & Natural Gas Corporation Ltd.", "ONGC"),
    ("Power Grid Corporation of India Ltd.", "POWERGRID"),
    ("Reliance Industries Ltd.", "RELIANCE"),
    ("SBI Life Insurance Company Ltd.", "SBILIFE"),
    ("Shriram Finance Ltd.", "SHRIRAMFIN"),
    ("State Bank of India", "SBIN"),
    ("Sun Pharmaceutical Industries Ltd.", "SUNPHARMA"),
    ("Tata Consultancy Services Ltd.", "TCS"),
    ("Tata Consumer Products Ltd.", "TATACONSUM"),
    ("Tata Motors Ltd.", "TATAMOTORS"),
    ("Tata Steel Ltd.", "TATASTEEL"),
    ("Tech Mahindra Ltd.", "TECHM"),
    ("Titan Company Ltd.", "TITAN"),
    ("UltraTech Cement Ltd.", "ULTRACEMCO"),
    ("Wipro Ltd.", "WIPRO")
    ]
    

def get_month_range():
    return  [f"2025-{str(m).zfill(2)}" for m in range(6, 7)]

def scrape_month(company_name, symbol, start_date, end_date, page):
    query = f"{company_name} financial news after:{start_date} before:{end_date}"
    encoded = urllib.parse.quote_plus(query)
    page.goto(f"https://www.google.com/search?q={encoded}&tbm=nws")
    time.sleep(3)
    data = []

    articles = page.query_selector_all('div.SoAPf')
    for article in articles:
        try:
            heading = article.query_selector('div.n0jPhd').inner_text()
            source = article.query_selector('div.MgUUmf span').inner_text()
            date = article.query_selector('div.OSrXXb').inner_text()
            data.append([heading, source, date, symbol])
        except:
            continue
    return data

def fetch_news_for_all_months():
    months = get_month_range()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        for month in months:
            year, m = map(int, month.split("-"))
            next_month = datetime(year + (m // 12), (m % 12) + 1, 1)
            start_date = f"{year}-{str(m).zfill(2)}-01"
            end_date = next_month.strftime("%Y-%m-%d")
            for company_name, symbol in nifty_companies:
                print(f"[SCRAPE] {company_name} | {month}")
                page = browser.new_page()
                try:
                    news = scrape_month(company_name, symbol, start_date, end_date, page)
                except Exception as e:
                    print(f"[ERROR] scraping {symbol}: {e}")
                    news = []
                # page.close()
                time.sleep(5)
                save_dir = f"data/news/{month}"
                os.makedirs(save_dir, exist_ok=True)
                save_path = os.path.join(save_dir, f"{symbol}.csv")
                with open(save_path, mode='w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Heading', 'Source', 'Date', 'Symbol'])
                    writer.writerows(news)
                print(f"[OK] Saved {len(news)} articles to {save_path}")
        browser.close()

# if __name__ == "__main__":
fetch_news_for_all_months()
