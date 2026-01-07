-- Agent Orchestrator Database Schema
-- PostgreSQL 14+

-- =====================================================
-- 초기화 (개발 환경에서만 사용)
-- =====================================================
-- DROP SCHEMA public CASCADE;
-- CREATE SCHEMA public;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =====================================================
-- ROLES TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Insert default roles
INSERT INTO roles (name, description) VALUES 
    ('admin', '관리자 - 에이전트 관리 및 모든 기능에 접근 가능'),
    ('user', '일반 사용자 - 채팅 및 에이전트 활성화/비활성화만 가능')
ON CONFLICT (name) DO NOTHING;

-- =====================================================
-- USERS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE,                      -- 로그인용 아이디 (admin 등)
    email VARCHAR(255) UNIQUE NOT NULL,               -- 이메일 (필수)
    password_hash VARCHAR(255) NOT NULL,              -- bcrypt 해시된 비밀번호
    name VARCHAR(100) NOT NULL,                       -- 표시 이름
    role_id INTEGER REFERENCES roles(id) DEFAULT 2,   -- 기본값: user (2)
    is_active BOOLEAN DEFAULT TRUE,                   -- 계정 활성화 여부
    kauth_user_id UUID UNIQUE,                        -- K-Auth 사용자 ID (SSO 연동)
    auth_provider VARCHAR(20) DEFAULT 'local',        -- 인증 제공자 ('local' or 'kauth')
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_kauth_id ON users(kauth_user_id);

-- =====================================================
-- USER SESSIONS TABLE (refresh tokens)
-- =====================================================
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    refresh_token VARCHAR(500) NOT NULL,
    user_agent TEXT,
    ip_address VARCHAR(45),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(refresh_token);
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);

-- =====================================================
-- K-AUTH REFRESH TOKENS TABLE (K-Auth SSO용)
-- =====================================================
CREATE TABLE IF NOT EXISTS kauth_refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    refresh_token TEXT NOT NULL,                          -- K-Auth에서 발급한 refresh token
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,         -- 만료 시간
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)                                       -- 사용자당 하나의 K-Auth refresh token
);

CREATE INDEX IF NOT EXISTS idx_kauth_refresh_tokens_user ON kauth_refresh_tokens(user_id);

-- =====================================================
-- USER AGENT PREFERENCES TABLE (에이전트 활성화 상태)
-- =====================================================
CREATE TABLE IF NOT EXISTS user_agent_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    agent_id VARCHAR(100) NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, agent_id)
);

CREATE INDEX IF NOT EXISTS idx_user_agent_prefs_user ON user_agent_preferences(user_id);

-- =====================================================
-- CONVERSATIONS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) DEFAULT 'New Chat',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);

-- =====================================================
-- MESSAGES TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    agent_used VARCHAR(100),
    task_id VARCHAR(100),                             -- A2A 프로토콜 taskId
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);

-- =====================================================
-- USER MCP TOKENS TABLE (사용자별 MCPHub 토큰)
-- =====================================================
CREATE TABLE IF NOT EXISTS user_mcp_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    encrypted_token TEXT NOT NULL,                      -- AES-256-GCM 암호화된 토큰
    token_name VARCHAR(100) DEFAULT 'default',          -- 토큰 별칭 (여러 개 관리 시)
    is_active BOOLEAN DEFAULT TRUE,                     -- 활성화 여부
    last_used_at TIMESTAMP WITH TIME ZONE,              -- 마지막 사용 시각
    expires_at TIMESTAMP WITH TIME ZONE,                -- 만료 시각 (null이면 무기한)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, token_name)
);

CREATE INDEX IF NOT EXISTS idx_user_mcp_tokens_user_id ON user_mcp_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_user_mcp_tokens_active ON user_mcp_tokens(user_id, is_active);

-- =====================================================
-- REGISTERED AGENTS TABLE (영구 저장)
-- =====================================================
CREATE TABLE IF NOT EXISTS registered_agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    url VARCHAR(500) UNIQUE NOT NULL,
    version VARCHAR(50) DEFAULT '1.0.0',
    skills JSONB DEFAULT '[]',
    capabilities JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'offline',
    registered_by UUID REFERENCES users(id),
    last_seen TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_registered_agents_url ON registered_agents(url);
CREATE INDEX IF NOT EXISTS idx_registered_agents_status ON registered_agents(status);

-- =====================================================
-- FUNCTIONS
-- =====================================================

-- updated_at 자동 갱신 함수
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_conversations_updated_at ON conversations;
CREATE TRIGGER update_conversations_updated_at
    BEFORE UPDATE ON conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_registered_agents_updated_at ON registered_agents;
CREATE TRIGGER update_registered_agents_updated_at
    BEFORE UPDATE ON registered_agents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_user_agent_prefs_updated_at ON user_agent_preferences;
CREATE TRIGGER update_user_agent_prefs_updated_at
    BEFORE UPDATE ON user_agent_preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_user_mcp_tokens_updated_at ON user_mcp_tokens;
CREATE TRIGGER update_user_mcp_tokens_updated_at
    BEFORE UPDATE ON user_mcp_tokens
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- VIEWS
-- =====================================================

-- 사용자 + 역할 정보 뷰
CREATE OR REPLACE VIEW users_with_roles AS
SELECT 
    u.id,
    u.username,
    u.email,
    u.name,
    u.is_active,
    u.last_login,
    u.created_at,
    u.updated_at,
    r.name as role_name,
    r.description as role_description
FROM users u
JOIN roles r ON u.role_id = r.id;

-- =====================================================
-- DEFAULT ADMIN USER
-- 계정: admin / admin123
-- =====================================================
-- bcrypt hash for 'admin123': $2b$12$gWgCmFlgnR9vSUCRTrr7KObAGjBlXk028Nx12u7X.pf56KJ1fn4ie
-- 주의: 프로덕션에서는 반드시 비밀번호를 변경하세요!

INSERT INTO users (username, email, password_hash, name, role_id) VALUES 
    ('admin', 'admin@orchestrator.local', '$2b$12$gWgCmFlgnR9vSUCRTrr7KObAGjBlXk028Nx12u7X.pf56KJ1fn4ie', 'Administrator', 1)
ON CONFLICT (username) DO UPDATE SET
    password_hash = '$2b$12$gWgCmFlgnR9vSUCRTrr7KObAGjBlXk028Nx12u7X.pf56KJ1fn4ie',
    role_id = 1;
