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

import cn.hutool.core.util.StrUtil;
import com.nageoffer.ai.ragent.core.parser.mineru.MinerUProperties;
import com.nageoffer.ai.ragent.core.parser.model.Block;
import com.nageoffer.ai.ragent.core.parser.model.ParagraphBlock;
import com.nageoffer.ai.ragent.core.parser.model.ParsedDocument;
import com.nageoffer.ai.ragent.core.parser.model.Provenance;
import com.nageoffer.ai.ragent.core.parser.registry.ParseProfile;
import com.nageoffer.ai.ragent.framework.exception.ServiceException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.apache.tika.Tika;
import org.springframework.stereotype.Component;

import java.io.ByteArrayInputStream;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * Apache Tika 解析器：纯文本类格式的兜底，覆盖 HTML / JSON / XML / RTF 及未被更专门的解析器认领的
 * {@code text/*}；复杂版面（PDF / Word / PPT）走 MinerU，表格走 POI / CSV，markdown 走 commonmark
 * <p>
 * 长尾靠 {@code text/*} 通配键覆盖，精确键一律优先于通配键，因此 {@code text/csv}、
 * {@code text/plain}、{@code text/x-web-markdown}（Tika 探测 {@code .md} 的产出）都不会落到这里
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class TikaDocumentParser implements DocumentParser {

    private static final Tika TIKA = new Tika();

    /**
     * 判断 MinerU 是否在位：在位则由它认领富文档，本解析器只做纯文本长尾
     */
    private final MinerUProperties minerUProperties;

    // 此处原有 static 块 new 了一个 PDFParserConfig 设置内联图片开关，但既没挂到 TIKA 上
    // （TIKA.parseToString 用不到它），设的还是 Tika 的默认值，等于两重空操作，已删

    @Override
    public String getParserType() {
        return ParserType.TIKA.getType();
    }

    /**
     * 结构化解析：Tika 输出是平文本，无章节标题 / 表格结构可挖，故按 {@code \n\n+} 空行分段，只产 ParagraphBlock
     */
    @Override
    public ParsedDocument parseStructured(byte[] content, String mimeType, Map<String, Object> options) {
        if (content == null || content.length == 0) {
            return ParsedDocument.of(List.of());
        }

        String text;
        try (ByteArrayInputStream is = new ByteArrayInputStream(content)) {
            text = TIKA.parseToString(is);
            text = TextCleanupUtil.cleanup(text);
        } catch (Exception e) {
            log.error("Tika 结构化解析失败，MIME 类型: {}", mimeType, e);
            throw new ServiceException("文档解析失败: " + e.getMessage());
        }

        Provenance prov = Provenance.ofFile(extractSourceFile(options));
        List<Block> blocks = new ArrayList<>();
        for (String segment : text.split("\\n{2,}")) {
            String trimmed = segment.strip();
            if (trimmed.isEmpty()) {
                continue;
            }
            blocks.add(new ParagraphBlock(prov, trimmed));
        }
        return ParsedDocument.of(blocks, Map.of("parser", getParserType(), "mimeType", mimeType == null ? "" : mimeType));
    }

    private String extractSourceFile(Map<String, Object> options) {
        if (options == null) {
            return "";
        }
        Object v = options.get("sourceFile");
        return v == null ? "" : v.toString();
    }

    /**
     * 精确键覆盖已声明支持的格式，{@code text/*} 通配只兜未声明的长尾；刻意不认领 image 与未知 MIME，
     * 认不出来就报错，不要兜底产出垃圾文本
     * <p>
     * 富文档（PDF / Word / PPT）平时由 MinerU 精确认领，本解析器只在**未配置 MinerU**时补认领——
     * 注册表对同一键的两个认领者直接判定冲突并拒绝启动，所以两边必须互斥：
     * 有 key 时 MinerU 认领（有版面分析），无 key 时 Tika 认领（纯文本，但可用）
     */
    @Override
    public Map<ParseProfile, Set<String>> supportedMimeTypes() {
        Set<String> mimes = new HashSet<>(Set.of(
                "text/*",
                "text/html",
                "application/json",
                "application/xml",
                "application/xhtml+xml",
                "application/rtf"
        ));
        mimes.addAll(PDF_MIME_TYPES);
        if (StrUtil.isBlank(minerUProperties.getApiKey())) {
            mimes.addAll(WORD_AND_SLIDE_MIME_TYPES);
        }
        return Map.of(ParseProfile.FAST, Set.copyOf(mimes));
    }

    /**
     * 恒定由 Tika 解析的 PDF
     * <p>
     * MinerU 的 PDF 通道实测卡死（批任务长期 pending），已把 PDF 从它的认领清单摘掉，
     * 这里就固定接住——不再受 MinerU 是否配置影响，否则配了 key 反而没人认领 PDF、启动自检直接失败。
     * 代价是版面分析能力：表格退化为文本行、公式丢失、扫描件抽不出内容
     */
    private static final Set<String> PDF_MIME_TYPES = Set.of(
            "application/pdf",
            "application/x-pdf"
    );

    /**
     * MinerU 缺席时由 Tika 代管的 Word / PPT
     * <p>
     * MinerU 在位时这几个格式归它（版面还原明显更好，且实测正常），只有没配 key 才落到这里
     */
    private static final Set<String> WORD_AND_SLIDE_MIME_TYPES = Set.of(
            "application/msword",
            "application/vnd.ms-word",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.ms-powerpoint",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "application/vnd.openxmlformats-officedocument.presentationml.slideshow"
    );
}
