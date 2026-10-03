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

package com.nageoffer.ai.ragent.core.parser.mineru;

import com.nageoffer.ai.ragent.core.parser.DocumentParser;
import com.nageoffer.ai.ragent.core.parser.ParserType;
import com.nageoffer.ai.ragent.core.parser.TikaDocumentParser;
import com.nageoffer.ai.ragent.core.parser.model.ParsedDocument;
import com.nageoffer.ai.ragent.core.parser.registry.ParseProfile;
import com.nageoffer.ai.ragent.framework.exception.ServiceException;
import jakarta.annotation.PostConstruct;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.redisson.api.RPermitExpirableSemaphore;
import org.redisson.api.RedissonClient;
import org.springframework.boot.autoconfigure.condition.ConditionalOnExpression;
import org.springframework.stereotype.Component;

import java.time.Duration;
import java.util.HashMap;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;

/**
 * MinerU 文档解析器（PDF / Word / PPT / Excel）：走官方「本地文件批量上传解析」，上传后轮询等结果
 * <p>
 * 本地上传链路不依赖任何公网可达的源文件 URL，适配内网部署；解析许可由 {@link RPermitExpirableSemaphore}
 * 跨实例发放，压住 MinerU 侧同时在跑的任务数，配置项见 {@link MinerUProperties}
 */
@Slf4j
@Component
@RequiredArgsConstructor
@ConditionalOnExpression("'${mineru.api-key:}'.length() > 0")
public class MinerUDocumentParser implements DocumentParser {

    /**
     * 版面解析类：Word / PPT（含 97-2003 老格式）由 MinerU 承担
     * <p>
     * <b>PDF 不在此列</b>：MinerU 的 PDF 通道实测卡死——批任务长期停在 pending、err_msg 为空，
     * 换 model_version、换文件（含新生成的简单单页 PDF）、重传均无效，而同账号同时段的 DOC/DOCX/PPTX
     * 都在 20 秒内完成，属其服务端单条管线故障。PDF 已交回本地 {@code TikaDocumentParser}：
     * 牺牲版面分析（表格退化为文本、公式丢失），换掉每次必等的超时干等。
     * MinerU 的 PDF 通道恢复后，把两个 pdf MIME 加回本清单即可，Tika 侧会因精确键被抢占而自动让位
     */
    private static final Set<String> LAYOUT_MIME_TYPES = Set.of(
            "application/msword",
            "application/vnd.ms-word",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.ms-powerpoint",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "application/vnd.openxmlformats-officedocument.presentationml.slideshow"
    );

    // 此处原有 SPREADSHEET_MIME_TYPES，把 Excel 的保真档也让 MinerU 认领，现已移除，原因有二：
    // ① MinerU 的表格通道实测不可用——文件上传成功但批任务长期停在 pending，轮询到超时也不动，
    //    只能回落 Tika，3 分钟里 180 秒是干等；而本地 POI 解析同一文件只要 1 秒；
    // ② 回落产物反不如 POI：POI 产出结构化 TableBlock（表头与行分开），Tika 只给一坨纯文本。
    //    即「走 MinerU」既不快也不准，故 Excel 一律交回 POI。
    // 连带效果：注册表不再报告 Excel 是「档位敏感格式」，前端据此隐藏档位选择器，
    // 存量 fidelity 文档也会经 ParserRegistry.find 的 FAST 回落自动改走 POI。
    // MinerU 表格通道恢复后，把认领加回来即可一并复原。

    /**
     * options 字段：文件名，写入 Provenance.sourceFile
     */
    public static final String OPT_SOURCE_FILE = "sourceFile";

    /**
     * options 字段：文档 ID，用于资产 key 命名，不传时自动生成 UUID
     */
    public static final String OPT_DOCUMENT_ID = "documentId";

    /**
     * ParsedDocument.metadata 字段：MinerU 分配的 batchId，排障时凭它去 MinerU 侧查任务
     */
    public static final String META_BATCH_ID = "minerU.batchId";

    /**
     * ParsedDocument.metadata 字段：zip 下载 URL
     */
    public static final String META_ZIP_URL = "minerU.zipUrl";

    private final MinerUClient minerUClient;
    private final MinerUPollingExecutor pollingExecutor;
    private final MinerUResultUnpacker resultUnpacker;
    private final MinerUProperties properties;
    private final RedissonClient redissonClient;

    /**
     * MinerU 不可用时的回落解析器，解析失败即改走本地 Tika
     */
    private final TikaDocumentParser tikaFallback;

    @PostConstruct
    void initSemaphore() {
        RPermitExpirableSemaphore semaphore = redissonClient.getPermitExpirableSemaphore(properties.getSemaphoreName());
        semaphore.setPermits(properties.getConcurrencyLimit());
        log.info("MinerU 分布式解析限流初始化: semaphoreName={}, maxConcurrent={}",
                properties.getSemaphoreName(), properties.getConcurrencyLimit());
    }

    @Override
    public String getParserType() {
        return ParserType.MINERU.getType();
    }

    @Override
    public Map<ParseProfile, Set<String>> supportedMimeTypes() {
        return Map.of(ParseProfile.FAST, LAYOUT_MIME_TYPES);
    }

