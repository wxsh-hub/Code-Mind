#!/bin/bash
# ============================================================
# MCP Gateway 独立测试脚本
# 测试所有模块的单元测试（不需要 ragent 运行）
# ============================================================

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo -e "${YELLOW}=========================================="
echo "  MCP Gateway 单元测试"
echo -e "==========================================${NC}"
echo ""

cd "$(dirname "$0")"

# 运行所有新测试
echo "运行 RAG Client 测试..."
python -m pytest tests/test_rag_client.py -v --tb=short
echo ""

echo "运行 RAG Tools 测试..."
python -m pytest tests/test_rag_tools.py -v --tb=short
echo ""

echo "运行 Collector 测试..."
python -m pytest tests/test_collector.py -v --tb=short
echo ""

echo "运行 Conflict 测试..."
python -m pytest tests/test_conflict.py -v --tb=short
echo ""

echo -e "${YELLOW}=========================================="
echo "  运行全部测试"
echo -e "==========================================${NC}"
echo ""

python -m pytest tests/test_rag_client.py tests/test_rag_tools.py tests/test_collector.py tests/test_conflict.py -v --tb=short

echo ""
echo -e "${GREEN}✅ 所有测试完成${NC}"
