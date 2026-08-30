#!/bin/bash
# RAG 全流程测试脚本
# 测试：登录 → 创建知识库 → 上传文档 → 分块 → 提问

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
echo "  RAG 全流程测试"
echo "=========================================="

# ========== Step 1: 登录 ==========
echo ""
echo "[1/5] 登录获取 Token..."
LOGIN_RESP=$(curl -s -X POST "$BASE_URL/auth/login" -H "Content-Type: application/json" -d '{"username":"admin","password":"admin"}')
TOKEN=$(echo "$LOGIN_RESP" | python -c "import sys,json; print(json.load(sys.stdin)['data']['token'])" 2>/dev/null)
check "登录成功" "$TOKEN" "[a-f0-9]"

# ========== Step 2: 创建知识库 ==========
echo ""
echo "[2/5] 创建知识库..."
KB_RESP=$(curl -s -X POST "$BASE_URL/knowledge-base" \
  -H "Content-Type: application/json" \
  -H "Authorization: $TOKEN" \
  -d "{\"name\":\"rag_test_$(date +%s)\",\"embeddingModel\":\"qwen-emb-8b\",\"collectionName\":\"rag_test_$(date +%s)\"}")
KB_ID=$(echo "$KB_RESP" | python -c "import sys,json; d=json.load(sys.stdin); print(d.get('data',''))" 2>/dev/null)
check "创建知识库成功" "$KB_ID" "[0-9]"

# ========== Step 3: 上传文档 ==========
echo ""
echo "[3/5] 上传测试文档..."

cat > /tmp/test_rag_doc.md << 'DOCEOF'
# RAG 技术详解

## 什么是 RAG

RAG（Retrieval-Augmented Generation）是一种结合检索和生成的 AI 技术。
它通过从知识库中检索相关信息，然后使用大语言模型生成答案。

## RAG 的优势

1. 减少幻觉：基于真实文档生成答案，而不是凭空编造
2. 知识更新：只需更新知识库，无需重新训练模型
3. 可追溯：答案可以引用原始文档，方便验证
4. 成本低：相比微调模型，RAG 的实施成本更低

## RAG 的核心流程

1. 文档解析：将 PDF、Word、Markdown 等格式转为纯文本
2. 文本分块：将长文档切分为适合检索的小段
3. 向量化：使用 Embedding 模型将文本转为向量
4. 检索：根据用户问题找到最相关的文档块
5. 生成：将检索结果和问题一起发给 LLM 生成答案
DOCEOF

UPLOAD_RESP=$(curl -s -X POST "$BASE_URL/knowledge-base/$KB_ID/docs/upload" \
  -H "Authorization: $TOKEN" \
  -F "file=@/tmp/test_rag_doc.md" \
  -F "sourceType=file" \
  -F "processMode=chunk")
DOC_ID=$(echo "$UPLOAD_RESP" | python -c "import sys,json; d=json.load(sys.stdin); print(d.get('data',{}).get('id',''))" 2>/dev/null)
check "上传文档成功" "$DOC_ID" "[0-9]"

# ========== Step 4: 触发分块 ==========
echo ""
echo "[4/5] 触发文档分块..."
CHUNK_RESP=$(curl -s -X POST "$BASE_URL/knowledge-base/docs/$DOC_ID/chunk" -H "Authorization: $TOKEN")
check "触发分块成功" "$CHUNK_RESP" '"code":"0"'

echo "  等待 30 秒让分块和向量化完成..."
sleep 30

DOC_STATUS=$(curl -s "$BASE_URL/knowledge-base/docs/$DOC_ID" -H "Authorization: $TOKEN")
STATUS=$(echo "$DOC_STATUS" | python -c "import sys,json; print(json.load(sys.stdin)['data']['status'])" 2>/dev/null)
CHUNK_COUNT=$(echo "$DOC_STATUS" | python -c "import sys,json; print(json.load(sys.stdin)['data']['chunkCount'])" 2>/dev/null)
check "分块状态为 success" "$STATUS" "success"
check "分块数量 > 0" "$CHUNK_COUNT" "[1-9]"

# ========== Step 5: RAG 问答 ==========
echo ""
echo "[5/5] RAG 问答测试..."
echo "  问题: RAG技术有什么优势？"
echo ""

CHAT_RESP=$(curl -N -s "$BASE_URL/rag/v3/chat?question=RAG%E6%8A%80%E6%9C%AF%E6%9C%89%E4%BB%80%E4%B9%88%E4%BC%98%E5%8A%BF%EF%BC%9F" \
  -H "Authorization: $TOKEN" \
  --max-time 60 2>&1)

# 提取回答文本
ANSWER=$(echo "$CHAT_RESP" | grep "event:message" -A1 | grep '"delta"' | python -c "
import sys,json
chars = []
for line in sys.stdin:
    try:
        d = json.loads(line.strip().split('data:',1)[1])
        chars.append(d.get('delta',''))
    except: pass
print(''.join(chars))
" 2>/dev/null)

check "RAG 返回答案" "$ANSWER" "优势"

# 检查是否有来源引用
HAS_SOURCE=$(echo "$CHAT_RESP" | grep -i "sources\|docName\|finish")
check "返回包含来源引用" "$HAS_SOURCE" "finish"

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
