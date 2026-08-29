#!/bin/bash
# Skills 存储功能测试

set -e

BASE_URL="http://localhost:9090/api/ragent"
PASS=0
FAIL=0

check() {
    if echo "$2" | grep -q "$3"; then
        echo "  [PASS] $1"
        PASS=$((PASS + 1))
    else
        echo "  [FAIL] $1"
        FAIL=$((FAIL + 1))
    fi
}

echo "=========================================="
echo "  Skills Test"
echo "=========================================="

# Login
echo "[1] Login"
TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" -H "Content-Type: application/json" -d '{"username":"admin","password":"admin"}' | python -c "import sys,json; print(json.load(sys.stdin)['data']['token'])")
check "Login" "$TOKEN" "[a-f0-9]"

# Create KB
echo "[2] Create KB"
KB_ID=$(curl -s -X POST "$BASE_URL/knowledge-base" -H "Content-Type: application/json" -H "Authorization: $TOKEN" --data-binary "{\"name\":\"skills_test_$(date +%s)\",\"embeddingModel\":\"qwen-emb-8b\",\"collectionName\":\"skills_$(date +%s)_col\"}" | python -c "import sys,json; print(json.load(sys.stdin).get('data',''))")
check "Create KB" "$KB_ID" "[0-9]"

# Upload skills
echo "[3] Upload Skills"
for skill in "Java_Naming:Use PascalCase for classes" "Git_Commit:Use conventional commits" "Unit_Testing:Write tests with JUnit" "Docker_Deploy:Use Dockerfile"; do
    name="${skill%%:*}"
    content="${skill#*:}"
    echo "$content" > /tmp/skill_${name}.md
    RESP=$(curl -s -X POST "$BASE_URL/knowledge-base/$KB_ID/docs/upload" -H "Authorization: $TOKEN" -F "file=@/tmp/skill_${name}.md" -F "sourceType=file" -F "processMode=chunk")
    DOC_ID=$(echo "$RESP" | python -c "import sys,json; print(json.load(sys.stdin).get('data',{}).get('id',''))")
    curl -s -X POST "$BASE_URL/knowledge-base/docs/$DOC_ID/chunk" -H "Authorization: $TOKEN" > /dev/null
    check "Upload $name" "$DOC_ID" "[0-9]"
    rm -f /tmp/skill_${name}.md
done

echo "  Waiting 30s..."
sleep 30

# Search
echo "[4] Search"
for query in "PascalCase" "conventional commits" "JUnit" "Dockerfile"; do
    RESULT=$(curl -s -X POST "$BASE_URL/knowledge-base/search/similar" -H "Authorization: $TOKEN" -H "Content-Type: application/json" --data-binary "{\"query\":\"$query\",\"kbId\":\"$KB_ID\",\"topK\":2}")
    COUNT=$(echo "$RESULT" | python -c "import sys,json; print(len(json.load(sys.stdin).get('data',[])))")
    check "Search '$query'" "$COUNT" "[1-9]"
done

# Cleanup
echo "[5] Cleanup"
curl -s -X DELETE "$BASE_URL/knowledge-base/$KB_ID" -H "Authorization: $TOKEN" > /dev/null
check "Cleanup" "ok" "ok"

echo ""
echo "Pass: $PASS  Fail: $FAIL"
if [ $FAIL -eq 0 ]; then
    echo "[SUCCESS] All tests passed!"
    exit 0
else
    echo "[FAIL] $FAIL tests failed"
    exit 1
fi
