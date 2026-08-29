# MCP-Proxy Tests

This directory contains tests for the MCP-Proxy project.

## Running Tests

To run all tests:

```bash
python -m pytest
```

To run a specific test file:

```bash
python -m pytest tests/test_basic_guardrail.py
```

## Test Structure

- `test_basic_guardrail.py`: Basic tests for guardrail functionality
- `simple_pii_example.py`: Example script demonstrating PII detection

## Adding New Tests

When adding new tests, please follow these guidelines:

1. Use proper type annotations and docstrings
2. Properly configure logging using the standard logging module
3. Use pytest fixtures and markers appropriately
4. Follow the existing patterns for interacting with the API
5. Skip tests appropriately when external dependencies are not available
