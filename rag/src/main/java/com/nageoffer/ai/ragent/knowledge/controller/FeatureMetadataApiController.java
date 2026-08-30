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
import com.nageoffer.ai.ragent.knowledge.dao.entity.FeatureMetadataDO;
import com.nageoffer.ai.ragent.knowledge.dao.mapper.FeatureMetadataMapper;
import lombok.Data;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 功能元数据管理 API
 */
@RestController
@RequiredArgsConstructor
public class FeatureMetadataApiController {

    private final FeatureMetadataMapper featureMapper;

    /**
     * 创建功能
     */
    @PostMapping("/feature-metadata")
    public Result<Map<String, Object>> createFeature(@RequestBody CreateFeatureRequest request) {
        // 检查编号是否已存在
        LambdaQueryWrapper<FeatureMetadataDO> wrapper = new LambdaQueryWrapper<FeatureMetadataDO>()
                .eq(FeatureMetadataDO::getFeatureCode, request.getFeatureCode())
                .eq(FeatureMetadataDO::getDeleted, 0);
        if (featureMapper.selectCount(wrapper) > 0) {
            Map<String, Object> error = new HashMap<>();
            error.put("error", "功能编号已存在");
            return Results.success(error);
        }

        FeatureMetadataDO feature = FeatureMetadataDO.builder()
                .featureCode(request.getFeatureCode())
                .featureName(request.getFeatureName())
                .moduleName(request.getModuleName())
                .description(request.getDescription())
                .status("active")
                .build();
        featureMapper.insert(feature);

        Map<String, Object> result = new HashMap<>();
        result.put("id", feature.getId());
        result.put("featureCode", feature.getFeatureCode());
        result.put("featureName", feature.getFeatureName());
        result.put("moduleName", feature.getModuleName());
        result.put("status", feature.getStatus());
        return Results.success(result);
    }

    /**
     * 列出功能（可按模块过滤）
     */
    @GetMapping("/feature-metadata")
    public Result<List<FeatureMetadataDO>> listFeatures(
            @RequestParam(required = false) String module) {
        LambdaQueryWrapper<FeatureMetadataDO> wrapper = new LambdaQueryWrapper<FeatureMetadataDO>()
                .eq(FeatureMetadataDO::getDeleted, 0)
                .eq(FeatureMetadataDO::getStatus, "active");

        if (module != null && !module.isEmpty()) {
            wrapper.eq(FeatureMetadataDO::getModuleName, module);
        }

        wrapper.orderByDesc(FeatureMetadataDO::getCreatedAt);
        return Results.success(featureMapper.selectList(wrapper));
    }

    /**
     * 搜索功能元数据（模糊匹配功能名称和描述）
     * 支持多个关键词，用空格分隔，任意一个关键词匹配即返回
     */
    @GetMapping("/feature-metadata/search")
    public Result<List<FeatureMetadataDO>> searchFeatures(
            @RequestParam String keyword,
            @RequestParam(defaultValue = "5") int limit) {
        // 分割关键词（支持空格、逗号、句号等分隔符）
        String[] keywords = keyword.split("[\\s,.!?;:]+");

        LambdaQueryWrapper<FeatureMetadataDO> wrapper = new LambdaQueryWrapper<FeatureMetadataDO>()
                .eq(FeatureMetadataDO::getDeleted, 0)
                .eq(FeatureMetadataDO::getStatus, "active");

        // 对任意一个关键词进行模糊匹配（OR 关系）
        if (keywords.length > 0) {
            wrapper.and(w -> {
                boolean[] first = {true};
                for (String kw : keywords) {
                    final String trimmedKw = kw.trim();
                    if (trimmedKw.isEmpty() || trimmedKw.length() < 2) continue;

                    if (!first[0]) {
                        w.or();
                    }
                    w.and(inner -> inner
                            .like(FeatureMetadataDO::getFeatureName, trimmedKw)
                            .or()
                            .like(FeatureMetadataDO::getDescription, trimmedKw)
                    );
                    first[0] = false;
                }
            });
        }

        wrapper.last("LIMIT " + limit);
        return Results.success(featureMapper.selectList(wrapper));
    }

    /**
     * 获取功能详情
     */
    @GetMapping("/feature-metadata/{code}")
    public Result<Map<String, Object>> getFeature(@PathVariable String code) {
        LambdaQueryWrapper<FeatureMetadataDO> wrapper = new LambdaQueryWrapper<FeatureMetadataDO>()
                .eq(FeatureMetadataDO::getFeatureCode, code)
                .eq(FeatureMetadataDO::getDeleted, 0);
        FeatureMetadataDO feature = featureMapper.selectOne(wrapper);
        if (feature == null) {
            Map<String, Object> error = new HashMap<>();
            error.put("error", "功能不存在");
            return Results.success(error);
        }

        Map<String, Object> result = new HashMap<>();
        result.put("id", feature.getId());
        result.put("featureCode", feature.getFeatureCode());
        result.put("featureName", feature.getFeatureName());
        result.put("moduleName", feature.getModuleName());
        result.put("description", feature.getDescription());
        result.put("status", feature.getStatus());
        result.put("createdAt", feature.getCreatedAt());
        return Results.success(result);
    }

    /**
     * 删除功能（级联删除向量）
     */
    @DeleteMapping("/feature-metadata/{code}")
    public Result<Map<String, Object>> deleteFeature(@PathVariable String code) {
        LambdaQueryWrapper<FeatureMetadataDO> wrapper = new LambdaQueryWrapper<FeatureMetadataDO>()
                .eq(FeatureMetadataDO::getFeatureCode, code)
                .eq(FeatureMetadataDO::getDeleted, 0);
        FeatureMetadataDO feature = featureMapper.selectOne(wrapper);
        if (feature == null) {
            Map<String, Object> error = new HashMap<>();
            error.put("error", "功能不存在");
            return Results.success(error);
        }

        // 逻辑删除功能
        featureMapper.deleteById(feature.getId());

        // TODO: 级联删除该功能的向量
        // 需要查询 metadata->'feature_codes' 包含该编号的向量并删除

        Map<String, Object> result = new HashMap<>();
        result.put("deleted_feature", code);
        result.put("deleted_chunks", 0); // TODO: 实际删除数量
        return Results.success(result);
    }

    @Data
    public static class CreateFeatureRequest {
        private String featureCode;
        private String featureName;
        private String moduleName;
        private String description;
    }
}
