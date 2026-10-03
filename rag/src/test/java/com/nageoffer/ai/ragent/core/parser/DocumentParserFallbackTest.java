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

import com.nageoffer.ai.ragent.core.parser.mineru.MinerUClient;
import com.nageoffer.ai.ragent.core.parser.mineru.MinerUDocumentParser;
import com.nageoffer.ai.ragent.core.parser.mineru.MinerUPollingExecutor;
import com.nageoffer.ai.ragent.core.parser.mineru.MinerUProperties;
import com.nageoffer.ai.ragent.core.parser.mineru.MinerUResultUnpacker;
import com.nageoffer.ai.ragent.core.parser.model.ParsedDocument;
import com.nageoffer.ai.ragent.core.parser.registry.ParseProfile;
import com.nageoffer.ai.ragent.framework.exception.ServiceException;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.redisson.api.RPermitExpirableSemaphore;
import org.redisson.api.RedissonClient;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.TimeUnit;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

/**
 * 富文档解析的「MinerU 优先、Tika 兜底」策略
 * <p>
 * 两条防线各测一遍：
 * ① 路由层——MinerU 不在场时由 Tika 认领 PDF/Word/PPT，否则注册表会因无人认领而拒绝启动；
 * ② 运行层——MinerU 在位但解析失败（实测存在「上传成功却长期 pending」的故障）时回落 Tika
 */
class DocumentParserFallbackTest {

    private static final String PDF_MIME = "application/pdf";

    private static MinerUProperties propsWithKey(String key) {
        MinerUProperties p = new MinerUProperties();
        p.setApiKey(key);
        return p;
    }

    private byte[] samplePdf() throws IOException {
        Path path = Paths.get("src/test/resources/fixtures/chunking/merchant-manual.pdf");
        assertTrue(Files.exists(path), "测试素材缺失: " + path.toAbsolutePath());
        return Files.readAllBytes(path);
    }

    // ---------- ① 路由层：谁认领富文档 ----------

    @Test
    @DisplayName("未配置 MinerU 时，Tika 认领 PDF/Word/PPT 兜底")
    void tikaClaimsRichDocumentsWhenMinerUAbsent() {
        TikaDocumentParser tika = new TikaDocumentParser(propsWithKey(""));

        Set<String> claimed = tika.supportedMimeTypes().get(ParseProfile.FAST);

        assertTrue(claimed.contains(PDF_MIME), "没有 MinerU 时必须由 Tika 认领 PDF，否则注册表启动自检不过");
        assertTrue(claimed.contains("application/vnd.openxmlformats-officedocument.wordprocessingml.document"));
        assertTrue(claimed.contains("application/vnd.openxmlformats-officedocument.presentationml.presentation"));
    }

    @Test
    @DisplayName("配置了 MinerU 时，Word/PPT 让给它；PDF 仍由 Tika 接管")
    void tikaYieldsWordAndSlidesButKeepsPdf() {
        TikaDocumentParser tika = new TikaDocumentParser(propsWithKey("sk-test"));

        Set<String> claimed = tika.supportedMimeTypes().get(ParseProfile.FAST);

        assertFalse(claimed.contains("application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
                "MinerU 在场时 Word 归它，Tika 重复认领会让同一键有两个认领者而启动失败");
        assertTrue(claimed.contains(PDF_MIME),
                "PDF 与 MinerU 在位与否无关：它的 PDF 通道实测卡死，恒由本地 Tika 接管");
        assertTrue(claimed.contains("text/*"), "纯文本长尾仍由 Tika 兜");
    }

    // ---------- ② 运行层：MinerU 失败回落 Tika ----------

    private MinerUDocumentParser mineruParser(MinerUClient client, TikaDocumentParser tika)
            throws InterruptedException {
        MinerUProperties props = propsWithKey("sk-test");
        RedissonClient redisson = mock(RedissonClient.class);
        RPermitExpirableSemaphore semaphore = mock(RPermitExpirableSemaphore.class);
        when(redisson.getPermitExpirableSemaphore(anyString())).thenReturn(semaphore);
        when(semaphore.tryAcquire(anyLong(), anyLong(), any(TimeUnit.class))).thenReturn("permit-1");
        when(semaphore.tryRelease("permit-1")).thenReturn(true);

        return new MinerUDocumentParser(client, mock(MinerUPollingExecutor.class),
                mock(MinerUResultUnpacker.class), props, redisson, tika);
    }

    @Test
    @DisplayName("MinerU 解析失败时回落到 Tika，解析结果不为空")
    void fallsBackToTikaWhenMinerUFails() throws Exception {
        MinerUClient client = mock(MinerUClient.class);
        // 实测过的故障形态：批任务长期 pending，轮询到超时
        when(client.requestUpload(any())).thenThrow(new ServiceException("MinerU 任务超时 batchId=x"));

        MinerUDocumentParser parser = mineruParser(client, new TikaDocumentParser(propsWithKey("sk-test")));
        ParsedDocument parsed = parser.parseStructured(samplePdf(), PDF_MIME, Map.of());

        assertNotNull(parsed);
        assertFalse(parsed.blocks().isEmpty(), "回落路径必须真的产出内容，否则等于换了个报错");
        assertEquals(ParserType.TIKA.getType(), parsed.metadata().get("parser"), "应标记为由 Tika 解析，便于排查");
    }

    @Test
    @DisplayName("MinerU 抛的是 ServiceException 才回落，其它异常照常上抛")
    void doesNotSwallowUnexpectedExceptions() throws Exception {
        MinerUClient client = mock(MinerUClient.class);
        when(client.requestUpload(any())).thenThrow(new IllegalStateException("编程错误"));

        MinerUDocumentParser parser = mineruParser(client, new TikaDocumentParser(propsWithKey("sk-test")));

        // 只兜「外部服务不可用」这一类，代码缺陷不该被降级掩盖
        try {
            parser.parseStructured(samplePdf(), PDF_MIME, Map.of());
            org.junit.jupiter.api.Assertions.fail("非 ServiceException 应原样抛出");
        } catch (IllegalStateException expected) {
            // 符合预期
        }
    }
}
