/*
 * Licensed to the Apache Software Foundation (ASF) under one or more
 * contributor license agreements. See the NOTICE file distributed with
 * this work for additional information regarding copyright ownership.
 * The ASF licenses this file to You under the Apache License, Version 2.0
 * (the "License"); you may not use this file except in compliance with
 * the License.
 */
package com.nageoffer.ai.ragent.initializer;

import com.nageoffer.ai.ragent.framework.security.SensitiveDataFilter;

import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

/**
 * 存量分块敏感数据巡检与修复
 * <p>
 * {@link SensitiveDataFilter} 只在摄取阶段生效，已入库的历史分块不会被回溯处理。
 * 本工具按同一套规则扫描 {@code t_knowledge_chunk}，把命中敏感数据的行就地改写。
 * <p>
 * 刻意直接复用 {@link SensitiveDataFilter} 而非另写一套 SQL 正则：规则是唯一权威源，
 * 两处各写一遍必然漂移，而漂移的后果是「新数据干净、旧数据漏网」且无人察觉。
 * <p>
 * 用法（在项目根目录执行）：
 * <pre>
 *   javac -encoding UTF-8 -d /tmp/repair-classes \
 *     -cp framework/target/classes \
 *     resources/initializer/common/*.java \
 *     resources/initializer/sensitive-data-repair/*.java
 *
 *   java -cp /tmp/repair-classes:framework/target/classes \
 *     com.nageoffer.ai.ragent.initializer.RepairSensitiveDataMain \
 *     --config resources/initializer/sensitive-data-repair/repair.properties \
 *     --dry-run
 * </pre>
 * 不带 {@code --dry-run} 时会真实改写，需额外提供 {@code --confirm <确认串>}。
 */
public final class RepairSensitiveDataMain {

    /**
     * 单批改写条数：一批一个事务，避免全文扫描期间长事务占住连接
     */
    private static final int BATCH_SIZE = 200;

    private RepairSensitiveDataMain() {
    }

    public static void main(String[] args) {
        try {
            run(args);
        } catch (Exception ex) {
            System.err.println("[repair] FAILED: " + ex.getMessage());
            if (Boolean.parseBoolean(System.getenv().getOrDefault("RAGENT_INITIALIZER_DEBUG", "false"))) {
                ex.printStackTrace(System.err);
            }
            System.exit(1);
        }
    }

    private static void run(String[] args) throws Exception {
        Arguments arguments = Arguments.parse(args);
        InitializerConfig config = InitializerConfig.load(arguments.configFile());

        if (!arguments.dryRun()) {
            String expected = config.require("repair.confirmation");
            if (!expected.equals(arguments.confirmation())) {
                throw new IllegalArgumentException("这是改写数据的操作，请增加参数 --confirm " + expected);
            }
        }

        // 可选按知识库收窄范围，为空表示全量；仅对关系库分块表生效（向量库无 kb_id 列）
        String kbFilter = config.get("repair.kb-id", "");

        try (JdbcClient jdbc = new JdbcClient(config)) {
            System.out.println("[repair] 目标库: " + jdbc.description());
            System.out.println("[repair] 模式: " + (arguments.dryRun() ? "DRY-RUN（只报告不改写）" : "改写"));

            // 关系库分块表：content 对外展示，embedding_text 供换模型时重嵌入，两列都是明文
            long chunkChanges = repairTable(jdbc, arguments, "t_knowledge_chunk",
                    "SELECT id, content, COALESCE(embedding_text, '') FROM t_knowledge_chunk "
                            + (kbFilter.isBlank() ? "" : "WHERE kb_id = " + JdbcClient.literal(kbFilter))
                            + " ORDER BY id",
                    true);

            // 向量库：检索结果直接取自这里的 content，是泄漏的第一现场；
            // 无 deleted / kb_id 列，无法按库收窄，故全量扫描
            long vectorChanges = repairTable(jdbc, arguments, "t_knowledge_vector",
                    "SELECT id, content, '' FROM t_knowledge_vector ORDER BY id",
                    false);

            long changed = chunkChanges + vectorChanges;
            System.out.println("[repair] 扫描完成，命中 " + changed + " 条");
            if (arguments.dryRun()) {
                System.out.println("[repair] DRY-RUN 结束，未改写任何数据。去掉 --dry-run 并补 --confirm 才会落地");
            } else {
                System.out.println("[repair] 已改写 " + changed + " 条（chunk=" + chunkChanges + ", vector=" + vectorChanges + "）");
            }
            System.out.println("[repair] SUCCESS");
        }
    }

