#!/bin/bash
# 测试 KnowledgeChunkApiController 的所有接口
# 包括：相似检索、引用计数、矛盾标记、废弃标记

BASE_URL="http://localhost:9090/api/ragent"
PASS=0
FAIL=0

check() {
    local name="$1"
    local actual="$2"
    local expected="$3"
    if echo "$actual" | grep -q "$expected"; then
        echo "  ✅ $name"
        PASS=$((PASS + 1))
    else
        echo "  ❌ $name (expected: $expected)"
        echo "     got: $actual"
        FAIL=$((FAIL + 1))
    fi
}

echo "=========================================="
echo "  KnowledgeChunkApiController 测试"
echo "=========================================="

# 登录
TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" -H "Content-Type: application/json" -d '{"username":"admin","password":"admin"}' | python -c "import sys,json; print(json.load(sys.stdin)['data']['token'])")
check "登录获取 Token" "$TOKEN" "[a-f0-9]"

# 创建知识库
KB_RESP=$(curl -s -X POST "$BASE_URL/knowledge-base" -H "Content-Type: application/json; charset=UTF-8" -H "Authorization: $TOKEN" --data-binary "{\"name\":\"api_test_$(date +%s)\",\"embeddingModel\":\"qwen-emb-8b\",\"collectionName\":\"api_test_$(date +%s)\"}")
KB_ID=$(echo "$KB_RESP" | python -c "import sys,json; d=json.load(sys.stdin); print(d.get('data',''))" 2>/dev/null)
check "创建知识库" "$KB_ID" "[0-9]"

# 上传文档
UPLOAD_RESP=$(curl -s -X POST "$BASE_URL/knowledge-base/$KB_ID/docs/upload" \
  -H "Authorization: $TOKEN" \
  -F "file=@/tmp/test_dev_standards.md" \
  -F "sourceType=file" \
  -F "processMode=chunk")
DOC_ID=$(echo "$UPLOAD_RESP" | python -c "import sys,json; d=json.load(sys.stdin); print(d.get('data',{}).get('id',''))" 2>/dev/null)
check "上传文档" "$DOC_ID" "[0-9]"

# 触发分块
CHUNK_RESP=$(curl -s -X POST "$BASE_URL/knowledge-base/docs/$DOC_ID/chunk" -H "Authorization: $TOKEN")
check "触发分块" "$CHUNK_RESP" '"code":"0"'

echo ""
echo "等待 30 秒让分块完成..."
sleep 30

