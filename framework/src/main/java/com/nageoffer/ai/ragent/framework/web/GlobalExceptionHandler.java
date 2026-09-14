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

import cn.dev33.satoken.exception.NotLoginException;
import cn.dev33.satoken.exception.NotRoleException;
import cn.hutool.core.collection.CollectionUtil;
import cn.hutool.core.util.StrUtil;
import com.nageoffer.ai.ragent.framework.convention.Result;
import com.nageoffer.ai.ragent.framework.errorcode.BaseErrorCode;
import com.nageoffer.ai.ragent.framework.exception.AbstractException;
import jakarta.servlet.ServletOutputStream;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.SneakyThrows;
import lombok.extern.slf4j.Slf4j;
import org.apache.tomcat.util.http.fileupload.impl.FileSizeLimitExceededException;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.MessageSourceResolvable;
import org.springframework.validation.BindingResult;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.context.request.async.AsyncRequestNotUsableException;
import org.springframework.web.method.annotation.HandlerMethodValidationException;
import org.springframework.web.multipart.MaxUploadSizeExceededException;

import java.nio.charset.StandardCharsets;
import java.util.Optional;

/**
 * 全局异常处理器
 * 拦截指定异常并通过优雅构建方式返回前端信息
 */
@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler {

    @Value("${spring.servlet.multipart.max-file-size:50MB}")
    private String maxFileSize;

    @Value("${spring.servlet.multipart.max-request-size:100MB}")
    private String maxRequestSize;

    /**
     * 拦截参数验证异常
     */
    @SneakyThrows
    @ExceptionHandler(value = MethodArgumentNotValidException.class)
    public Result<Void> validExceptionHandler(HttpServletRequest request, MethodArgumentNotValidException ex) {
        BindingResult bindingResult = ex.getBindingResult();
        FieldError firstFieldError = CollectionUtil.getFirst(bindingResult.getFieldErrors());
        String exceptionStr = Optional.ofNullable(firstFieldError)
                .map(FieldError::getDefaultMessage)
                .orElse(StrUtil.EMPTY);
        log.error("[{}] {} [ex] {}", request.getMethod(), getUrl(request), exceptionStr);
        return Results.failure(BaseErrorCode.CLIENT_ERROR.code(), exceptionStr);
    }

    /**
     * 拦截方法参数校验异常
     * 不接住会落到兜底分支，前端只能看到一句「系统执行出错」
     */
    @ExceptionHandler(value = HandlerMethodValidationException.class)
    public Result<Void> methodValidationExceptionHandler(HttpServletRequest request,
                                                        HandlerMethodValidationException ex) {
        String message = ex.getParameterValidationResults().stream()
                .flatMap(result -> result.getResolvableErrors().stream())
                .map(MessageSourceResolvable::getDefaultMessage)
                .filter(StrUtil::isNotBlank)
                .findFirst()
                .orElse("请求参数不合法");
        log.warn("[{}] {} [ex] {}", request.getMethod(), getUrl(request), message);
        return Results.failure(BaseErrorCode.CLIENT_ERROR.code(), message);
    }

    /**
     * 拦截应用内抛出的异常
     */
    @ExceptionHandler(value = {AbstractException.class})
    public Result<Void> abstractException(HttpServletRequest request, AbstractException ex) {
        if (ex.getCause() != null) {
            log.error("[{}] {} [ex] {}", request.getMethod(), request.getRequestURL().toString(), ex, ex.getCause());
            return Results.failure(ex);
        }
        StringBuilder stackTraceBuilder = new StringBuilder();
        stackTraceBuilder.append(ex.getClass().getName()).append(": ").append(ex.getErrorMessage()).append("\n");
        StackTraceElement[] stackTrace = ex.getStackTrace();
        for (int i = 0; i < Math.min(5, stackTrace.length); i++) {
            stackTraceBuilder.append("\tat ").append(stackTrace[i]).append("\n");
        }
        log.error("[{}] {} [ex] {} \n\n{}", request.getMethod(), request.getRequestURL().toString(), ex, stackTraceBuilder);
        return Results.failure(ex);
    }

    /**
     * 拦截未登录异常
     */
    @ExceptionHandler(value = NotLoginException.class)
    public Object notLoginException(HttpServletRequest request, NotLoginException ex,
                                     HttpServletResponse response) {
        log.warn("[{}] {} [auth] not-login: {}", request.getMethod(), getUrl(request), ex.getMessage());
        if (isEventStream(request, response)) {
            return writeSseError(response, 401, "未登录或登录已过期");
        }
        return Results.failure(BaseErrorCode.CLIENT_ERROR.code(), "未登录或登录已过期");
    }

    /**
     * 拦截无角色权限异常
     */
    @ExceptionHandler(value = NotRoleException.class)
    public Result<Void> notRoleException(HttpServletRequest request, NotRoleException ex) {
        log.warn("[{}] {} [auth] no-role: {}", request.getMethod(), getUrl(request), ex.getMessage());
        return Results.failure(BaseErrorCode.CLIENT_ERROR.code(), "权限不足");
    }

    /**
     * 拦截文件上传大小超限异常
     */
    @ExceptionHandler(value = MaxUploadSizeExceededException.class)
    public Result<Void> maxUploadSizeExceededException(HttpServletRequest request, MaxUploadSizeExceededException ex) {
        log.warn("[{}] {} [upload] 文件上传大小超限: {}", request.getMethod(), getUrl(request), ex.getMessage());
        String message;
        if (ex.getCause() instanceof IllegalStateException
                && ex.getCause().getCause() instanceof FileSizeLimitExceededException) {
            message = "上传文件大小超过限制，单个文件最大允许 " + maxFileSize;
        } else {
            message = "上传请求大小超过限制，单次请求最大允许 " + maxRequestSize;
        }
        return Results.failure(BaseErrorCode.CLIENT_ERROR.code(), message);
    }

    /**
     * 拦截未捕获异常
     */
    @ExceptionHandler(value = Throwable.class)
    public Object defaultErrorHandler(HttpServletRequest request, Throwable throwable,
                                       HttpServletResponse response) {
        log.error("[{}] {} ", request.getMethod(), getUrl(request), throwable);

        // 提取更有用的错误信息
        String message = extractFriendlyMessage(throwable);

        if (isEventStream(request, response)) {
            // SSE 流已经开始推送（meta 事件先于模型调用发出），此处必须以 SSE 事件收尾：
            // 回退成 JSON 会撞上已锁定的 text/event-stream Content-Type，触发
            // HttpMessageNotWritableException，错误信息反而送不到前端
            return writeSseError(response, 500, message);
        }

        return Results.failure(BaseErrorCode.SERVICE_ERROR.code(), message);
    }

    /**
     * 客户端断连：SSE 流在推送途中对端已关闭，响应不可再用
     * <p>
     * 单独拦截而非落进 {@link #defaultErrorHandler}，是因为这属于正常的用户行为
     * （关页面、切路由），不是服务端故障，记 error 会污染日志、也不该尝试写入任何响应
     */
    @ExceptionHandler(value = AsyncRequestNotUsableException.class)
    public void clientDisconnected(HttpServletRequest request, AsyncRequestNotUsableException ex) {
        log.debug("[{}] {} 客户端已断开，放弃本次响应: {}",
                request.getMethod(), getUrl(request), ex.getMessage());
    }

    /**
     * 判定本次响应是否应按 SSE 事件格式收尾
     * <p>
     * 以响应侧 Content-Type 为主：SSE 接口的 {@code produces} 会让容器在流开始推送时就锁定该类型，
     * 它比请求头的 Accept 更能反映「此刻正在以什么协议说话」。仅当响应尚未定型时，
     * 才回退看 Accept（例如未登录在控制器之前就被拦下，此时响应还没建立）
     */
    private boolean isEventStream(HttpServletRequest request, HttpServletResponse response) {
        String contentType = response.getContentType();
        if (contentType != null && contentType.contains("text/event-stream")) {
            return true;
        }
        if (response.isCommitted()) {
            // 响应已提交却拿不到 SSE 类型，说明在此之前已有内容写出，无法再改协议
            return false;
        }
        String accept = request.getHeader("Accept");
        return accept != null && accept.contains("text/event-stream");
    }

    /**
     * 以 SSE 事件格式写出错误并结束响应
     * <p>
     * 走 OutputStream 而非 Writer：SseEmitter 全程用 {@code getOutputStream()} 推送，
     * 二者互斥，此处再用 {@code getWriter()} 会直接抛 "getOutputStream() has already been called"
     *
     * @return 恒为 null，供 {@code @ExceptionHandler} 直接返回，表示响应已由本方法接管
     */
    private Object writeSseError(HttpServletResponse response, int status, String message) {
        if (response.isCommitted()) {
            // 响应头已发出，状态码改不动了，但事件体仍可追加，前端至少能拿到错误
            log.warn("[SSE] 响应已提交，仅追加 error 事件，status={} 不再生效", status);
        } else {
            response.setContentType("text/event-stream;charset=UTF-8");
            response.setStatus(status);
        }
        try {
            String payload = "{\"error\": \"" + escapeJson(message) + "\"}";
            byte[] frame = ("event: error\ndata: " + payload + "\n\n")
                    .getBytes(StandardCharsets.UTF_8);
            ServletOutputStream out = response.getOutputStream();
            out.write(frame);
            out.flush();
        } catch (Exception writeFailure) {
            log.warn("[SSE] error 事件写出失败，前端将只能看到流中断: {}", writeFailure.getMessage());
        }
        return null;
    }

    /**
     * 转义 JSON 字符串值：反斜杠与双引号必须转义，换行会让 data 行断成两行、破开 SSE 帧
     */
    private String escapeJson(String value) {
        if (value == null) {
            return "";
        }
        return value.replace("\\", "\\\\")
                .replace("\"", "\\\"")
                .replace("\r", " ")
                .replace("\n", " ");
    }

    /**
     * 提取友好的错误信息
     */
    private String extractFriendlyMessage(Throwable throwable) {
        if (throwable == null) {
            return "系统执行出错";
        }

        // 获取根本原因
        Throwable cause = throwable;
        while (cause.getCause() != null && cause.getCause() != cause) {
            cause = cause.getCause();
        }

        String className = cause.getClass().getSimpleName();
        String message = cause.getMessage();

        // 模型侧异常优先：其类名来自 AgentScope / OpenAI SDK，命名五花八门，
        // 且原始 message 会带上供应商名、HTTP 状态与响应体，直接透给用户既难懂又暴露内部细节
        String modelFriendly = extractModelFriendlyMessage(throwable, cause);
        if (modelFriendly != null) {
            return modelFriendly;
        }

        // 根据异常类型返回友好信息
        if (className.contains("NullPointer")) {
            return "数据处理异常，请检查输入参数";
        } else if (className.contains("IndexOutOfBounds")) {
            return "数据索引越界，请检查请求参数";
        } else if (className.contains("IO") || className.contains("Connection")) {
            return "网络连接异常，请稍后重试";
        } else if (className.contains("Timeout")) {
            return "请求超时，请稍后重试";
        } else if (className.contains("SQL") || className.contains("DataAccess")) {
            return "数据访问异常，请联系管理员";
        } else if (className.contains("Permission") || className.contains("Access")) {
            return "权限不足，请联系管理员";
        } else if (className.contains("Validation") || className.contains("IllegalArgument")) {
            return "参数验证失败: " + (message != null ? message : "请检查输入");
        }

        // 如果有具体消息，返回它
        if (message != null && !message.isEmpty() && message.length() < 200) {
            return message;
        }

        return "系统执行出错: " + className;
    }

    /**
     * 识别模型调用失败并给出面向用户的提示，认不出则返回 null 交给通用分支
     * <p>
     * 沿异常链自上而下找第一个匹配项，而非只看根因：AgentScope 会把供应商异常
     * 包进自己的类型，根因有时是 IOException 这类泛化异常，靠它判不出是鉴权还是限流。
     * 真正的判据是链上任何一层类名带 Authentication/Credits/RateLimit 这类语义
     * <p>
     * 只回固定文案，不透传原始 message：后者含供应商域名、HTTP 状态码与响应体，
     * 既让用户看不懂，也把内部集成细节暴露给了外部
     */
    private String extractModelFriendlyMessage(Throwable throwable, Throwable rootCause) {
        for (Throwable current = throwable; current != null; current = current.getCause()) {
            String name = current.getClass().getSimpleName();
            if (name.contains("Authentication")
                    || name.contains("Unauthorized")
                    || name.contains("ApiKey")
                    || name.contains("PermissionDenied")) {
                return "AI 服务鉴权失败，请联系管理员检查模型 API Key 配置";
            }
            if (name.contains("InsufficientBalance") || name.contains("Credits")) {
                return "AI 服务额度不足，请联系管理员充值";
            }
            if (name.contains("RateLimit") || name.contains("Throttl")) {
                return "AI 服务请求过于频繁，请稍后重试";
            }
            if (name.contains("Timeout")) {
                return "AI 服务响应超时，请稍后重试";
            }
            if (current == rootCause) {
                break;
            }
        }

        // 类名认不出，再用原始 message 嗅探供应商返回的错误码（如 SiliconFlow 的 30014）
        String rootMessage = rootCause == null ? null : rootCause.getMessage();
        if (rootMessage != null) {
            if (rootMessage.contains("Token is invalid") || rootMessage.contains("invalid_api_key")) {
                return "AI 服务鉴权失败，请联系管理员检查模型 API Key 配置";
            }
            if (rootMessage.contains("insufficient") && rootMessage.contains("balance")) {
                return "AI 服务额度不足，请联系管理员充值";
            }
        }
        return null;
    }

    private String getUrl(HttpServletRequest request) {
        if (StrUtil.isBlank(request.getQueryString())) {
            return request.getRequestURL().toString();
        }
        return request.getRequestURL().toString() + "?" + request.getQueryString();
    }
}
