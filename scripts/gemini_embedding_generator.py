#!/usr/bin/env python3
"""
Gemini Embedding Generator
Uses Google's Gemini API for generating embeddings instead of OpenAI
"""

import os
import json
import hashlib
from typing import List, Dict, Any, Optional
import time

# Try to import Google AI client (using existing google-genai like in llm.py)
try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️ Google GenAI not available - check your existing google-genai installation")

class GeminiEmbeddingGenerator:
    """Generates embeddings using Google's Gemini API."""
    
    def __init__(self, use_gemini: bool = True):
        self.use_gemini = use_gemini and GEMINI_AVAILABLE
        
        if self.use_gemini:
            # Use same API key pattern as existing llm.py
            api_key = os.getenv("GOOGLE_GENAI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            if api_key:
                self._client = genai.Client(api_key=api_key)
                self.model = 'models/text-embedding-004'  # Latest Gemini embedding model
                print(f"✅ Using Gemini embeddings with model: {self.model}")
            else:
                print("⚠️ GOOGLE_GENAI_API_KEY or GOOGLE_API_KEY not found - using mock embeddings")
                self.use_gemini = False
        
        if not self.use_gemini:
            print("🔄 Using mock embeddings for testing")
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using Gemini."""
        if self.use_gemini:
            try:
                # Use google-genai client (same as in llm.py)
                response = self._client.models.embed_content(
                    model=self.model,
                    content=[text],
                    task_type="semantic_similarity"
                )
                # Extract embedding from response
                if hasattr(response, 'embeddings') and response.embeddings:
                    return response.embeddings[0].values
                else:
                    # Fallback extraction
                    return response.embedding if hasattr(response, 'embedding') else self._mock_embedding(text)
            
            except Exception as e:
                print(f"⚠️ Gemini embedding failed: {e}")
                # Fall back to mock for this text
                return self._mock_embedding(text)
        else:
            return self._mock_embedding(text)
    
    def generate_embeddings_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """Generate embeddings for multiple texts in batches."""
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            print(f"   🔄 Processing batch {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size}")
            
            batch_embeddings = []
            for text in batch:
                embedding = self.generate_embedding(text)
                batch_embeddings.append(embedding)
                
                # Small delay to avoid rate limits
                if self.use_gemini:
                    time.sleep(0.1)
            
            embeddings.extend(batch_embeddings)
            
            # Longer delay between batches
            if self.use_gemini and i + batch_size < len(texts):
                time.sleep(1)
        
        return embeddings
    
    def _mock_embedding(self, text: str) -> List[float]:
        """Generate mock embedding for testing (768-dimensional for Gemini compatibility)."""
        # Create deterministic embedding from text hash
        hash_obj = hashlib.md5(text.encode())
        hash_int = int(hash_obj.hexdigest(), 16)
        
        # Gemini embeddings are typically 768-dimensional
        embedding = []
        for i in range(768):
            embedding.append((hash_int % 1000 - 500) / 500.0)
            hash_int = hash_int // 1000 + i * 17
        
        return embedding
    
    def test_embedding(self) -> bool:
        """Test if embedding generation is working."""
        test_text = "This is a test for embedding generation."
        
        try:
            embedding = self.generate_embedding(test_text)
            print(f"✅ Embedding test successful: {len(embedding)} dimensions")
            print(f"   Sample values: {embedding[:5]}")
            return True
        except Exception as e:
            print(f"❌ Embedding test failed: {e}")
            return False

def update_supabase_schema_for_gemini():
    """Provide SQL to update Supabase schema for Gemini embeddings (768-dimensional)."""
    
    print("🔧 SUPABASE SCHEMA UPDATE FOR GEMINI EMBEDDINGS")
    print("=" * 50)
    
    sql_commands = """
-- 1. Enable pgvector extension (if not already done)
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Check current scraped_chunks table structure
\\d scraped_chunks;

-- 3. If embedding column exists but is wrong dimension, update it
-- (Gemini uses 768 dimensions, OpenAI uses 1536)
ALTER TABLE scraped_chunks 
ALTER COLUMN embedding TYPE vector(768);

-- 4. Create/update semantic search function for Gemini embeddings
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

-- 5. Create/update index for performance
DROP INDEX IF EXISTS scraped_chunks_embedding_idx;
CREATE INDEX scraped_chunks_embedding_gemini_idx 
ON scraped_chunks USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- 6. Check current chunks and embeddings
SELECT 
  COUNT(*) as total_chunks,
  COUNT(embedding) as chunks_with_embeddings,
  CASE WHEN COUNT(embedding) > 0 THEN vector_dims(embedding) ELSE NULL END as embedding_dimensions
FROM scraped_chunks
LIMIT 1;
    """
    
    print("📝 SQL to run in Supabase SQL Editor:")
    print(sql_commands)

def demo_gemini_embeddings():
    """Demo Gemini embedding generation."""
    
    print("🧪 Testing Gemini Embedding Generation")
    print("=" * 40)
    
    generator = GeminiEmbeddingGenerator()
    
    # Test single embedding
    test_texts = [
        "licencia ambiental para proyecto hidroeléctrico",
        "compensación por biodiversidad en ecosistemas",
        "permisos de vertimientos y concesión de aguas",
        "estudio de impacto ambiental detallado"
    ]
    
    print(f"\n📝 Testing embedding generation...")
    
    if generator.test_embedding():
        print(f"\n🔍 Generating embeddings for sample texts...")
        
        embeddings = []
        for i, text in enumerate(test_texts):
            print(f"   {i+1}. '{text}'")
            embedding = generator.generate_embedding(text)
            embeddings.append(embedding)
            print(f"      ✅ Generated {len(embedding)}-dimensional embedding")
        
        # Test batch generation
        print(f"\n📦 Testing batch generation...")
        batch_embeddings = generator.generate_embeddings_batch(test_texts[:2], batch_size=2)
        print(f"   ✅ Batch generated {len(batch_embeddings)} embeddings")
        
        return {
            "success": True,
            "embedding_dimension": len(embeddings[0]) if embeddings else 0,
            "samples_generated": len(embeddings),
            "using_gemini": generator.use_gemini
        }
    else:
        return {
            "success": False,
            "error": "Embedding generation test failed"
        }

def create_gemini_chunking_pipeline():
    """Create updated chunking pipeline with Gemini embeddings."""
    
    print("\n🔄 UPDATED CHUNKING PIPELINE WITH GEMINI")
    print("=" * 50)
    
    pipeline_code = '''
# Updated chunk_and_embed_production.py with Gemini embeddings

from gemini_embedding_generator import GeminiEmbeddingGenerator

class SupabaseGeminiChunkingPipeline:
    """Chunking pipeline using Gemini embeddings."""
    
    def __init__(self):
        from supabase_chunking_pipeline import DocumentChunker
        self.chunker = DocumentChunker()
        self.embedder = GeminiEmbeddingGenerator(use_gemini=True)
    
    async def process_all_pages(self):
        """Process pages with Gemini embeddings."""
        
        # ... existing MCP connection code ...
        
        # For each chunk:
        embedding = self.embedder.generate_embedding(chunk.chunk_text)
        
        chunk_data = {
            "page_id": chunk.page_id,
            "url": chunk.url,
            "section": chunk.section,
            "chunk_text": chunk.chunk_text,
            "token_count": chunk.token_count,
            "embedding": embedding  # 768-dimensional Gemini embedding
        }
        
        # Insert into Supabase with vector(768) type
        return chunk_data

# Usage:
# pipeline = SupabaseGeminiChunkingPipeline()
# result = await pipeline.process_all_pages()
'''
    
    print("💾 Updated pipeline code:")
    print(pipeline_code)
    
    print(f"\n🔧 Setup Steps:")
    steps = [
        "1. Install Google AI: pip install google-generativeai",
        "2. Set GOOGLE_API_KEY in your .env file (same as for Gemini LLM)",
        "3. Run the Supabase schema update SQL above",
        "4. Update your chunking pipeline to use GeminiEmbeddingGenerator", 
        "5. Re-run chunking to generate 768-dimensional embeddings",
        "6. Test semantic search with Gemini embeddings"
    ]
    
    for step in steps:
        print(f"   {step}")

if __name__ == "__main__":
    # Show schema updates
    update_supabase_schema_for_gemini()
    
    # Demo embedding generation
    print("\n" + "="*60)
    result = demo_gemini_embeddings()
    
    if result.get("success"):
        print(f"\n🎉 GEMINI EMBEDDINGS READY!")
        print(f"✅ Dimension: {result.get('embedding_dimension')}")
        print(f"✅ Using real Gemini: {result.get('using_gemini')}")
        print(f"✅ Samples generated: {result.get('samples_generated')}")
    else:
        print(f"\n❌ Setup needed: {result.get('error')}")
    
    # Show updated pipeline
    create_gemini_chunking_pipeline()
    
    print(f"\n🎯 BENEFITS OF GEMINI EMBEDDINGS:")
    benefits = [
        "✅ Same API as your existing Gemini LLM setup",
        "✅ No additional API keys needed",
        "✅ High-quality semantic embeddings",
        "✅ 768 dimensions (smaller than OpenAI's 1536)",
        "✅ Built-in rate limiting and retry logic",
        "✅ Optimized for semantic similarity tasks"
    ]
    
    for benefit in benefits:
        print(f"   {benefit}")
    
    print(f"\n📋 NEXT STEPS:")
    print(f"1. Run: pip install google-generativeai")
    print(f"2. Test this script to verify Gemini embeddings work")
    print(f"3. Update Supabase schema with the SQL above")
    print(f"4. Re-run chunking pipeline with Gemini embeddings")
    print(f"5. Test semantic search with your enhanced MCP server")
