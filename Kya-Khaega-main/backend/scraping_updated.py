import csv
import logging
import time
from typing import List, Dict

from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# ─── Configuration ──────────────────────────────────────────────────────────────
CITY_RESTAURANTS_URL = "https://www.zomato.com/pune/restaurants"  # Changed to broader Pune area
OUTPUT_CSV = "pune_zomato_restaurants_updated.csv"
SCROLL_PAUSE = 4.0  # seconds - increased for better loading
MAX_SCROLL_LOOPS = 800  # even higher limit to capture ~738 restaurants
TIMEOUT = 30  # increased timeout

# ─── Logging Setup ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)


def init_driver(headless: bool = False) -> webdriver.Chrome:
    """Initialize Chrome WebDriver with optional headless mode."""
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option('useAutomationExtension', False)
    opts.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=opts)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.set_window_size(1920, 1080)
    return driver


def find_restaurant_elements(driver):
    """Try to find restaurant elements using various selectors."""
    possible_selectors = [
        # Modern Zomato selectors
        "div[data-testid='restaurant-card']",
        "[data-testid='res-card']",
        ".sc-1mo3ldo-0",
        ".sc-1s0saks-17",
        
        # Generic restaurant card selectors
        "div[class*='restaurant']",
        "div[class*='card']",
        "article",
        "div[role='article']",
        
        # Fallback selectors
        "a[href*='/restaurant/']",
        "div.col-s-16",
        ".res-card",
        
        # Very generic fallback
        "div[class*='sc-']"
    ]
    
    for selector in possible_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                logging.info(f"Found {len(elements)} elements with selector: {selector}")
                # Filter elements that seem to contain restaurant data
                restaurant_elements = []
                for el in elements:
                    try:
                        text = el.text.lower()
                        # Check if element contains restaurant-like content
                        if any(keyword in text for keyword in ['₹', 'cuisine', 'delivery', 'rating', 'min']):
                            restaurant_elements.append(el)
                    except:
                        continue
                
                if restaurant_elements:
                    logging.info(f"Filtered to {len(restaurant_elements)} restaurant-like elements")
                    return restaurant_elements, selector
        except Exception as e:
            logging.debug(f"Selector {selector} failed: {e}")
            continue
    
    return [], None


def extract_restaurant_data(element) -> Dict:
    """Extract restaurant data from an element."""
    data = {
        "Name": "N/A",
        "Area": "N/A", 
        "Cuisine": "N/A",
        "Rating": "N/A",
        "Rating Count": "N/A",
        "Price": "N/A",
        "Availability": "N/A"
    }
    
    try:
        # Get all text content
        full_text = element.text.strip()
        lines = [line.strip() for line in full_text.split('\n') if line.strip()]
        
        # Extract restaurant name (usually the first heading)
        name_elements = element.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, h5, h6, a[href*='/restaurant/']")
        if name_elements:
            name = name_elements[0].text.strip()
            if name and len(name) > 1:
                data["Name"] = name
        
        # Parse lines to extract structured data
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # Extract rating (look for decimal numbers between 1-5)
            if data["Rating"] == "N/A" and any(char.isdigit() for char in line):
                import re
                rating_match = re.search(r'\b([1-5]\.\d)\b', line)
                if rating_match:
                    data["Rating"] = rating_match.group(1)
            
            # Extract price (look for ₹ symbol)
            if '₹' in line and 'for two' in line_lower:
                data["Price"] = line.strip()
            
            # Extract area/location (lines containing city names and distance)
            if any(city in line_lower for city in ['pune', 'baner', 'wakad', 'aundh', 'hinjawadi']):
                if 'km' in line_lower or 'm' in line:
                    # This line likely contains area info
                    area_match = re.search(r'([A-Za-z\s]+),\s*Pune', line)
                    if area_match:
                        data["Area"] = area_match.group(1).strip()
            
            # Extract cuisine (look for common cuisine patterns)
            cuisine_indicators = [
                'north indian', 'south indian', 'chinese', 'italian', 'continental',
                'pizza', 'biryani', 'kebab', 'seafood', 'desserts', 'beverages',
                'mughlai', 'punjabi', 'gujarati', 'maharashtrian', 'bengali',
                'asian', 'american', 'mexican', 'thai', 'japanese', 'korean',
                'cafe', 'bakery', 'fast food', 'street food', 'bar food'
            ]
            
            if data["Cuisine"] == "N/A" and any(cuisine in line_lower for cuisine in cuisine_indicators):
                # Check if this line contains multiple cuisines (comma-separated)
                if ',' in line and len(line) < 200:  # Reasonable length for cuisine list
                    # This might be a cuisine line
                    cuisine_parts = [part.strip() for part in line.split(',')]
                    if len(cuisine_parts) >= 2:  # Multiple cuisines
                        data["Cuisine"] = line.strip()
            
            # Extract availability info
            availability_keywords = ['delivery', 'dine', 'takeaway', 'pickup', 'open', 'closed', 'temporarily closed']
            if any(keyword in line_lower for keyword in availability_keywords):
                if data["Availability"] == "N/A":
                    data["Availability"] = line.strip()
                else:
                    data["Availability"] += "; " + line.strip()
        
        # Additional parsing for rating count (if found near rating)
        rating_text = " ".join(lines)
        if data["Rating"] != "N/A":
            # Look for rating count patterns near the rating
            import re
            rating_count_match = re.search(r'(\d+\.?\d*k?)\s*rating', rating_text.lower())
            if rating_count_match:
                data["Rating Count"] = rating_count_match.group(1)
        
        # Clean up availability field
        if data["Availability"] != "N/A" and len(data["Availability"]) > 200:
            data["Availability"] = data["Availability"][:200] + "..."
        
        logging.info(f"Extracted: {data['Name'][:30]}... | Area: {data['Area'][:20]} | Rating: {data['Rating']} | Price: {data['Price'][:30]}")
        
    except Exception as e:
        logging.error(f"Error extracting data: {e}")
    
    return data


