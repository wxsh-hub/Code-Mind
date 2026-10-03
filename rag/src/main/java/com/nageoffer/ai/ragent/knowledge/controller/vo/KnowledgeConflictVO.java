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

package com.nageoffer.ai.ragent.knowledge.controller.vo;

import lombok.Builder;
import lombok.Data;

import java.util.Date;

/**
 * 矛盾记录视图
 * <p>
 * 审核页要同时看到「当前原文」和「提交时原文」，两者可能已被别的流程改动，
 * 对不上时说明知识在审核前被动过，审核人应据此重新判断
 */
@Data
@Builder
public class KnowledgeConflictVO {

    private String id;

    private String kbId;

    /**
     * 知识库名称，供审核页直接展示
     */
    private String kbName;

    private String chunkId;

    private String relatedChunkId;

    /**
     * 提交时的原文快照
     */
    private String chunkContent;

    /**
     * 当前实际原文，分块已被删除时为 null
     */
    private String currentContent;

    private String reason;

    private String suggestion;

    private String status;

    private String submittedBy;

    private String reviewedBy;

    private String reviewComment;

    private Date reviewTime;

    private Date createTime;
}
