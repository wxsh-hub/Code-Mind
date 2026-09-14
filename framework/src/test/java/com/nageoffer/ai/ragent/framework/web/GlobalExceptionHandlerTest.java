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

package com.nageoffer.ai.ragent.framework.web;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.test.util.ReflectionTestUtils;

import java.sql.SQLException;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * 错误信息面向用户的措辞：既要说清处置方向，也不能把供应商细节透出去
 * <p>
 * 判据是异常**类名**而非 message，故此处按真实异常链的形态构造：
 * 供应商异常（类名带语义）被 AgentScope 包装后位于链中，不一定正好是根因
 */
class GlobalExceptionHandlerTest {

    private final GlobalExceptionHandler handler = new GlobalExceptionHandler();

    private String friendly(Throwable throwable) {
        return (String) ReflectionTestUtils.invokeMethod(handler, "extractFriendlyMessage", throwable);
    }

    @Test
    @DisplayName("鉴权失败：沿异常链找到带语义的类名并给出中文提示")
    void authenticationFailureIsTranslated() {
        // 复刻真实形态：供应商异常被包在内层，message 里带着状态码与供应商原文
        Throwable supplierFailure = new AuthenticationException(
                "HTTP transport error during streaming: HTTP request failed with status 401 "
                        + "| {\"code\":30014,\"message\":\"Token is invalid.\"}");
        Throwable wrapped = new IllegalStateException("provider rejected the request", supplierFailure);
        Throwable top = new RuntimeException("stream failed", wrapped);

        String message = friendly(top);

        assertThat(message).contains("鉴权失败");
        assertThat(message).doesNotContain("401");
        assertThat(message).doesNotContain("Token is invalid");
        assertThat(message).doesNotContain("30014");
    }

    @Test
    @DisplayName("鉴权失败：类名认不出时按供应商错误码嗅探")
    void authenticationSniffedFromProviderMessage() {
        Throwable throwable = new RuntimeException(
                "HTTP request failed with status 401 | {\"code\":30014,\"message\":\"Token is invalid.\"}");

        String message = friendly(throwable);

        assertThat(message).contains("鉴权失败");
        assertThat(message).doesNotContain("30014");
    }

    @Test
    @DisplayName("额度不足与限流各有独立文案")
    void balanceAndRateLimitHaveDistinctMessages() {
        assertThat(friendly(new InsufficientBalanceException("quota exhausted"))).contains("额度不足");
        assertThat(friendly(new RateLimitException("too many requests"))).contains("请求过于频繁");
    }

    @Test
    @DisplayName("模型提示只回固定文案，不泄漏供应商域名与响应体")
    void providerDetailsAreNeverLeaked() {
        Throwable throwable = new RuntimeException(
                "call failed",
                new IllegalStateException("openai transport",
                        new AuthenticationException(
                                "https://api.siliconflow.cn/v1/chat/completions "
                                        + "| Status: 401 | Response body: {\"code\":30014}")));

        String message = friendly(throwable);

        assertThat(message)
                .doesNotContain("siliconflow")
                .doesNotContain("api.siliconflow.cn")
                .doesNotContain("Response body")
                .doesNotContain("401");
    }

    @Test
    @DisplayName("非模型类异常仍走通用分支，不受此次改动影响")
    void nonModelExceptionsKeepGenericMapping() {
        assertThat(friendly(new NullPointerException())).contains("数据处理异常");
        assertThat(friendly(new SQLException("bad sql"))).contains("数据访问异常");
        assertThat(friendly(new IllegalArgumentException("参数不合法"))).contains("参数验证失败");
    }

    @Test
    @DisplayName("无 cause 的单层异常也能正确判定")
    void singleLevelExceptionIsHandled() {
        assertThat(friendly(new AuthenticationException("Token is invalid"))).contains("鉴权失败");
    }

    @Test
    @DisplayName("null 异常返回兜底文案")
    void nullThrowableReturnsFallback() {
        assertThat(friendly(null)).isEqualTo("系统执行出错");
    }

    /**
     * 以下三个占位类型仅用于让**类名**带上语义，对应生产环境里 AgentScope 与
     * OpenAI SDK 各自的异常类型；此处不复制其实现，只复刻命名特征
     */
    private static final class AuthenticationException extends RuntimeException {
        AuthenticationException(String message) {
            super(message);
        }
    }

    private static final class InsufficientBalanceException extends RuntimeException {
        InsufficientBalanceException(String message) {
            super(message);
        }
    }

    private static final class RateLimitException extends RuntimeException {
        RateLimitException(String message) {
            super(message);
        }
    }
}
