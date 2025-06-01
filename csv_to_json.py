import pandas as pd
import json

# Read the CSV file
df = pd.read_csv('london_playgrounds.csv')

# Convert DataFrame to JSON
# orient='records' will make each row a JSON object in a list
json_data = df.to_json(orient='records', indent=2)

# Write to a JSON file
with open('london_playgrounds.json', 'w') as f:
    f.write(json_data)

# Print summary
print(f"\nConversion completed:")
print(f"Input: london_playgrounds.csv")
print(f"Output: london_playgrounds.json")
print(f"Number of playgrounds converted: {len(df)}") 