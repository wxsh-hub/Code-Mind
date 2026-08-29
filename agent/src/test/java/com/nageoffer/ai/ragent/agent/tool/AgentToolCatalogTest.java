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

package com.nageoffer.ai.ragent.agent.tool;

import com.nageoffer.ai.ragent.agent.service.AgentConversationService;
import com.nageoffer.ai.ragent.rag.core.intent.IntentNode;
import com.nageoffer.ai.ragent.rag.core.intent.IntentNodeRegistry;
import com.nageoffer.ai.ragent.rag.core.mcp.McpToolExecutor;
import com.nageoffer.ai.ragent.rag.core.mcp.McpToolRegistry;
import com.nageoffer.ai.ragent.rag.core.prompt.AgentPromptResolver;
import com.nageoffer.ai.ragent.rag.core.prompt.AgentPromptSlot;
import com.nageoffer.ai.ragent.rag.enums.IntentKind;
import com.nageoffer.ai.ragent.rag.service.KnowledgeSearchFacade;
import io.agentscope.core.tool.Toolkit;
import io.modelcontextprotocol.spec.McpSchema.CallToolResult;
import io.modelcontextprotocol.spec.McpSchema.JsonSchema;
import io.modelcontextprotocol.spec.McpSchema.Tool;
import io.modelcontextprotocol.spec.McpSchema.ToolAnnotations;
import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

class AgentToolCatalogTest {

    @Test
    void shouldRegisterKnowledgeAndIntentTreeConfiguredMcpToolsOnly() {
        IntentNodeRegistry intentNodeRegistry = mock(IntentNodeRegistry.class);
        McpToolRegistry mcpToolRegistry = mock(McpToolRegistry.class);
        when(intentNodeRegistry.listMcpToolNodes()).thenReturn(List.of(
                mcpNode("sales", "销售查询", "查询实时销售数据", "sales_query"),
                mcpNode("missing", "缺失工具", "当前没有执行器", "missing_query")));
        when(mcpToolRegistry.listAllExecutors()).thenReturn(List.of(
                executor("sales_query", "MCP 服务端描述"),
                executor("unconfigured_query", "未配置到意图树")));
        AgentPromptResolver agentPromptResolver = mock(AgentPromptResolver.class);
        when(agentPromptResolver.resolve(AgentPromptSlot.KNOWLEDGE_TOOL_DESCRIPTION))
                .thenReturn("当前 Agent 的知识库工具描述");

        AgentToolCatalog catalog = new AgentToolCatalog(
                mock(KnowledgeSearchFacade.class),
                mock(AgentConversationService.class),
                intentNodeRegistry,
                mcpToolRegistry,
                agentPromptResolver);

        AgentToolCatalog.ResolvedCatalog resolved = catalog.resolve();
        Toolkit toolkit = catalog.buildToolkit(resolved);

        assertThat(toolkit.getToolNames())
                .containsExactlyInAnyOrder(KnowledgeSearchTool.TOOL_NAME, "sales_query");
        assertThat(toolkit.getTool(KnowledgeSearchTool.TOOL_NAME).getDescription())
                .isEqualTo("当前 Agent 的知识库工具描述");
        assertThat(toolkit.getTool("sales_query").getDescription()).isEqualTo("查询实时销售数据");
        assertThat(resolved.displayNameOf("sales_query")).isEqualTo("销售查询");
        assertThat(catalog.mcpToolCount()).isEqualTo(1);
        assertThat(resolved.fingerprint().knowledgeToolDescription())
                .isEqualTo("当前 Agent 的知识库工具描述");
        assertThat(resolved.fingerprint().mcpTools())
                .singleElement()
                .satisfies(tool -> assertThat(tool.toolId()).isEqualTo("sales_query"));
    }

    @Test
    void shouldTreatMcpToolWithoutReadOnlyHintAsWritable() {
        Toolkit toolkit = buildToolkitFor(
                executor("no_annotation_query", "无 annotation", null),
                executor("blank_hint_query", "有 annotation 但未声明 readOnlyHint",
                        new ToolAnnotations(null, null, null, null, null, null)));

        assertThat(toolkit.getTool("no_annotation_query").isReadOnly()).isFalse();
        assertThat(toolkit.getTool("blank_hint_query").isReadOnly()).isFalse();
        // 知识库工具的只读是真的，不随 MCP 透传变化
        assertThat(toolkit.getTool(KnowledgeSearchTool.TOOL_NAME).isReadOnly()).isTrue();
    }

    @Test
    void shouldPassThroughMcpReadOnlyHint() {
        Toolkit toolkit = buildToolkitFor(
                executor("read_query", "只读工具", readOnlyHint(true)),
                executor("write_query", "写工具", readOnlyHint(false)));

        assertThat(toolkit.getTool("read_query").isReadOnly()).isTrue();
        assertThat(toolkit.getTool("write_query").isReadOnly()).isFalse();
    }

    private Toolkit buildToolkitFor(McpToolExecutor... executors) {
        List<McpToolExecutor> executorList = List.of(executors);
        IntentNodeRegistry intentNodeRegistry = mock(IntentNodeRegistry.class);
        when(intentNodeRegistry.listMcpToolNodes()).thenReturn(executorList.stream()
                .map(executor -> mcpNode(
                        executor.getToolId(), executor.getToolId(), "意图树描述", executor.getToolId()))
                .toList());
        McpToolRegistry mcpToolRegistry = mock(McpToolRegistry.class);
        when(mcpToolRegistry.listAllExecutors()).thenReturn(executorList);
        AgentPromptResolver agentPromptResolver = mock(AgentPromptResolver.class);
        when(agentPromptResolver.resolve(AgentPromptSlot.KNOWLEDGE_TOOL_DESCRIPTION))
                .thenReturn("当前 Agent 的知识库工具描述");

        AgentToolCatalog catalog = new AgentToolCatalog(
                mock(KnowledgeSearchFacade.class),
                mock(AgentConversationService.class),
                intentNodeRegistry,
                mcpToolRegistry,
                agentPromptResolver);
        return catalog.buildToolkit(catalog.resolve());
    }

    private ToolAnnotations readOnlyHint(boolean readOnly) {
        return new ToolAnnotations(null, readOnly, null, null, null, null);
    }

    private IntentNode mcpNode(String id, String name, String description, String toolId) {
        return IntentNode.builder()
                .id(id)
                .name(name)
                .description(description)
                .kind(IntentKind.MCP)
                .mcpToolId(toolId)
                .build();
    }

    private McpToolExecutor executor(String toolId, String description) {
        return executor(toolId, description, null);
    }

    private McpToolExecutor executor(String toolId, String description, ToolAnnotations annotations) {
        JsonSchema schema = new JsonSchema("object", Map.of(), List.of(), false, null, null);
        Tool tool = Tool.builder()
                .name(toolId)
                .description(description)
                .inputSchema(schema)
                .annotations(annotations)
                .build();
        return new McpToolExecutor() {
            @Override
            public Tool getToolDefinition() {
                return tool;
            }

            @Override
            public CallToolResult execute(Map<String, Object> parameters) {
                return null;
            }
        };
    }
}
