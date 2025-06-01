import pandas as pd
import json
from typing import Dict, List
import numpy as np
from datetime import datetime
import re
from geopy.distance import geodesic
from slugify import slugify

class PlaygroundDirectoryProcessor:
    def __init__(self, input_file: str):
        """Initialize the processor with input file"""
        self.df = pd.read_csv(input_file)
        self.processed_entries = []
        
        # Initialize missing columns
        required_columns = ['postcode', 'city', 'description', 'tripadvisor_reviews']
        for col in required_columns:
            if col not in self.df.columns:
                self.df[col] = ''
        
    def clean_and_standardize(self):
        """Clean and standardize the data"""
        # Standardize location names
        self.df['city'] = self.df['city'].str.strip()
        
        # Create region field
        self.df['region'] = self.df['city'].apply(self.determine_region)
        
        # Generate URL-friendly slugs
        self.df['slug'] = self.df['name'].apply(lambda x: slugify(str(x)))
        
        # Clean and standardize postcodes
        self.df['postcode'] = self.df['postcode'].astype(str).str.upper().str.strip()
        
        # Convert reviews from string to structured data
        self.df['tripadvisor_reviews'] = self.df['tripadvisor_reviews'].apply(self.parse_reviews)
        
    def determine_region(self, city: str) -> str:
        """Determine the region based on city"""
        if pd.isna(city) or not city:
            return "Unknown"
        city_lower = str(city).lower()
        if any(keyword in city_lower for keyword in ['london', 'greater london']):
            return "Greater London"
        elif any(keyword in city_lower for keyword in ['glasgow', 'city of glasgow']):
            return "City of Glasgow"
        return "Other"
        
    def parse_reviews(self, review_str: str) -> List[Dict]:
        """Parse review string into structured data"""
        if not review_str or pd.isna(review_str) or review_str == '':
            return []
        try:
            cleaned_str = str(review_str).replace("'", '"')
            return json.loads(cleaned_str)
        except:
            return []
            
    def extract_key_features(self):
        """Extract and structure key features for the directory"""
        # Age suitability with more detailed parsing
        age_patterns = [
            r'suitable for (\d+-\d+|\d+\+?) years',
            r'ages? (\d+-\d+|\d+\+?)',
            r'(\d+-\d+|\d+\+?) years? old'
        ]
        
        def extract_age_range(text):
            if pd.isna(text):
                return None
            text = str(text)
            for pattern in age_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return match.group(1)
            return None
            
        self.df['age_range'] = self.df['description'].apply(extract_age_range)
        
        # Equipment types with expanded categories
        equipment_categories = {
            'climbing': ['climbing frame', 'monkey bars', 'climbing wall', 'rope climb'],
            'swings': ['swing', 'baby swing', 'tire swing'],
            'slides': ['slide', 'spiral slide', 'tube slide'],
            'activity': ['sandbox', 'seesaw', 'trampoline', 'zipline', 'obstacle course'],
            'sports': ['basketball', 'football', 'tennis', 'sports court'],
            'water': ['splash pad', 'water play', 'fountain'],
            'sensory': ['musical', 'sensory wall', 'interactive play']
        }
        
        for category, keywords in equipment_categories.items():
            self.df[f'has_{category}'] = self.df['description'].str.contains('|'.join(keywords), case=False, na=False)
            
        # Enhanced amenities detection
        amenity_keywords = {
            'has_parking': ['parking', 'car park', 'parking lot'],
            'has_toilets': ['toilet', 'restroom', 'bathroom', 'changing facilities'],
            'has_cafe': ['cafe', 'coffee', 'food', 'refreshment', 'kiosk'],
            'has_seating': ['bench', 'seating', 'picnic', 'table'],
            'has_shade': ['shade', 'shelter', 'covered', 'canopy'],
            'has_fencing': ['fenced', 'enclosed', 'gated'],
            'has_accessibility': ['wheelchair', 'accessible', 'disability', 'inclusive'],
            'has_bike_parking': ['bike rack', 'bicycle parking', 'cycle stand']
        }
        
        for amenity, keywords in amenity_keywords.items():
            self.df[amenity] = self.df['description'].str.contains('|'.join(keywords), case=False, na=False)
            
        # Safety features
        safety_keywords = {
            'has_safety_surface': ['rubber', 'safety surface', 'soft surface', 'impact absorbing'],
            'has_lighting': ['lighting', 'lit', 'floodlight'],
            'has_cctv': ['cctv', 'surveillance', 'monitored'],
            'has_first_aid': ['first aid', 'medical', 'emergency']
        }
        
        for feature, keywords in safety_keywords.items():
            self.df[feature] = self.df['description'].str.contains('|'.join(keywords), case=False, na=False)
            
        # Calculate ratings and review metrics
        self.df['review_count'] = self.df['tripadvisor_reviews'].apply(len)
        
        def calculate_avg_rating(reviews):
            if not reviews:
                return None
            ratings = [review.get('rating', 0) for review in reviews if review.get('rating', 0) > 0]
            return np.mean(ratings) if ratings else None
            
        self.df['avg_rating'] = self.df['tripadvisor_reviews'].apply(calculate_avg_rating)
        
        # Calculate popularity score
        max_reviews = self.df['review_count'].max() if len(self.df) > 0 else 1
        self.df['popularity_score'] = self.df.apply(
            lambda row: (
                (row['avg_rating'] * 0.7 if pd.notna(row['avg_rating']) else 0) +
                (row['review_count'] / max_reviews * 0.3 if max_reviews > 0 else 0)
            ),
            axis=1
        ).fillna(0)
        
    def create_search_metadata(self):
        """Create enhanced searchable metadata fields"""
        # Initialize tags
        self.df['search_tags'] = ''
        self.df['primary_tags'] = ''
        self.df['feature_tags'] = ''
        
        # Add equipment category tags
        equipment_cols = [col for col in self.df.columns if col.startswith('has_')]
        for col in equipment_cols:
            self.df.loc[self.df[col], 'feature_tags'] += f" {col.replace('has_', '')}"
            
        # Add age range tags with categories
        def categorize_age(age_range):
            if pd.isna(age_range):
                return []
            tags = []
            age_str = str(age_range)
            if any(x in age_str for x in ['0-', '1-', '2-', '3-', '4-']):
                tags.append('toddler_friendly')
            if any(x in age_str for x in ['5-', '6-', '7-', '8-']):
                tags.append('child_friendly')
            if any(x in age_str for x in ['9-', '10-', '11-', '12+']):
                tags.append('older_kids')
            return tags
            
        self.df['age_tags'] = self.df['age_range'].apply(categorize_age)
        self.df['primary_tags'] += self.df['age_tags'].apply(lambda x: ' ' + ' '.join(x))
        
        # Add rating-based tags
        self.df.loc[self.df['avg_rating'] >= 4.5, 'primary_tags'] += ' top_rated'
        self.df.loc[self.df['avg_rating'] >= 4.0, 'primary_tags'] += ' highly_rated'
        self.df.loc[self.df['review_count'] >= 10, 'primary_tags'] += ' popular'
        
        # Add amenity combination tags
        self.df.loc[
            self.df['has_toilets'] & self.df['has_parking'] & self.df['has_cafe'],
            'primary_tags'
        ] += ' family_friendly'
        
        self.df.loc[
            self.df['has_fencing'] & self.df['has_safety_surface'],
            'primary_tags'
        ] += ' safe_play'
        
        # Combine all tags
        self.df['search_tags'] = (
            self.df['primary_tags'] + ' ' + 
            self.df['feature_tags'] + ' ' + 
            self.df['region'].str.lower()
        )
        
        # Clean tags
        for tag_col in ['search_tags', 'primary_tags', 'feature_tags']:
            self.df[tag_col] = self.df[tag_col].str.strip().str.lower()
        
    def format_directory_entry(self, row) -> Dict:
        """Format a single directory entry with enhanced structure"""
        # Calculate nearby amenities (example: could be expanded with real data)
        nearby_amenities = {
            'restaurants': False,
            'shops': False,
            'public_transport': False
        }
        
        # Format opening hours (placeholder - could be extracted from description)
        opening_hours = {
            'monday_friday': '9:00 AM - Dusk',
            'weekend': '9:00 AM - Dusk',
            'holidays': '9:00 AM - Dusk'
        }
        
        return {
            'id': row.name,
            'name': row['name'],
            'slug': row['slug'],
            'location': {
                'address': row.get('address', ''),
                'city': row['city'],
                'region': row['region'],
                'postcode': row.get('postcode', ''),
                'coordinates': {
                    'latitude': row.get('latitude', None),
                    'longitude': row.get('longitude', None)
                }
            },
            'features': {
                'equipment_categories': {
                    category: row.get(f'has_{category}', False)
                    for category in ['climbing', 'swings', 'slides', 'activity', 'sports', 'water', 'sensory']
                },
                'age_range': row.get('age_range', None),
                'age_categories': row['age_tags'],
                'amenities': {
                    amenity.replace('has_', ''): row.get(amenity, False)
                    for amenity in row.index if amenity.startswith('has_')
                }
            },
            'safety': {
                feature.replace('has_safety_', ''): row.get(feature, False)
                for feature in row.index if feature.startswith('has_safety_')
            },
            'ratings': {
                'average': row.get('avg_rating', None),
                'review_count': row.get('review_count', 0),
                'popularity_score': row.get('popularity_score', 0),
                'reviews': row.get('tripadvisor_reviews', [])
            },
            'metadata': {
                'primary_tags': row.get('primary_tags', '').split(),
                'feature_tags': row.get('feature_tags', '').split(),
                'search_tags': row.get('search_tags', '').split()
            },
            'additional_info': {
                'nearby_amenities': nearby_amenities,
                'opening_hours': opening_hours,
                'last_updated': datetime.now().isoformat()
            },
            'description': row.get('description', '')
        }
        
    def create_directory_entries(self):
        """Create structured directory entries"""
        self.processed_entries = []
        for _, row in self.df.iterrows():
            entry = self.format_directory_entry(row)
            self.processed_entries.append(entry)
            
    def save_directory(self):
        """Save the unified directory"""
        # Save as JSON for richer data structure
        with open('playground_directory.json', 'w') as f:
            json.dump({
                'metadata': {
                    'total_entries': len(self.processed_entries),
                    'regions': self.df['region'].value_counts().to_dict(),
                    'last_updated': datetime.now().isoformat()
                },
                'entries': self.processed_entries
            }, f, indent=2)
            
        # Save a CSV version for compatibility
        self.df.to_csv('playground_directory.csv', index=False)
        
        # Print summary
        print("\nDirectory Creation Summary:")
        print("-" * 50)
        print(f"Total playgrounds: {len(self.processed_entries)}")
        print("\nBy Region:")
        for region, count in self.df['region'].value_counts().items():
            print(f"{region}: {count}")
            
def main():
    """Main function to process playground directory"""
    processor = PlaygroundDirectoryProcessor("playground_clean - v.3_with_descriptions_with_additional_reviews.csv")
    
    # Process the data
    processor.clean_and_standardize()
    processor.extract_key_features()
    processor.create_search_metadata()
    processor.create_directory_entries()
    processor.save_directory()
    
if __name__ == "__main__":
    main() 