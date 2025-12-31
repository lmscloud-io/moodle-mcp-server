import hashlib
import json
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from fastmcp import Context
from fastmcp.exceptions import FastMCPError
from fastmcp.server.middleware.middleware import Middleware, MiddlewareContext
from fastmcp.tools.tool import Tool, ToolResult
from typing_extensions import override
from .tools import MoodleTool
from .utils import Utils
from mcp.types import Icon


@dataclass
class AccessCredentials:
    url: str
    token: str

class MoodleMiddleware(Middleware):
    """Middleware class for Moodle API communication."""

    moodleLogo = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+CiAgICA8cGF0aCBzdHlsZT0ibGluZS1oZWlnaHQ6bm9ybWFsO3RleHQtaW5kZW50OjA7dGV4dC1hbGlnbjpzdGFydDt0ZXh0LWRlY29yYXRpb24tbGluZTpub25lO3RleHQtZGVjb3JhdGlvbi1zdHlsZTpzb2xpZDt0ZXh0LWRlY29yYXRpb24tY29sb3I6IzAwMDt0ZXh0LXRyYW5zZm9ybTpub25lO2Jsb2NrLXByb2dyZXNzaW9uOnRiO2lzb2xhdGlvbjphdXRvO21peC1ibGVuZC1tb2RlOm5vcm1hbCIgZD0iTSAxNCAzIEwgNiA0IEwgMCA4IEwgMSA4IEwgMSAxOCBMIDIgMTggTCAyIDggTCA0LjAxMTcxODggOCBDIDQuMDA5NTAxMSA4LjA2NzQ2NDIgNCA4LjEyMzQ0NTYgNCA4LjE5MzM1OTQgQyA0IDkuMzc3MzU5NCA0LjMyMjI2NTYgMTAuMTk3MjY2IDQuMzIyMjY1NiAxMC4xOTcyNjYgTCA4Ljc2NTYyNSAxMS4yNjE3MTkgTCAxMi4wMTM2NzIgNy41ODc4OTA2IEMgMTIuMDEzNjcyIDcuNTg3ODkwNiAxMS43MTk2MjQgNi4zNjAzODQ1IDExLjA0ODgyOCA1LjQ1ODk4NDQgTCAxNCAzIHogTSAxOC41IDcgQyAxNi45MjkwMTIgNyAxNS41MDc2NDkgNy42NzQ4NzEyIDE0LjUwMTk1MyA4Ljc0NDE0MDYgQyAxNC4yNDM1ODggOC40NjkzOTggMTMuOTYxNjUxIDguMjE1NDU2OSAxMy42NTIzNDQgNy45OTgwNDY5IEwgMTEuNjMyODEyIDEwLjI4MzIwMyBDIDEyLjQ0MDgxMiAxMC42OTgyMDMgMTMgMTEuNTMxIDEzIDEyLjUgTCAxMyAyMCBMIDE2IDIwIEwgMTYgMTIuNSBDIDE2IDExLjEwMTc3NCAxNy4xMDE3NzQgMTAgMTguNSAxMCBDIDE5Ljg5ODIyNiAxMCAyMSAxMS4xMDE3NzQgMjEgMTIuNSBMIDIxIDIwIEwgMjQgMjAgTCAyNCAxMi41IEMgMjQgOS40ODAyMjU5IDIxLjUxOTc3NCA3IDE4LjUgNyB6IE0gNS4wMzMyMDMxIDExLjkxMDE1NiBDIDUuMDEyMjAzMSAxMi4xMDQxNTYgNSAxMi4zMDEgNSAxMi41IEwgNSAyMCBMIDggMjAgTCA4IDEyLjYyMTA5NCBMIDUuMDMzMjAzMSAxMS45MTAxNTYgeiIgZm9udC13ZWlnaHQ9IjQwMCIgZm9udC1mYW1pbHk9InNhbnMtc2VyaWYiIHdoaXRlLXNwYWNlPSJub3JtYWwiIG92ZXJmbG93PSJ2aXNpYmxlIi8+Cjwvc3ZnPg=="
    icon = Icon(src=moodleLogo, mimeType="image/svg+xml")

    def __init__(self) -> None:
        self._all_client_tools: Dict[str, Dict[str, Tool]] = {}


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

        if tool_name == "upload_files":
            return await MoodleTool.upload_files(arguments)
        elif tool_name == "download_file":
            return await MoodleTool.download_file(arguments)

        if not tool_name in self._all_client_tools:
            # Something somewhere expired or server restarted. We need to send an error and tell the client to re-request list of tools.
            await context.fastmcp_context.send_tool_list_changed()
            raise FastMCPError(f"Something went wrong, there is a possible cache issue in the MCP server. Please repeat the request.")

        tool = self._all_client_tools[tool_name]
        return await MoodleTool.execute_moodle_web_service(
            name=tool_name,
            arguments=arguments,
            # We pass output_schema so we can fix empty arrays in the result. A bit stupid that because of Moodle bug we need to
            # add a huge layer of caching.
            tools=tool.values(),
        )


    async def load_functions_from_wsdiscovery(self, ctx: Context) -> List[Dict[str, Any]]:
        """If tool_wsdiscovery plugin is installed on the Moodle site, use it to get the list of available functions."""
        baseurl, wstoken = Utils.verify_has_credentials(ctx)

        structure = Utils.request_post_json(f"{baseurl}/admin/tool/wsdiscovery/moodle.php",
                                    headers={'Authorization': 'Bearer ' + wstoken})
        functions = structure.get("functions", [])
        return self.prepare_schemas({"functions": functions})


    async def load_functions_from_site_info(self, ctx: Context) -> List[Dict[str, Any]]:
        """Request a list of available functions using core_webservice_get_site_info external function (fallback if tool_wsdiscovery is not installed)."""
        result = await MoodleTool.execute_moodle_web_service(
            name="core_webservice_get_site_info",
            arguments={},
            tools=[])
        content, structured_content = result.to_mcp_result()
        function_names = structured_content.get("result", {}).get("functions", [])
        return self.prepare_schemas({"functionnames": function_names})


    def prepare_schemas(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Request the function schemas from MCP Ready lookup service. Your credentials are never sent to this service."""
        jsonresult = Utils.request_post_json("https://api.mcp-ready.lmscloud.io/noauth/lookup", json=payload)
        return jsonresult.get("functions", []) if isinstance(jsonresult, dict) else []


    async def load_tools(self, ctx: Context) -> List[Tool]:
        """Load available Moodle tools from the site."""
        functions = await self._load_function_definitions(ctx)
        return self._register_tools(functions)


    async def _load_function_definitions(self, ctx: Context) -> List[Dict[str, Any]]:
        """Load function definitions from Moodle using available methods."""
        try:
            return await self.load_functions_from_wsdiscovery(ctx)
        except FastMCPError as e1:
            try:
                return await self.load_functions_from_site_info(ctx)
            except FastMCPError as e2:
                raise FastMCPError(
                    "Unable to load available external functions from your Moodle site. "
                    "Make sure that you either installed tool_wsdiscovery plugin or "
                    "enabled function core_webservice_get_site_info. \n\n"
                    f"More details about the error:\n1. {str(e1)}\n2. {str(e2)}"
                )


    def _register_tools(self, functions: List[Dict[str, Any]]) -> List[Tool]:
        """Register tools from function definitions."""
        client_tools: List[Tool] = []

        for toolinfo in functions:
            tool = self._create_tool_from_info(toolinfo)
            output_schema_hash = self._compute_schema_hash(toolinfo.get("outputSchema"))

            client_tools.append(tool)

            # Initialize nested dict if needed
            if tool.name not in self._all_client_tools:
                self._all_client_tools[tool.name] = {}

            self._all_client_tools[tool.name][output_schema_hash] = tool

        return client_tools


    def _create_tool_from_info(self, toolinfo: Dict[str, Any]) -> Tool:
        """Create a Tool instance from tool info dictionary."""
        return Tool(
            name=toolinfo.get("name"),
            description=toolinfo.get("description"),
            parameters=toolinfo.get("inputSchema"),
            output_schema=toolinfo.get("outputSchema"),
            icons=[self.icon],
            enabled=True,
        )


    def _compute_schema_hash(self, schema: Optional[Any]) -> str:
        """Compute SHA256 hash of schema for caching."""
        return hashlib.sha256(json.dumps(schema).encode('utf-8')).hexdigest()