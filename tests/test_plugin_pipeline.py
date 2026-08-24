"""Tests for the plugin manager pipeline - chaining, blocking, error handling."""

import pytest
from typing import Any, Dict, Optional
from unittest.mock import MagicMock, patch

from mcp_gateway.plugins.base import Plugin, PluginContext, GuardrailPlugin, TracingPlugin


class MockGuardrailPlugin(GuardrailPlugin):
    """A mock guardrail plugin for testing."""

    plugin_name = "mock_guardrail"

    def __init__(self, transform_fn=None, block_request=False, block_response=False):
        self.transform_fn = transform_fn
        self.block_request = block_request
        self.block_response = block_response
        self.loaded = False

    def load(self, config=None):
        self.loaded = True

    def process_request(self, context: PluginContext):
        if self.block_request:
            return None
        if self.transform_fn and context.arguments:
            return {k: self.transform_fn(v) for k, v in context.arguments.items()}
        return context.arguments

    def process_response(self, context: PluginContext):
        if self.block_response:
            return None
        return context.response


class MockTracingPlugin(TracingPlugin):
    """A mock tracing plugin for testing."""

    plugin_name = "mock_tracing"

    def __init__(self):
        self.request_traced = False
        self.response_traced = False

    def load(self, config=None):
        pass

    def process_request(self, context: PluginContext):
        self.request_traced = True
        return context.arguments

    def process_response(self, context: PluginContext):
        self.response_traced = True
        return context.response


@pytest.fixture
def plugin_manager():
    """Create a fresh PluginManager for each test, with mocked plugin discovery."""
    with patch("mcp_gateway.plugins.manager.discover_plugins"):
        from mcp_gateway.plugins.manager import PluginManager
        return PluginManager(enabled_types=[], enabled_plugins={})


class TestPluginManagerInit:
    """Tests for PluginManager initialization."""

    def test_init_with_empty_config(self) -> None:
        with patch("mcp_gateway.plugins.manager.discover_plugins"):
            from mcp_gateway.plugins.manager import PluginManager
            pm = PluginManager(enabled_types=[], enabled_plugins={})
            assert pm.enabled_types == []
            assert pm.enabled_plugins == {}

    def test_init_with_guardrail_type(self) -> None:
        with patch("mcp_gateway.plugins.manager.discover_plugins"):
            from mcp_gateway.plugins.manager import PluginManager
            pm = PluginManager(
                enabled_types=["guardrail"],
                enabled_plugins={"guardrail": ["mock_guardrail"]},
            )
            assert "guardrail" in pm.enabled_types


class TestPluginManagerPipeline:
    """Tests for the plugin processing pipeline."""

    @pytest.mark.asyncio
    async def test_process_request_passes_through(
        self, plugin_manager
    ) -> None:
        """Arguments should pass through when no plugins modify them."""
        context = PluginContext(
            server_name="test",
            capability_type="tool",
            capability_name="test_tool",
            arguments={"key": "value"},
        )

        result = await plugin_manager.process_request(context)
        assert result == {"key": "value"}

    @pytest.mark.asyncio
    async def test_process_response_passes_through(
        self, plugin_manager
    ) -> None:
        """Response should pass through when no plugins modify it."""
        context = PluginContext(
            server_name="test",
            capability_type="tool",
            capability_name="test_tool",
            arguments={},
            response="original_response",
        )

        result = await plugin_manager.process_response(context)
        assert result == "original_response"


class TestPluginContext:
    """Tests for PluginContext."""

    def test_creation(self) -> None:
        context = PluginContext(
            server_name="server",
            capability_type="tool",
            capability_name="my_tool",
            arguments={"arg1": "val1"},
            response="response_data",
        )
        assert context.server_name == "server"
        assert context.capability_type == "tool"
        assert context.capability_name == "my_tool"
        assert context.arguments == {"arg1": "val1"}
        assert context.response == "response_data"

    def test_to_dict(self) -> None:
        context = PluginContext(
            server_name="server",
            capability_type="tool",
            capability_name="my_tool",
            arguments={"key": "value"},
        )
        d = context.to_dict()
        assert d["server_name"] == "server"
        assert d["capability_type"] == "tool"
        assert d["arguments"] == {"key": "value"}

    def test_replace_arguments(self) -> None:
        context = PluginContext(
            server_name="server",
            capability_type="tool",
            capability_name="my_tool",
            arguments={"old": "data"},
        )
        context._replace({"new": "data"})
        assert context.arguments == {"new": "data"}
