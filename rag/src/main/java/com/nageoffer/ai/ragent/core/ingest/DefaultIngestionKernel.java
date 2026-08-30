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

import com.nageoffer.ai.ragent.core.chunk.ChunkingService;
import com.nageoffer.ai.ragent.core.chunk.model.Chunk;
import com.nageoffer.ai.ragent.core.chunk.model.EmbeddedChunk;
import com.nageoffer.ai.ragent.core.ingest.embed.ChunkEmbeddingService;
import com.nageoffer.ai.ragent.core.ingest.sink.ChunkIndexWriter;
import com.nageoffer.ai.ragent.core.parser.DocumentParser;
import com.nageoffer.ai.ragent.core.parser.mime.MimeTypeDetector;
import com.nageoffer.ai.ragent.core.parser.model.Block;
import com.nageoffer.ai.ragent.core.parser.model.*;
import com.nageoffer.ai.ragent.core.parser.registry.ParserRegistry;
import com.nageoffer.ai.ragent.framework.exception.ClientException;
import com.nageoffer.ai.ragent.framework.security.SensitiveDataFilter;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/**
 * 摄取内核默认实现：固定五步骨架，全文唯一一条摄取执行序列
 * <p>
 * 入口不收 MIME 也不收嵌入模型，任务状态与摄取日志一概不碰
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class DefaultIngestionKernel implements IngestionKernel {

    /**
     * 解析器 options 键：原始文件名，写进块来源信息
     */
    private static final String OPT_SOURCE_FILE = "sourceFile";

    /**
     * 解析器 options 键：文档 ID，决定图片资产的归属目录 {@code assets/{docId}/...}
     */
    private static final String OPT_DOCUMENT_ID = "documentId";

    private final ParserRegistry parserRegistry;
    private final ChunkingService chunkingService;
    private final ChunkEmbeddingService chunkEmbeddingService;
    private final ChunkIndexWriter chunkIndexWriter;

    @Override
    public IngestionOutcome run(DocumentRef doc,
                                byte[] bytes,
                                IngestionSpec spec,
                                VectorTarget target) {
        if (bytes == null || bytes.length == 0) {
            throw new ClientException("文件内容为空：docId=" + doc.docId());
        }
        IngestionSpec effectiveSpec = spec == null ? IngestionSpec.defaults() : spec;

        // ① identity：全链路唯一一次类型识别
        String mimeType = MimeTypeDetector.detect(bytes, doc.filename());
        if (!StringUtils.hasText(mimeType)) {
            throw new ClientException("无法识别文件类型：docId=" + doc.docId() + ", filename=" + doc.filename());
        }

        // ② parse：(MIME × 档位) → 解析器
        long parseStart = System.currentTimeMillis();
        DocumentParser parser = parserRegistry.require(mimeType, effectiveSpec.parseProfile());
        ParsedDocument parsed = parser.parseStructured(bytes, mimeType, parserOptions(doc));
        List<Block> blocks = parsed.blocks() == null ? List.of() : parsed.blocks();
        long parseMillis = System.currentTimeMillis() - parseStart;
        log.info("摄取-解析完成 docId={} mime={} 档位={} 解析器={} blocks={}",
                doc.docId(), mimeType, effectiveSpec.parseProfile().getCode(), parser.getParserType(), blocks.size());

        // ②.5 sanitize：敏感数据过滤（密钥 / Token / PII）
        blocks = sanitizeBlocks(blocks);

        // ③ chunk：Block 类型 → chunker + 预算
        long chunkStart = System.currentTimeMillis();
        List<Chunk> chunks = chunkingService.chunk(blocks, effectiveSpec.budget());
        long chunkMillis = System.currentTimeMillis() - chunkStart;

        if (chunks.isEmpty()) {
            throw new ClientException("分块结果为空：docId=" + doc.docId() + ", mime=" + mimeType);
        }

        // ④ embed：模型与维度都来自落点，此处校验维度
        long embedStart = System.currentTimeMillis();
        List<EmbeddedChunk> embedded = chunkEmbeddingService.embed(chunks, target);
        long embedMillis = System.currentTimeMillis() - embedStart;

        // ⑤ index：扇出到全部落点，事务边界在写入器内
        long indexStart = System.currentTimeMillis();
        chunkIndexWriter.replaceDocument(target, doc, embedded);
        long indexMillis = System.currentTimeMillis() - indexStart;

        return new IngestionOutcome(mimeType, parser.getParserType(), blocks.size(), chunks,
                new IngestionOutcome.IngestionTimings(parseMillis, chunkMillis, embedMillis, indexMillis));
    }

    /**
     * 组装解析器入参：docId 必须传，解析器用它给图片资产命名，漏传则资产与文档失联
     */
    private Map<String, Object> parserOptions(DocumentRef doc) {
        Map<String, Object> options = new HashMap<>();
        if (StringUtils.hasText(doc.filename())) {
            options.put(OPT_SOURCE_FILE, doc.filename());
        }
        options.put(OPT_DOCUMENT_ID, doc.docId());
        return options;
    }

    /**
     * 对 Block 列表做敏感数据过滤
     * <p>
     * record 是不可变的，需要根据类型创建新实例替换文本字段。
     * 仅对含文本内容的 Block 做过滤，ImageBlock 的 caption/description 也覆盖。
     */
    private List<Block> sanitizeBlocks(List<Block> blocks) {
        List<Block> result = new java.util.ArrayList<>(blocks.size());
        boolean anyFiltered = false;
        for (Block block : blocks) {
            Block sanitized = sanitizeSingleBlock(block);
            if (sanitized != block) {
                anyFiltered = true;
            }
            result.add(sanitized);
        }
        if (anyFiltered) {
            log.info("敏感数据过滤：已对 blocks 做脱敏处理，共 {} 个 block", blocks.size());
        }
        return result;
    }

    private Block sanitizeSingleBlock(Block block) {
        if (block instanceof ParagraphBlock b) {
            String filtered = SensitiveDataFilter.filter(b.text());
            return filtered.equals(b.text()) ? b : new ParagraphBlock(b.provenance(), filtered);
        } else if (block instanceof HeadingBlock b) {
            String filtered = SensitiveDataFilter.filter(b.text());
            return filtered.equals(b.text()) ? b : new HeadingBlock(b.provenance(), b.level(), filtered);
        } else if (block instanceof CodeBlock b) {
            String filtered = SensitiveDataFilter.filter(b.code());
            return filtered.equals(b.code()) ? b : new CodeBlock(b.provenance(), b.language(), filtered);
        } else if (block instanceof ListBlock b) {
            List<String> filteredItems = filterStringList(b.items());
            return filteredItems == b.items() ? b : new ListBlock(b.provenance(), b.ordered(), filteredItems);
        } else if (block instanceof TableBlock b) {
            List<String> filteredHeaders = filterStringList(b.headers());
            List<List<String>> filteredRows = filterRows(b.rows());
            boolean changed = filteredHeaders != b.headers() || filteredRows != b.rows();
            return changed ? new TableBlock(b.provenance(), filteredHeaders, filteredRows) : b;
        } else if (block instanceof HtmlTableBlock b) {
            String filtered = SensitiveDataFilter.filter(b.html());
            return filtered.equals(b.html()) ? b : new HtmlTableBlock(b.provenance(), filtered);
        } else if (block instanceof ImageBlock b) {
            String caption = SensitiveDataFilter.filter(b.caption());
            String altText = SensitiveDataFilter.filter(b.altText());
            String desc = SensitiveDataFilter.filter(b.description());
            boolean changed = !caption.equals(b.caption()) || !altText.equals(b.altText())
                    || !Objects.equals(desc, b.description());
            return changed ? new ImageBlock(b.provenance(), b.asset(), caption, altText, desc) : b;
        }
        return block;
    }

    private List<String> filterStringList(List<String> items) {
        if (items == null || items.isEmpty()) {
            return items;
        }
        List<String> result = new java.util.ArrayList<>(items.size());
        boolean changed = false;
        for (String item : items) {
            String filtered = SensitiveDataFilter.filter(item);
            result.add(filtered);
            if (!filtered.equals(item)) {
                changed = true;
            }
        }
        return changed ? result : items;
    }

    private List<List<String>> filterRows(List<List<String>> rows) {
        if (rows == null || rows.isEmpty()) {
            return rows;
        }
        List<List<String>> result = new java.util.ArrayList<>(rows.size());
        boolean changed = false;
        for (List<String> row : rows) {
            List<String> filteredRow = filterStringList(row);
            result.add(filteredRow);
            if (filteredRow != row) {
                changed = true;
            }
        }
        return changed ? result : rows;
    }

}
