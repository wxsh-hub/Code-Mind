/*
 * Licensed to the Apache Software Foundation (ASF) under one or more
 * contributor license agreements.  See the NOTICE file distributed with
 * this work for additional information regarding copyright ownership.
 * The ASF licenses this file to You under the Apache License, Version 2.0
 * (the "License"); you may not use this file except in compliance with
 * the License.  You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package com.nageoffer.ai.ragent.knowledge.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.nageoffer.ai.ragent.framework.convention.Result;
import com.nageoffer.ai.ragent.framework.web.Results;
import com.nageoffer.ai.ragent.knowledge.dao.entity.KnowledgeChunkDO;
import com.nageoffer.ai.ragent.knowledge.dao.mapper.KnowledgeChunkMapper;
import lombok.Data;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 知识库 Chunk 对外 API（供 MCP Gateway 等外部系统调用）
 * <p>
 * 提供相似 chunk 检索和引用计数功能，用于矛盾检测和投票机制
 */
@RestController
@RequiredArgsConstructor
public class KnowledgeChunkApiController {

    private final KnowledgeChunkMapper chunkMapper;

    /**
     * 相似 chunk 检索（供外部系统调用，如矛盾检测）
     * <p>
     * 基于内容关键词模糊匹配，返回相似 chunk 及其元数据。
     * 支持按功能编号和模块过滤。
     */
    @PostMapping("/knowledge-base/search/similar")
    public Result<List<Map<String, Object>>> searchSimilar(
            @RequestBody SimilarSearchRequest request) {
        LambdaQueryWrapper<KnowledgeChunkDO> wrapper = new LambdaQueryWrapper<KnowledgeChunkDO>()
                .eq(KnowledgeChunkDO::getEnabled, 1)
                .eq(KnowledgeChunkDO::getDeleted, 0);

        // 内容匹配
        if (request.getQuery() != null && !request.getQuery().isEmpty()) {
            wrapper.like(KnowledgeChunkDO::getContent, request.getQuery());
        }

        // 知识库过滤
        if (request.getKbId() != null && !request.getKbId().isEmpty()) {
            wrapper.eq(KnowledgeChunkDO::getKbId, request.getKbId());
        }

        // 功能编号过滤（JSONB）
        if (request.getFeatureCodes() != null && !request.getFeatureCodes().isEmpty()) {
            String[] codes = request.getFeatureCodes().split(",");
            for (String code : codes) {
                wrapper.apply("metadata->'feature_codes' @> '[\"{0}\"]'", code.trim());
            }
        }

        // 模块过滤（JSONB）
        if (request.getModule() != null && !request.getModule().isEmpty()) {
            wrapper.apply("metadata->>'module' = {0}", request.getModule());
        }

        wrapper.last("LIMIT " + request.getTopK());

        List<KnowledgeChunkDO> chunks = chunkMapper.selectList(wrapper);

        List<Map<String, Object>> results = chunks.stream().map(chunk -> {
            Map<String, Object> item = new HashMap<>();
            item.put("chunkId", chunk.getId());
            item.put("content", chunk.getContent());
            item.put("docId", chunk.getDocId());
            item.put("kbId", chunk.getKbId());

            // 基础元数据
            Map<String, Object> metadata = new HashMap<>();
            metadata.put("sourceType", chunk.getSourceType());
            metadata.put("sourceRef", chunk.getSourceRef());
            metadata.put("chunkVersion", chunk.getChunkVersion());
            metadata.put("voteCount", chunk.getVoteCount());
            metadata.put("conflictPairId", chunk.getConflictPairId());
            metadata.put("deprecated", chunk.getDeprecated());
            item.put("metadata", metadata);

            // 上传统计
            item.put("uploadCount", chunk.getUploadCount() != null ? chunk.getUploadCount() : 1);
            item.put("lastUploadAt", chunk.getLastUploadAt());
            item.put("confidence", chunk.getConfidence() != null ? chunk.getConfidence() : 1);

            return item;
        }).toList();

        return Results.success(results);
    }

    /**
     * 记录 chunk 被引用（供外部系统调用，如投票机制）
     * <p>
     * 每次调用 vote_count + 1
     */
    @PostMapping("/knowledge-base/chunks/{chunkId}/reference")
    public Result<Void> recordReference(@PathVariable String chunkId) {
        KnowledgeChunkDO chunk = chunkMapper.selectById(chunkId);
        if (chunk == null) {
            return Results.success();
        }

        int currentVote = chunk.getVoteCount() != null ? chunk.getVoteCount() : 0;
        KnowledgeChunkDO update = new KnowledgeChunkDO();
        update.setId(chunkId);
        update.setVoteCount(currentVote + 1);
        chunkMapper.updateById(update);

        return Results.success();
    }

    /**
     * 查询 chunk 投票分数
     */
    @GetMapping("/knowledge-base/chunks/{chunkId}/vote")
    public Result<Integer> getVoteScore(@PathVariable String chunkId) {
        KnowledgeChunkDO chunk = chunkMapper.selectById(chunkId);
        if (chunk == null) {
            return Results.success(0);
        }
        return Results.success(chunk.getVoteCount() != null ? chunk.getVoteCount() : 0);
    }

