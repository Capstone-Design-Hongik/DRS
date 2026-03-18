-- 1. Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Convert vector column from REAL[] to vector(128)
ALTER TABLE graph_segments 
ALTER COLUMN vector TYPE vector(128) USING vector::text::vector;

-- 3. Create an HNSW index for fast Cosine similarity search (<=>)
CREATE INDEX ON graph_segments USING hnsw (vector vector_cosine_ops);
