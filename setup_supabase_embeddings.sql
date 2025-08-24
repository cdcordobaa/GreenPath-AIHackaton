-- Supabase Schema Setup for 768-dimensional Gemini Embeddings
-- Run this in your Supabase SQL Editor before importing chunks

-- 1. Enable pgvector extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Check current scraped_chunks table structure
\d scraped_chunks;

-- 3. Update embedding column to support 768 dimensions (Gemini compatible)
-- Note: This will fail if there are existing embeddings with different dimensions
-- In that case, you may need to drop and recreate the column
ALTER TABLE scraped_chunks 
ALTER COLUMN embedding TYPE vector(768);

-- Alternative if the above fails (will lose existing embeddings):
-- ALTER TABLE scraped_chunks DROP COLUMN IF EXISTS embedding;
-- ALTER TABLE scraped_chunks ADD COLUMN embedding vector(768);

-- 4. Create semantic search function for Gemini embeddings
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

-- 5. Create performance index for vector similarity search
-- Drop existing index if it exists with wrong dimensions
DROP INDEX IF EXISTS scraped_chunks_embedding_idx;

-- Create new index optimized for 768-dimensional vectors
CREATE INDEX scraped_chunks_embedding_gemini_idx 
ON scraped_chunks USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- 6. Create a helper function to generate mock embeddings for testing
CREATE OR REPLACE FUNCTION generate_test_embedding(input_text text)
RETURNS vector(768)
LANGUAGE plpgsql
AS $$
DECLARE
    result vector(768);
    hash_val bigint;
    i integer;
BEGIN
    -- Generate a simple hash-based embedding for testing
    hash_val := abs(hashtext(input_text));
    
    -- Create array of 768 values
    FOR i IN 1..768 LOOP
        result[i] := (((hash_val + i * 17) % 1000) - 500) / 500.0;
    END LOOP;
    
    RETURN result;
END;
$$;

-- 7. Verify setup
SELECT 
  COUNT(*) as total_chunks,
  COUNT(embedding) as chunks_with_embeddings,
  CASE 
    WHEN COUNT(embedding) > 0 THEN vector_dims((SELECT embedding FROM scraped_chunks WHERE embedding IS NOT NULL LIMIT 1))
    ELSE NULL 
  END as embedding_dimensions
FROM scraped_chunks;

-- 8. Test the semantic search function (will work after importing chunks)
-- SELECT chunk_text, similarity 
-- FROM match_chunks_gemini(
--     generate_test_embedding('licencia ambiental'),
--     0.7,
--     5
-- );

-- 9. Create a view for easier querying
CREATE OR REPLACE VIEW chunks_with_embeddings AS
SELECT 
    chunk_id,
    page_id,
    url,
    section,
    chunk_text,
    token_count,
    CASE WHEN embedding IS NOT NULL THEN 'Yes' ELSE 'No' END as has_embedding,
    CASE WHEN embedding IS NOT NULL THEN vector_dims(embedding) ELSE NULL END as embedding_dims
FROM scraped_chunks;

-- 10. Grant necessary permissions (adjust as needed for your setup)
-- GRANT SELECT ON chunks_with_embeddings TO authenticated;
-- GRANT EXECUTE ON FUNCTION match_chunks_gemini TO authenticated;
-- GRANT EXECUTE ON FUNCTION generate_test_embedding TO authenticated;

-- Summary query to check everything is set up correctly
SELECT 
    'Setup Complete' as status,
    (SELECT COUNT(*) FROM scraped_chunks) as total_chunks,
    (SELECT COUNT(*) FROM scraped_chunks WHERE embedding IS NOT NULL) as chunks_with_embeddings,
    (SELECT COUNT(*) FROM pg_indexes WHERE indexname = 'scraped_chunks_embedding_gemini_idx') as vector_index_exists,
    (SELECT COUNT(*) FROM pg_proc WHERE proname = 'match_chunks_gemini') as search_function_exists;
