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

package com.nageoffer.ai.ragent.knowledge.dao.entity;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableLogic;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.Date;

/**
 * 知识矛盾记录实体
 * <p>
 * 由 AI 或人工提出、后台审核处置。chunkContent 是提交当刻的原文快照——
 * 知识可能在被审核前就被别的流程改掉，审核人要看到的是「提出时它长什么样」
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@TableName("t_knowledge_conflict")
public class KnowledgeConflictDO {

    @TableId(type = IdType.ASSIGN_ID)
    private String id;

    /**
     * 所属知识库
     */
    private String kbId;

    /**
     * 被质疑的知识分块 ID
     */
    private String chunkId;

    /**
     * 与之冲突的另一条分块 ID，可为空
     */
    private String relatedChunkId;

    /**
     * 提交时被质疑分块的原文快照
     */
    private String chunkContent;

    /**
     * 矛盾原因
     */
    private String reason;

    /**
     * 建议改成什么
     */
    private String suggestion;

    /**
     * 审核状态，见 {@link com.nageoffer.ai.ragent.knowledge.enums.ConflictStatus}
     */
    private String status;

    /**
     * 提交人
     */
    private String submittedBy;

    /**
     * 审核人
     */
    private String reviewedBy;

    /**
     * 审核意见
     */
    private String reviewComment;

    /**
     * 审核时间
     */
    private Date reviewTime;

    @TableField(fill = FieldFill.INSERT)
    private Date createTime;

    @TableField(fill = FieldFill.INSERT_UPDATE)
    private Date updateTime;

    @TableLogic
    private Integer deleted;
}
