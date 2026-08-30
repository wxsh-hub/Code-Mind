import { api } from "./api";

export interface VectorDeleteResult {
  status: string;
  deleted_count: number;
  failed_count: number;
  errors: Array<{ chunk_id: string; error: string }>;
}

// 标记单个向量为废弃
export const deprecateChunk = async (chunkId: string): Promise<void> => {
  await api.post(`/knowledge-base/chunks/${chunkId}/deprecate`);
};

// 批量标记向量为废弃
export const batchDeprecateChunks = async (
  chunkIds: string[]
): Promise<VectorDeleteResult> => {
  return api.post<VectorDeleteResult, VectorDeleteResult>(
    "/knowledge-base/chunks/batch-deprecate",
    { chunk_ids: chunkIds }
  );
};

// 按功能编号删除向量
export const deleteByFeatureCode = async (
  code: string
): Promise<VectorDeleteResult> => {
  return api.delete<VectorDeleteResult, VectorDeleteResult>(
    `/knowledge-base/chunks/by-feature/${code}`
  );
};

// 按模块删除向量
export const deleteByModule = async (
  module: string
): Promise<VectorDeleteResult> => {
  return api.delete<VectorDeleteResult, VectorDeleteResult>(
    `/knowledge-base/chunks/by-module/${module}`
  );
};
