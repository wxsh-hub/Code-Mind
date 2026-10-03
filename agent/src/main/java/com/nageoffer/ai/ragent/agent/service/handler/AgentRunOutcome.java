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

/**
 * Agent 单轮运行的最终结局
 * <p>
 * 释放钩子的签名是 {@code Runnable}，拿不到结局；而落链路追踪需要区分成功、失败与用户打断。
 * 结局由 {@link AgentRunHandle} 在结算时写定，钩子读它即可
 */
public enum AgentRunOutcome {

    /**
     * 还在跑
     */
    RUNNING,

    /**
     * 正常答完
     */
    COMPLETED,

    /**
     * 用户主动打断或连接断开
     */
    CANCELLED,

    /**
     * 中途抛错
     */
    FAILED
}
