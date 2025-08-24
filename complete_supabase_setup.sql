-- Complete Supabase Setup for Embeddings and Chunks Import
-- Run these commands in your Supabase SQL Editor in order

-- ============================================================================
-- STEP 1: Enable pgvector extension and verify schema
-- ============================================================================

-- Enable pgvector extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS vector;

-- Check current scraped_chunks table structure
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'scraped_chunks' 
ORDER BY ordinal_position;

-- ============================================================================
-- STEP 2: Update schema for 768-dimensional embeddings
-- ============================================================================

-- Update embedding column to support 768 dimensions (Gemini compatible)
-- This may fail if there are existing embeddings with different dimensions
DO $$
BEGIN
    -- Try to alter the column type
    BEGIN
        ALTER TABLE scraped_chunks ALTER COLUMN embedding TYPE vector(768);
        RAISE NOTICE 'Successfully updated embedding column to vector(768)';
    EXCEPTION WHEN OTHERS THEN
        -- If it fails, we might need to recreate the column
        RAISE NOTICE 'Failed to alter column, attempting to recreate: %', SQLERRM;
        
        -- Drop the column and recreate it (this will lose existing embeddings)
        ALTER TABLE scraped_chunks DROP COLUMN IF EXISTS embedding;
        ALTER TABLE scraped_chunks ADD COLUMN embedding vector(768);
        RAISE NOTICE 'Recreated embedding column as vector(768)';
    END;
END $$;

-- ============================================================================
-- STEP 3: Handle Row Level Security (RLS)
-- ============================================================================

-- Check current RLS status
SELECT schemaname, tablename, rowsecurity, hasrls 
FROM pg_tables 
WHERE tablename = 'scraped_chunks';

-- Option A: Temporarily disable RLS for import (RECOMMENDED for import)
ALTER TABLE scraped_chunks DISABLE ROW LEVEL SECURITY;

-- Option B: Create permissive policy (alternative to disabling RLS)
-- Uncomment these lines if you prefer to keep RLS enabled:
/*
DROP POLICY IF EXISTS "Allow all operations on scraped_chunks" ON scraped_chunks;
CREATE POLICY "Allow all operations on scraped_chunks" 
ON scraped_chunks FOR ALL 
USING (true) 
WITH CHECK (true);
*/

-- ============================================================================
-- STEP 4: Create semantic search function for Gemini embeddings
-- ============================================================================

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

-- ============================================================================
-- STEP 5: Create performance indexes
-- ============================================================================

-- Drop existing embedding index if it exists
DROP INDEX IF EXISTS scraped_chunks_embedding_idx;
DROP INDEX IF EXISTS scraped_chunks_embedding_gemini_idx;

-- Create new index optimized for 768-dimensional vectors
-- Note: This will be created after we have data
-- CREATE INDEX scraped_chunks_embedding_gemini_idx 
-- ON scraped_chunks USING ivfflat (embedding vector_cosine_ops)
-- WITH (lists = 100);

-- ============================================================================
-- STEP 6: Create helper functions for testing
-- ============================================================================

-- Function to generate test embeddings
CREATE OR REPLACE FUNCTION generate_test_embedding(input_text text)
RETURNS vector(768)
LANGUAGE plpgsql
AS $$
DECLARE
    result float[];
    hash_val bigint;
    i integer;
BEGIN
    -- Generate a simple hash-based embedding for testing
    hash_val := abs(hashtext(input_text));
    
    -- Create array of 768 values
    result := array[]::float[];
    FOR i IN 1..768 LOOP
        result := result || (((hash_val + i * 17) % 1000) - 500) / 500.0;
    END LOOP;
    
    RETURN result::vector(768);
END;
$$;

