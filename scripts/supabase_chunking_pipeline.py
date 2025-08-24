#!/usr/bin/env python3
"""
Supabase Chunking and Embedding Pipeline
Creates chunks from scraped_pages and generates embeddings
"""

import os
import re
import json
import asyncio
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

# For production embeddings
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️ OpenAI not available - will use mock embeddings")

@dataclass
class DocumentChunk:
    """Represents a document chunk for processing."""
    page_id: int
    url: str
    section: str
    chunk_text: str
    token_count: int
    chunk_index: int

class DocumentChunker:
    """Chunks documents into manageable pieces for embedding."""
    
    def __init__(self, max_chunk_size: int = 800, overlap_size: int = 100):
        self.max_chunk_size = max_chunk_size  # tokens
        self.overlap_size = overlap_size      # tokens
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)."""
        return len(text.split()) + len(text) // 4
    
    def split_text_into_chunks(self, text: str, max_size: int = None) -> List[str]:
        """Split text into overlapping chunks."""
        if max_size is None:
            max_size = self.max_chunk_size
        
        # Clean text
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence_tokens = self.estimate_tokens(sentence)
            
            # If adding this sentence would exceed max size, finalize current chunk
            if current_size + sentence_tokens > max_size and current_chunk:
                chunk_text = ' '.join(current_chunk)
                chunks.append(chunk_text)
                
                # Start new chunk with overlap
                overlap_sentences = current_chunk[-2:] if len(current_chunk) >= 2 else current_chunk
                current_chunk = overlap_sentences
                current_size = sum(self.estimate_tokens(s) for s in overlap_sentences)
            
            current_chunk.append(sentence)
            current_size += sentence_tokens
        
        # Add final chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append(chunk_text)
        
        return chunks
    
    def extract_sections(self, content: str, url: str) -> List[Tuple[str, str]]:
        """Extract sections from content."""
        sections = []
        
        # Try to identify sections by headers
        header_pattern = r'^(#{1,6})\s+(.+)$'
        lines = content.split('\n')
        
        current_section = "Introduction"
        current_content = []
        
        for line in lines:
            header_match = re.match(header_pattern, line.strip())
            if header_match:
                # Save previous section
                if current_content:
                    section_text = '\n'.join(current_content).strip()
                    if section_text:
                        sections.append((current_section, section_text))
                
                # Start new section
                current_section = header_match.group(2).strip()
                current_content = []
            else:
                current_content.append(line)
        
        # Add final section
        if current_content:
            section_text = '\n'.join(current_content).strip()
            if section_text:
                sections.append((current_section, section_text))
        
        # If no sections found, treat entire content as one section
        if not sections:
            sections.append(("Main Content", content))
        
        return sections
    
    def chunk_document(self, page_id: int, url: str, content: str) -> List[DocumentChunk]:
        """Chunk a document into smaller pieces."""
        chunks = []
        
        # Extract sections
        sections = self.extract_sections(content, url)
        
        chunk_index = 0
        for section_name, section_content in sections:
            # Split section into chunks
            text_chunks = self.split_text_into_chunks(section_content)
            
            for chunk_text in text_chunks:
                if len(chunk_text.strip()) < 50:  # Skip very small chunks
                    continue
                
                token_count = self.estimate_tokens(chunk_text)
                
                chunk = DocumentChunk(
                    page_id=page_id,
                    url=url,
                    section=section_name,
                    chunk_text=chunk_text.strip(),
                    token_count=token_count,
                    chunk_index=chunk_index
                )
                chunks.append(chunk)
                chunk_index += 1
        
        return chunks

class EmbeddingGenerator:
    """Generates embeddings for text chunks."""
    
    def __init__(self, use_openai: bool = True):
        self.use_openai = use_openai and OPENAI_AVAILABLE
        if self.use_openai:
            openai.api_key = os.getenv('OPENAI_API_KEY')
            if not openai.api_key:
                print("⚠️ OPENAI_API_KEY not found - using mock embeddings")
                self.use_openai = False
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text."""
        if self.use_openai:
            try:
                response = openai.embeddings.create(
                    input=text,
                    model="text-embedding-3-small"
                )
                return response.data[0].embedding
            except Exception as e:
                print(f"⚠️ OpenAI embedding failed: {e}")
                return self._mock_embedding(text)
        else:
            return self._mock_embedding(text)
    
    def _mock_embedding(self, text: str) -> List[float]:
        """Generate mock embedding for testing."""
        # Create deterministic embedding from text hash
        hash_obj = hashlib.md5(text.encode())
        hash_int = int(hash_obj.hexdigest(), 16)
        
        embedding = []
        for i in range(1536):  # Standard embedding dimension
            embedding.append((hash_int % 1000 - 500) / 500.0)
            hash_int = hash_int // 1000 + i * 17
        
        return embedding

