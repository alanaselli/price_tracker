# Price Tracker CLI

A lightweight Python-based tool to monitor product prices on Shopify e-commerce sites and send email alerts when a sale is detected.

## Features

- **Automated Monitoring:** Checks prices daily at a scheduled time.
- **Shopify Integration:** Specifically designed to work with Shopify's product JSON endpoints.
- **Variant Support:** Tracks specific product variants (e.g., size or color).
- **Email Notifications:** Sends alerts directly to your inbox when an item is on sale and in stock.
- **Simple CLI:** Easy-to-use commands to manage your tracked items.

## Prerequisites

- Python 3.12+
- A Gmail account (or any SMTP-capable email) for sending notifications.

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd price_tracker
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

The tool uses environment variables for secure configuration. Create a `.env` file in the root directory:

```env
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_app_password
RECEIVER_EMAIL=recipient_email@gmail.com
```

*Note: If using Gmail, you will need to generate an **App Password**.*

## Usage

### Add a Product to Track
Provide the full URL of the Shopify product variant.
```bash
python tracker.py --add-item "https://example.com/products/item?variant=12345"
```

### List Tracked Items
See all currently monitored URLs and their indices.
```bash
python tracker.py --list-items
```

### Remove a Product
Remove an item from tracking using its index from the list.
```bash
python tracker.py --remove-item 0
```

### Start the Scheduler
Run the tool in the background to perform daily checks (default: 09:00 AM).
```bash
python tracker.py --serve
```

## How It Works

The tool appends `.js` to the product URL to fetch the official Shopify JSON data. It then compares the current `price` with the `compare_at_price`. If the item is in stock and the current price is lower than the comparison price, it triggers an email alert.
