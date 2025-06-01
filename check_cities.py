import pandas as pd

# Read the CSV file
input_file = 'playground_clean - v.3_with_descriptions_with_additional_reviews.csv'
df = pd.read_csv(input_file)

# Print unique cities and their counts
print("\nUnique cities and their counts:")
print(df['city'].value_counts()) 