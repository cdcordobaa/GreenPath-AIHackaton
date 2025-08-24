#!/usr/bin/env python3
"""
Fix Supabase RLS issues and import chunks.
This script handles Row Level Security policies that prevent chunk imports.
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

def fix_rls_and_import():
    """Fix RLS issues and import chunks."""
    
    print("🔧 Fixing Supabase RLS and Importing Chunks")
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
    
    # Get Supabase credentials - try service role key first
    url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_SERVICE_KEY")
    anon_key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    
    if not url:
        print("❌ SUPABASE_URL not found")
        return False
    
    # Try service role key first (bypasses RLS)
    if service_key:
        print("✅ Using service role key (bypasses RLS)")
        key = service_key
    elif anon_key:
        print("⚠️ Using anon key - may need to disable RLS")
        key = anon_key
    else:
        print("❌ No Supabase key found")
        print("   Need SUPABASE_SERVICE_ROLE_KEY or SUPABASE_KEY")
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
    
    # Test connection and check RLS
    print("\n🔍 Testing Supabase connection...")
    try:
        # Try to read from scraped_chunks
        result = supabase.table("scraped_chunks").select("chunk_id").limit(1).execute()
        print(f"✅ Can read from scraped_chunks: {len(result.data)} rows")
        
        # Try to insert a test record
        test_chunk = {
            "page_id": 999999,
            "url": "test://rls-test",
            "section": "Test Section",
            "chunk_text": "This is a test chunk for RLS verification",
            "token_count": 10,
            "embedding": [0.1] * 768  # 768-dimensional test embedding
        }
        
        try:
            test_result = supabase.table("scraped_chunks").insert(test_chunk).execute()
            print("✅ Can insert into scraped_chunks - RLS not blocking")
            
            # Clean up test record
            if test_result.data:
                test_id = test_result.data[0].get('chunk_id')
                if test_id:
                    supabase.table("scraped_chunks").delete().eq('chunk_id', test_id).execute()
                    print("✅ Test record cleaned up")
            
            rls_blocking = False
        except Exception as e:
            if "row-level security" in str(e).lower():
                print("❌ RLS is blocking inserts")
                rls_blocking = True
            else:
                print(f"❌ Insert test failed: {e}")
                return False
                
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False
    
    # If RLS is blocking, provide solutions
    if rls_blocking:
        print(f"\n🔧 RLS SOLUTIONS:")
        print("=" * 20)
        
        solutions = [
            "1. Use service role key instead of anon key",
            "2. Temporarily disable RLS on scraped_chunks table",
            "3. Create RLS policy that allows inserts",
            "4. Use Supabase dashboard to import manually"
        ]
        
        for solution in solutions:
            print(f"   {solution}")
        
        print(f"\n📝 SQL to temporarily disable RLS:")
        disable_rls_sql = """
-- Run in Supabase SQL Editor:
ALTER TABLE scraped_chunks DISABLE ROW LEVEL SECURITY;

-- After import, re-enable if needed:
-- ALTER TABLE scraped_chunks ENABLE ROW LEVEL SECURITY;
"""
        print(disable_rls_sql)
        
        print(f"\n📝 SQL to create permissive RLS policy:")
        create_policy_sql = """
-- Run in Supabase SQL Editor:
CREATE POLICY "Allow all operations on scraped_chunks" 
ON scraped_chunks FOR ALL 
USING (true) 
WITH CHECK (true);
"""
        print(create_policy_sql)
        
        return False
    
    # Load and import chunks
    chunks_file = "chunks_with_embeddings_768.json"
    if not os.path.exists(chunks_file):
        print(f"❌ Chunks file not found: {chunks_file}")
        return False
    
    print(f"\n📄 Loading chunks from {chunks_file}...")
    try:
        with open(chunks_file) as f:
            chunks = json.load(f)
        print(f"✅ Loaded {len(chunks)} chunks")
    except Exception as e:
        print(f"❌ Failed to load chunks: {e}")
        return False
    
    # Import chunks in smaller batches
    print(f"\n💾 Starting import of {len(chunks)} chunks...")
    batch_size = 50  # Smaller batches for better error handling
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
            
            # Stop on first failure to avoid spam
            if batch_num <= 3:  # Show first few errors
                print(f"         💡 Error details: {str(e)[:200]}...")
    
    # Summary
    print(f"\n📊 Import Summary:")
    print(f"   ✅ Successfully imported: {successful_imports} chunks")
    print(f"   ❌ Failed imports: {failed_imports} chunks")
    
    if successful_imports > 0:
        success_rate = successful_imports/(successful_imports+failed_imports)*100
        print(f"   📈 Success rate: {success_rate:.1f}%")
        print(f"\n🎉 Import completed! {successful_imports} chunks available for semantic search.")
        return True
    else:
        print(f"   📈 Success rate: 0.0%")
        print(f"\n❌ Import failed completely.")
        return False

def show_manual_import_options():
    """Show alternative import methods."""
    
    print(f"\n📋 MANUAL IMPORT OPTIONS:")
    print("=" * 30)
    
    options = [
        "1. 🌐 Supabase Dashboard Import:",
        "   • Go to your Supabase dashboard",
        "   • Navigate to Table Editor > scraped_chunks",
        "   • Use 'Import data' feature",
        "   • Upload chunks_with_embeddings_768.json",
        "",
        "2. 🔧 SQL Import (for smaller batches):",
        "   • Use the provided SQL in setup_supabase_embeddings.sql",
        "   • Manually insert chunks using SQL statements",
        "",
        "3. 🐍 Direct psql connection:",
        "   • Connect directly to PostgreSQL",
        "   • Use COPY command for bulk import",
        "",
        "4. 🔑 Service Role Key:",
        "   • Get service role key from Supabase dashboard",
        "   • Add SUPABASE_SERVICE_ROLE_KEY to .env file",
        "   • Re-run this script"
    ]
    
    for option in options:
        print(f"   {option}")

if __name__ == "__main__":
    print("🎯 Supabase RLS Fix and Import Script")
    print("=" * 60)
    
    success = fix_rls_and_import()
    
    if not success:
        show_manual_import_options()
    
    print(f"\n{'🎉 SUCCESS!' if success else '❌ FAILED - See solutions above'}")
    sys.exit(0 if success else 1)
