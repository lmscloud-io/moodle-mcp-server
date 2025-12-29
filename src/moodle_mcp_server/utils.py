from fastmcp.exceptions import ToolError
from fastmcp import Context
from fastmcp.server.dependencies import get_http_headers
import os
from urllib.parse import urlparse
from typing import Optional
import requests
from fastmcp.exceptions import FastMCPError


class Utils:

    @staticmethod
    def get_credentials(ctx: Context) -> tuple[str, str]:
        """Retrieves Moodle credentials (site URL and web service token) from HTTP headers or environment variables."""

        # wstoken = ctx.get_state("moodle_wstoken")
        # baseurl = ctx.get_state("moodle_baseurl")
        # wstoken = "" if wstoken is None else wstoken
        # baseurl = "" if baseurl is None else baseurl

        # Get token/baseurl from HTTP headers first
        headers = get_http_headers()
        wstoken = headers.get("x-token", "")
        baseurl = Utils.clean_baseurl(headers.get("x-moodle", ""), True)

        # Then try environment variables
        wstoken = os.environ.get("TOKEN", "").strip() if wstoken == "" else wstoken
        baseurl = Utils.clean_baseurl(os.environ.get("MOODLE", ""), True) if baseurl == "" else baseurl

        # hascredentials = wstoken != "" and baseurl != ""
        # ctx.set_state("moodle_has_credentials", hascredentials)
        # ctx.set_state("moodle_baseurl", baseurl if hascredentials else "")
        # ctx.set_state("moodle_wstoken", wstoken if hascredentials else "")
        # clienthash = hashlib.sha256(f"{baseurl}|{wstoken}".encode('utf-8')).hexdigest() if hascredentials else ""
        # ctx.set_state("moodle_client_hash", clienthash)
        return baseurl, wstoken



    @staticmethod
    def verify_has_credentials(ctx: Context) -> tuple[str, str]:
        """Verifies that Moodle credentials (site URL and web service token) are specified and returns them."""
        baseurl, wstoken = Utils.get_credentials(ctx)
        if wstoken == "" or baseurl == "":
            # TODO show different error for different transport types (HTTP headers vs environment variables)
            raise ToolError("Moodle site URL or web service token not provided. Please provide them using 'x-moodle' and 'x-token' HTTP headers or environment variables 'MOODLE' and 'TOKEN'.")
            #raise ToolError("Moodle credentials (site URL and web service token) not provided.")
        return baseurl, wstoken


    @staticmethod
    def clean_baseurl(url: str, discardInvalid: bool = False) -> str:
        url = url.strip().rstrip('/').lower()
        # TODO potentially - remove query string, fragments, and if the path ends with "/login/index.php", /login" or "/index.php"
        return "" if discardInvalid and not Utils.is_valid_url(url) else url


    @staticmethod
    def is_valid_url(url: str, ctx: Optional[Context] = None) -> bool:
        try:
            result = urlparse(url)
            isvalid = all([result.scheme, result.netloc]) and result.scheme in ['http', 'https']
        except ValueError:
            isvalid = False
        if isvalid == False and ctx is not None:
            # TODO ctx.error is async!
            ctx.error(f"The URL '{url}' is not valid")
        return isvalid


    @staticmethod
    def request_post_json(url: str, **kwargs) -> dict:
        """Sends a POST request and returns the JSON response."""
        args = {**kwargs}
        args["headers"] = args.get("headers", {})
        args["headers"]["Accept"] = "application/json"
        if "json" in args:
            args["headers"]["Content-Type"] = "application/json"
        result = requests.post(url, **args)
        if result.status_code != 200:
            raise FastMCPError(f"Request to {url} returned {result.status_code}: {result.text}")
        try:
            jsonresult = result.json()
        except Exception as e:
            raise FastMCPError(f"Request to {url} returned invalid JSON: {str(e)}")
        return jsonresult


    @staticmethod
    def request_post_json_moodle(url: str, **kwargs) -> dict:
        """Sends a POST request to Moodle and returns the JSON response. Moodle can return 200 status code even for errors."""
        jsonresult = Utils.request_post_json(url, **kwargs)
        if (isinstance(jsonresult, dict) and jsonresult.get("exception", None) is not None):
            raise ToolError(jsonresult.get("message", jsonresult.get("exception")))
        return jsonresult
