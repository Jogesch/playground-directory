import json
from datetime import datetime
from typing import Dict, List
from neo4j import GraphDatabase
import logging
from tqdm import tqdm
import requests
from time import sleep

class PlaygroundNeo4jMigrator:
    def __init__(self, uri: str, username: str, password: str, json_file: str):
        """Initialize the migrator"""
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        self.json_file = json_file
        self.logger = logging.getLogger(__name__)
        
    def close(self):
        """Close the Neo4j connection"""
        self.driver.close()
        
    def load_json_data(self) -> Dict:
        """Load data from JSON file"""
        with open(self.json_file, 'r') as f:
            return json.load(f)
            
    def get_location_from_name(self, name: str) -> str:
        """Extract location information from the playground name"""
        # Common location indicators that might appear in names
        location_indicators = ['street', 'road', 'avenue', 'lane', 'way', 'close', 'drive', 
                             'grove', 'gardens', 'park', 'square', 'hill', 'place', 'terrace',
                             'court', 'crescent', 'boulevard', 'row', 'walk', 'alley']
        
        name_parts = name.lower().split()
        for i, word in enumerate(name_parts):
            if word in location_indicators and i > 0:
                # Return the word before the indicator plus the indicator
                return f"{name_parts[i-1].title()} {word.title()}"
        return ""

    def get_street_from_coordinates(self, lat: float, lon: float) -> str:
        """Use Nominatim to get street name from coordinates"""
        try:
            # Be nice to the Nominatim API
            sleep(1)
            
            url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
            headers = {
                'User-Agent': 'PlaygroundDirectory/1.0'
            }
            
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                
                # Try to get the street name from the address
                if 'address' in data:
                    addr = data['address']
                    # Try different fields in order of preference
                    for field in ['road', 'street', 'footway', 'path', 'pedestrian']:
                        if field in addr:
                            return addr[field]
                            
                    # If no street found but we have a suburb or neighbourhood
                    for field in ['suburb', 'neighbourhood', 'quarter']:
                        if field in addr:
                            return f"{addr[field]} Area"
                            
            return ""
        except Exception as e:
            self.logger.warning(f"Error in reverse geocoding: {str(e)}")
            return ""
            
    def get_street_name(self, address: str, city: str, lat: float = None, lon: float = None) -> str:
        """Extract or generate a street name from address or nearby location"""
        if address:
            # Split address and process each part
            parts = [p.strip() for p in address.split(',')]
            
            # Look for street indicators
            street_indicators = ['street', 'road', 'avenue', 'lane', 'way', 'close', 'drive', 
                               'grove', 'gardens', 'park', 'square', 'hill', 'place', 'terrace',
                               'court', 'crescent', 'boulevard', 'row', 'walk', 'alley']
            
            # First try to find a part containing a street indicator
            for part in parts:
                part_lower = part.lower()
                if any(indicator in part_lower for indicator in street_indicators):
                    return part.strip()
            
            # If no street indicator found, use the first non-empty part that's not just the city name
            for part in parts:
                if part and part.lower() != city.lower():
                    return part.strip()
        
        # If no address or no suitable part found, try reverse geocoding
        if lat is not None and lon is not None:
            street = self.get_street_from_coordinates(lat, lon)
            if street:
                return street
                
        # If all else fails
        return f"Unknown {city} Location"
        
    def is_generic_name(self, name: str) -> bool:
        """Determine if a playground name is generic and needs location context"""
        # Strictly generic names that don't include location information
        generic_names = {
            'playground',
            'play area',
            "children's playground",
            'kids playground',
            'play park',
            'playpark',
            'kids playzone',
            'play ground',
            'childrens playground',
            'kids play area',
            'play space',
            'playspace'
        }
        
        name_lower = name.lower().strip()
        
        # If the name is exactly one of our generic names
        if name_lower in generic_names:
            return True
            
        # If it's just "[Something] Playground" where Something is very generic
        if name_lower.endswith('playground'):
            prefix = name_lower.replace('playground', '').strip()
            generic_prefixes = {'the', 'local', 'community', 'public', 'new', 'old'}
            if prefix in generic_prefixes:
                return True
                
        return False
        
    def clean_playground_name(self, name: str, address: str, city: str, lat: float = None, lon: float = None) -> str:
        """Clean generic playground names by adding location context"""
        if self.is_generic_name(name):
            # First try to get location from address or coordinates
            street = self.get_street_name(address, city, lat, lon)
            
            # If no proper street name found, try to extract from original name
            if street.startswith('Unknown'):
                location_from_name = self.get_location_from_name(name)
                if location_from_name:
                    return f"Playground on {location_from_name}"
                else:
                    return f"Unnamed Playground in {city}"
            return f"Playground on {street}"
        return name
        
    def generate_friendly_description(self, entry: Dict) -> str:
        """Generate a varied, matter-of-fact description for a playground"""
        features = entry["features"]
        equipment = features["equipment_categories"]
        amenities = features["amenities"]
        ratings = entry["ratings"]
        
        # Build description components
        parts = []
        
        # Start with different types of openings
        avg_rating = ratings.get("average") if ratings.get("average") is not None else 0
        equipment_list = [k.replace("_", " ") for k, v in equipment.items() if v]
        
        # Choose an opening based on the playground's key features
        if equipment_list:
            if len(equipment_list) == 1:
                parts.append(f"A playground centered around its {equipment_list[0]} area")
            elif len(equipment_list) == 2:
                parts.append(f"{equipment_list[0].title()} and {equipment_list[1]} equipment form the core of this playground")
            else:
                equipment_str = ", ".join(equipment_list[:-1]) + f", and {equipment_list[-1]}"
                parts.append(f"A diverse playground offering {equipment_str}")
        elif avg_rating >= 4:
            parts.append("A highly-rated playground in the local community")
        elif amenities.get("fencing") and (amenities.get("seating") or amenities.get("shade")):
            parts.append("A secure, family-friendly playground")
        else:
            parts.append("A neighborhood playground")
            
        # Add location if available
        if entry["location"]["address"]:
            parts[0] += f" located on {entry['location']['address']}"
        parts[0] += "."
        
        # Age range as a separate statement if specific
        if features.get("age_range") and features["age_range"] != "all":
            parts.append(f"Best suited for {features['age_range']}.")
        
        # Amenities description with varied sentence structures
        amenity_desc = []
        if amenities.get("seating") and amenities.get("shade"):
            amenity_desc.append("shaded seating areas")
        elif amenities.get("seating"):
            amenity_desc.append("seating areas")
        elif amenities.get("shade"):
            amenity_desc.append("shaded areas")
            
        if amenities.get("toilets") and amenities.get("cafe"):
            amenity_desc.append("toilets and café")
        elif amenities.get("toilets"):
            amenity_desc.append("toilet facilities")
        elif amenities.get("cafe"):
            amenity_desc.append("café")
            
        if amenities.get("parking") and amenities.get("bike_parking"):
            amenity_desc.append("car and bike parking")
        elif amenities.get("parking"):
            amenity_desc.append("parking")
        elif amenities.get("bike_parking"):
            amenity_desc.append("bike racks")
            
        if amenities.get("fencing"):
            amenity_desc.append("secure fencing")
            
        if amenity_desc:
            # Vary the sentence structure based on the number and type of amenities
            if len(amenity_desc) == 1:
                if "fencing" in amenity_desc[0]:
                    parts.append(f"The area is enclosed with {amenity_desc[0]}.")
                elif "parking" in amenity_desc[0]:
                    parts.append(f"{amenity_desc[0].title()} available.")
                else:
                    parts.append(f"Includes {amenity_desc[0]}.")
            else:
                amenities_str = ", ".join(amenity_desc[:-1]) + f", and {amenity_desc[-1]}"
                parts.append(f"Facilities include {amenities_str}.")
        
        # Safety features with varied descriptions
        safety_desc = []
        if amenities.get("safety_surface"):
            safety_desc.append("safety surfacing")
        if amenities.get("lighting"):
            safety_desc.append("lighting")
        if amenities.get("cctv"):
            safety_desc.append("CCTV")
        if amenities.get("first_aid"):
            safety_desc.append("first aid station")
            
        if safety_desc:
            if len(safety_desc) == 1:
                parts.append(f"Equipped with {safety_desc[0]}.")
            else:
                safety_str = ", ".join(safety_desc)
                parts.append(f"Safety features: {safety_str}.")
        
        # Add rating information if significant
        if avg_rating > 0:
            stars = "★" * int(round(avg_rating))
            review_count = ratings.get("review_count", 0) or 0
            if review_count > 20:
                parts.append(f"Popular with the community, rated {stars} across {review_count} reviews.")
            elif review_count > 10:
                parts.append(f"Rated {stars} based on {review_count} community reviews.")
            elif avg_rating >= 4:
                parts.append(f"Early visitors rate this playground {stars}.")
        
        # Join all parts into a cohesive paragraph
        description = " ".join(parts)
            
        return description
        
    def migrate_playground(self, tx, entry: Dict):
        """Migrate a single playground entry"""
        # Get the address and coordinates
        address = entry["location"]["address"] or ""
        lat = entry["location"]["coordinates"]["latitude"]
        lon = entry["location"]["coordinates"]["longitude"]
        
        # Clean up generic names
        cleaned_name = self.clean_playground_name(
            entry["name"],
            address,
            entry["location"]["city"],
            lat,
            lon
        )
        
        # Generate friendly description
        description = self.generate_friendly_description(entry)
        
        # Create location-aware slug with coordinates
        base_slug = entry["slug"]
        coord_str = f"{lat:.6f}-{lon:.6f}".replace(".", "p")  # Replace dots with 'p' for valid slug
        
        location_parts = [
            base_slug,
            entry['location']['city'].lower().replace(' ', '-'),
        ]
        
        if entry['location']['postcode']:
            location_parts.append(entry['location']['postcode'].lower().replace(' ', '-'))
            
        location_parts.append(coord_str)
        location_slug = "-".join(location_parts)
            
        # Create playground node with composite key of name and location
        playground_query = """
        MERGE (p:Playground {
            slug: $slug,
            name: $name,
            region: $region,
            city: $city,
            postcode: $postcode,
            location: point({latitude: $latitude, longitude: $longitude}),
            address: $address
        })
        SET p += {
            description: $description,
            age_range: $age_range,
            avg_rating: $avg_rating,
            review_count: $review_count,
            popularity_score: $popularity_score,
            last_updated: datetime($last_updated),
            base_slug: $base_slug
        }
        RETURN elementId(p) as playground_id
        """
        
        # Handle null ratings with defaults
        avg_rating = entry["ratings"]["average"] if entry["ratings"]["average"] is not None else 0.0
        review_count = entry["ratings"]["review_count"] if entry["ratings"]["review_count"] is not None else 0
        popularity_score = entry["ratings"]["popularity_score"] if entry["ratings"]["popularity_score"] is not None else 0.0
        
        result = tx.run(
            playground_query,
            slug=location_slug,
            base_slug=base_slug,
            name=cleaned_name,
            description=description,
            region=entry["location"]["region"],
            address=address,
            city=entry["location"]["city"],
            postcode=entry["location"]["postcode"],
            latitude=lat,
            longitude=lon,
            age_range=entry["features"]["age_range"] or "all",
            avg_rating=avg_rating,
            review_count=review_count,
            popularity_score=popularity_score,
            last_updated=entry["additional_info"]["last_updated"]
        )
        
        playground_id = result.single()["playground_id"]
        
        # First, remove any existing relationships and related nodes
        cleanup_query = """
        MATCH (p:Playground)-[r]->(n)
        WHERE elementId(p) = $playground_id
        DETACH DELETE n
        """
        tx.run(cleanup_query, playground_id=playground_id)
        
        # Create equipment relationships (from equipment_categories)
        equipment_query = """
        MATCH (p:Playground) WHERE elementId(p) = $playground_id
        MERGE (et:Value {name: $type, category: 'EquipmentType'})
        CREATE (e:Equipment {has_equipment: $has_equipment})
        CREATE (p)-[:HAS_EQUIPMENT]->(e)-[:IS_TYPE]->(et)
        """
        
        for equip_type, has_equip in entry["features"]["equipment_categories"].items():
            tx.run(equipment_query,
                playground_id=playground_id,
                type=equip_type,
                has_equipment=has_equip
            )
            
        # Create amenities node (from amenities, excluding equipment fields)
        equipment_fields = {'climbing', 'swings', 'slides', 'activity', 'sports', 'water', 'sensory', 'safety_surface'}
        amenities = {
            f"has_{k}": v 
            for k, v in entry["features"]["amenities"].items() 
            if k not in equipment_fields
        }
        
        amenities_query = """
        MATCH (p:Playground) WHERE elementId(p) = $playground_id
        CREATE (a:Amenities {
            has_parking: $has_parking,
            has_toilets: $has_toilets,
            has_cafe: $has_cafe,
            has_seating: $has_seating,
            has_shade: $has_shade,
            has_fencing: $has_fencing,
            has_accessibility: $has_accessibility,
            has_bike_parking: $has_bike_parking
        })
        CREATE (p)-[:HAS_AMENITIES]->(a)
        """
        
        tx.run(amenities_query,
            playground_id=playground_id,
            **amenities
        )
        
        # Create safety features node
        safety_fields = {'lighting', 'cctv', 'first_aid'}
        safety_features = {
            f"has_{k}": entry["features"]["amenities"].get(k, False)
            for k in safety_fields
        }
        safety_features["has_safety_surface"] = entry["features"]["amenities"].get("safety_surface", False)
        
        safety_query = """
        MATCH (p:Playground) WHERE elementId(p) = $playground_id
        CREATE (s:Safety {
            has_safety_surface: $has_safety_surface,
            has_lighting: $has_lighting,
            has_cctv: $has_cctv,
            has_first_aid: $has_first_aid
        })
        CREATE (p)-[:HAS_SAFETY_FEATURES]->(s)
        """
        
        tx.run(safety_query,
            playground_id=playground_id,
            **safety_features
        )
        
        # Create reviews
        if entry["ratings"]["reviews"]:
            review_query = """
            MATCH (p:Playground) WHERE elementId(p) = $playground_id
            CREATE (r:Review {
                title: $title,
                text: $text,
                rating: $rating,
                date: datetime($date),
                source: $source
            })
            CREATE (p)-[:HAS_REVIEW]->(r)
            """
            
            for review_data in entry["ratings"]["reviews"]:
                if review_data.get("text"):  # Only create reviews with actual content
                    tx.run(review_query,
                        playground_id=playground_id,
                        **review_data
                    )
            
        # Create tags
        tag_query = """
        MATCH (p:Playground) WHERE elementId(p) = $playground_id
        MERGE (t:Tag {value: $tag, category: $category})
        CREATE (p)-[:TAGGED_WITH]->(t)
        """
        
        for category, tag_list in entry["metadata"].items():
            category = category.replace("_tags", "")
            for tag_value in tag_list:
                tx.run(tag_query,
                    playground_id=playground_id,
                    tag=tag_value,
                    category=category
                )
                
    def migrate_all(self):
        """Migrate all playground data to Neo4j"""
        data = self.load_json_data()
        total = len(data["entries"])
        
        print(f"Starting migration of {total} playgrounds...")
        
        with self.driver.session() as session:
            for entry in tqdm(data["entries"], desc="Migrating playgrounds"):
                try:
                    session.execute_write(self.migrate_playground, entry)
                except Exception as e:
                    self.logger.error(f"Error migrating playground {entry.get('name', 'Unknown')}: {str(e)}")
                    raise
                
        print("\nMigration completed successfully!")
        
        # Print summary
        self._print_summary()
        
    def _print_summary(self):
        """Print migration summary"""
        summary_queries = {
            "Total playgrounds": "MATCH (p:Playground) RETURN count(p) as count",
            "Total equipment": "MATCH (:Playground)-[:HAS_EQUIPMENT]->(e:Equipment) RETURN count(e) as count",
            "Total reviews": "MATCH (:Playground)-[:HAS_REVIEW]->(r:Review) RETURN count(r) as count",
            "Total tags": "MATCH (:Playground)-[:TAGGED_WITH]->(t:Tag) RETURN count(t) as count",
            "By region": """
                MATCH (p:Playground)
                RETURN p.region as region, count(p) as count
                ORDER BY count DESC
            """
        }
        
        print("\nMigration Summary:")
        print("-" * 50)
        
        with self.driver.session() as session:
            for label, query in summary_queries.items():
                result = session.run(query)
                if label == "By region":
                    print("\nPlaygrounds by region:")
                    for record in result:
                        print(f"  {record['region']}: {record['count']}")
                else:
                    count = result.single()["count"]
                    print(f"{label}: {count}")
                    
def main():
    """Main function to run the migration"""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Neo4j connection details (should be in environment variables in production)
    uri = "neo4j://localhost:7687"
    username = "neo4j"
    password = "ah3EBPP9U_JCkru"  # Updated password
    json_file = "playground_directory.json"
    
    try:
        migrator = PlaygroundNeo4jMigrator(uri, username, password, json_file)
        migrator.migrate_all()
        migrator.close()
    except Exception as e:
        print(f"Error during migration: {str(e)}")
        raise
        
if __name__ == "__main__":
    main() 