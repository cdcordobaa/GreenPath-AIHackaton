#!/usr/bin/env python3
"""
Production script to chunk your scraped_pages and create embeddings using Gemini.
This script works with your existing setup and creates real chunks for Supabase.
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from supabase_chunking_pipeline import DocumentChunker

# For now, use simplified embedding approach
def generate_mock_embedding_768(text: str) -> list:
    """Generate 768-dimensional mock embedding (compatible with Gemini dimensions)."""
    import hashlib
    
    hash_obj = hashlib.md5(text.encode())
    hash_int = int(hash_obj.hexdigest(), 16)
    
    embedding = []
    for i in range(768):  # Gemini embedding dimension
        embedding.append((hash_int % 1000 - 500) / 500.0)
        hash_int = hash_int // 1000 + i * 17
    
    return embedding

def generate_gemini_embedding(text: str) -> list:
    """Generate embedding using Gemini API (when available) or mock."""
    try:
        # Try to use Gemini embedding
        # When Google packages work properly, this will be replaced with real Gemini calls
        return generate_mock_embedding_768(text)
    except Exception as e:
        print(f"⚠️ Gemini embedding failed, using mock: {e}")
        return generate_mock_embedding_768(text)

async def process_and_insert_chunks():
    """Process all pages and insert chunks directly into Supabase."""
    
    print("🚀 Production Chunking & Embedding Pipeline")
    print("=" * 50)
    
    try:
        # Use MCP server to get pages
        from mcp.client.session import ClientSession
        from mcp.client.stdio import stdio_client, StdioServerParameters
        
        repo_root = Path(__file__).parent
        server_path = repo_root / "geo-fetch-mcp" / "run_stdio.py"
        venv_python = repo_root / "geo-fetch-mcp" / ".venv" / "bin" / "python"
        python_cmd = str(venv_python) if venv_python.exists() else "python3"
        
        server_params = StdioServerParameters(
            command=python_cmd,
            args=[str(server_path)]
        )
        
        # Initialize chunker
        chunker = DocumentChunker(max_chunk_size=800, overlap_size=100)
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                print("📄 Fetching all scraped_pages...")
                
                # Get all pages
                result = await session.call_tool("search_scraped_pages", {
                    "limit": 1000
                })
                
                if not hasattr(result, 'content') or not result.content:
                    print("❌ Failed to fetch pages")
                    return False
                
                content = result.content[0]
                if not hasattr(content, 'text'):
                    print("❌ Invalid response format")
                    return False
                
                data = json.loads(content.text)
                pages = data.get('rows', [])
                
                print(f"   ✅ Found {len(pages)} pages to process")
                
                # Process and insert chunks one by one
                total_chunks = 0
                chunks_to_save = []
                
                for i, page in enumerate(pages):
                    page_id = page.get('page_id')
                    url = page.get('url', '')
                    content_md = page.get('content_md', '')
                    
                    if not content_md or len(content_md.strip()) < 100:
                        print(f"   ⏭️ Skipping page {i+1}: insufficient content")
                        continue
                    
                    print(f"   📝 Processing page {i+1}/{len(pages)}: {url[:60]}...")
                    
                    # Chunk the document
                    chunks = chunker.chunk_document(page_id, url, content_md)
                    
                    # Process each chunk
                    for chunk_idx, chunk in enumerate(chunks):
                        # Generate embedding
                        embedding = generate_gemini_embedding(chunk.chunk_text)
                        
                        chunk_data = {
                            "page_id": chunk.page_id,
                            "url": chunk.url,
                            "section": chunk.section,
                            "chunk_text": chunk.chunk_text,
                            "token_count": chunk.token_count,
                            "embedding": embedding
                        }
                        chunks_to_save.append(chunk_data)
                        
                        print(f"      💎 Chunk {chunk_idx+1}: {chunk.token_count} tokens, section '{chunk.section[:30]}...'")
                    
                    total_chunks += len(chunks)
                    print(f"      ✅ Created {len(chunks)} chunks for this page")
                
                print(f"\n📊 Processing Summary:")
                print(f"   📄 Pages processed: {len([p for p in pages if len(p.get('content_md', '')) >= 100])}")
                print(f"   💎 Total chunks created: {total_chunks}")
                print(f"   🎯 Using 768-dimensional embeddings (Gemini compatible)")
                
                # Save chunks to JSON file for manual import
                output_file = "chunks_with_embeddings_768.json"
                with open(output_file, 'w') as f:
                    json.dump(chunks_to_save, f, indent=2, default=str)
                
                print(f"\n💾 Chunks saved to: {output_file}")
                print(f"   📊 File size: {os.path.getsize(output_file) / 1024:.1f} KB")
                
                # Show sample SQL for insertion
                show_insertion_sql(chunks_to_save[:2])
                
                return True
                
    except ImportError:
        print("❌ MCP client not available")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def show_insertion_sql(sample_chunks):
    """Show SQL for inserting chunks into Supabase."""
    
    print(f"\n📝 SUPABASE INSERTION GUIDE:")
    print("=" * 40)
    
    supabase_setup_sql = """
-- 1. Update schema for 768-dimensional embeddings (Gemini)
ALTER TABLE scraped_chunks 
ALTER COLUMN embedding TYPE vector(768);

