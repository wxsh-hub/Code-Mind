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
     * 生产环境应使用向量检索替代。
     */
    @PostMapping("/knowledge-base/search/similar")
    public Result<List<Map<String, Object>>> searchSimilar(
            @RequestBody SimilarSearchRequest request) {
        LambdaQueryWrapper<KnowledgeChunkDO> wrapper = new LambdaQueryWrapper<KnowledgeChunkDO>()
                .eq(KnowledgeChunkDO::getEnabled, 1)
                .eq(KnowledgeChunkDO::getDeleted, 0)
                .like(KnowledgeChunkDO::getContent, request.getQuery())
                .last("LIMIT " + request.getTopK());

        if (request.getKbId() != null && !request.getKbId().isEmpty()) {
            wrapper.eq(KnowledgeChunkDO::getKbId, request.getKbId());
        }

        List<KnowledgeChunkDO> chunks = chunkMapper.selectList(wrapper);

        List<Map<String, Object>> results = chunks.stream().map(chunk -> {
            Map<String, Object> item = new HashMap<>();
            item.put("chunkId", chunk.getId());
            item.put("content", chunk.getContent());
            item.put("docId", chunk.getDocId());
            item.put("kbId", chunk.getKbId());

            Map<String, Object> metadata = new HashMap<>();
            metadata.put("sourceType", chunk.getSourceType());
            metadata.put("sourceRef", chunk.getSourceRef());
            metadata.put("chunkVersion", chunk.getChunkVersion());
            metadata.put("voteCount", chunk.getVoteCount());
            metadata.put("conflictPairId", chunk.getConflictPairId());
            metadata.put("deprecated", chunk.getDeprecated());
            item.put("metadata", metadata);

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

    // --- 请求 DTO ---

    @Data
    public static class SimilarSearchRequest {
        /** 检索文本 */
        private String query;
        /** 限定知识库（可选） */
        private String kbId;
        /** 返回条数，默认 10 */
        private Integer topK = 10;
    }

    @Data
    public static class ConflictPairRequest {
        /** 矛盾对的另一个 chunk ID */
        private String conflictPairId;
    }
}
