import pytest
import logging
from typing import Dict, List, Set
from mcp_gateway.plugins.manager import (
    _PLUGIN_REGISTRY,
    _PLUGIN_NAME_TO_INFO,
    discover_plugins,
)


@pytest.fixture(scope="module")
def plugin_registry() -> Dict[str, List]:
    """
    Fixture providing access to the plugin registry.

    Returns:
        Dict mapping plugin types to lists of plugin classes
    """
    # Ensure plugins are discovered
    discover_plugins()
    return _PLUGIN_REGISTRY


@pytest.fixture(scope="module")
def plugin_name_mapping() -> Dict[str, Dict]:
    """
    Fixture providing access to the plugin name to class mapping.

    Returns:
        Dict mapping plugin names to plugin information
    """
    # Ensure plugins are discovered
    discover_plugins()
    return _PLUGIN_NAME_TO_INFO


def test_no_duplicate_plugin_names(
    plugin_registry: Dict[str, List], plugin_name_mapping: Dict[str, Dict]
) -> None:
    """
    Test that there are no plugins with the same name.

    This test verifies that each plugin has a unique name within its type category
    to prevent conflicts in plugin registration and selection.

    Args:
        plugin_registry: The plugin registry mapping plugin types to plugin classes
        plugin_name_mapping: The mapping of plugin names to plugin information
    """
    # Check all plugin types
    for plugin_type, plugins in plugin_registry.items():
        # Skip if no plugins of this type
        if not plugins:
            continue

        # Get plugin names for this type
        plugin_names: Set[str] = set()
        duplicate_names: List[str] = []

        for plugin_cls in plugins:
            # Get plugin name (lowercase for case-insensitive comparison)
            plugin_name = getattr(plugin_cls, "plugin_name", "").lower()
            if not plugin_name:
                plugin_name = plugin_cls.__name__.lower()

            # Check for duplicates
            if plugin_name in plugin_names:
                duplicate_names.append(plugin_name)
            else:
                plugin_names.add(plugin_name)

        # Assert no duplicates found
        assert not duplicate_names, (
            f"Duplicate plugin names found for type '{plugin_type}': {duplicate_names}"
        )

    # Check the name-to-info mapping for any inconsistencies
    plugin_classes = set()
    for plugin_name, info in plugin_name_mapping.items():
        plugin_class = info.get("class")
        if plugin_class in plugin_classes:
            # This is fine as the same class can be registered with multiple names
            continue
        plugin_classes.add(plugin_class)

    # Log the successful validation
    logging.info(
        f"Validated {len(plugin_classes)} unique plugin classes with no duplicate names"
    )