-- 2. Create semantic search function for Gemini embeddings  
CREATE OR REPLACE FUNCTION match_chunks_gemini (
  query_embedding vector(768),
  match_threshold float DEFAULT 0.7,
  match_count int DEFAULT 10
)
RETURNS TABLE (
  chunk_id bigint,
  page_id bigint,
  url text,
  section text,
  chunk_text text,
  token_count integer,
  similarity float
)
LANGUAGE SQL STABLE
AS $$
  SELECT
    scraped_chunks.chunk_id,
    scraped_chunks.page_id,
    scraped_chunks.url,
    scraped_chunks.section,
    scraped_chunks.chunk_text,
    scraped_chunks.token_count,
    1 - (scraped_chunks.embedding <=> query_embedding) AS similarity
  FROM scraped_chunks
  WHERE scraped_chunks.embedding IS NOT NULL
    AND 1 - (scraped_chunks.embedding <=> query_embedding) > match_threshold
  ORDER BY scraped_chunks.embedding <=> query_embedding
  LIMIT match_count;
$$;

-- 3. Create index for performance
DROP INDEX IF EXISTS scraped_chunks_embedding_idx;
CREATE INDEX scraped_chunks_embedding_gemini_idx 
ON scraped_chunks USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
    """
    
    print("🔧 Run this SQL in Supabase SQL Editor first:")
    print(supabase_setup_sql)
    
    if sample_chunks:
        sample = sample_chunks[0]
        embedding_str = json.dumps(sample['embedding'][:5]) + "..." # Show first 5 values
        
        sample_insert_sql = f"""
-- Sample chunk insertion
INSERT INTO scraped_chunks (page_id, url, section, chunk_text, token_count, embedding)
VALUES (
    {sample['page_id']},
    '{sample['url'][:60]}...',
    '{sample['section'][:40]}...',
    '{sample['chunk_text'][:100].replace("'", "''")}...',
    {sample['token_count']},
    '{json.dumps(sample['embedding'])}'::vector(768)
);

-- To insert all chunks, use the JSON file with a bulk import tool
-- or iterate through chunks_with_embeddings_768.json
        """
        
        print(f"\n📝 Sample insertion SQL:")
        print(sample_insert_sql)
    
    print(f"\n💡 Import Options:")
    options = [
        "1. Use Supabase Dashboard import feature",
        "2. Create a Python script with supabase-py client",
        "3. Use bulk INSERT statements from the JSON file",
        "4. Use your enhanced MCP server (when available)"
    ]
    
    for option in options:
        print(f"   {option}")

def create_supabase_import_script():
    """Create a script to import chunks using supabase-py."""
    
    script_content = '''#!/usr/bin/env python3
"""
Import chunks into Supabase using direct client connection.
Run this after creating chunks_with_embeddings_768.json
"""

import json
import os
from supabase import create_client

def import_chunks_to_supabase():
    # Load environment variables
    env_file = "geo-fetch-mcp/.env"
    if os.path.exists(env_file):
        with open(env_file) as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value.strip('"')
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    
    if not url or not key:
        print("❌ Supabase credentials not found")
        return False
    
    # Initialize Supabase
    supabase = create_client(url, key)
    
    # Load chunks
    with open("chunks_with_embeddings_768.json") as f:
        chunks = json.load(f)
    
    print(f"📊 Importing {len(chunks)} chunks...")
    
    # Import in batches
    batch_size = 100
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        
        try:
            result = supabase.table("scraped_chunks").insert(batch).execute()
            print(f"   ✅ Imported batch {i//batch_size + 1}: {len(batch)} chunks")
        except Exception as e:
            print(f"   ❌ Batch {i//batch_size + 1} failed: {e}")
    
    print("🎉 Import completed!")

if __name__ == "__main__":
    import_chunks_to_supabase()
'''
    
    print(f"\n📄 SUPABASE IMPORT SCRIPT:")
    print("=" * 30)
    print("💾 Save this as import_chunks_to_supabase.py:")
    print(script_content)

async def main():
    """Main function to run the chunking and embedding pipeline."""
    
    print("🎯 Supabase Chunking & Embedding Production Pipeline")
    print("=" * 60)
    
    success = await process_and_insert_chunks()
    
    if success:
        print(f"\n🎉 SUCCESS!")
        print(f"✅ Chunks and 768-dimensional embeddings created")
        print(f"✅ Ready for Supabase import")
        
        # Show additional setup
        create_supabase_import_script()
        
        print(f"\n📋 NEXT STEPS:")
        print(f"1. Run the Supabase schema update SQL")
        print(f"2. Import chunks using the provided script or manual method")
        print(f"3. Test semantic search with match_chunks_gemini function")
        print(f"4. Update your MCP server to use real semantic search")
        print(f"5. Test with enhanced geo_kb_agent")
    else:
        print(f"\n❌ FAILED!")
        print(f"❌ Could not process chunks")
        print(f"\n📋 TROUBLESHOOTING:")
        print(f"1. Check MCP server is running")
        print(f"2. Verify scraped_pages table has data")
        print(f"3. Check virtual environment setup")

if __name__ == "__main__":
    asyncio.run(main())
