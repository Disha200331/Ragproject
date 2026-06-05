from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

neo4j_url = os.getenv("NEO4J_URL", "bolt://localhost:7687")
neo4j_username = os.getenv("NEO4J_USERNAME", "neo4j")
neo4j_password = os.getenv("NEO4J_PASSWORD")

print("Checking Neo4j Knowledge Graph...")
print("=" * 60)

try:
    driver = GraphDatabase.driver(neo4j_url, auth=(neo4j_username, neo4j_password))
    
    with driver.session() as session:
        # Check node count
        result = session.run("MATCH (n) RETURN COUNT(n) as node_count")
        node_count = result.single()["node_count"]
        print(f"✅ Total nodes in database: {node_count}")
        
        # Check relationship count
        result = session.run("MATCH ()-[r]->() RETURN COUNT(r) as rel_count")
        rel_count = result.single()["rel_count"]
        print(f"✅ Total relationships: {rel_count}")
        
        # Show sample nodes
        result = session.run("MATCH (n) RETURN n.id, labels(n) LIMIT 10")
        print(f"\n📊 Sample nodes:")
        for record in result:
            node_id = record["n.id"]
            labels = record["labels(n)"]
            print(f"   - {node_id} ({', '.join(labels)})")
        
        # Show sample relationships
        result = session.run("MATCH ()-[r]->() RETURN type(r) as rel_type LIMIT 10")
        print(f"\n🔗 Sample relationships:")
        for record in result:
            print(f"   - {record['rel_type']}")
        
        # Check if knowledge graph is empty
        if node_count == 0:
            print("\n❌ Knowledge graph is EMPTY!")
            print("   The pipeline may not have completed successfully.")
            print("   Run: python rag_pipeline.py")
        else:
            print(f"\n✅ Knowledge graph exists with {node_count} nodes!")
            print("   You can view it at: http://localhost:7474")
    
    driver.close()
    
except Exception as e:
    print(f"❌ Error connecting to Neo4j: {e}")
    print("   Make sure Neo4j is running: neo4j.bat console")
