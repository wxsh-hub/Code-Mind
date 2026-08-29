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

package com.nageoffer.ai.ragent.agent.memory;

import jakarta.validation.constraints.Min;
import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;
import org.springframework.validation.annotation.Validated;

import java.util.ArrayList;
import java.util.List;

/**
 * Agent 会话记忆配置（agent.memory 段），两道门按固定比例从 contextWindowChars 派生
 */
@Data
@Configuration
@ConfigurationProperties(prefix = "agent.memory")
@Validated
public class AgentMemoryProperties {

    /**
     * 裁剪门：过半即动手，只把老工具结果换成占位
     */
    private static final double TRIM_TRIGGER_RATIO = 0.5D;

    /**
     * 压缩门：裁剪顶不住才动手，余两成给压缩期间的模型调用
     */
    private static final double COMPACT_TRIGGER_RATIO = 0.8D;

    /**
     * 保留段：压缩切点之后至少留这么多原文
     */
    private static final double KEEP_RECENT_RATIO = 0.2D;

    /**
     * 往前保几个已完成的工具循环，本轮和未闭合的额外保护不占配额
     */
    private static final int KEEP_RECENT_CYCLES = 2;

    /**
     * 可回收量低于当前上下文的这个比例就不动
     */
    private static final double CLEAR_AT_LEAST_RATIO = 0.2D;

    /**
     * 摘要正文上限：0.1×预算 夹进 [1500, 6000]
     * 上限受同步阻塞预算约束，六千字符折约四千 token 输出已接近 STANDARD 档时限
     */
    private static final double SUMMARY_MAX_RATIO = 0.1D;
    private static final int SUMMARY_MAX_FLOOR_CHARS = 1500;
    private static final int SUMMARY_MAX_CEIL_CHARS = 6000;

    /**
     * 记忆总开关
     */
    private boolean enabled = true;

    /**
     * 会话上下文工程预算（字符），换模型只需要动这一个数
     * 不是模型标称窗口：人设、工具 schema、输出预留不走这份账，填值时先扣掉固定开销
     * 下限 8000：再小保留段装不下摘要（0.2 × 8000 > 摘要下限 1500）
     */
    @Min(8000)
    private int contextWindowChars = 1_200_000;

    /**
     * 关掉即只留裁剪层，摘要模型不可用时的运维出口
     */
    private boolean summaryEnabled = true;

    /**
     * 允许清理的工具白名单；默认值须可变，绑定器直接 clear + addAll
     */
    private List<String> evictableTools = new ArrayList<>(List.of("search_knowledge"));

    /**
     * 叫 resolve 不叫 get：绑定器会把 getXxx 当成可配置项
     */
    public int resolveTrimTriggerChars() {
        return (int) (contextWindowChars * TRIM_TRIGGER_RATIO);
    }

    public int resolveCompactTriggerChars() {
        return (int) (contextWindowChars * COMPACT_TRIGGER_RATIO);
    }

    public int resolveKeepRecentChars() {
        return (int) (contextWindowChars * KEEP_RECENT_RATIO);
    }

    public int resolveKeepRecentCycles() {
        return KEEP_RECENT_CYCLES;
    }

    public double resolveClearAtLeastRatio() {
        return CLEAR_AT_LEAST_RATIO;
    }

    /**
     * 夹在上下限之间返回
     */
    public int resolveSummaryMaxChars() {
        int derived = (int) (contextWindowChars * SUMMARY_MAX_RATIO);
        return Math.min(Math.max(derived, SUMMARY_MAX_FLOOR_CHARS), SUMMARY_MAX_CEIL_CHARS);
    }
}
