#!/usr/bin/env python3
"""
Production script to chunk your scraped_pages and create embeddings.
This processes your actual Supabase data.
"""

import os
import sys
import asyncio
from pathlib import Path
from supabase_chunking_pipeline import DocumentChunker, EmbeddingGenerator

# Add geo-fetch-mcp to path for Supabase client
sys.path.insert(0, str(Path(__file__).parent / "geo-fetch-mcp"))

async def chunk_all_pages_via_mcp():
    """Process all pages using MCP server and create chunks."""
    
    print("🚀 Production Chunking Pipeline - Via MCP")
    print("=" * 50)
    
    try:
        # Connect to MCP server
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
        
        # Initialize processors
        chunker = DocumentChunker(max_chunk_size=800, overlap_size=100)
        embedder = EmbeddingGenerator(use_openai=True)  # Try to use real OpenAI
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                print("📄 Fetching all scraped_pages...")
                
                # Get all pages
                result = await session.call_tool("search_scraped_pages", {
                    "limit": 1000  # Get all pages
                })
                
                if not hasattr(result, 'content') or not result.content:
                    print("❌ Failed to fetch pages")
                    return False
                
                content = result.content[0]
                if not hasattr(content, 'text'):
                    print("❌ Invalid response format")
                    return False
                
                import json
                data = json.loads(content.text)
                pages = data.get('rows', [])
                
                print(f"   ✅ Found {len(pages)} pages to process")
                
                # Process each page
                all_chunks_for_insert = []
                total_chunks = 0
                
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
                    
                    # Generate embeddings for each chunk
                    page_chunks = []
                    for chunk in chunks:
                        embedding = embedder.generate_embedding(chunk.chunk_text)
                        
                        chunk_data = {
                            "page_id": chunk.page_id,
                            "url": chunk.url,
                            "section": chunk.section,
                            "chunk_text": chunk.chunk_text,
                            "token_count": chunk.token_count,
                            "embedding": embedding
                        }
                        page_chunks.append(chunk_data)
                        all_chunks_for_insert.append(chunk_data)
                    
                    total_chunks += len(chunks)
                    print(f"      💎 Created {len(chunks)} chunks")
                
                print(f"\n✅ Chunking completed!")
                print(f"   📄 Pages processed: {len([p for p in pages if len(p.get('content_md', '')) >= 100])}")
                print(f"   💎 Total chunks created: {total_chunks}")
                print(f"   🎯 Using {'OpenAI' if embedder.use_openai else 'mock'} embeddings")
                
                # Save chunks to file for manual insertion
                output_file = "chunks_for_supabase.json"
                with open(output_file, 'w') as f:
                    json.dump(all_chunks_for_insert, f, indent=2, default=str)
                
                print(f"\n💾 Chunks saved to: {output_file}")
                print(f"   📊 File size: {os.path.getsize(output_file) / 1024:.1f} KB")
                
                # Show SQL for manual insertion
                print_insertion_sql(all_chunks_for_insert[:3])  # Show sample
                
                return True
                
    except ImportError:
        print("❌ MCP client not available")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def chunk_all_pages_direct():
    """Alternative: Process pages using direct Supabase connection."""
    
    print("🚀 Production Chunking Pipeline - Direct Supabase")
    print("=" * 50)
    
    try:
        from supabase import create_client
        
        # Get credentials from geo-fetch-mcp/.env
        env_file = Path(__file__).parent / "geo-fetch-mcp" / ".env"
        if env_file.exists():
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
        
        # Initialize processors
        chunker = DocumentChunker(max_chunk_size=800, overlap_size=100)
        embedder = EmbeddingGenerator(use_openai=True)
        
        print("📄 Fetching all scraped_pages from Supabase...")
        
        # Get all pages
        pages_response = supabase.table("scraped_pages").select("*").execute()
        pages = pages_response.data
        
        print(f"   ✅ Found {len(pages)} pages to process")
        
        all_chunks = []
        total_chunks = 0
        
        for i, page in enumerate(pages):
            page_id = page["page_id"]
            url = page["url"]
            content = page["content_md"]
            
            if not content or len(content.strip()) < 100:
                print(f"   ⏭️ Skipping page {i+1}: insufficient content")
                continue
            
            print(f"   📝 Processing page {i+1}/{len(pages)}: {url[:60]}...")
            
            # Chunk the document
            chunks = chunker.chunk_document(page_id, url, content)
            
            # Process each chunk
            for chunk in chunks:
                embedding = embedder.generate_embedding(chunk.chunk_text)
                
                chunk_data = {
                    "page_id": chunk.page_id,
                    "url": chunk.url,
                    "section": chunk.section,
                    "chunk_text": chunk.chunk_text,
                    "token_count": chunk.token_count,
                    "embedding": embedding
                }
                all_chunks.append(chunk_data)
                
                # Insert directly into Supabase
                try:
                    supabase.table("scraped_chunks").insert(chunk_data).execute()
                except Exception as e:
                    print(f"      ⚠️ Insert failed for chunk: {e}")
            
            total_chunks += len(chunks)
            print(f"      💎 Created and inserted {len(chunks)} chunks")
        
        print(f"\n✅ Processing completed!")
        print(f"   📄 Pages processed: {len([p for p in pages if len(p.get('content_md', '')) >= 100])}")
        print(f"   💎 Total chunks created: {total_chunks}")
        print(f"   💾 Chunks inserted into scraped_chunks table")
        
        return True
        
    except ImportError:
        print("❌ Supabase client not available - install with: pip install supabase")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def print_insertion_sql(sample_chunks):
    """Print sample SQL for manual chunk insertion."""
    
    print(f"\n📝 SAMPLE SQL FOR MANUAL INSERTION:")
    print("=" * 40)
    
    if not sample_chunks:
        print("No chunks to show")
        return
    
    sample = sample_chunks[0]
    
    sql = f"""
-- Sample chunk insertion (repeat for all chunks)
INSERT INTO scraped_chunks (page_id, url, section, chunk_text, token_count, embedding)
VALUES (
    {sample['page_id']},
    '{sample['url'][:50]}...',
    '{sample['section'][:30]}...',
    '{sample['chunk_text'][:100].replace("'", "''")}...',
    {sample['token_count']},
    '{str(sample['embedding'][:5])}...'::vector(1536)
);

-- To insert all chunks from JSON file:
-- 1. Load the chunks_for_supabase.json file
-- 2. Use a script or tool to batch insert all chunks
-- 3. Or use Supabase dashboard's import feature
    """
    
    print(sql)

