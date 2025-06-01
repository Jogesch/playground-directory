import pandas as pd
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging
from typing import List, Dict, Optional
from fake_useragent import UserAgent
from urllib.parse import quote

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('review_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ReviewScraper:
    def __init__(self):
        """Initialize the review scraper with Selenium WebDriver"""
        self.setup_driver()
        self.user_agent = UserAgent()
        
    def setup_driver(self):
        """Set up Chrome WebDriver with appropriate options"""
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument(f'user-agent={UserAgent().random}')
        self.driver = webdriver.Chrome(options=options)
        
    def search_tripadvisor(self, playground_name: str, location: str) -> Optional[str]:
        """Search for playground on TripAdvisor and return the attraction URL"""
        try:
            search_query = quote(f"{playground_name} {location} playground")
            search_url = f"https://www.tripadvisor.com/Search?q={search_query}"
            
            logger.info(f"Searching TripAdvisor for: {playground_name}")
            self.driver.get(search_url)
            
            # Wait for search results
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "result-title"))
            )
            
            # Get first result
            results = self.driver.find_elements(By.CLASS_NAME, "result-title")
            if results:
                href = results[0].get_attribute("href")
                return href
                
        except Exception as e:
            logger.error(f"Error searching TripAdvisor: {e}")
            
        return None
        
    def get_tripadvisor_reviews(self, url: str) -> List[Dict]:
        """Scrape reviews from TripAdvisor"""
        reviews = []
        try:
            self.driver.get(url)
            time.sleep(random.uniform(2, 4))  # Random delay
            
            # Click "More" button to expand reviews if present
            try:
                more_button = self.driver.find_element(By.CLASS_NAME, "Expand")
                more_button.click()
                time.sleep(1)
            except:
                pass
                
            # Get review elements
            review_elements = self.driver.find_elements(By.CLASS_NAME, "review-container")
            
            for element in review_elements:
                try:
                    review = {
                        'title': element.find_element(By.CLASS_NAME, "title").text,
                        'text': element.find_element(By.CLASS_NAME, "text").text,
                        'rating': element.find_element(By.CLASS_NAME, "ui_bubble_rating").get_attribute("class"),
                        'date': element.find_element(By.CLASS_NAME, "ratingDate").get_attribute("title"),
                        'source': 'TripAdvisor'
                    }
                    reviews.append(review)
                except:
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping TripAdvisor reviews: {e}")
            
        return reviews
        
    def process_playgrounds(self, input_file: str, output_file: str = None):
        """Process all playgrounds and scrape additional reviews"""
        try:
            # Load playground data
            df = pd.read_csv(input_file)
            logger.info(f"Loaded {len(df)} playgrounds")
            
            # Initialize new columns if they don't exist
            if 'tripadvisor_reviews' not in df.columns:
                df['tripadvisor_reviews'] = ''
                
            # Process each playground
            for index, row in df.iterrows():
                try:
                    name = row['name']
                    location = row.get('city', '') or row.get('location', '')
                    
                    logger.info(f"Processing {index + 1}/{len(df)}: {name}")
                    print(f"\rProcessing {index + 1}/{len(df)}: {name}", end='')
                    
                    # Search on TripAdvisor
                    tripadvisor_url = self.search_tripadvisor(name, location)
                    if tripadvisor_url:
                        reviews = self.get_tripadvisor_reviews(tripadvisor_url)
                        if reviews:
                            # Store reviews as JSON string
                            df.at[index, 'tripadvisor_reviews'] = str(reviews)
                            
                    # Add random delay between requests
                    time.sleep(random.uniform(3, 6))
                    
                except Exception as e:
                    logger.error(f"Error processing playground {name}: {e}")
                    continue
                    
            print("\n")  # New line after progress
            
            # Save results
            output_file = output_file or input_file.replace('.csv', '_with_additional_reviews.csv')
            df.to_csv(output_file, index=False)
            logger.info(f"Enhanced data saved to {output_file}")
            
            # Print summary
            print("\nProcessing Summary:")
            print("-" * 50)
            print(f"Total playgrounds processed: {len(df)}")
            print(f"Playgrounds with TripAdvisor reviews: {sum(df['tripadvisor_reviews'].str.len() > 0)}")
            
        except Exception as e:
            logger.error(f"Error in process_playgrounds: {e}")
            raise
            
        finally:
            self.driver.quit()
            
def main():
    """Main function to demonstrate usage"""
    try:
        scraper = ReviewScraper()
        input_file = "playground_clean - v.3_with_descriptions.csv"
        scraper.process_playgrounds(input_file)
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise

if __name__ == "__main__":
    main() 