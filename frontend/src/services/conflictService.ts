import { api } from "./api";

export type ConflictStatus = "pending" | "accepted" | "rejected";

export interface KnowledgeConflict {
  id: string;
  kbId: string;
  kbName?: string;
  chunkId: string;
  relatedChunkId?: string;
  /** 提交当时的原文快照 */
  chunkContent?: string;
  /** 当前实际原文；分块已被删除时为空 */
  currentContent?: string;
  reason: string;
  suggestion?: string;
  status: ConflictStatus;
  submittedBy?: string;
  reviewedBy?: string;
  reviewComment?: string;
  reviewTime?: string;
  createTime?: string;
}

export interface ConflictPage {
  records: KnowledgeConflict[];
  total: number;
  current: number;
  size: number;
}

/** 分页查询矛盾记录，status 留空查全部 */
export async function listConflicts(
  status: ConflictStatus | "",
  pageNum = 1,
  pageSize = 10
): Promise<ConflictPage> {
  const params: Record<string, unknown> = { pageNum, pageSize };
  if (status) {
    params.status = status;
  }
  return api.get<ConflictPage, ConflictPage>("/knowledge-base/conflicts", { params });
}

/**
 * 审核矛盾
 *
 * accept 会用建议内容替换原文（无建议时把原知识标记为废弃），reject 只留记录
 */
export async function reviewConflict(
  conflictId: string,
  action: "accept" | "reject",
  reviewComment?: string
): Promise<void> {
  await api.post(`/knowledge-base/conflicts/${conflictId}/review`, { action, reviewComment });
}
