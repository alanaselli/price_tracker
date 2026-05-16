import argparse
import json
import os
import requests
import smtplib
import time
import schedule
from dotenv import load_dotenv
from urllib.parse import urlparse, parse_qs
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- Configuration ---
load_dotenv()

DB_FILE = "tracked_items.json"
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}

# --- Database Functions ---
def get_tracked_items():
    """Loads items from GitHub Secret (JSON or comma-separated), falls back to local JSON."""
    secret_items = os.environ.get("TRACKED_ITEMS_SECRET")
    
    if secret_items:
        try:
            # 1. First, try to read the Secret as a JSON array (your current setup)
            urls = json.loads(secret_items)
            if isinstance(urls, list) and urls:
                print(f"☁️  Loaded {len(urls)} items from GitHub Secret (JSON format).")
                return urls
        except json.JSONDecodeError:
            # 2. If it's not valid JSON, fall back to the comma-separated method
            print("⚠️  Secret is not valid JSON. Attempting comma-separated text...")
            urls = [url.strip() for url in secret_items.split(",") if url.strip()]
            if urls:
                print(f"☁️  Loaded {len(urls)} items from GitHub Secret (Text format).")
                return urls

    # 3. Fallback to local JSON file if no Secret is found
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            urls = json.load(f)
            print(f"💻 Loaded {len(urls)} items from local {DB_FILE}.")
            return urls
            
    return []

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

# --- Core Logic ---
def check_item(target_url):
    try:
        parsed_url = urlparse(target_url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
        query_params = parse_qs(parsed_url.query)
        target_variant_id = query_params.get('variant', [None])[0]

        if not target_variant_id:
            return f"❌ Missing variant ID in URL: {target_url}"

        response = requests.get(base_url + ".js", headers=HEADERS, timeout=10)
        response.raise_for_status()
        product_data = response.json()

        for variant in product_data.get('variants', []):
            if str(variant['id']) == target_variant_id:
                title = variant.get('title')
                price = variant.get('price')
                compare_price = variant.get('compare_at_price')
                available = variant.get('available')

                if available and compare_price and compare_price > price:
                    send_email(target_url, title)
                    return f"✅ ALERT: {title} is on sale and in stock!"
                return f"ℹ️ {title}: In stock: {available}, On sale: {bool(compare_price and compare_price > price)}"
        
        return "❌ Variant not found in product data."
    except Exception as e:
        return f"❌ Error checking {target_url}: {e}"

def send_email(url, title):
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    msg['Subject'] = f"🚨 Price Drop: {title}"
    body = f"The item '{title}' is now on sale and in stock!\n\nBuy here: {url}"
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
    except Exception as e:
        print(f"Email failed: {e}")

def run_all_checks():
    print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] Starting daily check...")
    items = get_tracked_items()
    
    if not items:
        print("No items to track. Please add items locally or via GitHub Secrets.")
        return

    for item in items:
        result = check_item(item)
        print(result)

# --- CLI Setup ---
def main():
    parser = argparse.ArgumentParser(description="E-commerce Price Tracker CLI")
    parser.add_argument("--add-item", type=str, help="Add a product URL to track")
    parser.add_argument("--remove-item", type=int, help="Remove an item by its index number")
    parser.add_argument("--list-items", action="store_true", help="List all tracked items")
    parser.add_argument("--serve", action="store_true", help="Start the daily scheduler loop")
    parser.add_argument("--check-now", action="store_true", help="Run checks once and exit (For GitHub Actions)")
    
    args = parser.parse_args()

    # We only load the JSON explicitly here so local management still edits the file properly
    local_items = []
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            local_items = json.load(f)

    if args.add_item:
        if args.add_item not in local_items:
            local_items.append(args.add_item)
            save_db(local_items)
            print(f"Added: {args.add_item}")
        else:
            print("Item is already being tracked.")

    elif args.remove_item is not None:
        try:
            removed = local_items.pop(args.remove_item)
            save_db(local_items)
            print(f"Removed: {removed}")
        except IndexError:
            print("Invalid index. Use --list-items to see IDs.")

    elif args.list_items:
        print("\n--- Currently Tracked Items ---")
        for i, url in enumerate(local_items):
            print(f"[{i}] {url}")

    elif args.serve:
        print("Scheduler started. Checking daily at 09:00 AM. Press Ctrl+C to stop.")
        schedule.every().day.at("09:00").do(run_all_checks)
        # Run once on startup
        run_all_checks()
        while True:
            schedule.run_pending()
            time.sleep(60)

    elif args.check_now:
        run_all_checks()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()