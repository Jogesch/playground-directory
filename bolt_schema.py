from bolt import Bolt, Index, Field, Reference
from enum import Enum
from typing import List, Dict, Optional
from datetime import datetime

class Region(str, Enum):
    GREATER_LONDON = "Greater London"
    CITY_OF_GLASGOW = "City of Glasgow"
    OTHER = "Other"
    UNKNOWN = "Unknown"

class AgeGroup(str, Enum):
    TODDLER = "toddler_friendly"
    CHILD = "child_friendly"
    OLDER = "older_kids"

class EquipmentType(str, Enum):
    CLIMBING = "climbing"
    SWINGS = "swings"
    SLIDES = "slides"
    ACTIVITY = "activity"
    SPORTS = "sports"
    WATER = "water"
    SENSORY = "sensory"

# Define the Bolt schema
bolt = Bolt("playground_directory")

# Playground Schema
playground = bolt.table("playground", [
    Field("name", str, required=True),
    Field("slug", str, required=True, unique=True),
    Field("description", str, required=True),
    Field("region", Region, required=True),
    Field("address", str),
    Field("city", str),
    Field("postcode", str),
    Field("latitude", float),
    Field("longitude", float),
    Field("age_range", str),
    Field("age_categories", List[AgeGroup]),
    Field("avg_rating", float),
    Field("review_count", int),
    Field("popularity_score", float),
    Field("last_updated", datetime),
])

# Equipment Schema
equipment = bolt.table("equipment", [
    Field("playground_id", Reference("playground"), required=True),
    Field("type", EquipmentType, required=True),
    Field("has_equipment", bool, required=True),
])

# Amenities Schema
amenities = bolt.table("amenities", [
    Field("playground_id", Reference("playground"), required=True),
    Field("has_parking", bool),
    Field("has_toilets", bool),
    Field("has_cafe", bool),
    Field("has_seating", bool),
    Field("has_shade", bool),
    Field("has_fencing", bool),
    Field("has_accessibility", bool),
    Field("has_bike_parking", bool),
])

# Safety Features Schema
safety = bolt.table("safety_features", [
    Field("playground_id", Reference("playground"), required=True),
    Field("has_safety_surface", bool),
    Field("has_lighting", bool),
    Field("has_cctv", bool),
    Field("has_first_aid", bool),
])

# Reviews Schema
review = bolt.table("review", [
    Field("playground_id", Reference("playground"), required=True),
    Field("title", str),
    Field("text", str),
    Field("rating", float),
    Field("date", datetime),
    Field("source", str),
])

# Tags Schema
tag = bolt.table("tag", [
    Field("playground_id", Reference("playground"), required=True),
    Field("tag", str, required=True),
    Field("category", str, required=True),  # primary, feature, or search
])

# Create indexes for efficient querying
playground.create_index(Index("region_idx", ["region"]))
playground.create_index(Index("location_idx", ["latitude", "longitude"]))
playground.create_index(Index("popularity_idx", ["popularity_score"]))
playground.create_index(Index("rating_idx", ["avg_rating"]))
playground.create_index(Index("slug_idx", ["slug"], unique=True))

equipment.create_index(Index("equipment_type_idx", ["type", "has_equipment"]))
tag.create_index(Index("tag_search_idx", ["tag", "category"]))

# Create composite indexes for common queries
playground.create_index(Index("region_rating_idx", ["region", "avg_rating"]))
playground.create_index(Index("region_popularity_idx", ["region", "popularity_score"]))

# Create spatial index for location-based queries
playground.create_spatial_index("spatial_idx", ["latitude", "longitude"]) 