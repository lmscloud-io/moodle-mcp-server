# Running Moodle MCP Server

## Quick Start

### Method 1: Using the command-line script (Recommended)

After installing, you can run the server using the `moodle-mcp-server` command:

```bash
# Using uv (development)
uv run moodle-mcp-server

# Or if installed system-wide
moodle-mcp-server
```

### Method 2: Using Python module

```bash
# Using uv (development)
uv run python -m moodle_mcp_server.main

# Or with the virtual environment activated
.venv/bin/python -m moodle_mcp_server.main
```

### Method 3: Direct Python execution

```bash
# Using uv (development)
uv run python src/moodle_mcp_server/main.py
```

## Configuration

The server requires Moodle credentials to be provided via:

1. **Environment variables:**
   ```bash
   export MOODLE="https://your-moodle-site.com"
   export TOKEN="your_webservice_token"
   uv run moodle-mcp-server
   ```

2. **HTTP headers (when using HTTP transport):**
   - `x-moodle`: Your Moodle site URL
   - `x-token`: Your web service token

## Development

### Install in editable mode

```bash
uv pip install -e .
```

### Run with auto-reload (for development)

```bash
uv run moodle-mcp-server
```

## MCP Client Integration

To use this server with an MCP client (like Claude Desktop), add it to your MCP configuration:

```json
{
  "mcpServers": {
    "moodle": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/moodle-mcp-server",
        "run",
        "moodle-mcp-server"
      ],
      "env": {
        "MOODLE": "https://your-moodle-site.com",
        "TOKEN": "your_webservice_token"
      }
    }
  }
}
```

Or if installed globally:

```json
{
  "mcpServers": {
    "moodle": {
      "command": "moodle-mcp-server",
      "env": {
        "MOODLE": "https://your-moodle-site.com",
        "TOKEN": "your_webservice_token"
      }
    }
  }
}
```

## Troubleshooting

### ModuleNotFoundError

If you get `ModuleNotFoundError: No module named 'moodle_mcp_server'`:
- Make sure you've installed the package: `uv pip install -e .`
- Or use `uv run` which handles the environment automatically

### Missing credentials

If you get an error about missing Moodle credentials:
- Set the `MOODLE` and `TOKEN` environment variables
- Or configure your MCP client to pass them via HTTP headers
