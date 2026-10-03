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

package com.nageoffer.ai.ragent.knowledge.enums;

import lombok.Getter;
import lombok.RequiredArgsConstructor;

import java.util.Arrays;

/**
 * 矛盾审核状态
 */
@Getter
@RequiredArgsConstructor
public enum ConflictStatus {

    /**
     * 待审核：已记录，尚未处置，不影响检索
     */
    PENDING("pending"),

    /**
     * 已接受：按建议处置了原知识
     */
    ACCEPTED("accepted"),

    /**
     * 已拒绝：维持原样
     */
    REJECTED("rejected");

    private final String value;

    /**
     * 宽松解析，认不出返回 null 交由调用方判定
     */
    public static ConflictStatus parse(String raw) {
        if (raw == null) {
            return null;
        }
        String normalized = raw.trim().toLowerCase();
        return Arrays.stream(values())
                .filter(status -> status.value.equals(normalized))
                .findFirst()
                .orElse(null);
    }
}
