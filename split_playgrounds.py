import pandas as pd

# Read the CSV file
input_file = 'playground_clean - v.3_with_descriptions_with_additional_reviews.csv'
df = pd.read_csv(input_file)

# Change 'Londres' to 'London'
df['city'] = df['city'].replace('Londres', 'London')

# Create three separate dataframes based on city
london_df = df[df['city'].isin(['London', 'Uxbridge', 'Romford', 'Ilford', 'Croydon', 'Harrow', 'Enfield', 'Hounslow', 'Wembley', 'Hayes'])]  # Including Greater London areas
glasgow_df = df[df['city'] == 'Glasgow']
other_df = df[~df['city'].isin(['London', 'Uxbridge', 'Romford', 'Ilford', 'Croydon', 'Harrow', 'Enfield', 'Hounslow', 'Wembley', 'Hayes', 'Glasgow'])]

# Save to separate CSV files
london_df.to_csv('london_playgrounds.csv', index=False)
glasgow_df.to_csv('glasgow_playgrounds.csv', index=False)
other_df.to_csv('other_playgrounds.csv', index=False)

# Print summary
print(f"\nPlaygrounds split by city:")
print(f"London area: {len(london_df)} playgrounds")
print(f"Glasgow: {len(glasgow_df)} playgrounds")
print(f"Other locations: {len(other_df)} playgrounds")
print(f"\nFiles created: london_playgrounds.csv, glasgow_playgrounds.csv, other_playgrounds.csv") 