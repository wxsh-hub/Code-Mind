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

import com.nageoffer.ai.ragent.framework.context.LoginUser;
import com.nageoffer.ai.ragent.framework.context.UserContext;
import com.nageoffer.ai.ragent.framework.exception.ClientException;
import com.nageoffer.ai.ragent.knowledge.controller.request.KnowledgeChunkUpdateRequest;
import com.nageoffer.ai.ragent.knowledge.controller.request.KnowledgeConflictReviewRequest;
import com.nageoffer.ai.ragent.knowledge.controller.request.KnowledgeConflictSubmitRequest;
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
import com.nageoffer.ai.ragent.rag.core.vector.VectorStoreService;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class KnowledgeConflictServiceImplTest {

    private static final String CHUNK_ID = "1001";
    private static final String DOC_ID = "2001";
    private static final String KB_ID = "3001";
    private static final String COLLECTION = "kb_demo";

    @Mock
    private KnowledgeConflictMapper conflictMapper;

    @Mock
    private KnowledgeChunkMapper chunkMapper;

    @Mock
    private KnowledgeDocumentMapper documentMapper;

    @Mock
    private KnowledgeBaseMapper knowledgeBaseMapper;

    @Mock
    private KnowledgeChunkService chunkService;

    @Mock
    private VectorStoreService vectorStoreService;

    private KnowledgeConflictServiceImpl service;

    @BeforeEach
    void setUp() {
        service = new KnowledgeConflictServiceImpl(conflictMapper, chunkMapper, documentMapper,
                knowledgeBaseMapper, chunkService, vectorStoreService);
        LoginUser loginUser = new LoginUser();
        loginUser.setUsername("tester");
        UserContext.set(loginUser);
    }

    @AfterEach
    void tearDown() {
        UserContext.clear();
    }

    private KnowledgeChunkDO chunk() {
        KnowledgeChunkDO chunk = new KnowledgeChunkDO();
        chunk.setId(CHUNK_ID);
        chunk.setDocId(DOC_ID);
        chunk.setKbId(KB_ID);
        chunk.setContent("原内容：复核时限 3 个工作日");
        return chunk;
    }

    // ---------- 提交 ----------

    @Test
    @DisplayName("分块不存在时拒绝提交")
    void submitRejectsUnknownChunk() {
        when(chunkMapper.selectById(CHUNK_ID)).thenReturn(null);

        KnowledgeConflictSubmitRequest request = new KnowledgeConflictSubmitRequest();
        request.setChunkId(CHUNK_ID);
        request.setReason("内容过时");

        assertThrows(ClientException.class, () -> service.submit(request));
        verify(conflictMapper, never()).insert(any(KnowledgeConflictDO.class));
    }

    @Test
    @DisplayName("同一条知识已有待审核记录时拒绝重复提交")
    void submitRejectsDuplicatePending() {
        when(chunkMapper.selectById(CHUNK_ID)).thenReturn(chunk());
        when(conflictMapper.selectCount(any())).thenReturn(1L);

        KnowledgeConflictSubmitRequest request = new KnowledgeConflictSubmitRequest();
        request.setChunkId(CHUNK_ID);
        request.setReason("内容过时");

        assertThrows(ClientException.class, () -> service.submit(request));
        verify(conflictMapper, never()).insert(any(KnowledgeConflictDO.class));
    }

    @Test
    @DisplayName("提交时记录原文快照与提交人，且不改动知识本身")
    void submitStoresSnapshotWithoutTouchingKnowledge() {
        when(chunkMapper.selectById(CHUNK_ID)).thenReturn(chunk());
        when(conflictMapper.selectCount(any())).thenReturn(0L);

        KnowledgeConflictSubmitRequest request = new KnowledgeConflictSubmitRequest();
        request.setChunkId(CHUNK_ID);
        request.setReason("  复核时限已改  ");
        request.setSuggestion("复核时限 1 个工作日");

        service.submit(request);

        ArgumentCaptor<KnowledgeConflictDO> captor = ArgumentCaptor.forClass(KnowledgeConflictDO.class);
        verify(conflictMapper).insert(captor.capture());
        KnowledgeConflictDO saved = captor.getValue();

        assertEquals(CHUNK_ID, saved.getChunkId());
        assertEquals(KB_ID, saved.getKbId());
        assertEquals("原内容：复核时限 3 个工作日", saved.getChunkContent());
        // reason 前后空白应被裁掉，否则审核页会显示得参差不齐
        assertEquals("复核时限已改", saved.getReason());
        assertEquals("复核时限 1 个工作日", saved.getSuggestion());
        assertEquals(ConflictStatus.PENDING.getValue(), saved.getStatus());
        assertEquals("tester", saved.getSubmittedBy());

        verify(chunkMapper, never()).updateById(any(KnowledgeChunkDO.class));
        verify(vectorStoreService, never()).markDeprecated(any(), any(), eq(true));
    }

    // ---------- 审核 ----------

    private KnowledgeDocumentDO document() {
        KnowledgeDocumentDO document = new KnowledgeDocumentDO();
        document.setId(DOC_ID);
        document.setKbId(KB_ID);
        return document;
    }

    private KnowledgeConflictDO conflict(String status, String suggestion) {
        KnowledgeConflictDO entity = new KnowledgeConflictDO();
        entity.setId("9001");
        entity.setChunkId(CHUNK_ID);
        entity.setStatus(status);
        entity.setSuggestion(suggestion);
        return entity;
    }

    private KnowledgeConflictReviewRequest review(String action) {
        KnowledgeConflictReviewRequest request = new KnowledgeConflictReviewRequest();
        request.setAction(action);
        return request;
    }

    @Test
    @DisplayName("矛盾不存在时拒绝审核")
    void reviewRejectsUnknownConflict() {
        when(conflictMapper.selectById("9001")).thenReturn(null);

        assertThrows(ClientException.class, () -> service.review("9001", review("accept")));
    }

    @Test
    @DisplayName("已审核过的矛盾不能重复处置")
    void reviewRejectsAlreadyReviewed() {
        when(conflictMapper.selectById("9001")).thenReturn(conflict(ConflictStatus.ACCEPTED.getValue(), "x"));

        assertThrows(ClientException.class, () -> service.review("9001", review("accept")));
        verify(conflictMapper, never()).updateById(any(KnowledgeConflictDO.class));
    }

    @Test
    @DisplayName("非法的审核动作被拒绝")
    void reviewRejectsUnknownAction() {
        when(conflictMapper.selectById("9001")).thenReturn(conflict(ConflictStatus.PENDING.getValue(), "x"));

        assertThrows(ClientException.class, () -> service.review("9001", review("maybe")));
        verify(conflictMapper, never()).updateById(any(KnowledgeConflictDO.class));
    }

    @Test
    @DisplayName("接受且带建议时，用建议内容替换原文")
    void acceptWithSuggestionReplacesContent() {
        when(conflictMapper.selectById("9001")).thenReturn(conflict(ConflictStatus.PENDING.getValue(), "复核时限 1 个工作日"));
        when(chunkMapper.selectById(CHUNK_ID)).thenReturn(chunk());
        when(documentMapper.selectById(DOC_ID)).thenReturn(document());

        service.review("9001", review("accept"));

        ArgumentCaptor<KnowledgeChunkUpdateRequest> updateCaptor =
                ArgumentCaptor.forClass(KnowledgeChunkUpdateRequest.class);
        verify(chunkService).update(eq(DOC_ID), eq(CHUNK_ID), updateCaptor.capture());
        assertEquals("复核时限 1 个工作日", updateCaptor.getValue().getContent());

        // 替换路径不走废弃，否则新内容会被自己刚打的标记挡在检索之外
        verify(vectorStoreService, never()).markDeprecated(any(), any(), eq(true));

        ArgumentCaptor<KnowledgeConflictDO> captor = ArgumentCaptor.forClass(KnowledgeConflictDO.class);
        verify(conflictMapper).updateById(captor.capture());
        assertEquals(ConflictStatus.ACCEPTED.getValue(), captor.getValue().getStatus());
        assertEquals("tester", captor.getValue().getReviewedBy());
        assertNotNull(captor.getValue().getReviewTime());
    }

    @Test
    @DisplayName("接受且无建议时，把原知识标记为废弃并同步到向量表")
    void acceptWithoutSuggestionDeprecates() {
        when(conflictMapper.selectById("9001")).thenReturn(conflict(ConflictStatus.PENDING.getValue(), null));
        when(chunkMapper.selectById(CHUNK_ID)).thenReturn(chunk());
        when(documentMapper.selectById(DOC_ID)).thenReturn(document());
        KnowledgeBaseDO knowledgeBase = new KnowledgeBaseDO();
        knowledgeBase.setId(KB_ID);
        knowledgeBase.setCollectionName(COLLECTION);
        when(knowledgeBaseMapper.selectById(KB_ID)).thenReturn(knowledgeBase);

        service.review("9001", review("accept"));

        ArgumentCaptor<KnowledgeChunkDO> chunkCaptor = ArgumentCaptor.forClass(KnowledgeChunkDO.class);
        verify(chunkMapper).updateById(chunkCaptor.capture());
        assertEquals(Boolean.TRUE, chunkCaptor.getValue().getDeprecated());

        // 关键：标记必须落到向量表，只写 chunk 表的话检索侧读不到，废弃等于没做
        verify(vectorStoreService).markDeprecated(COLLECTION, CHUNK_ID, true);
        verify(chunkService, never()).update(any(), any(), any());
    }

    @Test
    @DisplayName("拒绝时只记录结论，不动任何知识")
    void rejectLeavesKnowledgeUntouched() {
        when(conflictMapper.selectById("9001")).thenReturn(conflict(ConflictStatus.PENDING.getValue(), "复核时限 1 个工作日"));

        service.review("9001", review("reject"));

        verify(chunkService, never()).update(any(), any(), any());
        verify(chunkMapper, never()).updateById(any(KnowledgeChunkDO.class));
        verify(vectorStoreService, never()).markDeprecated(any(), any(), eq(true));

        ArgumentCaptor<KnowledgeConflictDO> captor = ArgumentCaptor.forClass(KnowledgeConflictDO.class);
        verify(conflictMapper).updateById(captor.capture());
        assertEquals(ConflictStatus.REJECTED.getValue(), captor.getValue().getStatus());
    }
}
