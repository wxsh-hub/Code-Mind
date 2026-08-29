"""Tests for the sanitization dispatch layer."""

import pytest
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, MagicMock

from mcp import types

from mcp_gateway.sanitizers import (
    SanitizationError,
    sanitize_request,
    sanitize_response,
    sanitize_resource_read,
    sanitize_tool_call_args,
    sanitize_tool_call_result,
)
from mcp_gateway.plugins.base import PluginContext
from mcp_gateway.plugins.manager import PluginManager


@pytest.fixture
def mock_plugin_manager() -> PluginManager:
    """Create a mock PluginManager."""
    pm = MagicMock(spec=PluginManager)
    pm.process_request = AsyncMock()
    pm.process_response = AsyncMock()
    return pm


@pytest.fixture
def sample_call_tool_result() -> types.CallToolResult:
    """Create a sample CallToolResult."""
    return types.CallToolResult(
        content=[types.TextContent(type="text", text="Hello World")]
    )


class TestSanitizeRequest:
    """Tests for sanitize_request function."""

    @pytest.mark.asyncio
    async def test_returns_sanitized_args(
        self, mock_plugin_manager: PluginManager
    ) -> None:
        """Plugin manager returns sanitized args, sanitize_request should pass them through."""
        expected_args = {"key": "sanitized_value"}
        mock_plugin_manager.process_request.return_value = expected_args

        result = await sanitize_request(
            plugin_manager=mock_plugin_manager,
            server_name="test_server",
            capability_type="tool",
            name="test_tool",
            arguments={"key": "value"},
        )

        assert result == expected_args

    @pytest.mark.asyncio
    async def test_returns_none_when_blocked(
        self, mock_plugin_manager: PluginManager
    ) -> None:
        """Plugin manager returns None (blocked), sanitize_request should return None."""
        mock_plugin_manager.process_request.return_value = None

        result = await sanitize_request(
            plugin_manager=mock_plugin_manager,
            server_name="test_server",
            capability_type="tool",
            name="test_tool",
            arguments={"key": "value"},
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_blocks_on_plugin_error(
        self, mock_plugin_manager: PluginManager
    ) -> None:
        """Plugin manager raises exception, sanitize_request should block (return None)."""
        mock_plugin_manager.process_request.side_effect = RuntimeError("Plugin crash")

        result = await sanitize_request(
            plugin_manager=mock_plugin_manager,
            server_name="test_server",
            capability_type="tool",
            name="test_tool",
            arguments={"key": "value"},
        )

        assert result is None


class TestSanitizeResponse:
    """Tests for sanitize_response function."""

    @pytest.mark.asyncio
    async def test_returns_sanitized_response(
        self,
        mock_plugin_manager: PluginManager,
        sample_call_tool_result: types.CallToolResult,
    ) -> None:
        """Plugin manager returns sanitized response."""
        mock_plugin_manager.process_response.return_value = sample_call_tool_result

        result = await sanitize_response(
            plugin_manager=mock_plugin_manager,
            server_name="test_server",
            capability_type="tool",
            name="test_tool",
            response=sample_call_tool_result,
        )

        assert result == sample_call_tool_result

    @pytest.mark.asyncio
    async def test_raises_sanitization_error(
        self,
        mock_plugin_manager: PluginManager,
        sample_call_tool_result: types.CallToolResult,
    ) -> None:
        """SanitizationError from plugin should propagate."""
        mock_plugin_manager.process_response.side_effect = SanitizationError(
            "Policy violation"
        )

        with pytest.raises(SanitizationError, match="Policy violation"):
            await sanitize_response(
                plugin_manager=mock_plugin_manager,
                server_name="test_server",
                capability_type="tool",
                name="test_tool",
                response=sample_call_tool_result,
            )

    @pytest.mark.asyncio
    async def test_returns_original_on_generic_error(
        self,
        mock_plugin_manager: PluginManager,
        sample_call_tool_result: types.CallToolResult,
    ) -> None:
        """Generic error from plugin should return original response."""
        mock_plugin_manager.process_response.side_effect = RuntimeError("Crash")

        result = await sanitize_response(
            plugin_manager=mock_plugin_manager,
            server_name="test_server",
            capability_type="tool",
            name="test_tool",
            response=sample_call_tool_result,
        )

        assert result == sample_call_tool_result


class TestSanitizeToolCallArgs:
    """Tests for sanitize_tool_call_args wrapper."""

    @pytest.mark.asyncio
    async def test_delegates_to_sanitize_request(
        self, mock_plugin_manager: PluginManager
    ) -> None:
        """Should delegate to sanitize_request with capability_type='tool'."""
        mock_plugin_manager.process_request.return_value = {"clean": True}

        result = await sanitize_tool_call_args(
            plugin_manager=mock_plugin_manager,
            server_name="server",
            tool_name="my_tool",
            arguments={"dirty": "data"},
        )

        assert result == {"clean": True}


class TestSanitizeToolCallResult:
    """Tests for sanitize_tool_call_result wrapper."""

    @pytest.mark.asyncio
    async def test_returns_call_tool_result(
        self,
        mock_plugin_manager: PluginManager,
        sample_call_tool_result: types.CallToolResult,
    ) -> None:
        """Should return CallToolResult when plugin returns CallToolResult."""
        mock_plugin_manager.process_response.return_value = sample_call_tool_result

        result = await sanitize_tool_call_result(
            plugin_manager=mock_plugin_manager,
            server_name="server",
            tool_name="my_tool",
            result=sample_call_tool_result,
        )

        assert isinstance(result, types.CallToolResult)

    @pytest.mark.asyncio
    async def test_returns_original_on_type_mismatch(
        self,
        mock_plugin_manager: PluginManager,
        sample_call_tool_result: types.CallToolResult,
    ) -> None:
        """Should return original result if plugin returns wrong type."""
        mock_plugin_manager.process_response.return_value = "not a CallToolResult"

        result = await sanitize_tool_call_result(
            plugin_manager=mock_plugin_manager,
            server_name="server",
            tool_name="my_tool",
            result=sample_call_tool_result,
        )

        assert result == sample_call_tool_result


class TestSanitizeResourceRead:
    """Tests for sanitize_resource_read wrapper."""

    @pytest.mark.asyncio
    async def test_returns_sanitized_tuple(
        self, mock_plugin_manager: PluginManager
    ) -> None:
        """Should return (bytes, mime_type) tuple."""
        mock_plugin_manager.process_response.return_value = (
            b"clean content",
            "text/plain",
        )

        result = await sanitize_resource_read(
            plugin_manager=mock_plugin_manager,
            server_name="server",
            uri="file:///test.txt",
            content=b"dirty content",
            mime_type="text/plain",
        )

        assert result == (b"clean content", "text/plain")

    @pytest.mark.asyncio
    async def test_returns_original_on_type_mismatch(
        self, mock_plugin_manager: PluginManager
    ) -> None:
        """Should return original content if plugin returns wrong type."""
        mock_plugin_manager.process_response.return_value = "not a tuple"

        result = await sanitize_resource_read(
            plugin_manager=mock_plugin_manager,
            server_name="server",
            uri="file:///test.txt",
            content=b"original content",
            mime_type="text/plain",
        )

        assert result == (b"original content", "text/plain")
