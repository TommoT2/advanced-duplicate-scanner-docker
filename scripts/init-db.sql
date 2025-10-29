-- Initialize the duplicates database
-- This file is automatically executed when PostgreSQL container starts

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create indexes for common queries
-- (These will be created by SQLAlchemy, but we can add custom ones here)

-- Example: Create a composite index for fast duplicate lookups
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_files_hash_size 
-- ON file_records (blake3_hash, size) WHERE blake3_hash IS NOT NULL;

-- Create a function for file size formatting
CREATE OR REPLACE FUNCTION format_file_size(size_bytes BIGINT)
RETURNS TEXT AS $$
BEGIN
    IF size_bytes < 1024 THEN
        RETURN size_bytes || ' B';
    ELSIF size_bytes < 1024 * 1024 THEN
        RETURN ROUND(size_bytes / 1024.0, 1) || ' KB';
    ELSIF size_bytes < 1024 * 1024 * 1024 THEN
        RETURN ROUND(size_bytes / (1024.0 * 1024.0), 1) || ' MB';
    ELSE
        RETURN ROUND(size_bytes / (1024.0 * 1024.0 * 1024.0), 1) || ' GB';
    END IF;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE duplicates TO scanner;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO scanner;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO scanner;