# 查询分块列表
CHUNKS_RESP=$(curl -s "$BASE_URL/knowledge-base/docs/$DOC_ID/chunks" -H "Authorization: $TOKEN")
CHUNK_ID=$(echo "$CHUNKS_RESP" | python -c "
import sys,json,re
text = sys.stdin.read()
# 提取 id 字段（避免 JSON 中转义字符问题）
m = re.search(r'\"id\":\"(\d+)\"', text)
print(m.group(1) if m else '')
" 2>/dev/null)
check "查询分块列表获取 ChunkID" "$CHUNK_ID" "[0-9]"

if [ -z "$CHUNK_ID" ]; then
    echo ""
    echo "❌ 无法获取 ChunkID，跳过后续测试"
    echo "=========================================="
    echo "  结果: $PASS 通过, $FAIL 失败"
    echo "=========================================="
    exit 1
fi

# ========== 相似检索 ==========
echo ""
echo "--- 相似检索测试 ---"
# 用 Python 发送请求避免编码问题
SIMILAR_RESP=$(python -c "
import urllib.request, json
req = urllib.request.Request(
    '$BASE_URL/knowledge-base/search/similar',
    data=json.dumps({'query':'规范','topK':5}).encode('utf-8'),
    headers={'Authorization':'$TOKEN','Content-Type':'application/json; charset=UTF-8'}
)
print(urllib.request.urlopen(req).read().decode('utf-8'))
" 2>/dev/null)
check "相似检索返回成功" "$SIMILAR_RESP" '"code":"0"'
check "相似检索返回数据" "$SIMILAR_RESP" '"chunkId"'

# ========== 引用计数 ==========
echo ""
echo "--- 引用计数测试 ---"

# 查询初始投票分数
VOTE_RESP=$(curl -s "$BASE_URL/knowledge-base/chunks/$CHUNK_ID/vote" -H "Authorization: $TOKEN")
check "初始投票分数为0" "$VOTE_RESP" '"data":0'

# 记录引用3次
for i in 1 2 3; do
    curl -s -X POST "$BASE_URL/knowledge-base/chunks/$CHUNK_ID/reference" -H "Authorization: $TOKEN" > /dev/null
done

# 查询投票分数
VOTE_RESP=$(curl -s "$BASE_URL/knowledge-base/chunks/$CHUNK_ID/vote" -H "Authorization: $TOKEN")
check "引用3次后投票分数为3" "$VOTE_RESP" '"data":3'

# ========== 矛盾标记 ==========
echo ""
echo "--- 矛盾标记测试 ---"

# 创建第二个 chunk（模拟矛盾对）
UPLOAD2=$(curl -s -X POST "$BASE_URL/knowledge-base/$KB_ID/docs/upload" \
  -H "Authorization: $TOKEN" \
  -F "file=@/tmp/test_simple.md" \
  -F "sourceType=file" \
  -F "processMode=chunk")
DOC2_ID=$(echo "$UPLOAD2" | python -c "import sys,json; d=json.load(sys.stdin); print(d.get('data',{}).get('id',''))" 2>/dev/null)
curl -s -X POST "$BASE_URL/knowledge-base/docs/$DOC2_ID/chunk" -H "Authorization: $TOKEN" > /dev/null
sleep 20

CHUNKS2=$(curl -s "$BASE_URL/knowledge-base/docs/$DOC2_ID/chunks" -H "Authorization: $TOKEN")
CHUNK2_ID=$(echo "$CHUNKS2" | python -c "
import sys,json,re
text = sys.stdin.read()
m = re.search(r'\"id\":\"(\d+)\"', text)
print(m.group(1) if m else '')
" 2>/dev/null)

if [ -n "$CHUNK2_ID" ]; then
    # 设置矛盾对
    CONFLICT_RESP=$(curl -s -X POST "$BASE_URL/knowledge-base/chunks/$CHUNK_ID/conflict-pair" \
      -H "Authorization: $TOKEN" \
      -H "Content-Type: application/json" \
      -d "{\"conflictPairId\":\"$CHUNK2_ID\"}")
    check "设置矛盾对" "$CONFLICT_RESP" '"code":"0"'
else
    echo "  ⚠️ 第二个文档未分块成功，跳过矛盾标记测试"
fi

# ========== 废弃标记 ==========
echo ""
echo "--- 废弃标记测试 ---"
DEPRECATE_RESP=$(curl -s -X POST "$BASE_URL/knowledge-base/chunks/$CHUNK2_ID/deprecate" \
  -H "Authorization: $TOKEN")
check "标记废弃" "$DEPRECATE_RESP" '"code":"0"'

# 验证废弃状态
CHUNK_DETAIL=$(curl -s "$BASE_URL/knowledge-base/docs/$DOC_ID/chunks" -H "Authorization: $TOKEN")
check "验证废弃状态" "$CHUNK_DETAIL" '"deprecated"'

# ========== 清理 ==========
echo ""
echo "--- 清理测试数据 ---"
curl -s -X DELETE "$BASE_URL/knowledge-base/$KB_ID" -H "Authorization: $TOKEN" > /dev/null
echo "  已删除测试知识库"

# ========== 结果 ==========
echo ""
echo "=========================================="
echo "  结果: $PASS 通过, $FAIL 失败"
echo "=========================================="
exit $FAIL
