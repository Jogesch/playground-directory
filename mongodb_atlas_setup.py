from pymongo import MongoClient
import json
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def connect_to_mongodb():
    """Connect to MongoDB Atlas"""
    try:
        # Get MongoDB Atlas connection string from environment variable
        # Format: mongodb+srv://username:password@cluster.mongodb.net/
        connection_string = os.getenv('MONGODB_URI')
        
        if not connection_string:
            print("Please set your MONGODB_URI environment variable.")
            print("It should look like: mongodb+srv://username:password@cluster.mongodb.net/")
            return None
            
        # Connect to MongoDB Atlas
        client = MongoClient(connection_string)
        
        # Create/access the playground database
        db = client['playground_db']
        
        # Test the connection
        client.admin.command('ping')
        print("Successfully connected to MongoDB Atlas.")
        return db
    except Exception as e:
        print(f"Error connecting to MongoDB Atlas: {e}")
        return None

def import_playground_data(db, file_path, collection_name):
    """Import playground data from JSON file into MongoDB"""
    try:
        # Read JSON file
        with open(file_path, 'r') as file:
            playgrounds = json.load(file)
        
        # Get the collection
        collection = db[collection_name]
        
        # Drop existing collection to avoid duplicates
        collection.drop()
        
        # Add metadata to each playground
        for playground in playgrounds:
            playground['imported_at'] = datetime.now()
            
            # Convert coordinates to GeoJSON format for better geospatial queries
            if 'latitude' in playground and 'longitude' in playground:
                playground['location'] = {
                    'type': 'Point',
                    'coordinates': [playground['longitude'], playground['latitude']]
                }
        
        # Insert the data
        result = collection.insert_many(playgrounds)
        
        # Create geospatial index
        collection.create_index([('location', '2dsphere')])
        
        print(f"Successfully imported {len(result.inserted_ids)} playgrounds into {collection_name}")
        return True
    except Exception as e:
        print(f"Error importing data: {e}")
        return False

def main():
    # Connect to MongoDB Atlas
    db = connect_to_mongodb()
    if not db:
        return
    
    # Import London playgrounds
    print("\nImporting London playgrounds...")
    import_playground_data(db, 'london_playgrounds.json', 'london_playgrounds')
    
    # Basic query to verify data
    london_collection = db['london_playgrounds']
    count = london_collection.count_documents({})
    print(f"\nVerification:")
    print(f"Total London playgrounds in database: {count}")
    
    # Example of a playground near central London
    print("\nExample: Finding playgrounds near central London (near Big Ben)...")
    central_london = {
        'location': {
            '$near': {
                '$geometry': {
                    'type': 'Point',
                    'coordinates': [-0.124625, 51.500729]  # Big Ben coordinates
                },
                '$maxDistance': 2000  # 2km radius
            }
        }
    }
    
    nearby_playgrounds = london_collection.find(central_london).limit(3)
    print("\nNearby playgrounds:")
    for playground in nearby_playgrounds:
        print(f"- {playground['name']} ({playground['street']})")

if __name__ == "__main__":
    main() 