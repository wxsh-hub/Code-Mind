import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import {
  listConflicts,
  reviewConflict,
  type ConflictPage,
  type ConflictStatus,
  type KnowledgeConflict
} from "@/services/conflictService";
import { getErrorMessage } from "@/utils/error";

const STATUS_TABS: Array<{ value: ConflictStatus | ""; label: string }> = [
  { value: "pending", label: "待审核" },
  { value: "accepted", label: "已接受" },
  { value: "rejected", label: "已拒绝" },
  { value: "", label: "全部" }
];

const STATUS_LABEL: Record<ConflictStatus, string> = {
  pending: "待审核",
  accepted: "已接受",
  rejected: "已拒绝"
};

function formatTime(value?: string) {
  if (!value) return "";
  return value.replace("T", " ").slice(0, 16);
}

/** 原文与当前内容的对照；两者一致时只显示一份，避免审核人重复读 */
function ContentCompare({ conflict }: { conflict: KnowledgeConflict }) {
  const origin = conflict.chunkContent?.trim() || "";
  const current = conflict.currentContent?.trim() || "";
  const changed = Boolean(current) && current !== origin;

  return (
    <div className="space-y-3">
      <div>
        <p className="mb-1.5 text-xs font-medium text-muted-foreground">
          被质疑的原文{changed ? "（提交时）" : ""}
        </p>
        <pre className="max-h-40 overflow-auto whitespace-pre-wrap rounded-lg border border-border/70 bg-muted/40 p-3 text-xs leading-relaxed">
          {origin || "（原文已不可读）"}
        </pre>
      </div>
      {changed ? (
        <div>
          <p className="mb-1.5 text-xs font-medium text-muted-foreground">当前原文（提交后已被改动）</p>
          <pre className="max-h-40 overflow-auto whitespace-pre-wrap rounded-lg border border-border/70 bg-muted/40 p-3 text-xs leading-relaxed">
            {current}
          </pre>
        </div>
      ) : null}
      {!current ? (
        <p className="text-xs text-muted-foreground">该分块已被删除，接受审核不会改动任何知识。</p>
      ) : null}
    </div>
  );
}

export function ConflictReviewPage() {
  const [status, setStatus] = useState<ConflictStatus | "">("pending");
  const [page, setPage] = useState(1);
  const [data, setData] = useState<ConflictPage | null>(null);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [comments, setComments] = useState<Record<string, string>>({});
  const pageSize = 10;

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setData(await listConflicts(status, page, pageSize));
    } catch {
      // 拦截器已弹提示，此处只需保证页面不空转
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [status, page]);

  useEffect(() => {
    load();
  }, [load]);

  const handleReview = async (conflict: KnowledgeConflict, action: "accept" | "reject") => {
    setBusyId(conflict.id);
    try {
      await reviewConflict(conflict.id, action, comments[conflict.id]);
      toast.success(action === "accept" ? "已接受，原知识已按建议处置" : "已拒绝，原知识保持不变");
      setComments((prev) => ({ ...prev, [conflict.id]: "" }));
      await load();
    } catch (error) {
      toast.error(getErrorMessage(error, "审核失败，请重试"));
    } finally {
      setBusyId(null);
    }
  };

  const records = data?.records ?? [];
  const total = data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">矛盾审核</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          AI 自主发现 · 审核知识矛盾，接受则按建议改写原文
        </p>
      </div>

      <div className="flex gap-1 border-b border-border/70">
        {STATUS_TABS.map((tab) => (
          <button
            key={tab.value || "all"}
            type="button"
            onClick={() => {
              setStatus(tab.value);
              setPage(1);
            }}
            className={
              status === tab.value
                ? "border-b-2 border-primary px-4 py-2 text-sm font-medium text-foreground"
                : "border-b-2 border-transparent px-4 py-2 text-sm text-muted-foreground hover:text-foreground"
            }
          >
            {tab.label}
          </button>
        ))}
      </div>

      {loading ? (
        <p className="py-12 text-center text-sm text-muted-foreground">加载中…</p>
      ) : records.length === 0 ? (
        <p className="py-12 text-center text-sm text-muted-foreground">
          {status === "pending" ? "没有待审核的矛盾。" : "暂无记录。"}
        </p>
      ) : (
        <div className="space-y-4">
          {records.map((conflict) => {
            const pending = conflict.status === "pending";
            return (
              <Card key={conflict.id}>
                <CardContent className="space-y-4 pt-6">
                  <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                    <Badge variant={pending ? "default" : "outline"}>
                      {STATUS_LABEL[conflict.status] ?? conflict.status}
                    </Badge>
                    <span>{conflict.kbName || conflict.kbId}</span>
                    <span>·</span>
                    <span>{conflict.submittedBy || "未知"} 提交于 {formatTime(conflict.createTime)}</span>
                  </div>

                  <ContentCompare conflict={conflict} />

                  <div>
                    <p className="mb-1.5 text-xs font-medium text-muted-foreground">矛盾原因</p>
                    <p className="whitespace-pre-wrap text-sm leading-relaxed">{conflict.reason}</p>
                  </div>

                  {conflict.suggestion ? (
                    <div>
                      <p className="mb-1.5 text-xs font-medium text-muted-foreground">建议改成</p>
                      <pre className="max-h-40 overflow-auto whitespace-pre-wrap rounded-lg border border-emerald-500/30 bg-emerald-500/5 p-3 text-xs leading-relaxed">
                        {conflict.suggestion}
                      </pre>
                    </div>
                  ) : (
                    <p className="text-xs text-muted-foreground">
                      未给出建议内容，接受后只会把原知识标记为废弃。
                    </p>
                  )}

                  {pending ? (
                    <div className="space-y-2 border-t border-border/70 pt-4">
                      <Textarea
                        placeholder="审核意见（可选）"
                        value={comments[conflict.id] ?? ""}
                        onChange={(event) =>
                          setComments((prev) => ({ ...prev, [conflict.id]: event.target.value }))
                        }
                        rows={2}
                      />
                      <div className="flex justify-end gap-2">
                        <Button
                          variant="outline"
                          disabled={busyId === conflict.id}
                          onClick={() => handleReview(conflict, "reject")}
                        >
                          拒绝
                        </Button>
                        <Button
                          disabled={busyId === conflict.id}
                          onClick={() => handleReview(conflict, "accept")}
                        >
                          {busyId === conflict.id ? "处理中…" : "接受"}
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <div className="border-t border-border/70 pt-3 text-xs text-muted-foreground">
                      {conflict.reviewedBy || "未知"} 于 {formatTime(conflict.reviewTime)} 审核
                      {conflict.reviewComment ? `：${conflict.reviewComment}` : ""}
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {total > pageSize ? (
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">
            共 {total} 条，第 {page} / {totalPages} 页
          </span>
          <div className="flex gap-2">
            <Button variant="outline" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
              上一页
            </Button>
            <Button
              variant="outline"
              disabled={page >= totalPages}
              onClick={() => setPage((p) => p + 1)}
            >
              下一页
            </Button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