async def main():
    """Main function to run the chunking pipeline."""
    
    print("🎯 Supabase Chunking & Embedding Pipeline")
    print("=" * 60)
    
    # Try MCP approach first
    print("Attempting via MCP server...")
    success = await chunk_all_pages_via_mcp()
    
    if not success:
        print("\nAttempting direct Supabase connection...")
        success = chunk_all_pages_direct()
    
    if success:
        print(f"\n🎉 SUCCESS!")
        print(f"✅ Chunks and embeddings created successfully")
        print(f"✅ Ready to test semantic search")
        
        print(f"\n📋 NEXT STEPS:")
        print(f"1. Run the Supabase setup SQL from supabase_chunking_pipeline.py")
        print(f"2. Verify chunks in scraped_chunks table")
        print(f"3. Test semantic search with your enhanced MCP server")
        print(f"4. Use the enhanced geo_kb_agent with strategy='hybrid'")
    else:
        print(f"\n❌ FAILED!")
        print(f"❌ Could not process chunks")
        print(f"\n📋 TROUBLESHOOTING:")
        print(f"1. Check Supabase credentials in geo-fetch-mcp/.env")
        print(f"2. Install required packages: pip install supabase openai")
        print(f"3. Set OPENAI_API_KEY for real embeddings")
        print(f"4. Run supabase_chunking_pipeline.py for demo mode")

if __name__ == "__main__":
    asyncio.run(main())
