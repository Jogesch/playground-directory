# Playground Directory Data Enhancement Setup Guide

## Overview
This guide will help you set up and run the playground data enhancement system to scrape additional information from Google Maps, review sites, and official websites.

## Required Dependencies

Create a `requirements.txt` file with the following packages:

```
pandas>=1.5.0
requests>=2.28.0
beautifulsoup4>=4.11.0
selenium>=4.0.0
googlemaps>=4.10.0
google-search-results>=2.4.0
lxml>=4.9.0
python-dotenv>=0.19.0
webdriver-manager>=3.8.0
```

## API Keys Required

### 1. Google Places API Key
- Go to [Google Cloud Console](https://console.cloud.google.com/)
- Create a new project or select existing one
- Enable the following APIs:
  - Places API
  - Maps JavaScript API  
  - Geocoding API
- Create credentials (API key)
- **Cost**: ~$0.017 per request (first 100k requests free monthly)

### 2. SerpApi Key (Alternative/Supplement to Google)
- Sign up at [SerpApi.com](https://serpapi.com/)
- Get your API key from dashboard
- **Cost**: $50/month for 5,000 searches

### 3. Optional: Other Review Site APIs
- **TripAdvisor API**: For structured review data
- **Yelp Fusion API**: For business listings and reviews

## Installation Steps

### 1. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 2. Install Chrome WebDriver
```bash
# The script will auto-install ChromeDriver, but you can also:
# Download from https://chromedriver.chromium.org/
# Or use webdriver-manager (already in requirements)
```

### 3. Create Environment Variables
Create a `.env` file in your project root:

```env
GOOGLE_API_KEY=your_google_places_api_key_here
SERPAPI_KEY=your_serpapi_key_here
TRIPADVISOR_API_KEY=your_tripadvisor_key_here
YELP_API_KEY=your_yelp_key_here
```

## Usage Instructions

### Basic Usage
```python
from playground_enhancer import PlaygroundDataEnhancer
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize enhancer
enhancer = PlaygroundDataEnhancer(
    google_api_key=os.getenv('GOOGLE_API_KEY'),
    serpapi_key=os.getenv('SERPAPI_KEY')
)

# Load and process data
df = enhancer.load_playground_data('your_playground_data.csv')
enhanced_df = enhancer.process_all_playgrounds(df)
enhancer.export_enhanced_data(enhanced_df, 'enhanced_playgrounds.csv')

# Clean up
enhancer.close()
```

### Advanced Configuration
```python
# Process specific playgrounds only
selected_playgrounds = df[df['location'].isin(['London', 'Glasgow'])]
enhanced_df = enhancer.process_all_playgrounds(selected_playgrounds)

# Custom rate limiting
enhancer.rate_limit_delay = 2  # seconds between requests

# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Data Sources & What Gets Enhanced

### Google Places API
- ✅ Playground name verification
- ✅ Accurate address and coordinates  
- ✅ User ratings and review count
- ✅ Opening hours
- ✅ Contact information (phone, website)
- ✅ Photos
- ✅ Recent reviews
- ✅ Accessibility information

### Review Sites (TripAdvisor, Yelp)
- ✅ Additional ratings and reviews
- ✅ Family-specific feedback
- ✅ Equipment and facility mentions
- ✅ Safety and cleanliness comments

### Local Council Websites
- ✅ Official playground information
- ✅ Maintenance schedules
- ✅ Safety certifications
- ✅ Equipment specifications
- ✅ Age suitability guidelines

### Extracted Information
- ✅ Equipment list (swings, slides, climbing frames, etc.)
- ✅ Age group suitability
- ✅ Surface types (grass, rubber, wood chips)
- ✅ Accessibility features
- ✅ Nearby amenities (parking, toilets, cafes)
- ✅ Safety features
- ✅ Opening hours and seasonal variations

## Enhanced CSV Output Structure

The enhanced CSV will include these additional columns:

```
# Basic Info
name, address, coordinates_lat, coordinates_lng

# Ratings & Reviews  
google_rating, google_review_count, tripadvisor_rating, yelp_rating

# Contact & Hours
phone, website, managed_by, opening_hours_status, opening_hours_details

# Facilities & Equipment
facilities, surface_type, age_groups

# Accessibility
wheelchair_accessible, accessible_parking, accessible_toilets, accessible_equipment

# Location Context
nearby_amenities, photo_count, first_photo_url

# Data Quality
last_updated, data_sources, recent_reviews_summary
```

## Rate Limits & Costs

### Google Places API
- **Rate Limit**: 100 requests per second
- **Cost**: $0.017 per request
- **Free Tier**: 100,000 requests per month

### SerpApi  
- **Rate Limit**: 100 requests per second
- **Cost**: $50/month for 5,000 searches
- **Free Tier**: 100 requests per month

### Best Practices
- Process data in batches of 50-100 playgrounds
- Add 1-2 second delays between requests
- Cache results to avoid re-processing
- Monitor API usage in dashboards

## Expected Processing Time

For 1000 playgrounds:
- **With Google Places only**: ~30-45 minutes
- **With all sources**: ~2-3 hours
- **Rate limited (respectful)**: ~4-6 hours

## Troubleshooting

### Common Issues

1. **API Key Errors**
   ```
   Error: API key not valid
   ```
   - Verify API key in Google Cloud Console
   - Check API is enabled
   - Confirm billing is set up

2. **Rate Limit Exceeded**
   ```
   Error: Rate limit exceeded
   ```
   - Increase delay between requests
   - Check API quotas in console
   - Consider upgrading API plan

3. **Chrome Driver Issues**
   ```
   Error: ChromeDriver not found
   ```
   - Install Chrome browser
   - Update Chrome to latest version
   - Let webdriver-manager auto-install

4. **No Results Found**
   - Check playground names are accurate
   - Try alternative search terms
   - Verify location data is correct

### Debug Mode
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# This will show detailed API requests and responses
```

## Legal & Ethical Considerations

### Terms of Service Compliance
- ✅ Google Places API - Commercial use allowed with proper attribution
- ✅ SerpApi - Compliant automated data collection
- ⚠️ Direct website scraping - Check robots.txt and terms of service
- ⚠️ Review sites - Use official APIs when available

### Data Usage Rights
- Public playground information is generally public domain
- User reviews may have usage restrictions
- Always attribute data sources properly
- Consider data privacy for user-generated content

### Best Practices
- Implement respectful rate limiting
- Cache data to minimize repeat requests
- Provide clear attribution on your website
- Allow users to report incorrect information
- Regular data updates (monthly/quarterly)

## Deployment Considerations

### For Production Use
1. **Caching Strategy**: Implement Redis/database caching
2. **Queue System**: Use Celery for background processing
3. **Error Handling**: Robust retry logic and error reporting
4. **Monitoring**: Track API usage and success rates
5. **Data Validation**: Verify scraped data quality
6. **Update Schedule**: Automated monthly refreshes

### Scaling Up
- Use cloud functions for parallel processing
- Implement proper database storage
- Set up monitoring and alerting
- Consider CDN for playground images
- Add data backup and recovery

## Support Resources

- [Google Places API Documentation](https://developers.google.com/maps/documentation/places/web-service)
- [SerpApi Documentation](https://serpapi.com/google-maps-api)
- [Selenium Documentation](https://selenium-python.readthedocs.io/)
- [Beautiful Soup Documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)

For technical support with this implementation, check the error logs and API documentation first. Most issues are related to API keys, rate limits, or data format changes.