async def demo_chunking_pipeline():
    """Demonstrate the chunking pipeline without MCP dependencies."""
    
    print("🚀 Supabase Chunking Pipeline Demo")
    print("=" * 40)
    
    chunker = DocumentChunker()
    embedder = EmbeddingGenerator()
    
    # Sample document content (simulating scraped_pages data)
    sample_pages = [
        {
            "page_id": 1,
            "url": "https://anla.gov.co/licencias-ambientales",
            "content_md": """
# Licencias Ambientales en Colombia

## Marco Legal
La licencia ambiental es un instrumento de gestión que establece los requisitos, condiciones y obligaciones que debe cumplir el beneficiario durante las fases de construcción, operación, mantenimiento, desmantelamiento, abandono y/o terminación de un proyecto.

## Autoridad Competente
La Autoridad Nacional de Licencias Ambientales (ANLA) es la entidad competente para el otorgamiento de licencias ambientales de competencia del Ministerio de Ambiente y Desarrollo Sostenible.

## Requisitos Principales
Los proyectos que requieren licencia ambiental deben presentar:
- Estudio de Impacto Ambiental (EIA)
- Plan de Manejo Ambiental (PMA)
- Estudio de Riesgo
- Plan de Gestión del Riesgo

## Proceso de Evaluación
El proceso incluye evaluación técnica, jurídica y participación ciudadana. Los tiempos de evaluación varían según la complejidad del proyecto.
            """
        },
        {
            "page_id": 2,
            "url": "https://corporinoquia.gov.co/compensacion-biodiversidad",
            "content_md": """
# Compensación por Biodiversidad

## Objetivo
La compensación por biodiversidad busca resarcir las pérdidas de biodiversidad ocasionadas por el desarrollo de proyectos, obras o actividades.

## Metodología de Cálculo
La compensación se calcula considerando:
- Factor de compensación según ecosistema
- Representatividad del ecosistema
- Rareza del ecosistema
- Remanencia del ecosistema
- Tasa de transformación

## Implementación
Las medidas de compensación deben implementarse en ecosistemas equivalentes al afectado, prioritariamente dentro de la misma cuenca hidrográfica.
            """
        }
    ]
    
    all_chunks = []
    
    print(f"📄 Processing {len(sample_pages)} sample pages...")
    
    for page in sample_pages:
        page_id = page["page_id"]
        url = page["url"]
        content = page["content_md"]
        
        print(f"\n   📝 Processing: {url}")
        
        # Chunk the document
        chunks = chunker.chunk_document(page_id, url, content)
        
        print(f"   💎 Created {len(chunks)} chunks")
        
        # Generate embeddings for each chunk
        for chunk in chunks:
            embedding = embedder.generate_embedding(chunk.chunk_text)
            
            chunk_data = {
                "page_id": chunk.page_id,
                "url": chunk.url,
                "section": chunk.section,
                "chunk_text": chunk.chunk_text,
                "token_count": chunk.token_count,
                "embedding": embedding,
                "chunk_index": chunk.chunk_index
            }
            all_chunks.append(chunk_data)
            
            print(f"      🎯 Chunk {chunk.chunk_index}: {chunk.token_count} tokens, section '{chunk.section}'")
    
    print(f"\n✅ Demo completed!")
    print(f"   📄 Pages processed: {len(sample_pages)}")
    print(f"   💎 Total chunks created: {len(all_chunks)}")
    print(f"   🎯 Average chunks per page: {len(all_chunks)/len(sample_pages):.1f}")
    
    # Show sample chunks
    print(f"\n📋 Sample Chunks:")
    print("=" * 30)
    
    for i, chunk in enumerate(all_chunks[:3]):
        print(f"\nChunk {i+1}:")
        print(f"   🔗 URL: {chunk['url']}")
        print(f"   📂 Section: {chunk['section']}")
        print(f"   🎫 Tokens: {chunk['token_count']}")
        print(f"   📝 Text: {chunk['chunk_text'][:150]}...")
        print(f"   🎯 Embedding: {len(chunk['embedding'])} dimensions")
    
    return {
        "success": True,
        "pages_processed": len(sample_pages),
        "chunks_created": len(all_chunks),
        "chunks": all_chunks,
        "embedding_type": "openai" if embedder.use_openai else "mock"
    }

