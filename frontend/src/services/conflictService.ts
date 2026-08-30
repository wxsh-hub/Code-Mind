import { api } from "./api";

export interface ConflictChunk {
  id: string;
  content: string;
  confidence: number;
  score?: number;
}

export interface ConflictPair {
  chunk_a: ConflictChunk;
  chunk_b: ConflictChunk;
  confidence_diff: number;
  contradiction_type: string;
}

export interface ConflictPagination {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

export interface ConflictListResponse {
  status: string;
  project: string;
  conflicts: ConflictPair[];
  pagination: ConflictPagination;
  filters: {
    confidence_threshold: number;
    min_score: number;
  };
}

export interface ReviewResult {
  status: string;
  action: string;
  deprecated_chunk?: string;
  kept_chunk?: string;
  chunk_a?: string;
  chunk_b?: string;
  reason?: string;
}

export interface SubmitConflictResult {
  status: string;
  action: string;
  chunk_a: { id: string; content_preview: string };
  chunk_b: { id: string; content_preview: string };
  reason: string;
  ai_analysis: string;
  message: string;
}

// 列出待审核矛盾对
export const listConflicts = async (
  project: string,
  options?: {
    kb_id?: string;
    confidence_threshold?: number;
    page?: number;
    page_size?: number;
    min_score?: number;
  }
): Promise<ConflictListResponse> => {
  return api.post<ConflictListResponse, ConflictListResponse>("/conflicts/list", {
    project,
    ...options,
  });
};

// 审核矛盾对
export const reviewConflict = async (
  project: string,
  chunk_a_id: string,
  chunk_b_id: string,
  winner: "a" | "b" | "both",
  reason?: string
): Promise<ReviewResult> => {
  return api.post<ReviewResult, ReviewResult>("/conflicts/review", {
    project,
    chunk_a_id,
    chunk_b_id,
    winner,
    reason,
  });
};

// 提交矛盾对到后台审核
export const submitConflictForReview = async (
  project: string,
  chunk_a_id: string,
  chunk_b_id: string,
  reason: string,
  ai_analysis?: string
): Promise<SubmitConflictResult> => {
  return api.post<SubmitConflictResult, SubmitConflictResult>("/conflicts/submit", {
    project,
    chunk_a_id,
    chunk_b_id,
    reason,
    ai_analysis,
  });
};
