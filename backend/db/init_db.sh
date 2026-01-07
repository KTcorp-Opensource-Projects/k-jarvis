#!/bin/bash
# Agent Orchestrator - Database Initialization Script
# PostgreSQL 데이터베이스 초기화 스크립트

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     Agent Orchestrator - Database Initialization             ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# 환경 변수 (기본값)
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}
DB_NAME=${DB_NAME:-agent_orchestrator}
DB_USER=${DB_USER:-$(whoami)}
DB_PASSWORD=${DB_PASSWORD:-}

# .env 파일이 있으면 로드
if [ -f "../.env" ]; then
    echo -e "${YELLOW}📄 Loading configuration from .env file...${NC}"
    source "../.env"
fi

echo -e "${YELLOW}📋 Database Configuration:${NC}"
echo "   Host: $DB_HOST"
echo "   Port: $DB_PORT"
echo "   Database: $DB_NAME"
echo "   User: $DB_USER"
echo ""

# PostgreSQL 연결 확인
echo -e "${YELLOW}🔍 Checking PostgreSQL connection...${NC}"
if ! pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" > /dev/null 2>&1; then
    echo -e "${RED}❌ PostgreSQL is not running or not accessible${NC}"
    echo "   Please start PostgreSQL and try again."
    exit 1
fi
echo -e "${GREEN}✅ PostgreSQL is running${NC}"

# 데이터베이스 존재 확인
echo -e "${YELLOW}🔍 Checking if database exists...${NC}"
if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -lqt | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
    echo -e "${GREEN}✅ Database '$DB_NAME' already exists${NC}"
    
    echo ""
    read -p "Do you want to reset the database? (y/N): " reset_choice
    if [ "$reset_choice" = "y" ] || [ "$reset_choice" = "Y" ]; then
        echo -e "${YELLOW}⚠️  Dropping and recreating database...${NC}"
        psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -c "DROP DATABASE IF EXISTS $DB_NAME;"
        psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -c "CREATE DATABASE $DB_NAME;"
        echo -e "${GREEN}✅ Database recreated${NC}"
    fi
else
    echo -e "${YELLOW}📦 Creating database '$DB_NAME'...${NC}"
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -c "CREATE DATABASE $DB_NAME;"
    echo -e "${GREEN}✅ Database created${NC}"
fi

# 스키마 적용
echo ""
echo -e "${YELLOW}📜 Applying schema...${NC}"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "schema.sql"
echo -e "${GREEN}✅ Schema applied successfully${NC}"

# 결과 확인
echo ""
echo -e "${YELLOW}📊 Database Status:${NC}"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
SELECT 
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as columns
FROM information_schema.tables t
WHERE table_schema = 'public' 
AND table_type = 'BASE TABLE'
ORDER BY table_name;
"

# 관리자 계정 확인
echo ""
echo -e "${YELLOW}👤 Admin Account:${NC}"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
SELECT username, email, name, r.name as role FROM users u JOIN roles r ON u.role_id = r.id WHERE u.username = 'admin';
"

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Database initialization completed!${NC}"
echo ""
echo -e "${YELLOW}📌 Default Admin Credentials:${NC}"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
echo -e "${RED}⚠️  WARNING: Change the admin password in production!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"