    @Override
    public ParsedDocument parseStructured(byte[] content, String mimeType, Map<String, Object> options) {
        if (content == null || content.length == 0) {
            throw new ServiceException("MinerU 解析输入字节为空");
        }
        try {
            return parseViaMinerU(content, mimeType, options);
        } catch (ServiceException e) {
            // MinerU 是外部 SaaS，存在我方修不了的故障：已实测「上传成功但任务长期停在 pending」，
            // 轮询到超时也不动。此时退回本地 Tika，宁可少还原版面，也不让整个格式不可用
            log.warn("MinerU 解析失败，回落到本地解析 mime={}：{}", mimeType, e.getMessage());
            return tikaFallback.parseStructured(content, mimeType, options);
        }
    }

    private ParsedDocument parseViaMinerU(byte[] content, String mimeType, Map<String, Object> options) {
        String permitId = null;
        RPermitExpirableSemaphore semaphore = redissonClient.getPermitExpirableSemaphore(properties.getSemaphoreName());
        try {
            permitId = semaphore.tryAcquire(
                    properties.getMaxWaitSeconds(),
                    properties.getLeaseSeconds(),
                    TimeUnit.SECONDS
            );
            if (permitId == null) {
                throw new ServiceException("MinerU 解析任务过多，请稍后重试");
            }
            return doParseStructured(content, mimeType, options);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new ServiceException("MinerU 获取解析许可被中断");
        } finally {
            if (permitId != null) {
                boolean released = semaphore.tryRelease(permitId);
                if (!released) {
                    log.warn("MinerU parse permit already expired or released, permitId={}", permitId);
                }
            }
        }
    }

    private ParsedDocument doParseStructured(byte[] content, String mimeType, Map<String, Object> options) {
        String sourceFile = extractString(options, OPT_SOURCE_FILE, "");
        String documentId = extractString(options, OPT_DOCUMENT_ID, UUID.randomUUID().toString());
        String uploadName = resolveUploadName(sourceFile, mimeType, documentId);

        // 1. 申请上传链接，只提交元信息、不带 url
        BatchSubmitRequest request = buildSubmitRequest(uploadName, documentId);
        BatchUploadTicket ticket = minerUClient.requestUpload(request);

        // 2. 把源文件字节直接 PUT 上传到 MinerU OSS
        minerUClient.uploadFile(ticket.uploadUrl(), content);
        log.info("MinerU 源文件上传完毕 documentId={} batchId={}", documentId, ticket.batchId());

        // 3. 阻塞等待完成，上传动作本身就触发 MinerU 提交解析，无需再调提交接口
        MinerUStatus status;
        try {
            status = pollingExecutor
                    .submitAndAwait(ticket.batchId(), Duration.ofSeconds(properties.getTimeoutSeconds()))
                    .get(properties.getTimeoutSeconds() + 30, TimeUnit.SECONDS);
        } catch (TimeoutException e) {
            throw new ServiceException("MinerU 等待超时(包含调度缓冲)batchId=" + ticket.batchId());
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new ServiceException("MinerU 等待被中断 batchId=" + ticket.batchId());
        } catch (ExecutionException e) {
            Throwable cause = e.getCause();
            if (cause instanceof RuntimeException re) {
                throw re;
            }
            throw new ServiceException("MinerU 等待异常 batchId=" + ticket.batchId() + ": " + cause.getMessage());
        }

        // 4. 下载 zip
        byte[] zipBytes = minerUClient.downloadZip(status.zipUrl());

        // 5. 解包为 ParsedDocument
        ParsedDocument parsed = resultUnpacker.unpack(zipBytes, sourceFile, documentId);

        // 6. batchId + zipUrl 注入 metadata，供下游节点持久化后排障
        Map<String, Object> mergedMeta = new HashMap<>(parsed.metadata() == null ? Map.of() : parsed.metadata());
        mergedMeta.put(META_BATCH_ID, ticket.batchId());
        mergedMeta.put(META_ZIP_URL, status.zipUrl());
        mergedMeta.put("parser", getParserType());
        mergedMeta.put("mimeType", mimeType == null ? "" : mimeType);

        return ParsedDocument.of(parsed.blocks(), mergedMeta);
    }

    /**
     * 计算上传到 MinerU 的文件名，必须带扩展名，MinerU 靠它识别格式；缺原始文件名时按 mimeType 补全
     */
    private String resolveUploadName(String sourceFile, String mimeType, String documentId) {
        if (sourceFile != null && !sourceFile.isBlank()) {
            return sourceFile;
        }
        return "doc-" + documentId + extFromMime(mimeType);
    }

    private BatchSubmitRequest buildSubmitRequest(String fileName, String documentId) {
        return new BatchSubmitRequest(
                fileName,
                documentId,
                properties.isOcr(),
                properties.isEnableTable(),
                properties.isEnableFormula(),
                properties.getLanguage()
        );
    }

    private static String extFromMime(String mimeType) {
        if (mimeType == null) {
            return ".bin";
        }
        String lower = mimeType.toLowerCase(Locale.ROOT);
        if (lower.contains("pdf")) return ".pdf";
        if (lower.contains("wordprocessingml")) return ".docx";
        if (lower.contains("msword")) return ".doc";
        if (lower.contains("presentationml")) return ".pptx";
        if (lower.contains("powerpoint")) return ".ppt";
        if (lower.contains("spreadsheetml")) return ".xlsx";
        if (lower.contains("ms-excel") || lower.contains("excel")) return ".xls";
        return ".bin";
    }

    private static String extractString(Map<String, Object> options, String key, String defaultValue) {
        if (options == null) {
            return defaultValue;
        }
        Object v = options.get(key);
        return (v == null || v.toString().isBlank()) ? defaultValue : v.toString();
    }
}
