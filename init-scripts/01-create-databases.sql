-- =====================================================
-- K-Jarvis Platform - Database Initialization
-- Creates databases for K-Auth and Orchestrator
-- =====================================================

-- Create K-Auth database
CREATE DATABASE k_auth;

-- Create Orchestrator database
CREATE DATABASE orchestrator;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE k_auth TO postgres;
GRANT ALL PRIVILEGES ON DATABASE orchestrator TO postgres;

