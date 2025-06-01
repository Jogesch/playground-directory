import json
from datetime import datetime
from typing import Dict, List, Any
from neo4j import GraphDatabase
import logging
from tqdm import tqdm

class BoltExporter:
    def __init__(self, source_uri: str, source_username: str, source_password: str,
                 target_uri: str = None, target_username: str = None, target_password: str = None):
        """Initialize the exporter with source and optional target credentials"""
        self.source_driver = GraphDatabase.driver(source_uri, auth=(source_username, source_password))
        self.target_driver = None
        if target_uri and target_username and target_password:
            self.target_driver = GraphDatabase.driver(target_uri, auth=(target_username, target_password))
        self.logger = logging.getLogger(__name__)
        
    def close(self):
        """Close Neo4j connections"""
        self.source_driver.close()
        if self.target_driver:
            self.target_driver.close()
            
    def export_to_file(self, output_file: str):
        """Export Neo4j data to a Bolt-compatible format file"""
        data = {
            "metadata": {
                "exported_at": datetime.now().isoformat(),
                "format_version": "1.0"
            },
            "nodes": [],
            "relationships": []
        }
        
        with self.source_driver.session() as session:
            # Export nodes
            self.logger.info("Exporting nodes...")
            
            # Export Playground nodes
            playground_query = """
            MATCH (p:Playground)
            RETURN p
            """
            playgrounds = session.run(playground_query)
            for record in tqdm(playgrounds, desc="Exporting playgrounds"):
                node = record["p"]
                node_data = {
                    "id": node.element_id,
                    "labels": list(node.labels),
                    "properties": dict(node.items())
                }
                # Convert Neo4j Point to dict
                if "location" in node_data["properties"]:
                    location = node_data["properties"]["location"]
                    node_data["properties"]["location"] = {
                        "latitude": location.latitude,
                        "longitude": location.longitude
                    }
                # Convert datetime to ISO format
                if "last_updated" in node_data["properties"]:
                    node_data["properties"]["last_updated"] = node_data["properties"]["last_updated"].isoformat()
                data["nodes"].append(node_data)
                
            # Export Value nodes (equipment types)
            value_query = """
            MATCH (v:Value)
            RETURN v
            """
            values = session.run(value_query)
            for record in tqdm(values, desc="Exporting values"):
                node = record["v"]
                node_data = {
                    "id": node.element_id,
                    "labels": list(node.labels),
                    "properties": dict(node.items())
                }
                data["nodes"].append(node_data)
                
            # Export Equipment nodes
            equipment_query = """
            MATCH (e:Equipment)
            RETURN e
            """
            equipment = session.run(equipment_query)
            for record in tqdm(equipment, desc="Exporting equipment"):
                node = record["e"]
                node_data = {
                    "id": node.element_id,
                    "labels": list(node.labels),
                    "properties": dict(node.items())
                }
                data["nodes"].append(node_data)
                
            # Export relationships
            self.logger.info("Exporting relationships...")
            rel_query = """
            MATCH ()-[r]->()
            RETURN r, startNode(r) as source, endNode(r) as target
            """
            relationships = session.run(rel_query)
            for record in tqdm(relationships, desc="Exporting relationships"):
                rel = record["r"]
                rel_data = {
                    "id": rel.element_id,
                    "type": rel.type,
                    "source_id": record["source"].element_id,
                    "target_id": record["target"].element_id,
                    "properties": dict(rel.items())
                }
                data["relationships"].append(rel_data)
                
        # Write to file
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
            
        self.logger.info(f"Export completed. Data written to {output_file}")
        
        # Print summary
        print("\nExport Summary:")
        print("-" * 50)
        print(f"Total nodes: {len(data['nodes'])}")
        print(f"Total relationships: {len(data['relationships'])}")
        label_counts = {}
        for node in data["nodes"]:
            for label in node["labels"]:
                label_counts[label] = label_counts.get(label, 0) + 1
        print("\nNode counts by label:")
        for label, count in label_counts.items():
            print(f"  {label}: {count}")
            
    def import_from_file(self, input_file: str):
        """Import data from a Bolt-compatible format file into Neo4j"""
        if not self.target_driver:
            raise ValueError("Target Neo4j connection details not provided")
            
        with open(input_file, 'r') as f:
            data = json.load(f)
            
        with self.target_driver.session() as session:
            # Clear existing data
            self.logger.info("Clearing existing data...")
            session.run("MATCH (n) DETACH DELETE n")
            
            # Create nodes
            self.logger.info("Creating nodes...")
            for node in tqdm(data["nodes"], desc="Creating nodes"):
                labels = ":".join(node["labels"])
                props = {k: v for k, v in node["properties"].items()}
                
                # Handle location point
                if "location" in props:
                    loc = props["location"]
                    props["location"] = f"point({{latitude: {loc['latitude']}, longitude: {loc['longitude']}}})"
                    
                # Create node
                create_query = f"""
                CREATE (n:{labels})
                SET n = $props
                """
                session.run(create_query, props=props)
                
            # Create relationships
            self.logger.info("Creating relationships...")
            for rel in tqdm(data["relationships"], desc="Creating relationships"):
                create_query = f"""
                MATCH (source) WHERE id(source) = $source_id
                MATCH (target) WHERE id(target) = $target_id
                CREATE (source)-[r:{rel['type']}]->(target)
                SET r = $props
                """
                session.run(
                    create_query,
                    source_id=rel["source_id"],
                    target_id=rel["target_id"],
                    props=rel["properties"]
                )
                
        self.logger.info("Import completed successfully")

def main():
    """Main function to run the export"""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Neo4j connection details (should be in environment variables in production)
    source_uri = "neo4j://localhost:7687"
    source_username = "neo4j"
    source_password = "ah3EBPP9U_JCkru"
    
    try:
        exporter = BoltExporter(source_uri, source_username, source_password)
        exporter.export_to_file("playground_data_bolt.json")
        exporter.close()
    except Exception as e:
        print(f"Error during export: {str(e)}")
        raise
        
if __name__ == "__main__":
    main() 