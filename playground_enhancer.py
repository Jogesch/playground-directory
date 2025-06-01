import pandas as pd
import googlemaps
import os
from dotenv import load_dotenv
import logging
from typing import Dict, Optional
from pathlib import Path

# Load environment variables
load_dotenv()
logger = logging.getLogger(__name__)

# Check .env loading
env_file = Path('.env')
if env_file.exists():
    logger.info(f".env file found at {env_file.absolute()}")
else:
    logger.error(f".env file not found at {env_file.absolute()}")

# Configure logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('playground_enhancer.log'),
        logging.StreamHandler()
    ]
)

class PlaygroundEnhancer:
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the playground enhancer with Google Places API key
        
        Args:
            api_key: Google Places API key (optional, will use from env if not provided)
        """
        self.api_key = api_key or os.getenv('GOOGLE_PLACES_API_KEY')
        logger.info(f"API Key loaded: {'Not found' if not self.api_key else 'Found (length: ' + str(len(self.api_key)) + ')'}")
        
        if not self.api_key:
            raise ValueError("Google Places API key not found. Please set GOOGLE_PLACES_API_KEY in .env file")
            
        self.gmaps = googlemaps.Client(key=self.api_key)
        logger.info("PlaygroundEnhancer initialized successfully")
        
    def load_csv(self, file_path: str) -> pd.DataFrame:
        """
        Load playground data from CSV file
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            DataFrame containing playground data
        """
        try:
            if not Path(file_path).exists():
                raise FileNotFoundError(f"CSV file not found: {file_path}")
                
            df = pd.read_csv(file_path)
            required_columns = {'name', 'location', 'postcode'}
            missing_columns = required_columns - set(df.columns)
            
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
                
            logger.info(f"Successfully loaded {len(df)} playgrounds from {file_path}")
            return df
            
        except Exception as e:
            logger.error(f"Error loading CSV file: {e}")
            raise
            
    def enhance_playground(self, name: str, location: str, postcode: str) -> Dict:
        """
        Enhance a single playground with Google Places data
        
        Args:
            name: Name of the playground
            location: Location/area of the playground
            postcode: Postcode of the playground
            
        Returns:
            Dictionary containing enhanced playground data
        """
        try:
            logger.debug(f"Processing playground: {name}")
            
            # Search query combining name, location and postcode
            search_query = f"{name} playground {location} {postcode}"
            
            # Search for the playground
            places_result = self.gmaps.places(query=search_query)
            
            if not places_result['results']:
                logger.warning(f"No Google Places results found for: {search_query}")
                return self._create_basic_data(name, location, postcode)
                
            # Get first result
            place = places_result['results'][0]
            place_id = place['place_id']
            
            # Get detailed place information
            details = self.gmaps.place(
                place_id=place_id,
                fields=[
                    'name', 'formatted_address', 'geometry', 'rating',
                    'user_ratings_total', 'opening_hours', 'formatted_phone_number',
                    'website', 'reviews', 'photos', 'wheelchair_accessible_entrance'
                ]
            )
            
            # Extract and format the enhanced data
            enhanced_data = {
                'original_name': name,
                'original_location': location,
                'original_postcode': postcode,
                'google_place_id': place_id,
                'name': details['result'].get('name', name),
                'address': details['result'].get('formatted_address', ''),
                'latitude': details['result'].get('geometry', {}).get('location', {}).get('lat'),
                'longitude': details['result'].get('geometry', {}).get('location', {}).get('lng'),
                'rating': details['result'].get('rating', None),
                'total_ratings': details['result'].get('user_ratings_total', 0),
                'phone': details['result'].get('formatted_phone_number', ''),
                'website': details['result'].get('website', ''),
                'wheelchair_accessible': details['result'].get('wheelchair_accessible_entrance', False),
                'opening_hours': self._format_opening_hours(details['result'].get('opening_hours', {})),
                'photos_available': len(details['result'].get('photos', [])),
                'last_updated': pd.Timestamp.now().isoformat()
            }
            
            logger.info(f"Successfully enhanced playground: {name}")
            return enhanced_data
            
        except Exception as e:
            logger.error(f"Error enhancing playground {name}: {e}")
            return self._create_basic_data(name, location, postcode, error=str(e))
            
    def _create_basic_data(self, name: str, location: str, postcode: str, error: str = '') -> Dict:
        """Create basic data structure when enhancement fails"""
        return {
            'original_name': name,
            'original_location': location,
            'original_postcode': postcode,
            'error': error,
            'last_updated': pd.Timestamp.now().isoformat()
        }
        
    def _format_opening_hours(self, hours_data: Dict) -> Dict:
        """Format opening hours data into a consistent structure"""
        if not hours_data:
            return {'status': 'Unknown', 'hours': []}
            
        return {
            'status': 'Open' if hours_data.get('open_now', False) else 'Closed',
            'hours': hours_data.get('weekday_text', [])
        }
        
def main():
    """Main function to process all playgrounds"""
    try:
        # Initialize enhancer
        enhancer = PlaygroundEnhancer()
        
        # Load playground data
        df = enhancer.load_csv('playgrounds.csv')
        
        # Process all playgrounds
        enhanced_data_list = []
        for index, playground in df.iterrows():
            logger.info(f"Processing playground {index + 1}/{len(df)}: {playground['name']}")
            enhanced_data = enhancer.enhance_playground(
                name=playground['name'],
                location=playground['location'],
                postcode=playground['postcode']
            )
            enhanced_data_list.append(enhanced_data)
            
            # Print progress
            print(f"\rProcessed {index + 1}/{len(df)} playgrounds", end='')
            
        print("\n")  # New line after progress
        
        # Convert to DataFrame and save
        enhanced_df = pd.DataFrame(enhanced_data_list)
        output_file = 'enhanced_playgrounds.csv'
        enhanced_df.to_csv(output_file, index=False)
        logger.info(f"Enhanced data saved to {output_file}")
        
        # Print summary
        print("\nProcessing Summary:")
        print(f"Total playgrounds processed: {len(df)}")
        print(f"Enhanced data saved to: {output_file}")
        
        # Print sample of enhanced data
        print("\nSample of enhanced data (first playground):")
        for key, value in enhanced_data_list[0].items():
            print(f"{key}: {value}")
                
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise

if __name__ == "__main__":
    main() 