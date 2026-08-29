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
import com.nageoffer.ai.ragent.knowledge.dao.entity.ModuleDO;
import com.nageoffer.ai.ragent.knowledge.dao.mapper.ModuleMapper;
import lombok.Data;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 模块管理 API
 */
@RestController
@RequiredArgsConstructor
public class ModuleApiController {

    private final ModuleMapper moduleMapper;

    /**
     * 创建模块
     */
    @PostMapping("/modules")
    public Result<Map<String, Object>> createModule(@RequestBody CreateModuleRequest request) {
        // 检查名称是否已存在
        LambdaQueryWrapper<ModuleDO> wrapper = new LambdaQueryWrapper<ModuleDO>()
                .eq(ModuleDO::getName, request.getName())
                .eq(ModuleDO::getDeleted, 0);
        if (moduleMapper.selectCount(wrapper) > 0) {
            Map<String, Object> error = new HashMap<>();
            error.put("error", "模块名称已存在");
            return Results.success(error);
        }

        ModuleDO module = ModuleDO.builder()
                .name(request.getName())
                .description(request.getDescription())
                .build();
        moduleMapper.insert(module);

        Map<String, Object> result = new HashMap<>();
        result.put("id", module.getId());
        result.put("name", module.getName());
        result.put("description", module.getDescription());
        return Results.success(result);
    }

    /**
     * 列出所有模块
     */
    @GetMapping("/modules")
    public Result<List<ModuleDO>> listModules() {
        LambdaQueryWrapper<ModuleDO> wrapper = new LambdaQueryWrapper<ModuleDO>()
                .eq(ModuleDO::getDeleted, 0)
                .orderByDesc(ModuleDO::getCreatedAt);
        return Results.success(moduleMapper.selectList(wrapper));
    }

    /**
     * 获取模块详情
     */
    @GetMapping("/modules/{name}")
    public Result<Map<String, Object>> getModule(@PathVariable String name) {
        LambdaQueryWrapper<ModuleDO> wrapper = new LambdaQueryWrapper<ModuleDO>()
                .eq(ModuleDO::getName, name)
                .eq(ModuleDO::getDeleted, 0);
        ModuleDO module = moduleMapper.selectOne(wrapper);
        if (module == null) {
            Map<String, Object> error = new HashMap<>();
            error.put("error", "模块不存在");
            return Results.success(error);
        }

        Map<String, Object> result = new HashMap<>();
        result.put("id", module.getId());
        result.put("name", module.getName());
        result.put("description", module.getDescription());
        result.put("createdAt", module.getCreatedAt());
        return Results.success(result);
    }

    /**
     * 删除模块（级联删除功能和向量）
     */
    @DeleteMapping("/modules/{name}")
    public Result<Map<String, Object>> deleteModule(@PathVariable String name) {
        LambdaQueryWrapper<ModuleDO> wrapper = new LambdaQueryWrapper<ModuleDO>()
                .eq(ModuleDO::getName, name)
                .eq(ModuleDO::getDeleted, 0);
        ModuleDO module = moduleMapper.selectOne(wrapper);
        if (module == null) {
            Map<String, Object> error = new HashMap<>();
            error.put("error", "模块不存在");
            return Results.success(error);
        }

        // 逻辑删除模块
        moduleMapper.deleteById(module.getId());

        // TODO: 级联删除该模块下的功能和向量
        // 这需要调用 FeatureMetadataMapper 和 KnowledgeChunkMapper

        Map<String, Object> result = new HashMap<>();
        result.put("deleted_module", name);
        return Results.success(result);
    }

    @Data
    public static class CreateModuleRequest {
        private String name;
        private String description;
    }
}
