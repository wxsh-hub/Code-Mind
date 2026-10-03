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

package com.nageoffer.ai.ragent.knowledge.service.impl;

import cn.hutool.core.util.StrUtil;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.core.toolkit.Wrappers;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.nageoffer.ai.ragent.framework.context.UserContext;
import com.nageoffer.ai.ragent.framework.exception.ClientException;
import com.nageoffer.ai.ragent.knowledge.controller.request.KnowledgeChunkUpdateRequest;
import com.nageoffer.ai.ragent.knowledge.controller.request.KnowledgeConflictReviewRequest;
import com.nageoffer.ai.ragent.knowledge.controller.request.KnowledgeConflictSubmitRequest;
import com.nageoffer.ai.ragent.knowledge.controller.vo.KnowledgeConflictVO;
import com.nageoffer.ai.ragent.knowledge.dao.entity.KnowledgeBaseDO;
import com.nageoffer.ai.ragent.knowledge.dao.entity.KnowledgeChunkDO;
import com.nageoffer.ai.ragent.knowledge.dao.entity.KnowledgeConflictDO;
import com.nageoffer.ai.ragent.knowledge.dao.entity.KnowledgeDocumentDO;
import com.nageoffer.ai.ragent.knowledge.dao.mapper.KnowledgeBaseMapper;
import com.nageoffer.ai.ragent.knowledge.dao.mapper.KnowledgeChunkMapper;
import com.nageoffer.ai.ragent.knowledge.dao.mapper.KnowledgeConflictMapper;
import com.nageoffer.ai.ragent.knowledge.dao.mapper.KnowledgeDocumentMapper;
import com.nageoffer.ai.ragent.knowledge.enums.ConflictStatus;
import com.nageoffer.ai.ragent.knowledge.service.KnowledgeChunkService;
import com.nageoffer.ai.ragent.knowledge.service.KnowledgeConflictService;
import com.nageoffer.ai.ragent.rag.core.vector.VectorStoreService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Date;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.function.Function;
import java.util.stream.Collectors;

