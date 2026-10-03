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

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.nageoffer.ai.ragent.framework.convention.Result;
import com.nageoffer.ai.ragent.framework.web.Results;
import com.nageoffer.ai.ragent.knowledge.controller.request.KnowledgeConflictReviewRequest;
import com.nageoffer.ai.ragent.knowledge.controller.request.KnowledgeConflictSubmitRequest;
import com.nageoffer.ai.ragent.knowledge.controller.vo.KnowledgeConflictVO;
import com.nageoffer.ai.ragent.knowledge.service.KnowledgeConflictService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * 知识矛盾接口
 * <p>
 * 提交侧供 AI / 人工指出知识有误，审核侧供后台处置。
 * 提交不改动知识，只落一条待审核记录——处置权必须在人手上
 */
@RestController
@RequiredArgsConstructor
public class KnowledgeConflictController {

    private final KnowledgeConflictService conflictService;

    /**
     * 提交矛盾：指出某条知识有误，并说明原因与建议改法
     */
    @PostMapping("/knowledge-base/conflicts")
    public Result<String> submit(@Valid @RequestBody KnowledgeConflictSubmitRequest requestParam) {
        return Results.success(conflictService.submit(requestParam));
    }

    /**
     * 分页查询矛盾记录
     *
     * @param status 按状态过滤（pending / accepted / rejected），为空查全部
     */
    @GetMapping("/knowledge-base/conflicts")
    public Result<IPage<KnowledgeConflictVO>> pageQuery(@RequestParam(required = false) String status,
                                                        @RequestParam(defaultValue = "1") Integer pageNum,
                                                        @RequestParam(defaultValue = "10") Integer pageSize) {
        return Results.success(conflictService.pageQuery(status, pageNum, pageSize));
    }

    /**
     * 审核矛盾：接受则按建议处置原知识，拒绝则维持原样
     */
    @PostMapping("/knowledge-base/conflicts/{conflictId}/review")
    public Result<Void> review(@PathVariable String conflictId,
                               @Valid @RequestBody KnowledgeConflictReviewRequest requestParam) {
        conflictService.review(conflictId, requestParam);
        return Results.success();
    }
}