    /**
     * 扫描单表并按 {@link SensitiveDataFilter} 改写命中的行
     *
     * @param withEmbedding 该表是否有 embedding_text 列（向量库没有）
     * @return 命中并改写的行数
     */
    private static long repairTable(JdbcClient jdbc, Arguments arguments, String table,
                                    String selectSql, boolean withEmbedding) throws Exception {
        List<List<String>> rows = jdbc.queryRows(selectSql);
        System.out.println("[repair] " + table + " 扫描行数: " + rows.size());

        List<String> statements = new ArrayList<>();
        long changed = 0;

        for (List<String> row : rows) {
            String id = row.get(0);
            String content = row.get(1);
            String embeddingText = row.get(2);
            String filteredContent = SensitiveDataFilter.filter(content);
            // 空值跳过，不把 NULL 写成空串
            boolean hasEmbedding = withEmbedding && !embeddingText.isEmpty();
            String filteredEmbedding = hasEmbedding ? SensitiveDataFilter.filter(embeddingText) : embeddingText;

            boolean contentChanged = !filteredContent.equals(content);
            boolean embeddingChanged = hasEmbedding && !filteredEmbedding.equals(embeddingText);
            if (!contentChanged && !embeddingChanged) {
                continue;
            }
            changed++;
            if (arguments.dryRun()) {
                // 只报命中列与长度变化，不回显原文，避免巡检日志本身成为泄漏面
                System.out.printf("[repair]   %s 命中 id=%s content %s embedding %s%n", table, id,
                        contentChanged ? content.length() + "->" + filteredContent.length() : "未变",
                        embeddingChanged ? embeddingText.length() + "->" + filteredEmbedding.length() : "未变");
                continue;
            }
            StringBuilder update = new StringBuilder("UPDATE ").append(table).append(" SET content = ")
                    .append(JdbcClient.literal(filteredContent));
            if (embeddingChanged) {
                update.append(", embedding_text = ").append(JdbcClient.literal(filteredEmbedding));
            }
            update.append(" WHERE id = ").append(JdbcClient.literal(id));
            statements.add(update.toString());

            if (statements.size() >= BATCH_SIZE) {
                jdbc.executeBatch(List.copyOf(statements));
                statements.clear();
            }
        }

        if (!arguments.dryRun() && !statements.isEmpty()) {
            jdbc.executeBatch(List.copyOf(statements));
        }
        return changed;
    }

    /**
     * 极简参数解析：只认 {@code --key value} 与两个开关，不引入 Spring 的 CommandLineRunner
     */
    private record Arguments(Path configFile, boolean dryRun, String confirmation) {

        static Arguments parse(String[] args) {
            Path configFile = null;
            boolean dryRun = false;
            String confirmation = null;
            for (int index = 0; index < args.length; index++) {
                String key = args[index];
                switch (key) {
                    case "--config" -> {
                        if (index + 1 >= args.length) {
                            throw new IllegalArgumentException("--config 缺少值");
                        }
                        configFile = Path.of(args[++index]).toAbsolutePath().normalize();
                    }
                    case "--dry-run" -> dryRun = true;
                    case "--confirm" -> {
                        if (index + 1 >= args.length) {
                            throw new IllegalArgumentException("--confirm 缺少值");
                        }
                        confirmation = args[++index];
                    }
                    default -> throw new IllegalArgumentException("无法识别的参数: " + key);
                }
            }
            if (configFile == null) {
                throw new IllegalArgumentException("必须传入 --config <配置文件>");
            }
            return new Arguments(configFile, dryRun, confirmation);
        }
    }
}
