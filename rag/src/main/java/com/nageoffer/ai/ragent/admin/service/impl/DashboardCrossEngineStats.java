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

package com.nageoffer.ai.ragent.admin.service.impl;

import lombok.RequiredArgsConstructor;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;

import java.util.Date;
import java.util.List;
import java.util.Map;

/**
 * 仪表盘的跨引擎会话/消息统计
 * <p>
 * 两套对话引擎各写各的表：workflow 写 {@code t_conversation / t_message}，
 * agent 写 {@code t_agent_conversation / t_agent_message}，四张表的统计列同构。
 * 仪表盘反映的是「系统整体被用得怎么样」，不该随引擎切换而清零，故两边一律相加。
 * <p>
 * 这里用原生 SQL 而非 agent 模块的 Mapper：{@code agent} 依赖 {@code rag}，
 * 反向引用会形成循环依赖。表名与表达式只接受本类的内部常量，不拼外部输入。
 * <p>
 * 分组查询刻意返回 {@code List<Map<String, Object>>}（键为调用方要的 d / h，值为 cnt），
 * 与 Mapper#selectMaps 同形，调用侧的日期解析逻辑因此无需改动。
 * <p>
 * 沿用既有口径，不过滤 {@code deleted}——与原先单表统计保持一致，改了会让历史数据对不上
 */
@Component
@RequiredArgsConstructor
public class DashboardCrossEngineStats {

    private static final String CONVERSATIONS = "t_conversation";
    private static final String AGENT_CONVERSATIONS = "t_agent_conversation";
    private static final String MESSAGES = "t_message";
    private static final String AGENT_MESSAGES = "t_agent_message";

    private static final String ROLE_ASSISTANT = "assistant";
    private static final String ASSISTANT_CONDITION = "role = '" + ROLE_ASSISTANT + "'";

    private final JdbcTemplate jdbcTemplate;

    // ==================== 总量 ====================

    public long countAllConversations() {
        return sumAll(CONVERSATIONS, AGENT_CONVERSATIONS);
    }

    public long countAllMessages() {
        return sumAll(MESSAGES, AGENT_MESSAGES);
    }

    // ==================== 时间窗计数 ====================

    public long countConversations(Date start, Date end) {
        return sumCounts(CONVERSATIONS, AGENT_CONVERSATIONS, null, start, end);
    }

    public long countMessages(Date start, Date end) {
        return sumCounts(MESSAGES, AGENT_MESSAGES, null, start, end);
    }

    public long countAssistantMessages(Date start, Date end) {
        return sumCounts(MESSAGES, AGENT_MESSAGES, ASSISTANT_CONDITION, start, end);
    }

    /**
     * 时间窗内发过言的人数
     * <p>
     * 先 UNION 再 count distinct：分表各算一次 distinct 再相加会重复计人
     */
    public long countActiveUsers(Date start, Date end) {
        String sql = "SELECT count(DISTINCT user_id) FROM ("
                + "SELECT user_id FROM " + MESSAGES + " WHERE create_time >= ? AND create_time < ?"
                + " UNION ALL "
                + "SELECT user_id FROM " + AGENT_MESSAGES + " WHERE create_time >= ? AND create_time < ?"
                + ") u";
        return queryLong(sql, start, end, start, end);
    }

    /**
     * 时间窗内「未检索到文档」的回复数
     */
    public long countNoDocMessages(Date start, Date end, String noDocReply) {
        String condition = ASSISTANT_CONDITION + " AND content = ?";
        String sql = "SELECT (SELECT count(*) FROM " + MESSAGES
                + " WHERE create_time >= ? AND create_time < ? AND " + condition + ")"
                + " + (SELECT count(*) FROM " + AGENT_MESSAGES
                + " WHERE create_time >= ? AND create_time < ? AND " + condition + ")";
        return queryLong(sql, start, end, noDocReply, start, end, noDocReply);
    }

    // ==================== 按天分组 ====================

    public List<Map<String, Object>> conversationsByDay(Date start, Date end) {
        return group("to_char(create_time,'YYYY-MM-DD')", "d", CONVERSATIONS, AGENT_CONVERSATIONS, null, start, end);
    }

    public List<Map<String, Object>> messagesByDay(Date start, Date end) {
        return group("to_char(create_time,'YYYY-MM-DD')", "d", MESSAGES, AGENT_MESSAGES, null, start, end);
    }

    public List<Map<String, Object>> assistantMessagesByDay(Date start, Date end) {
        return group("to_char(create_time,'YYYY-MM-DD')", "d", MESSAGES, AGENT_MESSAGES,
                ASSISTANT_CONDITION, start, end);
    }

    public List<Map<String, Object>> noDocMessagesByDay(Date start, Date end, String noDocReply) {
        return group("to_char(create_time,'YYYY-MM-DD')", "d", MESSAGES, AGENT_MESSAGES,
                ASSISTANT_CONDITION + " AND content = ?", new Object[]{noDocReply}, start, end);
    }

