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

package com.nageoffer.ai.ragent.core.ingest;

import com.nageoffer.ai.ragent.core.parser.model.AssetRef;
import com.nageoffer.ai.ragent.core.parser.model.Block;
import com.nageoffer.ai.ragent.core.parser.model.ImageBlock;
import com.nageoffer.ai.ragent.core.parser.model.ListBlock;
import com.nageoffer.ai.ragent.core.parser.model.ParagraphBlock;
import com.nageoffer.ai.ragent.core.parser.model.Provenance;
import com.nageoffer.ai.ragent.core.parser.model.TableBlock;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertDoesNotThrow;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * 摄取脱敏环节的边界用例
 * <p>
 * 重点覆盖「字段可空」这一类：脱敏器对 null 原样返回，若比较走 {@code filtered.equals(origin)}
 * 就会在空字段上抛 NPE，且是在摄取链路上抛——整篇文档入库失败，从文档状态里看不出原因
 */
class DefaultIngestionKernelSanitizeTest {

    private final DefaultIngestionKernel kernel =
            new DefaultIngestionKernel(null, null, null, null);

    private static final Provenance PROV = Provenance.ofFile("test.md");
    private static final AssetRef ASSET = new AssetRef("http://localhost:9000/a.png", "image/png");

    // ---------- 空字段 ----------

    @Test
    @DisplayName("图片块三个文本字段全空时不抛异常")
    void imageBlockWithAllNullTextFieldsDoesNotThrow() {
        ImageBlock block = new ImageBlock(PROV, ASSET, null, null, null);

        Block result = assertDoesNotThrow(() -> kernel.sanitizeSingleBlock(block));
        assertSame(block, result, "无内容可脱敏时应原样返回，避免无谓重建");
    }

    @Test
    @DisplayName("图片块用四参构造（description 为 null）时不抛异常")
    void imageBlockWithNullDescriptionDoesNotThrow() {
        // MinerU / Excel 这类不产图生文的来源走这个构造，description 恒为 null
        ImageBlock block = new ImageBlock(PROV, ASSET, "退款流程图", null);

        Block result = assertDoesNotThrow(() -> kernel.sanitizeSingleBlock(block));
        assertSame(block, result);
    }

    @Test
    @DisplayName("列表项为 null 时不抛异常")
    void listBlockWithNullItemsDoesNotThrow() {
        ListBlock block = new ListBlock(PROV, false, null);

        assertDoesNotThrow(() -> kernel.sanitizeSingleBlock(block));
    }

    @Test
    @DisplayName("表格行内含 null 单元格时不抛异常")
    void tableBlockWithNullCellDoesNotThrow() {
        // 用 Arrays.asList 而非 List.of：后者不接受 null 元素，构造不出「单元格为空」这个用例
        List<List<String>> rows = new ArrayList<>();
        rows.add(Arrays.asList("订单号", "金额"));
        rows.add(Arrays.asList("SO20261001001", null));

        assertDoesNotThrow(() -> kernel.sanitizeSingleBlock(new TableBlock(PROV, List.of("a", "b"), rows)));
    }

    // ---------- 脱敏仍然生效 ----------

    @Test
    @DisplayName("图片题注里的手机号被替换")
    void masksSensitiveCaption() {
        ImageBlock block = new ImageBlock(PROV, ASSET, "联系 13812345678 获取", null, null);

        Block result = kernel.sanitizeSingleBlock(block);

        ImageBlock masked = assertInstanceOf(ImageBlock.class, result);
        assertTrue(masked.caption().contains("<MASKED_PHONE>"), "手机号应被替换: " + masked.caption());
        assertEquals(null, masked.altText(), "空字段应保持为空，不能被写成占位串");
    }

    @Test
    @DisplayName("段落里的密钥被替换")
    void masksSecretInParagraph() {
        ParagraphBlock block = new ParagraphBlock(PROV, "配置 sk-abcdefghijklmnopqrstuvwxyz012345 请勿外传");

        Block result = kernel.sanitizeSingleBlock(block);

        ParagraphBlock masked = assertInstanceOf(ParagraphBlock.class, result);
        assertTrue(masked.text().contains("<MASKED_API_KEY>"), "密钥应被替换: " + masked.text());
    }

    @Test
    @DisplayName("无敏感内容时原样返回，不重建对象")
    void keepsOriginalBlockWhenNothingToMask() {
        ParagraphBlock block = new ParagraphBlock(PROV, "订单创建接口需要传 requestId");

        assertSame(block, kernel.sanitizeSingleBlock(block));
    }
}
