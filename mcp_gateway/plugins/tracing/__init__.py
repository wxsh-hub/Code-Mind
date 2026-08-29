"""Tracing plugins for MCP Gateway.

These plugins help monitor system activity by logging requests and responses.
"""

# Lazy import to avoid xetrack's multiprocessing.set_start_method("fork") crash on Windows
try:
    from mcp_gateway.plugins.tracing.xetrack import XetrackTracingPlugin

    __all__ = ["XetrackTracingPlugin"]
except (ImportError, ValueError) as e:
    import logging

    logging.getLogger(__name__).warning(
        f"XetrackTracingPlugin not available: {e}"
    )
    __all__ = []
