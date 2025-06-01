# Playground Data Enhancer

This project enhances playground data using the Google Places API to add additional information such as ratings, opening hours, accessibility features, and more.

## Setup

1. Clone the repository
2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
   - Copy `.env.template` to `.env`
   - Add your Google Places API key to `.env`

## Input Data Format

The script expects a CSV file (`playgrounds.csv`) with the following columns:
- `name`: Name of the playground
- `location`: Location/area of the playground
- `postcode`: Postcode of the playground

Example:
```csv
name,location,postcode
Central Park Playground,Manchester,M14 5RB
```

## Usage

Run the script:
```bash
python playground_enhancer.py
```

The script will:
1. Load the playground data from CSV
2. Enhance each playground with Google Places data
3. Log the process in `playground_enhancer.log`
4. Print enhanced data for the first playground as an example

## Features

- Google Places API integration
- Error handling and logging
- Data validation
- Structured output format
- Configurable logging levels

## Output Data

The enhanced data includes:
- Original playground information
- Google Places ID
- Formatted address
- Coordinates (latitude/longitude)
- Rating and number of ratings
- Contact information (phone, website)
- Accessibility information
- Opening hours
- Number of available photos
- Timestamp of last update 