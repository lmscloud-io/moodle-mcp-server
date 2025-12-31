from fastmcp import FastMCP, Context
from moodle_mcp_server.middleware import MoodleMiddleware
from moodle_mcp_server import __version__


# Create the mcp instance at module level
mcp = FastMCP(
    name="Moodle MCP Server",
    instructions="Allows to execute web services from the Moodle site.",
    version=__version__,
    middleware=[MoodleMiddleware()],
    website_url="https://lmscloud.io/products/moodle-mcp/",
    icons=[MoodleMiddleware.icon]
)

def main():
    mcp.run()

if __name__ == "__main__":
    main()
