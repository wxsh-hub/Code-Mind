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

import lombok.Data;

import java.time.LocalDateTime;

/**
 * 知识库 Chunk 视图对象
 */
@Data
public class KnowledgeChunkVO {

    /**
     * ID
     */
    private String id;

    /**
     * 知识库ID
     */
    private String kbId;

    /**
     * 文档ID
     */
    private String docId;

    /**
     * 分块序号（从0开始）
     */
    private Integer chunkIndex;

    /**
     * 分块正文内容
     */
    private String content;

    /**
     * 内容哈希（用于幂等/去重）
     */
    private String contentHash;

    /**
     * 字符数
     */
    private Integer charCount;

    /**
     * Token数
     */
    private Integer tokenCount;

    /**
     * 是否启用 0：禁用 1：启用
     */
    private Integer enabled;

    /**
     * 来源类型：upload / gitlab / api
     */
    private String sourceType;

    /**
     * 来源引用
     */
    private String sourceRef;

    /**
     * chunk 版本号
     */
    private Integer chunkVersion;

    /**
     * 被引用/检索命中次数
     */
    private Integer voteCount;

    /**
     * 矛盾对的另一个 chunk ID
     */
    private String conflictPairId;

    /**
     * 是否已废弃
     */
    private Boolean deprecated;

    /**
     * 置信度分数
     */
    private Integer confidence;

    /**
     * 创建时间
     */
    private LocalDateTime createTime;

    /**
     * 更新时间
     */
    private LocalDateTime updateTime;
}
