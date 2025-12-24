# Zomato Data Scraper

This project is a Python-based web scraper designed to extract restaurant data from Zomato. It collects detailed information including restaurant names, addresses, ratings, menu items (with prices and descriptions), and customer reviews.

## Features

- **Automated Scraping**: Iterates through a list of Zomato URLs.
- **Data Extraction**:
  - Restaurant Name, Address, Rating, Rating Count.
  - Full Menu (Item Name, Price, Description).
  - Reviews (Reviewer Name, Rating, Comment).
- **Pagination Handling**: Automatically navigates through review pages.
- **JSON Output**: Saves data in a structured JSON format (`zomato_multi.json`).
- **Resilience**: Includes basic error handling and manual login step to bypass simple bot detection.

## Prerequisites

- Python 3.x
- Google Chrome Browser

## Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/keshorerode/Data_scrapping_Zomato.git
    cd Data_scrapping_Zomato
    ```

2.  Install required Python packages:
    ```bash
    pip install selenium webdriver-manager
    ```

## Usage

1.  **Prepare URL List**:
    Ensure you have a file named `erode_hotels.txt` in the script directory (e.g., `erode zomato/`). Add the Zomato restaurant URLs you want to scrape, one per line.

2.  **Run the Script**:
    Navigate to the directory containing the script and run it:
    ```bash
    cd "erode zomato"
    python zomato.py
    ```

3.  **Manual Login**:
    - The script will launch a Chrome browser window.
    - It will navigate to Zomato.com and pause.
    - **Action Required**: Manually log in to your Zomato account in this window.
    - Once logged in, return to your terminal and press `ENTER` to continue.

4.  **Scraping Process**:
    - The script will visit each URL in your list.
    - Progress is printed to the console.
    - Data is saved incrementally to `zomato_multi.json`.

## Output Structure

The output `zomato_multi.json` will contain a list of restaurant objects:

```json
[
  {
    "url": "https://www.zomato.com/...",
    "name": "Restaurant Name",
    "address": "Restaurant Address",
    "rating": "4.5",
    "rating_count": "100+ Ratings",
    "menu": [
      {
        "food_item_name": "Dish Name",
        "food_item_description": "Description...",
        "food_price": "₹200"
      }
    ],
    "reviews": [
      {
        "reviewer_name": "User Name",
        "review_rating_star": "5",
        "reviewer_comment": "Great food!"
      }
    ]
  }
]
```

## Disclaimer

This tool is for educational purposes only. Please respect Zomato's terms of service and robots.txt.