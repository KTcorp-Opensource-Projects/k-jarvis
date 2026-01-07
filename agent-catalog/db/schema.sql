-- Agent Catalog Service - PostgreSQL Schema
-- Version: 1.0.0

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Agent Cards table (main table)
CREATE TABLE IF NOT EXISTS agent_cards (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    url VARCHAR(500) NOT NULL UNIQUE,
    version VARCHAR(50) DEFAULT '1.0.0',
    protocol_version VARCHAR(20) DEFAULT '0.3.0',
    
    -- A2A Standard fields stored as JSONB
    skills JSONB DEFAULT '[]'::jsonb,
    capabilities JSONB DEFAULT '{}'::jsonb,
    default_input_modes JSONB DEFAULT '["text/plain"]'::jsonb,
    default_output_modes JSONB DEFAULT '["text/plain"]'::jsonb,
    
    -- A2A Optional fields
    provider JSONB DEFAULT NULL,
    security_schemes JSONB DEFAULT NULL,
    security JSONB DEFAULT NULL,
    preferred_transport VARCHAR(50) DEFAULT 'JSONRPC',
    additional_interfaces JSONB DEFAULT '[]'::jsonb,
    
    -- K-Jarvis Extensions (stored in extensions field for A2A compliance)
    extensions JSONB DEFAULT '{}'::jsonb,
    
    -- Status tracking
    status VARCHAR(20) DEFAULT 'unknown' CHECK (status IN ('online', 'offline', 'unknown')),
    last_seen TIMESTAMP WITH TIME ZONE,
    last_health_check TIMESTAMP WITH TIME ZONE,
    health_check_failures INTEGER DEFAULT 0,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_agent_cards_url ON agent_cards(url);
CREATE INDEX IF NOT EXISTS idx_agent_cards_name ON agent_cards(name);
CREATE INDEX IF NOT EXISTS idx_agent_cards_status ON agent_cards(status);
CREATE INDEX IF NOT EXISTS idx_agent_cards_created_at ON agent_cards(created_at DESC);

-- GIN index for JSONB full-text search on skills
CREATE INDEX IF NOT EXISTS idx_agent_cards_skills ON agent_cards USING GIN (skills);
CREATE INDEX IF NOT EXISTS idx_agent_cards_extensions ON agent_cards USING GIN (extensions);

-- Agent Skills table (normalized for efficient search)
CREATE TABLE IF NOT EXISTS agent_skills (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES agent_cards(id) ON DELETE CASCADE,
    skill_id VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    tags JSONB DEFAULT '[]'::jsonb,
    examples JSONB DEFAULT '[]'::jsonb,
    input_modes JSONB DEFAULT '["text/plain"]'::jsonb,
    output_modes JSONB DEFAULT '["text/plain"]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(agent_id, skill_id)
);

-- Indexes for skills search
CREATE INDEX IF NOT EXISTS idx_agent_skills_agent_id ON agent_skills(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_skills_name ON agent_skills(name);
CREATE INDEX IF NOT EXISTS idx_agent_skills_tags ON agent_skills USING GIN (tags);

-- Health check history (optional, for monitoring)
CREATE TABLE IF NOT EXISTS health_check_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES agent_cards(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL,
    response_time_ms INTEGER,
    error_message TEXT,
    checked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for health check history
CREATE INDEX IF NOT EXISTS idx_health_check_agent_id ON health_check_history(agent_id);
CREATE INDEX IF NOT EXISTS idx_health_check_checked_at ON health_check_history(checked_at DESC);

-- Trigger to auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_agent_cards_updated_at ON agent_cards;
CREATE TRIGGER update_agent_cards_updated_at
    BEFORE UPDATE ON agent_cards
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- View for agent summary (useful for listings)
CREATE OR REPLACE VIEW agent_summary AS
SELECT 
    ac.id,
    ac.name,
    ac.description,
    ac.url,
    ac.version,
    ac.status,
    ac.last_seen,
    ac.created_at,
    jsonb_array_length(ac.skills) as skill_count,
    ac.extensions->'routing'->>'domain' as domain,
    ac.extensions->'routing'->'keywords' as keywords
FROM agent_cards ac;

-- Comments
COMMENT ON TABLE agent_cards IS 'A2A Protocol compliant Agent Card storage';
COMMENT ON TABLE agent_skills IS 'Normalized agent skills for efficient search';
COMMENT ON TABLE health_check_history IS 'Agent health check history for monitoring';
COMMENT ON COLUMN agent_cards.extensions IS 'K-Jarvis specific extensions (requirements, routing)';

