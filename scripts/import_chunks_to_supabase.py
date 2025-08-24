#!/usr/bin/env python3
"""
Import chunks with embeddings into Supabase.
This script imports the chunks_with_embeddings_768.json file into your Supabase database.
"""

import json
import os
import sys
from pathlib import Path

def load_environment():
    """Load environment variables from geo-fetch-mcp/.env"""
    env_file = Path("geo-fetch-mcp/.env")
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if line.strip() and not line.startswith('#') and '=' in line:
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value.strip('"\'')
        print("✅ Environment variables loaded from geo-fetch-mcp/.env")
    else:
        print("⚠️ No .env file found, using system environment variables")

def import_chunks_to_supabase():
    """Import all chunks with embeddings to Supabase."""
    
    print("🚀 Importing Chunks with Embeddings to Supabase")
    print("=" * 50)
    
    # Load environment
    load_environment()
    
    try:
        from supabase import create_client
        print("✅ Supabase client imported successfully")
    except ImportError:
        print("❌ Supabase client not available")
        print("   Install with: pip install supabase")
        return False
    
    # Get Supabase credentials
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    
    if not url or not key:
        print("❌ Supabase credentials not found")
        print("   Required: SUPABASE_URL and SUPABASE_KEY in geo-fetch-mcp/.env")
        return False
    
    print(f"✅ Supabase URL: {url[:30]}...")
    print(f"✅ Supabase Key: {key[:20]}...")
    
    # Initialize Supabase client
    try:
        supabase = create_client(url, key)
        print("✅ Supabase client created successfully")
    except Exception as e:
        print(f"❌ Failed to create Supabase client: {e}")
        return False
    
    # Load chunks file
    chunks_file = "chunks_with_embeddings_768.json"
    if not os.path.exists(chunks_file):
        print(f"❌ Chunks file not found: {chunks_file}")
        print("   Run chunk_with_embeddings_production.py first")
        return False
    
    print(f"📄 Loading chunks from {chunks_file}...")
    try:
        with open(chunks_file) as f:
            chunks = json.load(f)
        print(f"✅ Loaded {len(chunks)} chunks ({os.path.getsize(chunks_file) / 1024:.1f} KB)")
    except Exception as e:
        print(f"❌ Failed to load chunks file: {e}")
        return False
    
    # Verify chunk structure
    if chunks and len(chunks) > 0:
        sample = chunks[0]
        required_fields = ['page_id', 'url', 'section', 'chunk_text', 'token_count', 'embedding']
        missing_fields = [field for field in required_fields if field not in sample]
        
        if missing_fields:
            print(f"❌ Missing required fields in chunks: {missing_fields}")
            return False
        
        embedding_dim = len(sample['embedding'])
        print(f"✅ Chunk structure verified: {embedding_dim}-dimensional embeddings")
        
        if embedding_dim != 768:
            print(f"⚠️ Warning: Expected 768 dimensions, got {embedding_dim}")
    
    # Import chunks in batches
    print(f"\n💾 Starting import of {len(chunks)} chunks...")
    batch_size = 100
    total_batches = (len(chunks) + batch_size - 1) // batch_size
    successful_imports = 0
    failed_imports = 0
    
    for i in range(0, len(chunks), batch_size):
        batch_num = i // batch_size + 1
        batch = chunks[i:i + batch_size]
        
        print(f"   📦 Importing batch {batch_num}/{total_batches}: {len(batch)} chunks...")
        
        try:
            result = supabase.table("scraped_chunks").insert(batch).execute()
            successful_imports += len(batch)
            print(f"      ✅ Batch {batch_num} imported successfully")
        except Exception as e:
            failed_imports += len(batch)
            print(f"      ❌ Batch {batch_num} failed: {e}")
            
            # Try to get more specific error info
            if "duplicate key" in str(e).lower():
                print(f"         💡 Tip: Some chunks may already exist in database")
            elif "vector" in str(e).lower():
                print(f"         💡 Tip: Check if Supabase schema supports vector(768)")
    
    # Summary
    print(f"\n📊 Import Summary:")
    print(f"   ✅ Successfully imported: {successful_imports} chunks")
    print(f"   ❌ Failed imports: {failed_imports} chunks")
    print(f"   📈 Success rate: {successful_imports/(successful_imports+failed_imports)*100:.1f}%")
    
    if successful_imports > 0:
        print(f"\n🎉 Import completed! Chunks are now available for semantic search.")
        return True
    else:
        print(f"\n❌ Import failed completely. Check Supabase schema and credentials.")
        return False

def verify_import():
    """Verify that chunks were imported correctly."""
    
    print(f"\n🔍 Verifying Import...")
    
    # Load environment
    load_environment()
    
    try:
        from supabase import create_client
        
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        supabase = create_client(url, key)
        
        # Check total count
        result = supabase.table("scraped_chunks").select("chunk_id", count="exact").execute()
        total_chunks = result.count if hasattr(result, 'count') else len(result.data)
        
        print(f"   📊 Total chunks in database: {total_chunks}")
        
        # Check chunks with embeddings
        result = supabase.table("scraped_chunks").select("chunk_id").not_.is_("embedding", "null").execute()
        chunks_with_embeddings = len(result.data)
        
        print(f"   🎯 Chunks with embeddings: {chunks_with_embeddings}")
        
        if chunks_with_embeddings > 0:
            print(f"   ✅ Embeddings successfully imported!")
            return True
        else:
            print(f"   ❌ No embeddings found in database")
            return False
            
    except Exception as e:
        print(f"   ❌ Verification failed: {e}")
        return False

def show_next_steps():
    """Show what to do after successful import."""
    
    print(f"\n🎯 NEXT STEPS AFTER SUCCESSFUL IMPORT:")
    print("=" * 40)
    
    steps = [
        "1. ✅ Chunks imported - Ready for semantic search!",
        "2. 🔧 Update your MCP server to use real embeddings",
        "3. 🧪 Test semantic search with match_chunks_gemini function",
        "4. 🤖 Use enhanced geo_kb_agent with hybrid strategies",
        "5. 🚀 Run full workflow with comprehensive document analysis"
    ]
    
    for step in steps:
        print(f"   {step}")
    
    print(f"\n💡 Test semantic search in Supabase SQL editor:")
    test_sql = """
-- Test semantic search (replace with actual embedding)
SELECT chunk_text, similarity 
FROM match_chunks_gemini(
    '[0.1, 0.2, 0.3, ...]'::vector(768),  -- Query embedding
    0.7,  -- Similarity threshold
    5     -- Number of results
);
"""
    print(test_sql)

if __name__ == "__main__":
    print("🎯 Supabase Chunks Import Script")
    print("=" * 60)
    
    success = import_chunks_to_supabase()
    
    if success:
        verify_import()
        show_next_steps()
    
    print(f"\n{'🎉 SUCCESS!' if success else '❌ FAILED!'}")
    sys.exit(0 if success else 1)