    public List<Map<String, Object>> activeUsersByDay(Date start, Date end) {
        return distinctUsers("to_char(create_time,'YYYY-MM-DD')", "d", start, end);
    }

    // ==================== 按小时分组 ====================

    public List<Map<String, Object>> conversationsByHour(Date start, Date end) {
        return group("to_char(create_time,'YYYY-MM-DD HH24:00:00')", "h",
                CONVERSATIONS, AGENT_CONVERSATIONS, null, start, end);
    }

    public List<Map<String, Object>> messagesByHour(Date start, Date end) {
        return group("to_char(create_time,'YYYY-MM-DD HH24:00:00')", "h",
                MESSAGES, AGENT_MESSAGES, null, start, end);
    }

    public List<Map<String, Object>> assistantMessagesByHour(Date start, Date end) {
        return group("to_char(create_time,'YYYY-MM-DD HH24:00:00')", "h",
                MESSAGES, AGENT_MESSAGES, ASSISTANT_CONDITION, start, end);
    }

    public List<Map<String, Object>> noDocMessagesByHour(Date start, Date end, String noDocReply) {
        return group("to_char(create_time,'YYYY-MM-DD HH24:00:00')", "h",
                MESSAGES, AGENT_MESSAGES, ASSISTANT_CONDITION + " AND content = ?",
                new Object[]{noDocReply}, start, end);
    }

    public List<Map<String, Object>> activeUsersByHour(Date start, Date end) {
        return distinctUsers("to_char(create_time,'YYYY-MM-DD HH24:00:00')", "h", start, end);
    }

    // ==================== 内部实现 ====================

    private long sumAll(String table, String agentTable) {
        String sql = "SELECT (SELECT count(*) FROM " + table + ")"
                + " + (SELECT count(*) FROM " + agentTable + ")";
        return queryLong(sql);
    }

    private long sumCounts(String table, String agentTable, String condition, Date start, Date end) {
        String suffix = condition == null ? "" : " AND " + condition;
        String sql = "SELECT (SELECT count(*) FROM " + table
                + " WHERE create_time >= ? AND create_time < ?" + suffix + ")"
                + " + (SELECT count(*) FROM " + agentTable
                + " WHERE create_time >= ? AND create_time < ?" + suffix + ")";
        return queryLong(sql, start, end, start, end);
    }

    /**
     * 两表按同一表达式分桶后合并同名桶
     */
    private List<Map<String, Object>> group(String timeExpr, String keyAlias,
                                            String table, String agentTable, String condition,
                                            Date start, Date end) {
        return group(timeExpr, keyAlias, table, agentTable, condition, new Object[0], start, end);
    }

    private List<Map<String, Object>> group(String timeExpr, String keyAlias,
                                            String table, String agentTable, String condition,
                                            Object[] extraArgs, Date start, Date end) {
        String suffix = condition == null ? "" : " AND " + condition;
        String sql = "SELECT k AS " + keyAlias + ", sum(cnt) AS cnt FROM ("
                + bucket(table, timeExpr, suffix) + " UNION ALL " + bucket(agentTable, timeExpr, suffix)
                + ") g GROUP BY k";
        Object[] args = new Object[4 + extraArgs.length * 2];
        args[0] = start;
        args[1] = end;
        System.arraycopy(extraArgs, 0, args, 2, extraArgs.length);
        args[2 + extraArgs.length] = start;
        args[3 + extraArgs.length] = end;
        return jdbcTemplate.queryForList(sql, args);
    }

    /**
     * 跨表去重的活跃人数分桶
     */
    private List<Map<String, Object>> distinctUsers(String timeExpr, String keyAlias, Date start, Date end) {
        String sql = "SELECT k AS " + keyAlias + ", count(DISTINCT user_id) AS cnt FROM ("
                + "SELECT " + timeExpr + " AS k, user_id FROM " + MESSAGES
                + " WHERE create_time >= ? AND create_time < ?"
                + " UNION ALL "
                + "SELECT " + timeExpr + " AS k, user_id FROM " + AGENT_MESSAGES
                + " WHERE create_time >= ? AND create_time < ?"
                + ") g GROUP BY k";
        return jdbcTemplate.queryForList(sql, start, end, start, end);
    }

    private String bucket(String table, String timeExpr, String suffix) {
        return "SELECT " + timeExpr + " AS k, count(*) AS cnt FROM " + table
                + " WHERE create_time >= ? AND create_time < ?" + suffix + " GROUP BY k";
    }

    private long queryLong(String sql, Object... args) {
        Long value = jdbcTemplate.queryForObject(sql, Long.class, args);
        return value == null ? 0L : value;
    }
}