def scrape_restaurants(url: str) -> List[Dict]:
    """Scrape restaurants from Zomato."""
    driver = init_driver(headless=True)  # Use headless mode for faster execution
    
    try:
        logging.info(f"Navigating to: {url}")
        driver.get(url)
        
        # Wait for page to load
        time.sleep(8)  # increased initial wait time
        
        logging.info(f"Current URL: {driver.current_url}")
        logging.info(f"Page title: {driver.title}")
        
        # Try to find restaurant elements
        restaurant_elements, selector = find_restaurant_elements(driver)
        
        if not restaurant_elements:
            logging.error("No restaurant elements found")
            # Save page source for debugging
            with open("page_source.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            logging.info("Page source saved to page_source.html for debugging")
            return []
        
        # Scroll to load ALL content - continue until absolutely no new content
        logging.info(f"Found {len(restaurant_elements)} initial elements, scrolling extensively to load ALL restaurants...")
        
        previous_count = len(restaurant_elements)
        no_change_count = 0
        scroll_attempts = 0
        
        while scroll_attempts < MAX_SCROLL_LOOPS:
            # Multiple scrolling techniques to ensure all content loads
            
            # Primary scrolling method - scroll to bottom
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(SCROLL_PAUSE)
            
            # Secondary scrolling - gradual scroll by large increments
            if scroll_attempts % 3 == 0:
                driver.execute_script("window.scrollBy(0, 2000);")
                time.sleep(2)
            
            # Tertiary scrolling - scroll to specific positions
            if scroll_attempts % 5 == 0:
                driver.execute_script("window.scrollBy(0, 1500);")
                time.sleep(1.5)
            
            # Press Page Down to trigger different loading mechanisms
            if scroll_attempts % 8 == 0:
                try:
                    driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.PAGE_DOWN)
                    time.sleep(1)
                    driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.PAGE_DOWN)
                    time.sleep(1)
                except:
                    pass
            
            # Additional aggressive scrolling every 10 attempts
            if scroll_attempts % 10 == 0:
                # Scroll to different parts of the page
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.8);")
                time.sleep(1)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
            # Extra wait time every 20 scrolls to allow content to load
            if scroll_attempts % 20 == 0:
                logging.info(f"Extended pause at scroll {scroll_attempts} to allow content loading...")
                time.sleep(6)
            
            scroll_attempts += 1
            
            # Check for new elements every scroll (more frequent checking)
            if scroll_attempts % 1 == 0:
                current_elements, _ = find_restaurant_elements(driver)
                current_count = len(current_elements) if current_elements else 0
                
                if current_count > previous_count:
                    logging.info(f"Scroll {scroll_attempts}: Found {current_count} elements (+{current_count - previous_count})")
                    previous_count = current_count
                    no_change_count = 0
                else:
                    no_change_count += 1
                    
                # Only stop if no new elements found for many consecutive attempts
                # Increased threshold to be more aggressive in searching
                if no_change_count >= 30:  # wait for 30 scrolls with no change
                    logging.info(f"No new elements found for {no_change_count} scrolls. Performing final deep check...")
                    
                    # Triple-check by scrolling more extensively
                    for extra_scroll in range(20):
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(3)
                        if extra_scroll % 5 == 0:
                            driver.execute_script("window.scrollBy(0, 3000);")
                            time.sleep(2)
                    
                    final_elements, _ = find_restaurant_elements(driver)
                    final_count = len(final_elements) if final_elements else 0
                    
                    if final_count == current_count:
                        logging.info(f"Confirmed: Reached end of page with {final_count} total elements")
                        break
                    else:
                        logging.info(f"Found more elements after extra scrolling: {final_count}")
                        previous_count = final_count
                        no_change_count = 0
        
        # Final element count
        restaurant_elements, _ = find_restaurant_elements(driver)
        logging.info(f"After exhaustive scrolling: {len(restaurant_elements)} total elements")
        
        # Extract data from ALL elements (no limit)
        restaurants = []
        total_elements = len(restaurant_elements)
        logging.info(f"Processing all {total_elements} restaurant elements...")
        
        for i, element in enumerate(restaurant_elements):
            try:
                data = extract_restaurant_data(element)
                if data["Name"] != "N/A" and len(data["Name"]) > 2:
                    restaurants.append(data)
                    if (i + 1) % 10 == 0:  # Log every 10 processed
                        logging.info(f"Processed {i+1}/{total_elements}: {data['Name']}")
            except Exception as e:
                logging.error(f"Error processing element {i}: {e}")
                continue
        
        return restaurants
        
    except Exception as e:
        logging.error(f"Error in scrape_restaurants: {e}")
        return []
    
    finally:
        driver.quit()


def save_to_csv(restaurants: List[Dict], filename: str):
    """Save restaurants data to CSV."""
    if not restaurants:
        logging.warning("No restaurant data to save.")
        return

    keys = restaurants[0].keys()
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(restaurants)
    logging.info(f"Data saved to {filename}")


if __name__ == "__main__":
    logging.info("Starting Zomato scraper...")
    data = scrape_restaurants(CITY_RESTAURANTS_URL)
    save_to_csv(data, OUTPUT_CSV)
    logging.info(f"Scraping completed. Found {len(data)} restaurants.")
