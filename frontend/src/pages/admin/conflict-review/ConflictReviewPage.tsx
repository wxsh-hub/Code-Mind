import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import { listConflicts, reviewConflict, ConflictPair } from "@/services/conflictService";

export function ConflictReviewPage() {
  const [conflicts, setConflicts] = useState<ConflictPair[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [pageSize] = useState(10);
  const [reviewingId, setReviewingId] = useState<string | null>(null);
  const [reviewReason, setReviewReason] = useState("");

  // 加载矛盾对列表
  const loadConflicts = async () => {
    setLoading(true);
    try {
      const result = await listConflicts("default", {
        page,
        page_size: pageSize,
      });
      setConflicts(result?.conflicts || []);
      setTotal(result?.pagination?.total || 0);
    } catch (error) {
      // 接口失败时不弹错误，显示空状态
      setConflicts([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadConflicts();
  }, [page]);

  // 审核矛盾对
  const handleReview = async (conflict: ConflictPair, winner: "a" | "b" | "both") => {
    const pairId = `${conflict.chunk_a.id}-${conflict.chunk_b.id}`;
    setReviewingId(pairId);

    try {
      await reviewConflict(
        "default",
        conflict.chunk_a.id,
        conflict.chunk_b.id,
        winner,
        reviewReason
      );

      toast.success(`已选择 ${winner === "a" ? "保留 A" : winner === "b" ? "保留 B" : "都保留"}`);

      // 重新加载列表
      setReviewReason("");
      loadConflicts();
    } catch (error) {
      toast.error("审核操作失败，请重试");
    } finally {
      setReviewingId(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">矛盾审核</h1>
        <div className="flex items-center gap-2">
          <Badge variant="outline">
            待审核: {total} 条
          </Badge>
          <Button onClick={loadConflicts} variant="outline" size="sm">
            刷新
          </Button>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-8">加载中...</div>
      ) : conflicts.length === 0 ? (
        <Card>
          <CardContent className="py-8 text-center text-muted-foreground">
            暂无待审核的矛盾对
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {conflicts.map((conflict, index) => {
            const pairId = `${conflict.chunk_a.id}-${conflict.chunk_b.id}`;
            const isReviewing = reviewingId === pairId;

            return (
              <Card key={pairId}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">
                      矛盾对 #{(page - 1) * pageSize + index + 1}
                    </CardTitle>
                    <Badge variant="secondary">
                      置信度差异: {(conflict.confidence_diff * 100).toFixed(0)}%
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-4 mb-4">
                    {/* 知识 A */}
                    <div className="p-4 bg-blue-50 rounded-lg border-l-4 border-blue-500">
                      <div className="flex items-center gap-2 mb-2">
                        <Badge className="bg-blue-500">A</Badge>
                        <span className="text-sm text-muted-foreground">
                          置信度: {conflict.chunk_a.confidence}
                        </span>
                      </div>
                      <p className="text-sm">{conflict.chunk_a.content}</p>
                    </div>

                    {/* 知识 B */}
                    <div className="p-4 bg-green-50 rounded-lg border-l-4 border-green-500">
                      <div className="flex items-center gap-2 mb-2">
                        <Badge className="bg-green-500">B</Badge>
                        <span className="text-sm text-muted-foreground">
                          置信度: {conflict.chunk_b.confidence}
                        </span>
                      </div>
                      <p className="text-sm">{conflict.chunk_b.content}</p>
                    </div>
                  </div>

                  {/* 审核原因 */}
                  <div className="mb-4">
                    <Textarea
                      placeholder="审核原因（可选）"
                      value={reviewReason}
                      onChange={(e) => setReviewReason(e.target.value)}
                      className="text-sm"
                    />
                  </div>

                  {/* 审核按钮 */}
                  <div className="flex justify-end gap-2">
                    <Button
                      variant="outline"
                      onClick={() => handleReview(conflict, "a")}
                      disabled={isReviewing}
                    >
                      保留 A
                    </Button>
                    <Button
                      className="bg-green-500 hover:bg-green-600"
                      onClick={() => handleReview(conflict, "b")}
                      disabled={isReviewing}
                    >
                      保留 B
                    </Button>
                    <Button
                      className="bg-yellow-500 hover:bg-yellow-600"
                      onClick={() => handleReview(conflict, "both")}
                      disabled={isReviewing}
                    >
                      都保留
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })}

          {/* 分页 */}
          {total > pageSize && (
            <div className="flex justify-center gap-2">
              <Button
                variant="outline"
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
              >
                上一页
              </Button>
              <span className="py-2 px-4">
                {page} / {Math.ceil(total / pageSize)}
              </span>
              <Button
                variant="outline"
                onClick={() => setPage(p => p + 1)}
                disabled={page >= Math.ceil(total / pageSize)}
              >
                下一页
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
