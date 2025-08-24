#!/usr/bin/env python3
"""
Debug Neo4j connection and database content
"""
import os
import sys
from pathlib import Path

# Add the mcp-geo2neo directory to Python path
sys.path.insert(0, str(Path("mcp-geo2neo").resolve()))

try:
    from neo4j_io import run_tx, driver
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    load_dotenv("mcp-geo2neo/.env", override=True)
    
    print("🔍 Neo4j Connection Debug")
    print("=" * 50)
    
    # Check environment variables
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USERNAME", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
    
    print(f"📊 Environment Configuration:")
    print(f"   NEO4J_URI: {neo4j_uri}")
    print(f"   NEO4J_USERNAME: {neo4j_user}")
    print(f"   NEO4J_PASSWORD: {'*' * len(neo4j_password) if neo4j_password else 'Not set'}")
    
    # Test basic connection
    print(f"\n🔌 Testing Neo4j Connection...")
    
    try:
        # Simple query to test connection
        records, meta = run_tx("RETURN 1 as test", {})
        print(f"   ✅ Connection successful!")
        print(f"   📊 Query metadata: {meta}")
        print(f"   📋 Test result: {records}")
        
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        print(f"   💡 Check if Neo4j is running and credentials are correct")
        sys.exit(1)
    
    # Check database content
    print(f"\n🗄️  Checking Database Content...")
    
    try:
        # Count all nodes
        records, meta = run_tx("MATCH (n) RETURN count(n) as total_nodes", {})
        total_nodes = records[0]['total_nodes'] if records else 0
        print(f"   📊 Total nodes in database: {total_nodes}")
        
        if total_nodes == 0:
            print(f"   ❌ Database is empty!")
            print(f"\n💡 Recommendations:")
            print(f"   - The Neo4j database is empty and needs to be populated")
            print(f"   - Check if there's a data import script or dump file")
            print(f"   - Verify the database name/connection is correct")
            sys.exit(0)
        
        # Get node labels
        records, meta = run_tx("CALL db.labels()", {})
        labels = [r['label'] for r in records] if records else []
        print(f"   🏷️  Node labels: {labels}")
        
        # Check for Category nodes specifically
        if 'Category' in labels:
            records, meta = run_tx("MATCH (c:Category) RETURN count(c) as category_count", {})
            category_count = records[0]['category_count'] if records else 0
            print(f"   📂 Category nodes: {category_count}")
            
            if category_count > 0:
                # Get sample categories and their aliases
                records, meta = run_tx("""
                    MATCH (c:Category) 
                    RETURN c.name as name, c.aliases as aliases 
                    LIMIT 10
                """, {})
                
                print(f"   📋 Sample Categories:")
                for record in records:
                    name = record.get('name', 'No name')
                    aliases = record.get('aliases', [])
                    print(f"      📂 {name}")
                    print(f"         🏷️  Aliases: {aliases}")
            else:
                print(f"   ❌ No Category nodes found!")
        else:
            print(f"   ❌ No 'Category' label found in database!")
        
        # Check for other important node types
        important_labels = ['Instrument', 'NormativeInstrument', 'Subcategory', 'Resource']
        for label in important_labels:
            if label in labels:
                records, meta = run_tx(f"MATCH (n:{label}) RETURN count(n) as count", {})
                count = records[0]['count'] if records else 0
                print(f"   📊 {label} nodes: {count}")
        
        # Check relationships
        records, meta = run_tx("CALL db.relationshipTypes()", {})
        rel_types = [r['relationshipType'] for r in records] if records else []
        print(f"   🔗 Relationship types: {rel_types}")
        
        # Count total relationships
        records, meta = run_tx("MATCH ()-[r]->() RETURN count(r) as total_rels", {})
        total_rels = records[0]['total_rels'] if records else 0
        print(f"   🔗 Total relationships: {total_rels}")
        
    except Exception as e:
        print(f"   ❌ Database inspection failed: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n💡 Recommendations:")
    if total_nodes == 0:
        print(f"   - The Neo4j database is empty and needs to be populated")
        print(f"   - Check if there's a data import script or dump file")
        print(f"   - Verify the database name/connection is correct")
    elif 'Category' not in labels:
        print(f"   - Database has data but no 'Category' nodes")
        print(f"   - Check if the data model is different than expected")
        print(f"   - Verify the Cypher query in map_by_aliases is correct")
    else:
        print(f"   - Database structure looks correct")
        print(f"   - Issue might be with specific category aliases")
        print(f"   - Try using the exact aliases shown above")

except ImportError as e:
    print(f"❌ Import error: {e}")
    print(f"💡 Make sure you're in the correct directory and dependencies are installed")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
