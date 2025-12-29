from fastmcp import FastMCP, Context
from .middleware import MoodleMiddleware

def main():

    mcp = FastMCP(
        name="Moodle MCP Server",
        instructions="Allows to execute web services from your Moodle site.",
        version="0.1.0",
        #website_url="",
        #icons=[],
        )
    middleware = MoodleMiddleware()
    mcp.add_middleware(middleware)
    mcp.run()



if __name__ == "__main__":
    main()