def setup_supabase_embeddings():
    """Provide setup instructions for Supabase embeddings."""
    
    print("\n🔧 SUPABASE EMBEDDINGS SETUP")
    print("=" * 40)
    
    setup_sql = """
-- 1. Enable pgvector extension (run once)
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Verify scraped_chunks table structure
\\d scraped_chunks;

-- 3. Create semantic search function
CREATE OR REPLACE FUNCTION match_chunks (
  query_embedding vector(1536),
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
  WHERE 1 - (scraped_chunks.embedding <=> query_embedding) > match_threshold
  ORDER BY scraped_chunks.embedding <=> query_embedding
  LIMIT match_count;
$$;

-- 4. Create index for performance
CREATE INDEX IF NOT EXISTS scraped_chunks_embedding_idx 
ON scraped_chunks USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- 5. Check current chunks count
SELECT COUNT(*) as total_chunks FROM scraped_chunks;

-- 6. Check if any embeddings exist
SELECT COUNT(*) as chunks_with_embeddings 
FROM scraped_chunks 
WHERE embedding IS NOT NULL;
    """
    
    print("📝 SQL to run in Supabase SQL Editor:")
    print(setup_sql)
    
    print("\n💡 How to Populate Real Chunks:")
    steps = [
        "1. Run the SQL above in your Supabase SQL editor",
        "2. Install OpenAI: pip install openai", 
        "3. Set OPENAI_API_KEY in geo-fetch-mcp/.env file",
        "4. Create a script to process your scraped_pages:",
        "   • Read all pages from scraped_pages table",
        "   • Chunk each page's content_md field",
        "   • Generate embeddings for each chunk",
        "   • Insert chunks into scraped_chunks table",
        "5. Update your MCP server to use real semantic search",
        "6. Test with your enhanced geo_kb_agent"
    ]
    
    for step in steps:
        print(f"   {step}")

def create_production_chunking_script():
    """Create a production script for chunking real data."""
    
    print(f"\n📋 PRODUCTION CHUNKING SCRIPT")
    print("=" * 40)
    
    script_code = '''
# Create this as chunk_and_embed_production.py

import os
import asyncio
from supabase import create_client
from supabase_chunking_pipeline import DocumentChunker, EmbeddingGenerator

async def chunk_all_pages():
    """Process all pages and insert chunks."""
    
    # Initialize Supabase
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    supabase = create_client(url, key)
    
    # Initialize processors
    chunker = DocumentChunker()
    embedder = EmbeddingGenerator(use_openai=True)  # Use real OpenAI
    
    # Get all pages
    pages_response = supabase.table("scraped_pages").select("*").execute()
    pages = pages_response.data
    
    print(f"Processing {len(pages)} pages...")
    
    for page in pages:
        page_id = page["page_id"]
        url = page["url"]
        content = page["content_md"]
        
        if not content or len(content.strip()) < 100:
            continue
        
        # Chunk the document
        chunks = chunker.chunk_document(page_id, url, content)
        
        # Process each chunk
        for chunk in chunks:
            embedding = embedder.generate_embedding(chunk.chunk_text)
            
            # Insert into scraped_chunks
            supabase.table("scraped_chunks").insert({
                "page_id": chunk.page_id,
                "url": chunk.url,
                "section": chunk.section,
                "chunk_text": chunk.chunk_text,
                "token_count": chunk.token_count,
                "embedding": embedding
            }).execute()
        
        print(f"Processed {url}: {len(chunks)} chunks")
    
    print("Chunking complete!")

if __name__ == "__main__":
    asyncio.run(chunk_all_pages())
'''
    
    print("💾 Save this as chunk_and_embed_production.py:")
    print(script_code)

if __name__ == "__main__":
    # Show setup instructions
    setup_supabase_embeddings()
    
    # Run the demo
    print("\n" + "="*60)
    result = asyncio.run(demo_chunking_pipeline())
    
    print(f"\n🎯 DEMO SUMMARY:")
    if result.get("success"):
        print(f"✅ Demo completed successfully")
        print(f"✅ Created {result.get('chunks_created', 0)} chunks from sample data")
        print(f"✅ Using {result.get('embedding_type', 'unknown')} embeddings")
    else:
        print(f"❌ Demo failed: {result.get('error', 'Unknown error')}")
    
    # Show production script
    create_production_chunking_script()
    
    print(f"\n📋 NEXT STEPS:")
    print(f"1. Run the Supabase setup SQL")
    print(f"2. Configure OPENAI_API_KEY in your .env")
    print(f"3. Create and run the production chunking script")
    print(f"4. Verify chunks are created in scraped_chunks table")
    print(f"5. Test semantic search with your MCP server")
