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

package com.nageoffer.ai.ragent.framework.security;

import lombok.extern.slf4j.Slf4j;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * 敏感数据过滤器
 * <p>
 * 在文档入库阶段对文本做正则匹配，将密钥、令牌、PII 等替换为占位符。
 * 设计原则：宁可漏打不可误杀，正则取高置信度子集。
 */
@Slf4j
public final class SensitiveDataFilter {

    private SensitiveDataFilter() {
    }

    /**
     * 所有规则按顺序执行；Map 保序，靠前的规则优先匹配
     */
    private static final Map<Pattern, String> RULES = new LinkedHashMap<>();

    static {
        // ---- 密钥 / Token ----
        // GitHub Personal Access Token (ghp_xxx / github_pat_xxx)
        rule("ghp_[0-9a-zA-Z]{36}", "<MASKED_GITHUB_TOKEN>");
        rule("github_pat_[0-9a-zA-Z_]{82}", "<MASKED_GITHUB_TOKEN>");
        // GitHub App / OAuth / Fine-grained
        rule("(?:ghu|ghs|gho)_[0-9a-zA-Z]{36}", "<MASKED_GITHUB_TOKEN>");
        // AWS Access Key
        rule("(?:AKIA|ASIA|ABIA|ACCA)[A-Z0-9]{16}", "<MASKED_AWS_KEY>");
        // Azure AD Client Secret (含 ~ 的典型模式)
        rule("[a-zA-Z0-9_~.]{3}\\dQ~[a-zA-Z0-9_~.-]{31,34}", "<MASKED_AZURE_SECRET>");
        // GCP API Key
        rule("AIza[\\w-]{35}", "<MASKED_GCP_KEY>");
        // 通用 sk- 开头的 API Key (OpenAI / Anthropic 等)
        rule("sk-[a-zA-Z0-9_-]{20,}", "<MASKED_API_KEY>");
        // Bearer Token / JWT
        rule("Bearer\\s+[a-zA-Z0-9._\\-]{20,}", "<MASKED_BEARER>");
        rule("eyJ[a-zA-Z0-9_-]{10,}\\.[a-zA-Z0-9._-]{10,}", "<MASKED_JWT>");
        // Slack / Teams Webhook
        rule("xapp-\\d-[A-Z0-9]+-\\d+-[a-z0-9]+", "<MASKED_SLACK_TOKEN>");
        rule("https://[a-z0-9]+\\.webhook\\.office\\.com/webhookb2/[a-zA-Z0-9@_./-]+", "<MASKED_WEBHOOK>");

        // ---- 连接串中的密码 ----
        // mysql://user:password@host  /  postgresql://...  /  mongodb://...
        rule("(\\w+://[^:]+:)([^@]{3,})(@[^\\s]+)", "$1<MASKED_PWD>$3");
        // password=xxx / passwd=xxx / pwd=xxx (行内)
        rule("(?i)(password|passwd|pwd)\\s*[=:]\\s*\\S+", "$1=<MASKED_PWD>");

        // ---- PII ----
        // 中国大陆手机号 (1[3-9]X XXXX XXXX) — 前后不能有数字，避免匹配长数字串
        rule("(?<!\\d)(1[3-9]\\d{9})(?!\\d)", "<MASKED_PHONE>");
        // 中国大陆身份证号 (18 位，带日期校验)
        rule("(?<!\\d)(\\d{6}(?:19|20)\\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\\d|3[01])\\d{3}[\\dXx])(?!\\d)", "<MASKED_ID_CARD>");
        // 银行卡号：仅匹配已知银行 BIN 开头 (622/621/620 等银联卡)，16-19 位
        // 避免误杀订单号、时间戳等纯数字
        rule("(?<!\\d)(6(?:2[0-9]{2}|[01]\\d{2})\\d{12,16})(?!\\d)", "<MASKED_CARD>");
        // 邮箱 — 前后不能是路径分隔符，避免匹配文件路径中的 @
        rule("(?<![/\\\\\\w])([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,})(?![/\\\\\\w])", "<MASKED_EMAIL>");
    }

    private static void rule(String regex, String replacement) {
        RULES.put(Pattern.compile(regex), replacement);
    }

    /**
     * 对输入文本执行全部规则，返回过滤后的文本
     *
     * @param text 原始文本，可为 null
     * @return 过滤后的文本，null 输入返回 null
     */
    public static String filter(String text) {
        if (text == null || text.isEmpty()) {
            return text;
        }
        String result = text;
        for (Map.Entry<Pattern, String> entry : RULES.entrySet()) {
            result = entry.getKey().matcher(result).replaceAll(entry.getValue());
        }
        if (!result.equals(text)) {
            log.info("敏感数据过滤已命中，原始长度={} 过滤后长度={}", text.length(), result.length());
        }
        return result;
    }

    /**
     * 检测文本中是否包含敏感数据（不做替换，仅检测）
     *
     * @param text 待检测文本
     * @return true 表示命中至少一条规则
     */
    public static boolean containsSensitiveData(String text) {
        if (text == null || text.isEmpty()) {
            return false;
        }
        for (Pattern pattern : RULES.keySet()) {
            if (pattern.matcher(text).find()) {
                return true;
            }
        }
        return false;
    }
}
