"""Tests for configuration loading and parsing."""

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

from mcp_gateway.config import (
    find_config_file,
    load_servers_config_from_path,
    load_config,
    get_tool_params_description,
    Constants,
)


@pytest.fixture
def temp_config_dir(tmp_path: Path):
    """Create a temporary directory for config files."""
    return tmp_path


class TestFindConfigFile:
    """Tests for find_config_file function."""

    def test_finds_existing_file(self, temp_config_dir: Path) -> None:
        config_file = temp_config_dir / "mcp.json"
        config_file.write_text("{}")
        result = find_config_file(str(config_file))
        assert result is not None
        assert result.is_file()

    def test_returns_none_for_missing_file(self, temp_config_dir: Path) -> None:
        config_file = temp_config_dir / "nonexistent.json"
        result = find_config_file(str(config_file))
        assert result is None

    def test_resolves_absolute_path(self, temp_config_dir: Path) -> None:
        config_file = temp_config_dir / "mcp.json"
        config_file.write_text("{}")
        result = find_config_file(str(config_file))
        assert result is not None
        assert result.is_absolute()


class TestLoadServersConfigFromPath:
    """Tests for load_servers_config_from_path function."""

    def test_loads_valid_config(self, temp_config_dir: Path) -> None:
        config = {
            "mcpServers": {
                "mcp-gateway": {
                    "command": "mcp-gateway",
                    "args": ["--mcp-json-path", "test"],
                    "servers": {
                        "filesystem": {
                            "command": "npx",
                            "args": ["-y", "@modelcontextprotocol/server-filesystem"],
                        }
                    },
                }
            }
        }
        config_file = temp_config_dir / "mcp.json"
        config_file.write_text(json.dumps(config))

        result = load_servers_config_from_path(config_file)
        assert "filesystem" in result
        assert result["filesystem"]["command"] == "npx"

    def test_returns_empty_for_missing_mcp_servers(self, temp_config_dir: Path) -> None:
        config = {"other_key": {}}
        config_file = temp_config_dir / "mcp.json"
        config_file.write_text(json.dumps(config))

        result = load_servers_config_from_path(config_file)
        assert result == {}

    def test_returns_empty_for_empty_servers(self, temp_config_dir: Path) -> None:
        config = {"mcpServers": {"mcp-gateway": {"command": "mcp-gateway", "servers": {}}}}
        config_file = temp_config_dir / "mcp.json"
        config_file.write_text(json.dumps(config))

        result = load_servers_config_from_path(config_file)
        assert result == {}

    def test_returns_empty_for_missing_servers_key(self, temp_config_dir: Path) -> None:
        config = {"mcpServers": {"mcp-gateway": {"command": "mcp-gateway"}}}
        config_file = temp_config_dir / "mcp.json"
        config_file.write_text(json.dumps(config))

        result = load_servers_config_from_path(config_file)
        assert result == {}

    def test_raises_on_invalid_json(self, temp_config_dir: Path) -> None:
        config_file = temp_config_dir / "mcp.json"
        config_file.write_text("not valid json {{{")

        with pytest.raises(json.JSONDecodeError):
            load_servers_config_from_path(config_file)


class TestLoadConfig:
    """Tests for load_config function."""

    def test_returns_empty_for_missing_file(self, temp_config_dir: Path) -> None:
        result = load_config(str(temp_config_dir / "nonexistent.json"))
        assert result == {}

    def test_loads_valid_config(self, temp_config_dir: Path) -> None:
        config = {
            "mcpServers": {
                "mcp-gateway": {
                    "command": "mcp-gateway",
                    "servers": {"my_server": {"command": "test"}},
                }
            }
        }
        config_file = temp_config_dir / "mcp.json"
        config_file.write_text(json.dumps(config))

        result = load_config(str(config_file))
        assert "my_server" in result


class TestConstants:
    """Tests for Constants class."""

    def test_servers_constant(self) -> None:
        assert Constants.SERVERS == "servers"


class TestGetToolParamsDescription:
    """Tests for get_tool_params_description function."""

    def test_extracts_string_params(self) -> None:
        tool = MagicMock()
        type(tool).inputSchema = MagicMock(
            return_value={
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "The file to read",
                    }
                }
            }
        )
        tool.inputSchema = {
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "The file to read",
                }
            }
        }

        params = get_tool_params_description(tool)
        assert len(params) == 1
        assert params[0][0] == "filename"
        assert params[0][1] == str
        assert params[0][2] == "The file to read"

    def test_extracts_multiple_params(self) -> None:
        tool = MagicMock()
        tool.inputSchema = {
            "properties": {
                "name": {"type": "string", "description": "Name"},
                "count": {"type": "integer", "description": "Count"},
                "active": {"type": "boolean", "description": "Active flag"},
            }
        }

        params = get_tool_params_description(tool)
        assert len(params) == 3

    def test_returns_empty_for_no_schema(self) -> None:
        tool = MagicMock()
        tool.inputSchema = None

        params = get_tool_params_description(tool)
        assert params == []

    def test_returns_empty_for_no_properties(self) -> None:
        tool = MagicMock()
        tool.inputSchema = {}

        params = get_tool_params_description(tool)
        assert params == []
