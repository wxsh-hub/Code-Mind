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

package com.nageoffer.ai.ragent.core.parser;

import com.nageoffer.ai.ragent.core.parser.excel.ExcelDocumentParser;
import com.nageoffer.ai.ragent.core.parser.mineru.MinerUClient;
import com.nageoffer.ai.ragent.core.parser.mineru.MinerUDocumentParser;
import com.nageoffer.ai.ragent.core.parser.mineru.MinerUPollingExecutor;
import com.nageoffer.ai.ragent.core.parser.mineru.MinerUProperties;
import com.nageoffer.ai.ragent.core.parser.mineru.MinerUResultUnpacker;
import com.nageoffer.ai.ragent.core.parser.registry.ParseProfile;
import com.nageoffer.ai.ragent.core.parser.registry.ParserRegistry;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.redisson.api.RedissonClient;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.Mockito.mock;

/**
 * Excel 的档位路由
 * <p>
 * 「复杂表格」原有唯一价值是让 Excel 走 MinerU，但实测 MinerU 表格通道不可用（批任务长期 pending），
 * 只能等超时回落，产物反不如本地 POI 的结构化表格。故 Excel 一律交回 POI，
 * 「档位」对 Excel 成为空操作——前端的选择器必须随之消失，否则用户仍会选到一个干等 3 分钟的档位
 */
class ExcelProfileRoutingTest {

    private static final String XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";

    /**
     * MinerU 在位（配了 key），排除「没注册所以不认领」这一干扰因素
     */
    private ParserRegistry registry() {
        MinerUProperties props = new MinerUProperties();
        props.setApiKey("sk-test");
        MinerUDocumentParser mineru = new MinerUDocumentParser(
                mock(MinerUClient.class), mock(MinerUPollingExecutor.class),
                mock(MinerUResultUnpacker.class), props, mock(RedissonClient.class), null);
        return new ParserRegistry(List.of(new ExcelDocumentParser(),
                new TikaDocumentParser(props), mineru));
    }

    @Test
    @DisplayName("Excel 不再是档位敏感格式，前端据此隐藏档位选择器")
    void excelIsNoLongerProfileSensitive() {
        assertFalse(registry().profileSensitiveMimeTypes().contains(XLSX),
                "两个档位命中同一个解析器时，档位是空操作，不能继续下发给前端当成可选项");
    }

    @Test
    @DisplayName("存量 fidelity 文档自动改走本地 POI")
    void fidelityExcelFallsBackToPoi() {
        // 用户此前用「复杂表格」建的文档还在库里，切档位不能要求他们逐篇改配置
        DocumentParser hit = registry().find(XLSX, ParseProfile.FIDELITY).orElseThrow();

        assertInstanceOf(ExcelDocumentParser.class, hit,
                "fidelity 无解析器认领时应经 FAST 回落落到 POI，而不是报「找不到解析器」");
    }

    @Test
    @DisplayName("PDF 改走本地 Tika，即使 MinerU 配了 key 也不经过它")
    void pdfRoutesToTikaEvenWhenMinerUConfigured() {
        // 实测 MinerU 的 PDF 通道卡死（批任务长期 pending），配着 key 也只会白等超时
        assertInstanceOf(TikaDocumentParser.class,
                registry().find("application/pdf", ParseProfile.FAST).orElseThrow(),
                "PDF 必须落本地 Tika，落到 MinerU 等于每次多等一轮超时");
    }

    @Test
    @DisplayName("Word / PPT 仍走 MinerU，未受 PDF 调整波及")
    void wordStillRoutesToMinerU() {
        assertInstanceOf(MinerUDocumentParser.class, registry()
                .find("application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        ParseProfile.FAST).orElseThrow());
    }

    @Test
    @DisplayName("规整表格仍走 POI")
    void fastExcelStillRoutesToPoi() {
        assertTrue(registry().find(XLSX, ParseProfile.FAST).orElseThrow() instanceof ExcelDocumentParser);
    }
}
