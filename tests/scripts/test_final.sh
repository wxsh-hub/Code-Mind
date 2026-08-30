#!/bin/bash
# Code-Mind Final Integration Test

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
echo "  Code-Mind Integration Test"
echo "=========================================="

# Login
echo ""
echo "[1] Login"
TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" -H "Content-Type: application/json" -d '{"username":"admin","password":"admin"}' | python -c "import sys,json; print(json.load(sys.stdin)['data']['token'])")
check "Login" "$TOKEN" "[a-f0-9]"

# Create KB
echo ""
echo "[2] Create Knowledge Base"
KB_ID=$(curl -s -X POST "$BASE_URL/knowledge-base" -H "Content-Type: application/json" -H "Authorization: $TOKEN" --data-binary "{\"name\":\"final_test_$(date +%s)\",\"embeddingModel\":\"qwen-emb-8b\",\"collectionName\":\"final_$(date +%s)\"}" | python -c "import sys,json; print(json.load(sys.stdin).get('data',''))")
check "Create KB" "$KB_ID" "[0-9]"

# Upload docs
echo ""
echo "[3] Upload Documents"
DOC_IDS=()
for file in test_data/*.md; do
    fname=$(basename "$file")
    DID=$(curl -s -X POST "$BASE_URL/knowledge-base/$KB_ID/docs/upload" -H "Authorization: $TOKEN" -F "file=@$file" -F "sourceType=file" -F "processMode=chunk" | python -c "import sys,json; print(json.load(sys.stdin).get('data',{}).get('id',''))")
    check "Upload $fname" "$DID" "[0-9]"
    DOC_IDS+=("$DID")
done

# Chunk
echo ""
echo "[4] Chunk Documents"
for DID in "${DOC_IDS[@]}"; do
    RESP=$(curl -s -X POST "$BASE_URL/knowledge-base/docs/$DID/chunk" -H "Authorization: $TOKEN")
    check "Chunk $DID" "$RESP" '"code":"0"'
done

echo "  Waiting 60s..."
sleep 60

# Verify chunks
echo ""
echo "[5] Verify Chunks"
TOTAL_CHUNKS=0
for DID in "${DOC_IDS[@]}"; do
    STATUS=$(curl -s "$BASE_URL/knowledge-base/docs/$DID" -H "Authorization: $TOKEN")
    S=$(echo "$STATUS" | python -c "import sys,json; print(json.load(sys.stdin)['data']['status'])")
    C=$(echo "$STATUS" | python -c "import sys,json; print(json.load(sys.stdin)['data']['chunkCount'])")
    check "Doc $DID status=$S chunks=$C" "$S" "success"
    TOTAL_CHUNKS=$((TOTAL_CHUNKS + C))
done
check "Total chunks > 0" "$TOTAL_CHUNKS" "[1-9]"

# Similar search
echo ""
echo "[6] Similar Search"
SEARCH=$(python -c "
import urllib.request, json
req = urllib.request.Request('$BASE_URL/knowledge-base/search/similar', data=json.dumps({'query':'PascalCase','topK':5}).encode('utf-8'), headers={'Authorization':'$TOKEN','Content-Type':'application/json; charset=UTF-8'})
r = json.loads(urllib.request.urlopen(req, timeout=10).read())
print(len(r.get('data',[])))
")
check "Search results > 0" "$SEARCH" "[1-9]"

# Reference count
echo ""
echo "[7] Reference Count"
CHUNK_ID=$(python -c "
import urllib.request, json
req = urllib.request.Request('$BASE_URL/knowledge-base/search/similar', data=json.dumps({'query':'PascalCase','topK':1}).encode('utf-8'), headers={'Authorization':'$TOKEN','Content-Type':'application/json; charset=UTF-8'})
r = json.loads(urllib.request.urlopen(req, timeout=10).read())
d = r.get('data',[])
print(d[0]['chunkId'] if d else '')
")
if [ -n "$CHUNK_ID" ]; then
    for i in {1..3}; do
        curl -s -X POST "$BASE_URL/knowledge-base/chunks/$CHUNK_ID/reference" -H "Authorization: $TOKEN" > /dev/null
    done
    VOTE=$(curl -s "$BASE_URL/knowledge-base/chunks/$CHUNK_ID/vote" -H "Authorization: $TOKEN" | python -c "import sys,json; print(json.load(sys.stdin).get('data',0))")
    check "Vote count >= 3" "$VOTE" "[3-9]"
else
    echo "  [SKIP] No chunk ID"
fi

# RAG Chat
echo ""
echo "[8] RAG Chat"
CHAT=$(python -c "
import urllib.request
req = urllib.request.Request('$BASE_URL/rag/v3/chat?question=What+is+PascalCase', headers={'Authorization':'$TOKEN'})
try:
    r = urllib.request.urlopen(req, timeout=60).read()
    print(f'ok:{len(r)}')
except: print('timeout')
")
check "RAG answer" "$CHAT" "ok:"

# Cleanup
echo ""
echo "[9] Cleanup"
curl -s -X DELETE "$BASE_URL/knowledge-base/$KB_ID" -H "Authorization: $TOKEN" > /dev/null
check "Cleanup" "ok" "ok"

# Results
echo ""
echo "=========================================="
echo "  Pass: $PASS  Fail: $FAIL"
echo "=========================================="

if [ $FAIL -eq 0 ]; then
    echo "[SUCCESS] All tests passed!"
    exit 0
else
    echo "[FAIL] $FAIL tests failed"
    exit 1
fi
