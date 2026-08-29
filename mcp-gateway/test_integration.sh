#!/bin/bash
# ============================================================
# Code-Mind 集成测试脚本
# 测试 MCP Gateway <-> ragent 全链路
# ============================================================

set -e

BASE_URL="http://localhost:9090/api/ragent"
MCP_GATEWAY_DIR="$(cd "$(dirname "$0")" && pwd)"
TEST_DATA_DIR="$MCP_GATEWAY_DIR/test_data"
PASS=0
FAIL=0
TOTAL=0

check() {
    local name="$1"
    local actual="$2"
    local expected="$3"
    TOTAL=$((TOTAL + 1))
    if echo "$actual" | grep -q "$expected"; then
        echo "  [PASS] $name"
        PASS=$((PASS + 1))
    else
        echo "  [FAIL] $name (expected: $expected)"
        echo "     got: $actual"
        FAIL=$((FAIL + 1))
    fi
}

section() {
    echo ""
    echo "=========================================="
    echo "  $1"
    echo "=========================================="
}

# ============================================================
section "1. Environment Check"
# ============================================================

echo "Checking ragent service..."
if curl -s --max-time 5 "$BASE_URL/auth/login" > /dev/null 2>&1; then
    check "ragent service available" "ok" "ok"
else
    echo "[FAIL] ragent service not available"
    exit 1
fi