-- Function to check embedding dimensions
CREATE OR REPLACE FUNCTION check_embedding_dimensions()
RETURNS TABLE (
    total_chunks bigint,
    chunks_with_embeddings bigint,
    embedding_dimensions integer,
    sample_embedding_preview text
)
LANGUAGE SQL
AS $$
  SELECT 
    COUNT(*) as total_chunks,
    COUNT(embedding) as chunks_with_embeddings,
    CASE 
      WHEN COUNT(embedding) > 0 THEN vector_dims((SELECT embedding FROM scraped_chunks WHERE embedding IS NOT NULL LIMIT 1))
      ELSE NULL 
    END as embedding_dimensions,
    CASE 
      WHEN COUNT(embedding) > 0 THEN 
        '[' || array_to_string((SELECT embedding FROM scraped_chunks WHERE embedding IS NOT NULL LIMIT 1)::float[][:5], ', ') || ', ...]'
      ELSE 'No embeddings found'
    END as sample_embedding_preview
  FROM scraped_chunks;
$$;

-- ============================================================================
-- STEP 7: Create useful views
-- ============================================================================

-- View for easier querying of chunks with embedding status
CREATE OR REPLACE VIEW chunks_with_embeddings AS
SELECT 
    chunk_id,
    page_id,
    url,
    section,
    LEFT(chunk_text, 100) || '...' as chunk_preview,
    token_count,
    CASE WHEN embedding IS NOT NULL THEN 'Yes' ELSE 'No' END as has_embedding,
    CASE WHEN embedding IS NOT NULL THEN vector_dims(embedding) ELSE NULL END as embedding_dims,
    created_at
FROM scraped_chunks
ORDER BY chunk_id;

-- ============================================================================
-- STEP 8: Verify setup
-- ============================================================================

-- Check the setup
SELECT * FROM check_embedding_dimensions();

-- Show RLS status
SELECT 
    'Row Level Security Status' as check_type,
    CASE WHEN rowsecurity THEN 'ENABLED' ELSE 'DISABLED' END as rls_status
FROM pg_tables 
WHERE tablename = 'scraped_chunks';

-- Show available functions
SELECT 
    'Available Functions' as check_type,
    string_agg(proname, ', ') as functions
FROM pg_proc 
WHERE proname IN ('match_chunks_gemini', 'generate_test_embedding', 'check_embedding_dimensions');

-- ============================================================================
-- STEP 9: Test queries (run after import)
-- ============================================================================

-- These queries will work after you import the chunks:

-- Test 1: Count chunks by embedding status
-- SELECT 
--     CASE WHEN embedding IS NOT NULL THEN 'With Embedding' ELSE 'Without Embedding' END as status,
--     COUNT(*) as count
-- FROM scraped_chunks
-- GROUP BY (embedding IS NOT NULL);

-- Test 2: Sample semantic search (replace with actual query embedding)
-- SELECT chunk_text, similarity 
-- FROM match_chunks_gemini(
--     generate_test_embedding('licencia ambiental hidroeléctrico'),
--     0.7,
--     3
-- );

-- Test 3: Check embedding dimensions consistency
-- SELECT 
--     vector_dims(embedding) as dimensions,
--     COUNT(*) as count
-- FROM scraped_chunks 
-- WHERE embedding IS NOT NULL
-- GROUP BY vector_dims(embedding);

-- ============================================================================
-- STEP 10: Post-import cleanup (run after successful import)
-- ============================================================================

-- After successful import, create the vector index:
-- CREATE INDEX CONCURRENTLY scraped_chunks_embedding_gemini_idx 
-- ON scraped_chunks USING ivfflat (embedding vector_cosine_ops)
-- WITH (lists = 100);

-- Optionally re-enable RLS if you disabled it:
-- ALTER TABLE scraped_chunks ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- SUMMARY
-- ============================================================================

SELECT 
    'Setup Summary' as status,
    'Ready for chunk import' as message,
    NOW() as timestamp;

-- Show what to do next
SELECT 
    'Next Steps' as step,
    CASE 
        WHEN step_num = 1 THEN 'Run: python3 fix_supabase_rls_and_import.py'
        WHEN step_num = 2 THEN 'Verify import with: SELECT * FROM check_embedding_dimensions();'
        WHEN step_num = 3 THEN 'Create vector index after import'
        WHEN step_num = 4 THEN 'Test semantic search with match_chunks_gemini()'
        WHEN step_num = 5 THEN 'Update MCP server to use real embeddings'
    END as instruction
FROM generate_series(1, 5) as step_num;
