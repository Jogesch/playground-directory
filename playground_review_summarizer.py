import pandas as pd
import googlemaps
import os
from dotenv import load_dotenv
import logging
from typing import Dict, List, Optional
import time
from pathlib import Path
import re

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('playground_reviews.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PlaygroundReviewSummarizer:
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with Google Places API key"""
        self.api_key = api_key or os.getenv('GOOGLE_PLACES_API_KEY')
        if not self.api_key:
            raise ValueError("Google Places API key not found. Please set GOOGLE_PLACES_API_KEY in .env file")
            
        self.gmaps = googlemaps.Client(key=self.api_key)
        logger.info("PlaygroundReviewSummarizer initialized successfully")
        
    def get_place_reviews(self, place_id: str) -> List[Dict]:
        """Fetch reviews for a specific place ID"""
        try:
            if not place_id:
                return []
                
            # Get detailed place information including reviews
            details = self.gmaps.place(
                place_id=place_id,
                fields=['reviews', 'rating', 'user_ratings_total']
            )
            
            return details.get('result', {}).get('reviews', [])
            
        except Exception as e:
            logger.error(f"Error fetching reviews for place_id {place_id}: {e}")
            return []
            
    def summarize_reviews(self, reviews: List[Dict]) -> str:
        """Generate a parent-friendly summary from reviews"""
        if not reviews:
            return "No reviews available for this playground."
            
        # Extract key information from reviews
        mentions = {
            'safety': 0,
            'cleanliness': 0,
            'equipment': 0,
            'age_groups': 0,
            'maintenance': 0,
            'shade': 0,
            'seating': 0,
            'parking': 0,
            'toilets': 0
        }
        
        equipment_types = set()
        positive_aspects = set()
        negative_aspects = set()
        age_mentions = set()
        
        # Keywords to track
        keywords = {
            'safety': ['safe', 'secure', 'dangerous', 'unsafe'],
            'cleanliness': ['clean', 'dirty', 'tidy', 'mess', 'rubbish'],
            'equipment': ['swing', 'slide', 'climbing', 'sandbox', 'roundabout', 'seesaw'],
            'age_groups': ['toddler', 'young', 'older', 'age', 'year old'],
            'maintenance': ['maintain', 'broken', 'repair', 'new', 'old'],
            'shade': ['shade', 'sun', 'shelter', 'covered'],
            'seating': ['bench', 'seat', 'sit', 'rest'],
            'parking': ['park', 'parking', 'car'],
            'toilets': ['toilet', 'bathroom', 'changing']
        }
        
        # Analyze reviews
        for review in reviews:
            text = review.get('text', '').lower()
            rating = review.get('rating', 0)
            
            # Track mentions
            for category, words in keywords.items():
                if any(word in text for word in words):
                    mentions[category] += 1
                    
            # Track sentiment based on rating
            if rating >= 4:
                if 'clean' in text: positive_aspects.add('cleanliness')
                if 'safe' in text: positive_aspects.add('safety')
                if any(word in text for word in keywords['equipment']): 
                    for word in keywords['equipment']:
                        if word in text:
                            equipment_types.add(word)
            elif rating <= 2:
                if 'dirty' in text: negative_aspects.add('cleanliness')
                if 'unsafe' in text: negative_aspects.add('safety')
                if 'broken' in text: negative_aspects.add('maintenance')
                
            # Track age group mentions
            if 'toddler' in text: age_mentions.add('toddlers')
            if 'young' in text: age_mentions.add('young children')
            if 'older' in text: age_mentions.add('older children')
            
        # Generate summary
        avg_rating = sum(review.get('rating', 0) for review in reviews) / len(reviews)
        
        summary_parts = []
        
        # Overall impression
        if avg_rating >= 4:
            summary_parts.append("This highly-rated playground")
        elif avg_rating >= 3:
            summary_parts.append("This well-received playground")
        else:
            summary_parts.append("This playground")
            
        # Age suitability
        if age_mentions:
            summary_parts.append(f"is particularly suitable for {', '.join(age_mentions)}")
            
        # Equipment
        if equipment_types:
            summary_parts.append(f"and features {', '.join(equipment_types)}")
            
        # Key positive aspects
        if positive_aspects:
            summary_parts.append(f". Parents particularly appreciate its {', '.join(positive_aspects)}")
            
        # Amenities
        amenities = []
        if mentions['shade'] > 0: amenities.append("shaded areas")
        if mentions['seating'] > 0: amenities.append("seating for parents")
        if mentions['parking'] > 0: amenities.append("parking facilities")
        if mentions['toilets'] > 0: amenities.append("toilet facilities")
        
        if amenities:
            summary_parts.append(f". The playground offers {', '.join(amenities)}")
            
        # Areas for improvement
        if negative_aspects:
            summary_parts.append(f". Some visitors have noted concerns about {', '.join(negative_aspects)}")
            
        # Combine parts
        summary = ' '.join(summary_parts).replace('..', '.').strip()
        if not summary.endswith('.'):
            summary += '.'
            
        return summary
        
    def process_playgrounds(self, input_file: str, output_file: str = None):
        """Process all playgrounds and add review summaries"""
        try:
            # Read the CSV file
            df = pd.read_csv(input_file)
            logger.info(f"Loaded {len(df)} playgrounds from {input_file}")
            
            # Initialize description column if it doesn't exist
            if 'description' not in df.columns:
                df['description'] = ''
                
            # Process each playground
            for index, row in df.iterrows():
                place_id = row.get('google_place_id', '')
                if not place_id:
                    logger.warning(f"No place_id for playground at index {index}")
                    continue
                    
                logger.info(f"Processing playground {index + 1}/{len(df)}: {row.get('name', 'Unknown')}")
                
                # Get and summarize reviews
                reviews = self.get_place_reviews(place_id)
                summary = self.summarize_reviews(reviews)
                
                # Update description
                df.at[index, 'description'] = summary
                
                # Print progress
                print(f"\rProcessed {index + 1}/{len(df)} playgrounds", end='')
                
                # Add delay to respect API limits
                time.sleep(2)
                
            print("\n")  # New line after progress
            
            # Save results
            output_file = output_file or input_file.replace('.csv', '_with_descriptions.csv')
            df.to_csv(output_file, index=False)
            logger.info(f"Enhanced data saved to {output_file}")
            
            # Print summary
            print(f"\nProcessing Summary:")
            print(f"Total playgrounds processed: {len(df)}")
            print(f"Enhanced data saved to: {output_file}")
            
        except Exception as e:
            logger.error(f"Error processing playgrounds: {e}")
            raise

def main():
    """Main function to process all playgrounds and check data completeness"""
    try:
        # Initialize summarizer
        summarizer = PlaygroundReviewSummarizer()
        
        # Load the CSV file
        input_file = "playground_clean - v.3.csv"
        df = pd.read_csv(input_file)
        logger.info(f"Loaded {len(df)} playgrounds")
        
        # Initialize or update description column
        if 'description' not in df.columns:
            df['description'] = ''
            
        # Track missing data
        missing_data = []
        processed_count = 0
        skipped_count = 0
        
        # Process each playground
        total_playgrounds = len(df)
        for index, playground in df.iterrows():
            name = playground.get('name', 'Unknown')
            print(f"\rProcessing {index + 1}/{total_playgrounds}: {name}", end='')
            
            # Check for required data
            place_id = playground.get('place_id')
            if not place_id:
                missing_data.append({
                    'name': name,
                    'reason': 'Missing place_id',
                    'index': index
                })
                skipped_count += 1
                continue
                
            try:
                # Get and summarize reviews
                reviews = summarizer.get_place_reviews(place_id)
                summary = summarizer.summarize_reviews(reviews)
                
                # Update description
                df.at[index, 'description'] = summary
                processed_count += 1
                
                # Add delay to respect API limits
                time.sleep(2)
                
            except Exception as e:
                missing_data.append({
                    'name': name,
                    'reason': f'Error: {str(e)}',
                    'index': index
                })
                skipped_count += 1
                logger.error(f"Error processing playground {name}: {e}")
                
        print("\n")  # New line after progress
        
        # Save updated data
        output_file = input_file.replace('.csv', '_with_descriptions.csv')
        df.to_csv(output_file, index=False)
        logger.info(f"Enhanced data saved to {output_file}")
        
        # Print summary report
        print("\nProcessing Summary:")
        print("-" * 50)
        print(f"Total playgrounds: {total_playgrounds}")
        print(f"Successfully processed: {processed_count}")
        print(f"Skipped/Errors: {skipped_count}")
        
        if missing_data:
            print("\nPlaygrounds with Missing Data:")
            print("-" * 50)
            for item in missing_data:
                print(f"Row {item['index'] + 1}: {item['name']}")
                print(f"Reason: {item['reason']}")
                print("-" * 30)
                
        # Analyze description completeness
        descriptions = df['description'].fillna('')
        empty_descriptions = descriptions.str.len() == 0
        short_descriptions = (descriptions.str.len() > 0) & (descriptions.str.len() < 100)
        
        print("\nDescription Analysis:")
        print("-" * 50)
        print(f"Complete descriptions: {len(df) - sum(empty_descriptions) - sum(short_descriptions)}")
        print(f"Short descriptions (<100 chars): {sum(short_descriptions)}")
        print(f"Empty descriptions: {sum(empty_descriptions)}")
        
        # Sample of complete description
        if not empty_descriptions.all():
            print("\nSample Complete Description:")
            print("-" * 50)
            sample = df[~empty_descriptions].iloc[0]
            print(f"Playground: {sample['name']}")
            print(sample['description'])
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise

if __name__ == "__main__":
    main() 