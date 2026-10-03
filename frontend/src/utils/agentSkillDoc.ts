/**
 * 生成「把企业知识库接入外部 AI」的说明文档
 *
 * 文档随当前登录账号与站点地址生成，token 直接写进正文——这份文件等同于账号凭证，
 * 下载页因此只提供下载、不做任何服务端存储，避免凭证在我们这边多留一份。
 */

const API_PREFIX = "/api/ragent";

export interface SkillDocContext {
  username: string;
  token: string;
}

function apiBase(): string {
  return `${window.location.origin}${API_PREFIX}`;
}

export function buildAgentSkillDoc({ username, token }: SkillDocContext): string {
  const base = apiBase();
  return `# 企业知识库接入说明

把这份文件追加到你的 AI 工具的规则文件里——Claude Code 用 \`CLAUDE.md\`、
Codex 用 \`AGENTS.md\`、Cursor 用 \`.cursor/rules/\` 下的任意 \`.md\`，
AI 就能读写我们团队的企业知识库。

## 你的身份

| 项 | 值 |
|---|---|
| 账号 | ${username} |
| 接口地址 | ${base} |
| 凭证 | ${token} |

下面所有请求都要带这个请求头（注意：**不要**加 \`Bearer \` 前缀）：

\`\`\`
Authorization: ${token}
\`\`\`

> 这份文件等同于账号密码，请勿分享或提交到公开仓库。有效期 30 天，过期后在平台重新下载。

---

## 一、查询知识库（最常用）

想知道团队内部某件事怎么做的，直接提问：

\`\`\`bash
curl -N "${base}/agent/v1/chat?question=订单支付回调怎么验签" \\
  -H "Authorization: ${token}"
\`\`\`

返回是 SSE 流，逐行推送。取 \`event: message\` 中 \`data\` 里 \`type\` 为 \`response\` 的
\`delta\` 字段依次拼接，即为完整回答。

这条链路走的是完整检索增强流程（意图识别 → 向量检索 → 精排 → 生成），
回答会引用知识库原文，**比直接问模型可信，优先使用它回答团队内部问题**。

---

## 二、创建知识库

一个项目建一个知识库即可，不要按文档建。

\`\`\`bash
curl -X POST "${base}/knowledge-base" \\
  -H "Authorization: ${token}" \\
  -H "Content-Type: application/json" \\
  -d '{"name":"订单中心","embeddingModel":"qwen-emb-8b","collectionName":"order_center"}'
\`\`\`

- \`embeddingModel\` **必传**，漏掉会被数据库直接拒绝，报「数据访问异常」这种看不出原因的错。
  填 \`qwen-emb-8b\` 即可，这是默认向量模型。
- 返回的 \`data\` 字段本身就是知识库 ID（一个字符串，不是对象），下文记作 \`{kbId}\`。

---

## 三、上传知识文档

### 文件名按这个格式

\`\`\`
项目名-模块-文档名-日期.md
\`\`\`

例如：\`订单中心-支付-回调验签说明-20261002.md\`

这样命名是为了**给人看**：后台文档列表一眼能认出归属，回答引用时显示的也是这个名字。

> 注意：文件名**不参与**检索范围判定。真正决定「按模块筛选」的是下面上传时的
> \`module\` 参数——它会写进这条知识的元数据，之后 \`search/similar\` 能按它过滤。
> 所以**文件名和 module 参数都要填对**，两者作用不同。

### 上传

\`\`\`bash
curl -X POST "${base}/knowledge-base/{kbId}/docs/upload" \\
  -H "Authorization: ${token}" \\
  -F "file=@order-center-payment-callback-20261002.md" \\
  -F "sourceType=file" \\
  -F "processMode=chunk" \\
  -F "module=payment"
\`\`\`

- \`module\` 决定这条知识属于哪个模块，后续可按它筛选，**必填且要和文件名里的模块一致**。
- \`processMode=chunk\` 表示用分块策略直接切分，普通文档都用这个。

拿到返回的 \`data.id\`（下文记作 \`{docId}\`）后，触发分块入库：

\`\`\`bash
curl -X POST "${base}/knowledge-base/docs/{docId}/chunk" \\
  -H "Authorization: ${token}"
\`\`\`

分块是异步的，调用后稍等片刻再检索，否则查不到新内容。

> ⚠️ **Windows 上务必注意**：在 Windows 的 cmd 或 Git Bash 里用 curl 上传**中文文件名**，
> 文件名会以乱码存进系统（正文不受影响，只是名字坏掉）。浏览器上传、或在 WSL / macOS / Linux
> 下执行都正常。若只能在 Windows 下用 curl，请把文件先改成英文名上传，再改名：

\`\`\`bash
curl -X PUT "${base}/knowledge-base/docs/{docId}" \\
  -H "Authorization: ${token}" \\
  -H "Content-Type: application/json" \\
  -d '{"docName":"订单中心-支付-回调验签说明-20261002.md"}'
\`\`\`

---

## 四、发现矛盾时提出

读文档或写代码时，如果发现知识库内容与事实不符、或两篇文档互相打架，
可以提出来。**这在团队里是有价值的贡献，发现就提，不要自己咽下去。**

### 第 1 步：定位是哪一条

\`\`\`bash
curl -X POST "${base}/knowledge-base/search/similar" \\
  -H "Authorization: ${token}" \\
  -H "Content-Type: application/json" \\
  -d '{"query":"支付回调验签","topK":5}'
\`\`\`

返回的 \`data\` 是一个数组，每项形如：

\`\`\`json
{
  "chunkId": "2105933717645209600",
  "content": "支付回调使用 RSA2 验签，公钥由支付中心下发……",
  "docId": "2105932933260021760",
  "score": 1.0,
  "metadata": { "deprecated": false, "voteCount": 0, "conflictPairId": null }
}
\`\`\`

\`chunkId\` 是知识片段的唯一编号，下一步要用它。
\`metadata.deprecated\` 为 \`true\` 说明这条已被标记过时，不用再提。

调这个接口有两个要点：

1. 它是**关键词匹配**不是语义检索，换个说法可能搜不到，多用几个关键词试。
2. 请求体可以带 \`module\` 限定范围，如 \`{"query":"验签","module":"payment","topK":5}\`，
   只返回该模块下的知识。找不准时先不加，命中后再加限定缩小范围。

### 第 2 步：提交矛盾

\`\`\`bash
curl -X POST "${base}/knowledge-base/conflicts" \\
  -H "Authorization: ${token}" \\
  -H "Content-Type: application/json" \\
  -d '{
    "chunkId": "{被质疑的那条 chunkId}",
    "relatedChunkId": "{和它冲突的另一条，没有就省略}",
    "reason": "为什么认为这条不对",
    "suggestion": "应该改成什么"
  }'
\`\`\`

两个字段要认真写，后台的人靠它们做判断：

- \`reason\` **必填**。只给结论不给理由，审核人无从判断该不该接受。
- \`suggestion\` **强烈建议填**。审核接受时会**用它替换原文**；
  留空的话，接受后只会把原知识整个废弃掉，等于让这条知识消失而不是被修正。

### 提交之后会怎样

提交**不会**改动任何知识，只是排进后台的审核队列，由人工处置：

| 审核结果 | 结果 |
|---|---|
| 接受 | 用你的 \`suggestion\` 替换原文并重新索引；没给 suggestion 则把原知识废弃 |
| 拒绝 | 原知识保持不变，你的意见作为记录留存 |

所以提交时不用担心改坏东西——**但要把话说清楚**，否则没人能替你判断。

> 同一条知识只能有一条待审核的矛盾，重复提交会被拒绝。

---

## 五、其他可用接口

| 用途 | 请求 |
|---|---|
| 查询片段被引用次数 | \`GET ${base}/knowledge-base/chunks/{chunkId}/vote\` |
| 标记这条知识被引用过（投票 +1） | \`POST ${base}/knowledge-base/chunks/{chunkId}/reference\` |
| 列出知识库 | \`GET ${base}/knowledge-base\` |
| 列出某库文档 | \`GET ${base}/knowledge-base/{kbId}/docs\` |
| 按**文件名**搜文档 | \`GET ${base}/knowledge-base/docs/search?keyword=xxx\` |
| 重命名文档 | \`PUT ${base}/knowledge-base/docs/{docId}\`，body \`{"docName":"新名字.md"}\` |
| 查自己提过的矛盾 | \`GET ${base}/knowledge-base/conflicts?status=pending\` |

> \`docs/search\` 只匹配**文件名**，不搜文档内容。想按内容找知识，用上面第四节的
> \`search/similar\`；想直接问问题，用第一节的问答接口。

---

## 六、行为准则

1. **改动前先问用户**。上传文档、废弃知识都是对团队共享数据的改动，先说清楚你打算做什么。
2. **优先查知识库再回答**。涉及团队内部约定的问题，先调接口查，不要凭模型记忆作答。
3. **不确定就说不确定**。检索结果为空时如实告知，不要编造团队内部规范。
4. **token 是本文件的一部分**，转发文件等于交出账号。
`;
}

export function downloadAgentSkillDoc(context: SkillDocContext): void {
  const content = buildAgentSkillDoc(context);
  const blob = new Blob([content], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `企业知识库接入说明-${context.username}.md`;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  URL.revokeObjectURL(url);
}
