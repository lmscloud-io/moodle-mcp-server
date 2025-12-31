from typing import Any, Dict
import os
import requests
from fastmcp import Context
from fastmcp.exceptions import FastMCPError, ToolError
from fastmcp.server.dependencies import get_http_headers
from urllib.parse import urlparse
from fastmcp.server.dependencies import get_http_request


class Utils:

    @staticmethod
    def clean_baseurl(url: str, discardInvalid: bool = False) -> str:
        url = url.strip().rstrip('/').lower()
        return "" if discardInvalid and not Utils.is_valid_url(url) else url


    @staticmethod
    def is_valid_url(url: str) -> bool:
        try:
            result = urlparse(url)
            isvalid = all([result.scheme, result.netloc]) and result.scheme in ['http', 'https']
        except ValueError:
            isvalid = False
        return isvalid


    @staticmethod
    def request_post_json(url: str, **kwargs: Any) -> Dict[str, Any]:
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
    def request_post_json_moodle(url: str, **kwargs: Any) -> Dict[str, Any]:
        """Sends a POST request to Moodle and returns the JSON response. Moodle can return 200 status code even for errors."""
        jsonresult = Utils.request_post_json(url, **kwargs)
        if (isinstance(jsonresult, dict) and jsonresult.get("exception", None) is not None):
            raise ToolError(jsonresult.get("message", jsonresult.get("exception")))
        return jsonresult
