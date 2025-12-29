# Moodle MCP Server

A Model Context Protocol (MCP) server for integrating AI assistants with Moodle LMS.

## Overview

This MCP server enables AI assistants to interact with Moodle Learning Management System, providing capabilities for course management, user interactions, and educational content delivery through the standardized Model Context Protocol.

## Features

- **Moodle API Integration**: Direct integration with Moodle's web services API
- **MCP Protocol Support**: Built on FastMCP for efficient protocol handling
- **Extensible Architecture**: Easy to add new Moodle-specific tools and resources

## Installation

### From PyPI (once published)

```bash
pip install moodle-mcp-server
```

### From Source

```bash
git clone https://github.com/lmscloud-io/moodle-mcp-server.git
cd moodle-mcp-server
pip install -e .
```

## Usage

```python
from moodle_mcp_server import main

main()
```

## Configuration

[Add configuration details here once implemented]

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/lmscloud-io/moodle-mcp-server.git
cd moodle-mcp-server

# Install with uv
uv sync

# Or with pip
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

## Requirements

- Python >= 3.11
- Moodle instance with web services enabled
- Valid Moodle API token

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the GNU General Public License v3.0 or later - see the [LICENSE](LICENSE) file for details.

## Links

- **Repository**: https://github.com/lmscloud-io/moodle-mcp-server
- **Issue Tracker**: https://github.com/lmscloud-io/moodle-mcp-server/issues
- **Moodle**: https://moodle.org
- **Model Context Protocol**: https://modelcontextprotocol.io

## Acknowledgments

Built with [FastMCP](https://github.com/jlowin/fastmcp) - A fast, modern MCP server framework.
