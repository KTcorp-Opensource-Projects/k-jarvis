-- =====================================================
-- K-Jarvis Platform - Database Initialization
-- Creates databases for K-Auth and Orchestrator
-- =====================================================

-- Create K-Auth database
CREATE DATABASE kauth;

-- Create Orchestrator database
CREATE DATABASE kjarvis;

-- Create Agent Catalog database
CREATE DATABASE agent_catalog;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE kauth TO postgres;
GRANT ALL PRIVILEGES ON DATABASE kjarvis TO postgres;
GRANT ALL PRIVILEGES ON DATABASE agent_catalog TO postgres;

