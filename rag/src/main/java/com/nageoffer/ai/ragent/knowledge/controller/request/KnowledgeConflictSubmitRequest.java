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

package com.nageoffer.ai.ragent.knowledge.controller.request;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Data;

/**
 * 提交知识矛盾
 */
@Data
public class KnowledgeConflictSubmitRequest {

    /**
     * 被质疑的知识分块 ID
     */
    @NotBlank(message = "被质疑的知识分块不能为空")
    private String chunkId;

    /**
     * 与之冲突的另一条分块 ID，仅指出本条有误时留空
     */
    private String relatedChunkId;

    /**
     * 矛盾原因：为什么认为这条不对
     * <p>
     * 必填——只给结论不给理由的矛盾记录，审核人无从判断该不该接受
     */
    @NotBlank(message = "矛盾原因不能为空")
    @Size(max = 2000, message = "矛盾原因不能超过 2000 字")
    private String reason;

    /**
     * 建议改成什么
     * <p>
     * 审核接受时用它替换原文；留空则接受后仅将原知识标记为废弃
     */
    @Size(max = 4000, message = "建议内容不能超过 4000 字")
    private String suggestion;
}
