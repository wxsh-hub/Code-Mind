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

package com.nageoffer.ai.ragent.knowledge.service;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.nageoffer.ai.ragent.knowledge.controller.request.KnowledgeConflictReviewRequest;
import com.nageoffer.ai.ragent.knowledge.controller.request.KnowledgeConflictSubmitRequest;
import com.nageoffer.ai.ragent.knowledge.controller.vo.KnowledgeConflictVO;

/**
 * 知识矛盾服务
 */
public interface KnowledgeConflictService {

    /**
     * 提交矛盾，返回矛盾记录 ID
     * <p>
     * 提交只做记录，不改变任何知识——处置权在后台审核
     */
    String submit(KnowledgeConflictSubmitRequest requestParam);

    /**
     * 分页查询矛盾记录
     *
     * @param status 按状态过滤，为空查全部
     */
    IPage<KnowledgeConflictVO> pageQuery(String status, Integer pageNum, Integer pageSize);

    /**
     * 审核：接受则按建议处置原知识，拒绝则维持原样
     */
    void review(String conflictId, KnowledgeConflictReviewRequest requestParam);
}
