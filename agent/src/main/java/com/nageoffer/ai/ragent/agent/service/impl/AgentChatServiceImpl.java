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

package com.nageoffer.ai.ragent.agent.service.impl;

import cn.hutool.core.util.IdUtil;
import cn.hutool.core.util.StrUtil;
import com.nageoffer.ai.ragent.agent.config.ConditionalOnAgentEngine;
import com.nageoffer.ai.ragent.agent.config.ReActAgentProvider;
import com.nageoffer.ai.ragent.agent.config.ReActAgentProvider.ActiveAgent;
import com.nageoffer.ai.ragent.agent.dto.AgentMetaPayload;
import com.nageoffer.ai.ragent.agent.enums.AgentSSEEventType;
import com.nageoffer.ai.ragent.agent.service.AgentChatService;
import com.nageoffer.ai.ragent.agent.service.AgentConversationService;
import com.nageoffer.ai.ragent.agent.service.handler.AgentRunGate;
import com.nageoffer.ai.ragent.agent.service.handler.AgentRunHandle;
import com.nageoffer.ai.ragent.agent.service.handler.AgentStreamEventBridge;
import com.nageoffer.ai.ragent.framework.context.UserContext;
import com.nageoffer.ai.ragent.framework.web.SseEmitterSender;
import com.nageoffer.ai.ragent.framework.web.StreamTaskManager;
import io.agentscope.core.ReActAgent;
import io.agentscope.core.agent.RuntimeContext;
import io.agentscope.core.event.AgentEvent;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;
import reactor.core.Disposable;
import reactor.core.publisher.Flux;

import java.util.concurrent.atomic.AtomicBoolean;

/**
 * Agent 流式对话编排：会话落库 -> ReAct 事件流 -> SSE 桥 -> 取消接线
 * 会话 ID 即 AgentScope 的 sessionId，多轮记忆由状态存储按次加载
 */
@Slf4j
@Service
@ConditionalOnAgentEngine
@RequiredArgsConstructor
public class AgentChatServiceImpl implements AgentChatService {

    private final ReActAgentProvider agentProvider;
    private final AgentConversationService conversationService;
    private final StreamTaskManager taskManager;
    private final AgentRunGate runGate;

    @Override
    public void streamChat(String question, String conversationId, SseEmitter emitter) {
        String userId = UserContext.getUserId();
        String actualConversationId = StrUtil.isBlank(conversationId)
                ? IdUtil.getSnowflakeNextIdStr()
                : conversationId;
        String taskId = IdUtil.getSnowflakeNextIdStr();

        // 闸门先于一切副作用：被拒的请求不该留下 META 事件、会话行与任务登记
        Runnable releaseGate = runGate.acquire(userId, taskId, actualConversationId);
        boolean started = false;
        try {
            startRun(question, userId, actualConversationId, taskId, emitter, releaseGate);
            started = true;
        } finally {
            // 启动期还没有收尾路可挂，就地归还闸门并撤销任务登记，否则该用户被挡到 TTL 过期
            // 用 finally 而非 catch RuntimeException：启动段抛 Error 同样会把闸门锁死半小时
            if (!started) {
                releaseGate.run();
                taskManager.unregister(taskId);
            }
        }
    }

    private void startRun(String question, String userId, String conversationId, String taskId,
                          SseEmitter emitter, Runnable releaseGate) {
        SseEmitterSender sender = new SseEmitterSender(emitter);
        sender.sendEvent(AgentSSEEventType.META.value(), new AgentMetaPayload(conversationId, taskId));

        String title = conversationService.touchConversation(conversationId, userId, question);
        String questionMessageId = conversationService.addUserMessage(conversationId, userId, question);

        AgentRunHandle runHandle = new AgentRunHandle(taskId, sender, taskManager);
        runHandle.onRelease(releaseGate);
        // 记忆常驻内存是确定性泄漏，流一结束就驱逐：三条收尾路都会执行，换来内存上界
        // 状态已在框架侧随本轮落库（正常完成与打断各自 save 后才发终答），下一轮从 PG 读回，代价是一次反序列化
        runHandle.onRelease(() -> agentProvider.evictStateCache(userId, conversationId));
        bindEmitterLifecycle(emitter, runHandle, taskId);
        // 实例与目录快照成对取出：事件展示名与 Toolkit 出自同一次解析
        ActiveAgent activeAgent = agentProvider.getAgent();
        AgentStreamEventBridge bridge = new AgentStreamEventBridge(AgentStreamEventBridge.Params.builder()
                .runHandle(runHandle)
                .conversationService(conversationService)
                .catalog(activeAgent.catalog())
                .conversationId(conversationId)
                .userId(userId)
                .title(title)
                .replyToMessageId(questionMessageId)
                .build());
        taskManager.register(taskId, userId, bridge::finishCancelledStream);

        @SuppressWarnings("resource")
        ReActAgent agent = activeAgent.agent();
        Flux<AgentEvent> events = agent.streamEvents(question, RuntimeContext.builder()
                .userId(userId)
                .sessionId(conversationId)
                .build());
        Disposable disposable = events.subscribe(bridge::onEvent, bridge::onError, bridge::onComplete);

        // 取消动作先断流再置中断旗标，收尾（落库 + cancel/done 事件）由 finalizer 完成
        runHandle.bindStream(disposable, () -> agent.interrupt(userId, conversationId));
        taskManager.bindHandle(taskId, runHandle::interruptUpstream);
    }

    /**
     * 把 SSE 通道的三条终止信号接到取消协议上
     * 不接则关页、断网、超时之后事件被静默丢弃，而 ReAct 循环照常跑满迭代上限
     */
    private void bindEmitterLifecycle(SseEmitter emitter, AgentRunHandle runHandle, String taskId) {
        AtomicBoolean recycled = new AtomicBoolean(false);
        Runnable recycleUpstream = () -> {
            // 已结算说明收尾路跑过了，再取消只会往 Redis 留一条 30 分钟的死标记
            if (!runHandle.isSettled() && recycled.compareAndSet(false, true)) {
                taskManager.cancel(taskId);
            }
        };
        emitter.onTimeout(recycleUpstream);
        emitter.onError(e -> recycleUpstream.run());
        // 客户端关页时写失败走的是 completeWithError，容器既不报超时也不报错，只有 completion 兜得住
        emitter.onCompletion(recycleUpstream);
    }

    @Override
    public void stopTask(String taskId) {
        taskManager.cancelByUser(taskId);
    }
}
