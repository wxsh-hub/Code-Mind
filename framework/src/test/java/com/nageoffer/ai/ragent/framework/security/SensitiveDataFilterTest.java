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

import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;

import static org.junit.jupiter.api.Assertions.*;

class SensitiveDataFilterTest {

    // ========== 密钥 / Token ==========

    @Test
    void ghp_token被替换() {
        // ghp_ 后面需要 36 个字符
        String input = "my token is ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef1234 ok";
        String result = SensitiveDataFilter.filter(input);
        assertFalse(result.contains("ghp_"), "GitHub token 应被替换");
        assertTrue(result.contains("<MASKED_GITHUB_TOKEN>"));
    }

    @Test
    void aws_key被替换() {
        String input = "access key: AKIAIOSFODNN7EXAMPLE";
        String result = SensitiveDataFilter.filter(input);
        assertFalse(result.contains("AKIAIOSFODNN7EXAMPLE"), "AWS key 应被替换");
        assertTrue(result.contains("<MASKED_AWS_KEY>"));
    }

    @Test
    void openai_sk_key被替换() {
        String input = "api_key=sk-abc123def456ghi789jkl012mno345";
        String result = SensitiveDataFilter.filter(input);
        assertFalse(result.contains("sk-abc123"), "sk- API key 应被替换");
        assertTrue(result.contains("<MASKED_API_KEY>"));
    }

    @Test
    void jwt被替换() {
        String input = "token: eyJhbGciOiJIUzI1NiJ9.eyJ0ZXN0IjoxfQ.abc123signature";
        String result = SensitiveDataFilter.filter(input);
        assertFalse(result.contains("eyJhbGciOi"), "JWT 应被替换");
        assertTrue(result.contains("<MASKED_JWT>"));
    }

    @Test
    void bearer_token被替换() {
        String input = "Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8u";
        String result = SensitiveDataFilter.filter(input);
        assertFalse(result.contains("Bearer eyJ"), "Bearer token 应被替换");
        assertTrue(result.contains("<MASKED_BEARER>"));
    }

    // ========== 连接串密码 ==========

    @Test
    void mysql连接串密码被替换() {
        String input = "mysql://root:MyS3cretP@ssw0rd!@db.internal.com:3306/production";
        String result = SensitiveDataFilter.filter(input);
        assertFalse(result.contains("MyS3cretP@ssw0rd!"), "连接串密码应被替换");
        assertTrue(result.contains("<MASKED_PWD>"));
    }

    @Test
    void 含at符号的密码被完整替换() {
        // 密码含 @ 时，贪婪匹配须回溯到最后一个 @，否则只脱敏前半段
        String input = "mysql://root:MyS3cretP@ssw0rd!@db.internal.com:3306/prod";
        String result = SensitiveDataFilter.filter(input);
        assertFalse(result.contains("ssw0rd!"), "密码后半段不得残留");
        assertFalse(result.contains("MyS3cretP"), "密码前半段不得残留");
        assertFalse(result.contains("P@ssw0rd"), "密码中段不得残留");
        assertTrue(result.contains("<MASKED_PWD>"), "应替换为占位符");
        assertTrue(result.contains("@db.internal.com:3306/prod"), "主机与库名须保留");
    }

    @Test
    void 多at符号的连接串被完整替换() {
        String input = "postgresql://admin:a@b@c@host:5432/mydb";
        String result = SensitiveDataFilter.filter(input);
        assertFalse(result.contains("a@b@c"), "多 @ 密码不得残留");
        assertTrue(result.contains("<MASKED_PWD>"));
        assertTrue(result.contains("@host:5432/mydb"), "主机须保留");
    }

    @Test
    void 无at符号的连接串密码被替换() {
        String input = "mysql://root:simplepass@host/db";
        String result = SensitiveDataFilter.filter(input);
        assertFalse(result.contains("simplepass"), "普通密码应被替换");
        assertTrue(result.contains("<MASKED_PWD>"));
    }

    @Test
    void password行被替换() {
        String input = "password=SuperSecret123\ndb_host=localhost";
        String result = SensitiveDataFilter.filter(input);
        assertFalse(result.contains("SuperSecret123"), "password= 应被替换");
        assertTrue(result.contains("<MASKED_PWD>"));
    }

    @Test
    void 中文密码关键词被替换() {
        // 企业中文文档写「密码: xxx」比写 password= 更常见，须一并覆盖
        String input = "密码: MyS3cretP@ssw0rd!";
        String result = SensitiveDataFilter.filter(input);
        assertFalse(result.contains("MyS3cretP"), "中文密码字段应被替换");
        assertTrue(result.contains("<MASKED_PWD>"));
    }

