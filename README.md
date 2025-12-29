# Moodle MCP Server

Connect AI agents to your Moodle site — administer, analyse, and automate with natural language.

## Overview

Model Context Protocol (MCP) is an open standard that enables large language models and AI agents to communicate with external data, applications, and tools. The **Moodle MCP Server** implements this protocol to execute **Moodle web services** directly from your preferred AI chat using your model of choice. Connect other MCP servers to extend capabilities and chain with retrieval, generation, or analysis tools.

Find detailed documentation and examples on [https://lmscloud.io/products/moodle-mcp/](https://lmscloud.io/products/moodle-mcp/)

## How to use

### Install uv (package manager) if not installed

For macOS/Linux:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

For Windows refer to: [https://docs.astral.sh/uv/getting-started/installation/](https://docs.astral.sh/uv/getting-started/installation/)

### Add MCP server to your preferred AI chat

Replace environment variables in the example below with your Moodle site URL and a valid web service token.
We recommend also adding the `unix_timestamps_mcp` server for better time handling.

```json
{
  "mcpServers": {
    "Moodle MCP": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/lmscloud-io/moodle-mcp-server",
        "moodle-mcp-server"
      ],
      "env": {
        "MOODLE": "https://your-moodle-site.com",
        "TOKEN": "your_webservice_token"
      }
    },
    "unix_timestamps_mcp": {
      "command": "npx",
      "args": ["-y", "github:Ivor/unix-timestamps-mcp"]
    }
  }
}
```

## License

This project is licensed under the GNU General Public License v3.0 or later - see the [LICENSE](LICENSE) file for details.

## Links

- **Website**: https://lmscloud.io/products/moodle-mcp/
- **Repository**: https://github.com/lmscloud-io/moodle-mcp-server
- **Issue Tracker**: https://github.com/lmscloud-io/moodle-mcp-server/issues
- **Moodle**: https://moodle.org
- **Model Context Protocol**: https://modelcontextprotocol.io
