import json
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Optional

from fastmcp import Context
from fastmcp.exceptions import FastMCPError
from fastmcp.server.middleware.middleware import Middleware, MiddlewareContext
from fastmcp.tools.tool import ToolResult
from fastmcp.tools.tool import Tool
from typing_extensions import override

from .tools import MoodleTool
from .utils import Utils

@dataclass
class AccessCredentials:
    url: str
    token: str

class MoodleMiddleware(Middleware):
    """Middleware class for Moodle API communication."""

    def __init__(self) -> None:

        self._all_client_tools: dict[str, Tool] = {}

    # async def on_initialize(
    #     self,
    #     context: MiddlewareContext,
    #     call_next,
    # ) -> None:
    #     return await call_next(context)


    # async def elicit_credentials(self, context: MiddlewareContext):
    #     """Eliciting credentials is not used at the moment, it does not work in HTTP and there is no way to store the values"""
    #     # Get token/baseurl from HTTP headers first
    #     headers = get_http_headers()
    #     baseurl, wstoken = self.get_credentials(context.fastmcp_context)
    #     #wstoken = headers.get("authorization", "").split(" ")[-1] if wstoken == "" else wstoken
    #     wstoken = headers.get("x-token", "") if wstoken == "" else wstoken
    #     baseurl = self.clean_baseurl(headers.get("x-moodle", ""), True) if baseurl == "" else baseurl

    #     # Then try environment variables
    #     wstoken = os.environ.get("TOKEN", "").strip() if wstoken == "" else wstoken
    #     baseurl = self.clean_baseurl(os.environ.get("MOODLE", ""), True) if baseurl == "" else baseurl

    #     if context.fastmcp_context == None or context.fastmcp_context.request_context == None:
    #         # To satisfy the checker - we cannot elicit without a request context
    #         # In fact, the elicitations do not work at all in fastmcp cloud with http transport
    #         context.fastmcp_context.set_state("moodle_wstoken", wstoken)
    #         context.fastmcp_context.set_state("moodle_baseurl", baseurl)
    #         return baseurl, wstoken

    #     if baseurl == "" and wstoken == "":
    #         # Both URL and token are missing - ask for both at once
    #         res = await context.fastmcp_context.elicit("Please provide your Moodle site URL and web service token.", response_type=AccessCredentials)
    #         if res.action == "accept":
    #             url = self.clean_baseurl(res.data.url)
    #             if self.is_valid_url(url, context):
    #                 baseurl = url
    #                 wstoken = res.data.token
    #     elif baseurl == "":
    #         # Only URL is missing
    #         res = await context.fastmcp_context.elicit("What is your Moodle site URL?", response_type=str)
    #         if res.action == "accept":
    #             url = self.clean_baseurl(res.data)
    #             if self.is_valid_url(url, context):
    #                 baseurl = url
    #     elif wstoken == "":
    #         # Only token is missing
    #         res = await context.fastmcp_context.elicit(f"What is your your token to execute web services on {baseurl} ?", response_type=str)
    #         if res.action == "accept":
    #             wstoken=res.data
    #     context.fastmcp_context.set_state("moodle_wstoken", wstoken)
    #     context.fastmcp_context.set_state("moodle_baseurl", baseurl)
    #     return baseurl, wstoken


    @override
    async def on_list_tools(
        self,
        context: MiddlewareContext,
        call_next,
    ) -> Sequence[Tool]:
        """Inject tools into the response."""
        Utils.verify_has_credentials(context.fastmcp_context)
        # await context.fastmcp_context.info(f"MoodleMiddleware: on_list_tools called, wstoken='{wstoken}', baseurl='{baseurl}', headers={get_http_headers()}'")
        #baseurl, wstoken = await self.elicit_credentials(context)
        # await context.fastmcp_context.info(f"After elicit, wstoken='{wstoken}', baseurl='{baseurl}'")

        #self.logger.error(f"Requesting list of available web services from {baseurl}...")
        #await context.fastmcp_context.info(f"Loading available web services from {baseurl}...")
        client_tools = await self.load_tools(context.fastmcp_context)
        return [*client_tools, *await call_next(context)]


    @override
    async def on_call_tool(
        self,
        context: MiddlewareContext,
        call_next,
    ) -> ToolResult:
        """Intercept tool calls to injected tools."""
        Utils.verify_has_credentials(context.fastmcp_context)
        tool_name = context.message.name
        arguments = context.message.arguments or {}

        # We can potentially access the tool object to check its metadata, but it is not available for dynamically injected tools
        # if context.fastmcp_context:
        #     try:
        #         tool = await context.fastmcp_context.fastmcp.get_tool(context.message.name)
        #     except Exception as e:
        #         # Tool not found or other error - let execution continue
        #         # and handle the error naturally
        #         pass

        if tool_name == "upload_files":
            return await MoodleTool.run_moodle_tool_upload(arguments)
        elif tool_name == "download_file":
            return await MoodleTool.run_moodle_tool_download(arguments)

        if not tool_name in self._all_client_tools:
            # Something somewhere expired or server restarted. We need to send an error and tell the client to re-request list of tools.
            await context.fastmcp_context.send_tool_list_changed()
            raise FastMCPError(f"Something went wrong, there is a possible cache issue in the MCP server. Please repeat the request.")

        tool = self._all_client_tools[tool_name]
        return await MoodleTool.run_moodle_tool(
            name=tool_name,
            arguments=arguments,
            # We pass output_schema so we can fix empty arrays in the result. A bit stupid that because of Moodle bug we need to
            # add a huge layer of caching.
            output_schema=tool.output_schema,
        )


    async def load_functions_from_wsdiscovery(self, ctx: Context):
        """If tool_wsdiscovery plugin is installed on the Moodle site, use it to get the list of available functions."""
        baseurl, wstoken = Utils.verify_has_credentials(ctx)

        structure = Utils.request_post_json(f"{baseurl}/admin/tool/wsdiscovery/moodle.php",
                                    headers={'Authorization': 'Bearer ' + wstoken})
        functions = structure.get("functions", [])
        return self.prepare_schemas({"functions": functions})


    async def load_functions_from_site_info(self, ctx: Context):
        """Request a list of available functions using core_webservice_get_site_info external function (fallback if tool_wsdiscovery is not installed)."""
        result = await MoodleTool.run_moodle_tool(
            name="core_webservice_get_site_info",
            arguments={},
            output_schema=None)
        content, structured_content = result.to_mcp_result()
        function_names = structured_content.get("result", {}).get("functions", [])
        return self.prepare_schemas({"functionnames": function_names})


    def prepare_schemas(self, payload):
        """Request the function schemas from MCP Ready lookup service. Your credentials are never sent to this service."""
        jsonresult = Utils.request_post_json("https://api.mcp-ready.lmscloud.io/noauth/lookup", json=payload)
        return jsonresult.get("functions", []) if isinstance(jsonresult, dict) else []


    async def load_tools(self, ctx: Context) -> list[Tool]:
        client_tools = []

        try:
            functions = await self.load_functions_from_wsdiscovery(ctx)
        except FastMCPError as e1:
            # await ctx.warning(f"Failed to load functions from Moodle site using wsdiscovery method: {str(e1)}. Trying site info method...")
            try:
                functions = await self.load_functions_from_site_info(ctx)
            except FastMCPError as e2:
                raise FastMCPError("Unable to load available external functions from your Moodle site. "+
                                   "Make sure that you either installed tool_wsdiscovery plugin or enabled function core_webservice_get_site_info. \n\n" +
                                   f"More details about the error:\n1. {str(e1)}\n2. {str(e2)}")

        for toolinfo in functions:
            #await ctx.info("Registering tool:" + json.dumps(toolinfo))
            tool = Tool(
                name=toolinfo.get("name"),
                description=toolinfo.get("description"),
                parameters=toolinfo.get("inputSchema", None),
                output_schema=toolinfo.get("outputSchema", None),
                enabled=True,
                # meta={"output_schema_hash": hashlib.sha256(json.dumps(result).encode('utf-8')).hexdigest()},
            )
            # TODO what if two clients need the same tool with different schemas? We need to either add some hash to the tool name or add a hash as a tag.
            client_tools.append(tool)
            self._all_client_tools[tool.name] = tool

        return client_tools