    @Test
    void 中文全角冒号密码被替换() {
        String input = "口令：abc123456";
        String result = SensitiveDataFilter.filter(input);
        assertFalse(result.contains("abc123456"), "全角冒号应被识别");
        assertTrue(result.contains("<MASKED_PWD>"));
    }

    @Test
    void 中文密码无分隔符不误杀() {
        // 「密码策略」「忘记密码」不含 = : ：，不应命中
        assertEquals("密码策略说明", SensitiveDataFilter.filter("密码策略说明"));
        assertEquals("忘记密码请联系管理员", SensitiveDataFilter.filter("忘记密码请联系管理员"));
    }

    // ========== PII ==========

    @Test
    void 手机号被替换() {
        String input = "联系人手机: 13812345678";
        String result = SensitiveDataFilter.filter(input);
        assertFalse(result.contains("13812345678"), "手机号应被替换");
        assertTrue(result.contains("<MASKED_PHONE>"));
    }

    @Test
    void 身份证号被替换() {
        String input = "身份证: 110101199003076019";
        String result = SensitiveDataFilter.filter(input);
        assertFalse(result.contains("110101199003076019"), "身份证号应被替换");
        assertTrue(result.contains("<MASKED_ID_CARD>"));
    }

    @Test
    void 银行卡号被替换() {
        String input = "银行卡: 6228480402564890018";
        String result = SensitiveDataFilter.filter(input);
        assertFalse(result.contains("6228480402564890018"), "银行卡号应被替换");
        assertTrue(result.contains("<MASKED_CARD>"));
    }

    @Test
    void 邮箱被替换() {
        String input = "联系邮箱: zhangsan@company.com";
        String result = SensitiveDataFilter.filter(input);
        assertFalse(result.contains("zhangsan@company.com"), "邮箱应被替换");
        assertTrue(result.contains("<MASKED_EMAIL>"));
    }

    // ========== 边界：银行卡只匹配银联 BIN ==========

    @Test
    void 银联卡号被替换() {
        // 6228 开头的银联卡
        String input = "银行卡: 6228480402564890018";
        String result = SensitiveDataFilter.filter(input);
        assertFalse(result.contains("6228480402564890018"), "银联卡号应被替换");
        assertTrue(result.contains("<MASKED_CARD>"));
    }

    @Test
    void 普通长数字不误杀() {
        // 订单号、流水号等非银联卡 BIN 的长数字不应被替换
        String input = "订单号: 202608301234567890";
        String result = SensitiveDataFilter.filter(input);
        assertTrue(result.contains("202608301234567890"), "非银行卡长数字不应被替换");
    }

    @Test
    void 邮箱在路径中不误杀() {
        // URL 路径中的 @ 不应被匹配
        String input = "访问 https://example.com/user@email.com/page 查看详情";
        String result = SensitiveDataFilter.filter(input);
        // @ 前后有 / ，不应匹配
        assertTrue(result.contains("user@email.com/page"), "路径中的邮箱不应被替换");
    }

    // ========== 不应误杀的场景 ==========

    @Test
    void 正常技术文档不误杀() {
        String input = """
                # Spring Boot 配置指南

                ## 数据源配置
                在 application.yml 中配置数据源：

                ```yaml
                spring:
                  datasource:
                    driver-class-name: com.mysql.cj.jdbc.Driver
                ```

                ## 常见问题
                1. 启动报错 ClassNotFoundException
                2. 连接超时请检查网络
                """;
        String result = SensitiveDataFilter.filter(input);
        assertEquals(input, result, "正常技术文档不应被修改");
    }

    @Test
    void null输入返回null() {
        assertNull(SensitiveDataFilter.filter(null));
    }

    @Test
    void 空字符串返回原值() {
        assertEquals("", SensitiveDataFilter.filter(""));
    }

    // ========== containsSensitiveData 检测方法 ==========

    @ParameterizedTest
    @ValueSource(strings = {
            "ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef1234",
            "AKIAIOSFODNN7EXAMPLE",
            "sk-test1234567890abcdefghijklmnop",
            "mysql://root:secret123@host/db",
            "13812345678",
            "zhangsan@test.com"
    })
    void containsSensitiveData_命中(String text) {
        assertTrue(SensitiveDataFilter.containsSensitiveData(text),
                "应检测到敏感数据: " + text.substring(0, Math.min(30, text.length())));
    }

    @ParameterizedTest
    @ValueSource(strings = {
            "这是一段正常的中文文本",
            "Spring Boot 是一个框架",
            "Hello World 12345",
            ""
    })
    void containsSensitiveData_不命中(String text) {
        assertFalse(SensitiveDataFilter.containsSensitiveData(text),
                "不应误判: " + text.substring(0, Math.min(30, text.length())));
    }
}