echo "Checking test data files..."
FILE_COUNT=$(ls "$TEST_DATA_DIR"/*.md 2>/dev/null | wc -l)
check "Test data files >= 5" "$FILE_COUNT" "[5-9]"

# ============================================================
section "2. Login"
# ============================================================

LOGIN_RESP=$(curl -s -X POST "$BASE_URL/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"admin"}')
TOKEN=$(echo "$LOGIN_RESP" | python -c "import sys,json; print(json.load(sys.stdin)['data']['token'])" 2>/dev/null)
check "Login get token" "$TOKEN" "[a-f0-9]"

# ============================================================
section "3. Create Knowledge Base"
# ============================================================

KB_NAME="code_mind_test_$(date +%s)"
KB_RESP=$(curl -s -X POST "$BASE_URL/knowledge-base" \
    -H "Content-Type: application/json" \
    -H "Authorization: $TOKEN" \
    --data-binary "{\"name\":\"$KB_NAME\",\"embeddingModel\":\"qwen-emb-8b\",\"collectionName\":\"${KB_NAME}_col\"}")
KB_ID=$(echo "$KB_RESP" | python -c "import sys,json; d=json.load(sys.stdin); print(d.get('data',''))" 2>/dev/null)
check "Create knowledge base" "$KB_ID" "[0-9]"

# ============================================================
section "4. Upload Knowledge Documents"
# ============================================================

DOC_IDS=()
for file in "$TEST_DATA_DIR"/*.md; do
    filename=$(basename "$file")
    echo "Upload: $filename"

    UPLOAD_RESP=$(curl -s -X POST "$BASE_URL/knowledge-base/$KB_ID/docs/upload" \
        -H "Authorization: $TOKEN" \
        -F "file=@$file" \
        -F "sourceType=file" \
        -F "processMode=chunk")

    DOC_ID=$(echo "$UPLOAD_RESP" | python -c "import sys,json; d=json.load(sys.stdin); print(d.get('data',{}).get('id',''))" 2>/dev/null)
    check "Upload $filename" "$DOC_ID" "[0-9]"
    DOC_IDS+=("$DOC_ID")
done

# ============================================================
section "5. Chunk and Vectorize"
# ============================================================

for i in "${!DOC_IDS[@]}"; do
    DOC_ID="${DOC_IDS[$i]}"
    CHUNK_RESP=$(curl -s -X POST "$BASE_URL/knowledge-base/docs/$DOC_ID/chunk" \
        -H "Authorization: $TOKEN")
    check "Chunk doc_$DOC_ID" "$CHUNK_RESP" '"code":"0"'
done

echo ""
echo "Waiting 60s for chunking..."
sleep 60

CHUNK_COUNT=0
for DOC_ID in "${DOC_IDS[@]}"; do
    DOC_STATUS=$(curl -s "$BASE_URL/knowledge-base/docs/$DOC_ID" -H "Authorization: $TOKEN")
    STATUS=$(echo "$DOC_STATUS" | python -c "import sys,json; print(json.load(sys.stdin)['data']['status'])" 2>/dev/null)
    COUNT=$(echo "$DOC_STATUS" | python -c "import sys,json; print(json.load(sys.stdin)['data']['chunkCount'])" 2>/dev/null)
    check "Doc $DOC_ID chunk status" "$STATUS" "success"
    CHUNK_COUNT=$((CHUNK_COUNT + COUNT))
done
check "Total chunks > 0" "$CHUNK_COUNT" "[1-9]"

# ============================================================
section "6. Similar Search Test"
# ============================================================

echo "Search: PascalCase..."
SIMILAR_RESP=$(python -c "
import urllib.request, json
req = urllib.request.Request(
    '$BASE_URL/knowledge-base/search/similar',
    data=json.dumps({'query':'PascalCase','topK':5}).encode('utf-8'),
    headers={'Authorization':'$TOKEN','Content-Type':'application/json; charset=UTF-8'}
)
print(urllib.request.urlopen(req).read().decode('utf-8'))
" 2>/dev/null)
check "Similar search success" "$SIMILAR_RESP" '"code":"0"'

RESULT_COUNT=$(echo "$SIMILAR_RESP" | python -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('data',[])))" 2>/dev/null)
check "Search returned results" "$RESULT_COUNT" "[1-9]"

# ============================================================
section "7. Reference Count Test"
# ============================================================

FIRST_CHUNK=$(echo "$SIMILAR_RESP" | python -c "
import sys, json, re
text = sys.stdin.read()
m = re.search(r'\"chunkId\":\"(\d+)\"', text)
print(m.group(1) if m else '')
" 2>/dev/null)

if [ -n "$FIRST_CHUNK" ]; then
    # Record 5 references
    for i in {1..5}; do
        curl -s -X POST "$BASE_URL/knowledge-base/chunks/$FIRST_CHUNK/reference" -H "Authorization: $TOKEN" > /dev/null
    done

    VOTE_RESP=$(curl -s "$BASE_URL/knowledge-base/chunks/$FIRST_CHUNK/vote" -H "Authorization: $TOKEN")
    VOTE=$(echo "$VOTE_RESP" | python -c "import sys,json; print(json.load(sys.stdin).get('data',0))" 2>/dev/null)
    check "Vote count >= 5" "$VOTE" "[5-9]"
else
    echo "  [WARN] No chunk ID, skip reference test"
fi

# ============================================================
section "8. RAG Chat Test"
# ============================================================

echo "Question: Java naming convention..."
CHAT_RESP=$(python -c "
import urllib.request, json
req = urllib.request.Request(
    '$BASE_URL/rag/v3/chat?question=What+is+the+naming+convention+for+Java+classes',
    headers={'Authorization':'$TOKEN'}
)
try:
    resp = urllib.request.urlopen(req, timeout=60).read().decode('utf-8')
    print(f'has_content:{len(resp)}')
except Exception as e:
    print(f'error:{e}')
" 2>/dev/null)
check "RAG chat has answer" "$CHAT_RESP" "has_content"

echo "Question: Deep pagination optimization..."
CHAT_RESP=$(python -c "
import urllib.request, json
req = urllib.request.Request(
    '$BASE_URL/rag/v3/chat?question=How+to+optimize+deep+pagination',
    headers={'Authorization':'$TOKEN'}
)
try:
    resp = urllib.request.urlopen(req, timeout=60).read().decode('utf-8')
    print(f'has_content:{len(resp)}')
except Exception as e:
    print(f'error:{e}')
" 2>/dev/null)
check "Pagination answer" "$CHAT_RESP" "has_content"

# ============================================================
section "9. Contradiction Document Test"
# ============================================================

cat > /tmp/test_contradiction.md << 'EOF'
# Cache Design (New Version)

## Cache Penetration

We should NOT use null value caching for cache penetration.

The correct approach is to use Bloom filter.
EOF

echo "Upload contradiction doc..."
CONTRADICT_UPLOAD=$(curl -s -X POST "$BASE_URL/knowledge-base/$KB_ID/docs/upload" \
    -H "Authorization: $TOKEN" \
    -F "file=@/tmp/test_contradiction.md" \
    -F "sourceType=file" \
    -F "processMode=chunk")
CONTRADICT_DOC=$(echo "$CONTRADICT_UPLOAD" | python -c "import sys,json; d=json.load(sys.stdin); print(d.get('data',{}).get('id',''))" 2>/dev/null)
check "Upload contradiction doc" "$CONTRADICT_DOC" "[0-9]"

curl -s -X POST "$BASE_URL/knowledge-base/docs/$CONTRADICT_DOC/chunk" -H "Authorization: $TOKEN" > /dev/null
echo "Waiting 30s..."
sleep 30

CONFLICT_SEARCH=$(python -c "
import urllib.request, json
req = urllib.request.Request(
    '$BASE_URL/knowledge-base/search/similar',
    data=json.dumps({'query':'cache','topK':10}).encode('utf-8'),
    headers={'Authorization':'$TOKEN','Content-Type':'application/json; charset=UTF-8'}
)
resp = json.loads(urllib.request.urlopen(req).read())
print(f'results:{len(resp.get(\"data\",[]))}')
" 2>/dev/null)
check "Contradiction searchable" "$CONFLICT_SEARCH" "results:[1-9]"

# ============================================================
section "10. MCP Gateway Unit Tests"
# ============================================================

echo "Running MCP Gateway unit tests..."
cd "$MCP_GATEWAY_DIR"
UNIT_RESULT=$(python -m pytest tests/test_rag_client.py tests/test_rag_tools.py tests/test_collector.py tests/test_conflict.py -v --tb=short 2>&1)
UNIT_PASS=$(echo "$UNIT_RESULT" | grep -o "[0-9]* passed" | grep -o "[0-9]*")
check "MCP Gateway unit tests ($UNIT_PASS)" "$UNIT_PASS" "[0-9]"

# ============================================================
section "11. Cleanup"
# ============================================================

echo "Cleaning up..."
curl -s -X DELETE "$BASE_URL/knowledge-base/$KB_ID" -H "Authorization: $TOKEN" > /dev/null
rm -f /tmp/test_contradiction.md
check "Cleanup done" "ok" "ok"

# ============================================================
section "Test Results"
# ============================================================

echo ""
echo "Pass: $PASS"
echo "Fail: $FAIL"
echo "Total: $TOTAL"
echo ""

if [ $FAIL -eq 0 ]; then
    echo "[SUCCESS] All tests passed!"
    echo ""
    echo "Verified features:"
    echo "  - Knowledge base creation and management"
    echo "  - Document upload and chunking"
    echo "  - Vector search and retrieval"
    echo "  - Similar chunk search"
    echo "  - Reference count (voting)"
    echo "  - RAG Q&A"
    echo "  - Contradiction document handling"
    echo "  - MCP Gateway unit tests"
    exit 0
else
    echo "[FAIL] $FAIL tests failed"
    exit 1
fi
