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

package com.nageoffer.ai.ragent.agent.service.handler;

import cn.hutool.core.util.IdUtil;
import cn.hutool.core.util.StrUtil;
import cn.hutool.json.JSONUtil;
import com.nageoffer.ai.ragent.agent.config.ConditionalOnAgentEngine;
import com.nageoffer.ai.ragent.framework.context.UserContext;
import com.nageoffer.ai.ragent.rag.config.RagTraceProperties;
import com.nageoffer.ai.ragent.rag.dao.entity.RagTraceRunDO;
import com.nageoffer.ai.ragent.rag.service.RagTraceRecordService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import java.util.Date;

/**
 * Agent 链路的链路追踪记录
 * <p>
 * workflow 引擎由 {@code StreamChatTraceRunner} 包着上报，agent 引擎走的是
 * ReAct 事件流、生命周期挂在自己的 {@link AgentRunHandle} 上，那套包装器接不上，
 * 故在此单独记一条 run。只记 run 粒度（起止、结局、耗时）——
 * 仪表盘的链路稳定性、慢响应率、P95 延迟都由 run 算出，节点级埋点不是必需。
 * <p>
 * 不记 run 的后果是仪表盘在 agent 模式下永远读不到新数据：它按 {@code t_rag_trace_run}
 * 统计，而这张表此前只有 workflow 链路在写
 */
@Slf4j
@Component
@ConditionalOnAgentEngine
@RequiredArgsConstructor
public class AgentChatTraceRecorder {

    private static final String TRACE_NAME = "agent-stream-chat";
    private static final String ENTRY_METHOD = "AgentChatService#streamChat";
    private static final String STATUS_RUNNING = "RUNNING";
    private static final String STATUS_SUCCESS = "SUCCESS";
    private static final String STATUS_ERROR = "ERROR";

    /**
     * 用户主动打断或连接断开。单列一个状态而不是并进 ERROR：
     * 打断是用户行为，算进错误率会让链路稳定性凭空变差
     */
    private static final String STATUS_CANCELLED = "CANCELLED";

    private final RagTraceRecordService traceRecordService;
    private final RagTraceProperties traceProperties;

    /**
     * 开一条追踪，返回收尾凭据；未开启追踪时返回 {@link TraceHandle#NOOP}
     */
    public TraceHandle begin(String question, String conversationId, String taskId) {
        if (!traceProperties.isEnabled()) {
            return TraceHandle.NOOP;
        }
        String traceId = IdUtil.getSnowflakeNextIdStr();
        long startMillis = System.currentTimeMillis();
        try {
            traceRecordService.startRun(RagTraceRunDO.builder()
                    .traceId(traceId)
                    .traceName(TRACE_NAME)
                    .entryMethod(ENTRY_METHOD)
                    .conversationId(conversationId)
                    .taskId(taskId)
                    .userId(UserContext.getUserId())
                    .status(STATUS_RUNNING)
                    .startTime(new Date(startMillis))
                    .extraData(JSONUtil.createObj()
                            .set("engine", "agent")
                            .set("question", question)
                            .toString())
                    .build());
        } catch (Exception e) {
            // 追踪是旁路：写不进去也不该拦住用户这一轮对话
            log.warn("Agent 链路追踪开启失败，本轮不记录, conversationId: {}", conversationId, e);
            return TraceHandle.NOOP;
        }
        return new TraceHandle(traceId, startMillis);
    }

    /**
     * 收尾。异常一律咽下——追踪失败不能反过来影响已经答完的对话
     */
    public void finish(TraceHandle handle, AgentRunOutcome outcome, String errorMessage) {
        if (handle == null || handle == TraceHandle.NOOP) {
            return;
        }
        try {
            long durationMs = System.currentTimeMillis() - handle.startMillis();
            traceRecordService.finishRun(handle.traceId(), statusOf(outcome),
                    StrUtil.maxLength(errorMessage, traceProperties.getMaxErrorLength()),
                    new Date(), durationMs);
        } catch (Exception e) {
            log.warn("Agent 链路追踪收尾失败, traceId: {}", handle.traceId(), e);
        }
    }

    private String statusOf(AgentRunOutcome outcome) {
        if (outcome == null) {
            return STATUS_ERROR;
        }
        return switch (outcome) {
            case COMPLETED -> STATUS_SUCCESS;
            case CANCELLED -> STATUS_CANCELLED;
            // RUNNING 走到收尾说明没经过任何结算路径，按异常记，好过静默丢一条
            case FAILED, RUNNING -> STATUS_ERROR;
        };
    }

    /**
     * 收尾凭据，只带 traceId 与起始时刻
     */
    public record TraceHandle(String traceId, long startMillis) {

        public static final TraceHandle NOOP = new TraceHandle(null, 0L);
    }
}