/**
 * 知识矛盾服务实现
 * <p>
 * 提交与审核分离：提交只落记录，审核才动知识。两件事分属不同的人，
 * 混在一起会让「谁改的」说不清楚
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class KnowledgeConflictServiceImpl implements KnowledgeConflictService {

    /**
     * 审核动作
     */
    private static final String ACTION_ACCEPT = "accept";
    private static final String ACTION_REJECT = "reject";

    private final KnowledgeConflictMapper conflictMapper;
    private final KnowledgeChunkMapper chunkMapper;
    private final KnowledgeDocumentMapper documentMapper;
    private final KnowledgeBaseMapper knowledgeBaseMapper;
    private final KnowledgeChunkService chunkService;
    private final VectorStoreService vectorStoreService;

    @Override
    @Transactional(rollbackFor = Exception.class)
    public String submit(KnowledgeConflictSubmitRequest requestParam) {
        KnowledgeChunkDO chunk = chunkMapper.selectById(requestParam.getChunkId());
        if (chunk == null) {
            throw new ClientException("被质疑的知识分块不存在：" + requestParam.getChunkId());
        }
        // 待审核的重复提交直接拒绝：同一条知识被反复提，审核队列会失去意义
        Long pending = conflictMapper.selectCount(Wrappers.lambdaQuery(KnowledgeConflictDO.class)
                .eq(KnowledgeConflictDO::getChunkId, chunk.getId())
                .eq(KnowledgeConflictDO::getStatus, ConflictStatus.PENDING.getValue()));
        if (pending != null && pending > 0) {
            throw new ClientException("这条知识已有待审核的矛盾记录，请等待审核完成");
        }

        KnowledgeConflictDO entity = KnowledgeConflictDO.builder()
                .kbId(chunk.getKbId())
                .chunkId(chunk.getId())
                .relatedChunkId(StrUtil.trimToNull(requestParam.getRelatedChunkId()))
                // 存快照而非引用：审核人要看的是「提出时它长什么样」
                .chunkContent(chunk.getContent())
                .reason(requestParam.getReason().trim())
                .suggestion(StrUtil.trimToNull(requestParam.getSuggestion()))
                .status(ConflictStatus.PENDING.getValue())
                .submittedBy(UserContext.getUsername())
                .build();
        conflictMapper.insert(entity);

        log.info("矛盾已提交，conflictId={}, chunkId={}, 提交人={}",
                entity.getId(), chunk.getId(), entity.getSubmittedBy());
        return entity.getId();
    }

    @Override
    public IPage<KnowledgeConflictVO> pageQuery(String status, Integer pageNum, Integer pageSize) {
        ConflictStatus parsed = ConflictStatus.parse(status);
        Page<KnowledgeConflictDO> page = new Page<>(
                pageNum == null || pageNum < 1 ? 1 : pageNum,
                pageSize == null || pageSize < 1 ? 10 : Math.min(pageSize, 100));

        IPage<KnowledgeConflictDO> result = conflictMapper.selectPage(page,
                Wrappers.lambdaQuery(KnowledgeConflictDO.class)
                        .eq(parsed != null, KnowledgeConflictDO::getStatus,
                                parsed == null ? null : parsed.getValue())
                        .orderByDesc(KnowledgeConflictDO::getCreateTime));

        List<KnowledgeConflictDO> records = result.getRecords();
        if (records.isEmpty()) {
            return new Page<>(result.getCurrent(), result.getSize(), result.getTotal());
        }

        Map<String, String> kbNames = loadKbNames(records);
        Map<String, String> currentContents = loadCurrentContents(records);

        IPage<KnowledgeConflictVO> voPage = new Page<>(result.getCurrent(), result.getSize(), result.getTotal());
        voPage.setRecords(records.stream()
                .map(record -> toVO(record, kbNames, currentContents))
                .toList());
        return voPage;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void review(String conflictId, KnowledgeConflictReviewRequest requestParam) {
        KnowledgeConflictDO conflict = conflictMapper.selectById(conflictId);
        if (conflict == null) {
            throw new ClientException("矛盾记录不存在：" + conflictId);
        }
        ConflictStatus current = ConflictStatus.parse(conflict.getStatus());
        if (current != ConflictStatus.PENDING) {
            throw new ClientException("该矛盾已审核过，不能重复处置");
        }

        String action = requestParam.getAction() == null ? "" : requestParam.getAction().trim().toLowerCase();
        boolean accept = ACTION_ACCEPT.equals(action);
        if (!accept && !ACTION_REJECT.equals(action)) {
            throw new ClientException("审核动作只能是 accept 或 reject");
        }

        if (accept) {
            applyAccept(conflict);
        }

        KnowledgeConflictDO update = new KnowledgeConflictDO();
        update.setId(conflictId);
        update.setStatus(accept ? ConflictStatus.ACCEPTED.getValue() : ConflictStatus.REJECTED.getValue());
        update.setReviewedBy(UserContext.getUsername());
        update.setReviewComment(StrUtil.trimToNull(requestParam.getReviewComment()));
        update.setReviewTime(new Date());
        conflictMapper.updateById(update);

        log.info("矛盾审核完成，conflictId={}, action={}, 审核人={}", conflictId, action, update.getReviewedBy());
    }

    /**
     * 接受审核：按建议替换原文；没有建议就只标废弃
     * <p>
     * 两条路都不物理删除——审核是人工判断，判断错了要能查得到原内容
     */
    private void applyAccept(KnowledgeConflictDO conflict) {
        KnowledgeChunkDO chunk = chunkMapper.selectById(conflict.getChunkId());
        if (chunk == null) {
            log.warn("矛盾接受时原分块已不存在，仅记录审核结论，conflictId={}, chunkId={}",
                    conflict.getId(), conflict.getChunkId());
            return;
        }
        KnowledgeDocumentDO document = documentMapper.selectById(chunk.getDocId());
        if (document == null) {
            log.warn("矛盾接受时所属文档已不存在，仅记录审核结论，conflictId={}, docId={}",
                    conflict.getId(), chunk.getDocId());
            return;
        }

        if (StrUtil.isNotBlank(conflict.getSuggestion())) {
            // 走既有分块更新链路：改写正文、重算哈希与 token、重新向量化一并完成，
            // 且 updateChunk 的 ON CONFLICT 会顺带解除废弃标记
            KnowledgeChunkUpdateRequest updateRequest = new KnowledgeChunkUpdateRequest();
            updateRequest.setContent(conflict.getSuggestion());
            chunkService.update(chunk.getDocId(), chunk.getId(), updateRequest);
            log.info("矛盾接受：已用建议内容替换原文，conflictId={}, chunkId={}", conflict.getId(), chunk.getId());
            return;
        }

        KnowledgeBaseDO knowledgeBase = knowledgeBaseMapper.selectById(document.getKbId());
        if (knowledgeBase == null || StrUtil.isBlank(knowledgeBase.getCollectionName())) {
            log.warn("矛盾接受时知识库或 collection 缺失，仅记录审核结论，conflictId={}, kbId={}",
                    conflict.getId(), document.getKbId());
            return;
        }

        // 走软废弃而非 enableChunk(false)：后者会物理删除向量记录，审核判断有误时
        // 只能靠重新向量化找回；软标记只是让检索跳过它，随时能解回来
        KnowledgeChunkDO chunkUpdate = new KnowledgeChunkDO();
        chunkUpdate.setId(chunk.getId());
        chunkUpdate.setDeprecated(true);
        chunkUpdate.setUpdatedBy(UserContext.getUsername());
        chunkMapper.updateById(chunkUpdate);

        vectorStoreService.markDeprecated(knowledgeBase.getCollectionName(), chunk.getId(), true);
        log.info("矛盾接受：无建议内容，已将原知识标记为废弃，conflictId={}, chunkId={}", conflict.getId(), chunk.getId());
    }

    private Map<String, String> loadKbNames(List<KnowledgeConflictDO> records) {
        Set<String> kbIds = records.stream()
                .map(KnowledgeConflictDO::getKbId)
                .filter(Objects::nonNull)
                .collect(Collectors.toSet());
        if (kbIds.isEmpty()) {
            return Map.of();
        }
        return knowledgeBaseMapper.selectByIds(kbIds).stream()
                .filter(kb -> kb.getId() != null)
                .collect(Collectors.toMap(KnowledgeBaseDO::getId,
                        kb -> StrUtil.emptyIfNull(kb.getName()), (left, right) -> left));
    }

    /**
     * 取分块当前正文，供审核页与提交时的快照对照
     */
    private Map<String, String> loadCurrentContents(List<KnowledgeConflictDO> records) {
        Set<String> chunkIds = records.stream()
                .map(KnowledgeConflictDO::getChunkId)
                .filter(Objects::nonNull)
                .collect(Collectors.toSet());
        if (chunkIds.isEmpty()) {
            return Map.of();
        }
        return chunkMapper.selectByIds(chunkIds).stream()
                .filter(chunk -> chunk.getId() != null)
                .collect(Collectors.toMap(KnowledgeChunkDO::getId,
                        chunk -> StrUtil.emptyIfNull(chunk.getContent()), (left, right) -> left));
    }

    private KnowledgeConflictVO toVO(KnowledgeConflictDO record,
                                     Map<String, String> kbNames,
                                     Map<String, String> currentContents) {
        return KnowledgeConflictVO.builder()
                .id(record.getId())
                .kbId(record.getKbId())
                .kbName(kbNames.get(record.getKbId()))
                .chunkId(record.getChunkId())
                .relatedChunkId(record.getRelatedChunkId())
                .chunkContent(record.getChunkContent())
                .currentContent(currentContents.get(record.getChunkId()))
                .reason(record.getReason())
                .suggestion(record.getSuggestion())
                .status(record.getStatus())
                .submittedBy(record.getSubmittedBy())
                .reviewedBy(record.getReviewedBy())
                .reviewComment(record.getReviewComment())
                .reviewTime(record.getReviewTime())
                .createTime(record.getCreateTime())
                .build();
    }
}