    /**
     * 更新 chunk 的矛盾对 ID
     */
    @PostMapping("/knowledge-base/chunks/{chunkId}/conflict-pair")
    public Result<Void> setConflictPair(@PathVariable String chunkId,
                                         @RequestBody ConflictPairRequest request) {
        KnowledgeChunkDO update = new KnowledgeChunkDO();
        update.setId(chunkId);
        update.setConflictPairId(request.getConflictPairId());
        chunkMapper.updateById(update);
        return Results.success();
    }

    /**
     * 标记 chunk 为已废弃
     */
    @PostMapping("/knowledge-base/chunks/{chunkId}/deprecate")
    public Result<Void> deprecate(@PathVariable String chunkId) {
        KnowledgeChunkDO update = new KnowledgeChunkDO();
        update.setId(chunkId);
        update.setDeprecated(true);
        chunkMapper.updateById(update);
        return Results.success();
    }

    /**
     * 计算并更新 chunk 的置信度
     * <p>
     * 置信度 = 语义相似的 chunk 数量（含自己）
     * 用于衡量知识的可信度：多人提交相似内容 → 更可信
     */
    @PostMapping("/knowledge-base/chunks/{chunkId}/calculate-confidence")
    public Result<Integer> calculateConfidence(@PathVariable String chunkId,
                                                @RequestParam(defaultValue = "0.7") Double threshold) {
        KnowledgeChunkDO chunk = chunkMapper.selectById(chunkId);
        if (chunk == null) {
            return Results.success(0);
        }

        // 搜索相似 chunk（基于内容关键词匹配）
        LambdaQueryWrapper<KnowledgeChunkDO> wrapper = new LambdaQueryWrapper<KnowledgeChunkDO>()
                .eq(KnowledgeChunkDO::getEnabled, 1)
                .eq(KnowledgeChunkDO::getDeleted, 0)
                .eq(KnowledgeChunkDO::getKbId, chunk.getKbId())
                .ne(KnowledgeChunkDO::getId, chunkId)
                .like(KnowledgeChunkDO::getContent, chunk.getContent().substring(0, Math.min(50, chunk.getContent().length())))
                .last("LIMIT 100");

        List<KnowledgeChunkDO> similarChunks = chunkMapper.selectList(wrapper);

        // 计算置信度（相似 chunk 数量 + 1 包含自己）
        int confidence = similarChunks.size() + 1;

        // 更新置信度
        KnowledgeChunkDO update = new KnowledgeChunkDO();
        update.setId(chunkId);
        update.setConfidence(confidence);
        chunkMapper.updateById(update);

        return Results.success(confidence);
    }

    /**
     * 获取 chunk 的置信度
     */
    @GetMapping("/knowledge-base/chunks/{chunkId}/confidence")
    public Result<Integer> getConfidence(@PathVariable String chunkId) {
        KnowledgeChunkDO chunk = chunkMapper.selectById(chunkId);
        if (chunk == null) {
            return Results.success(0);
        }
        return Results.success(chunk.getConfidence() != null ? chunk.getConfidence() : 1);
    }

    /**
     * 批量归一化置信度（用于召回后评分）
     * <p>
     * 将一组 chunk 的置信度按比例归一化到100 总分
     * 返回每个 chunk 的归一化分数
     */
    @PostMapping("/knowledge-base/chunks/normalize-confidence")
    public Result<List<Map<String, Object>>> normalizeConfidence(
            @RequestBody List<String> chunkIds) {
        if (chunkIds == null || chunkIds.isEmpty()) {
            return Results.success(List.of());
        }

        // 查询所有 chunk 的置信度
        List<KnowledgeChunkDO> chunks = chunkMapper.selectBatchIds(chunkIds);
        if (chunks.isEmpty()) {
            return Results.success(List.of());
        }

        // 计算总置信度
        int totalConfidence = chunks.stream()
                .mapToInt(c -> c.getConfidence() != null ? c.getConfidence() : 1)
                .sum();

        // 归一化到100 分
        List<Map<String, Object>> result = chunks.stream().map(chunk -> {
            Map<String, Object> item = new HashMap<>();
            int conf = chunk.getConfidence() != null ? chunk.getConfidence() : 1;
            double normalized = totalConfidence > 0 ? (conf * 100.0 / totalConfidence) : 0;

            item.put("chunkId", chunk.getId());
            item.put("confidence", conf);
            item.put("normalizedScore", Math.round(normalized * 100.0) / 100.0); // 保留两位小数
            return item;
        }).toList();

        return Results.success(result);
    }

    // --- 请求 DTO ---

    @Data
    public static class SimilarSearchRequest {
        /** 检索文本 */
        private String query;
        /** 限定知识库（可选） */
        private String kbId;
        /** 返回条数，默认 10 */
        private Integer topK = 10;
        /** 功能编号过滤（逗号分隔，可选） */
        private String featureCodes;
        /** 模块过滤（可选） */
        private String module;
    }

    @Data
    public static class ConflictPairRequest {
        /** 矛盾对的另一个 chunk ID */
        private String conflictPairId;
    }
}
