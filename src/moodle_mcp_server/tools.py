import base64
from typing import Any, Dict, List
from urllib.parse import urlencode
import requests
from fastmcp.exceptions import ToolError
from fastmcp.server.dependencies import get_context
from fastmcp.tools.tool import Tool, ToolResult
from .models import DownloadedFile
from .utils import Utils


class MoodleTool:
    """Communication with Moodle web services."""

    @staticmethod
    def urlencode_dict(d: Dict[str, Any]) -> str:
        """Encode a nested dictionary for Moodle web service requests."""
        def _flatten(list_of_dicts: List[Dict[str, Any]]) -> Dict[str, Any]:
            return {key: val for k in list_of_dicts for key, val in k.items()}

        def _append_prefix(arg: Any, prefix: str) -> Dict[str, Any]:
            if isinstance(arg, list):
                return _flatten([_append_prefix(value, f"{prefix}[{index}]") for index, value in enumerate(arg)])
            elif isinstance(arg, dict):
                return _flatten([_append_prefix(value, f"{prefix}[{index}]") for index, value in arg.items()])
            elif arg is None:
                return {prefix: ""}
            else:
                return {prefix: arg}

        return urlencode(_flatten([_append_prefix(value, index) for index, value in d.items()]), safe='[]')


    @staticmethod
    async def execute_moodle_web_service(name: str, arguments: Dict[str, Any], tools: List[Tool]) -> ToolResult:
        """Executes the tool by making a call to Moodle web service."""
        baseurl, wstoken = Utils.verify_has_credentials(get_context())

        data = {**arguments, "wstoken": wstoken, "wsfunction": name}
        jsonresult = Utils.request_post_json_moodle(f"{baseurl}/webservice/rest/server.php?moodlewsrestformat=json",
                               data=MoodleTool.urlencode_dict(data),
                               allow_redirects=True,
                               headers={'Content-Type': 'application/x-www-form-urlencoded'})
        structured_content = {"result": jsonresult}
        for tool in tools:
            structured_content = MoodleTool._fix_empty_arrays(structured_content, tool.output_schema)
        return ToolResult(structured_content=structured_content)


    @staticmethod
    def _fix_empty_arrays(result: Any, schema: Any) -> Any:
        """
        Fix PHP JSON encoding quirks where empty objects become empty arrays.

        Since JSON was encoded with PHP, empty objects may appear as empty arrays.
        This causes schema validation errors.
        """
        if schema is None or not isinstance(schema, dict) or schema.get("type", None) is None:
            return result

        # Fix empty arrays that should be objects
        if schema["type"] == "object" and isinstance(result, list) and len(result) == 0:
            return {}

        # Recursively fix nested elements
        if schema["type"] == "array" and isinstance(result, list) and schema.get("items", None) is not None:
            return [MoodleTool._fix_empty_arrays(item, schema["items"]) for item in result]
        if schema["type"] == "object" and isinstance(result, dict) and isinstance(schema.get("properties", None), dict):
            return {k: MoodleTool._fix_empty_arrays(v, schema["properties"].get(k, None)) for k, v in result.items()}
        return result


    @staticmethod
    async def upload_files(arguments: Dict[str, Any]) -> ToolResult:
        """Uploads one or more files to Moodle draft file area."""
        ctx = get_context()
        baseurl, wstoken = Utils.verify_has_credentials(ctx)

        files = await MoodleTool._prepare_upload_files(arguments.get("files", []))

        jsonresult = await MoodleTool._upload_to_moodle(baseurl, wstoken, arguments, files)

        structured_content = MoodleTool._parse_upload_response(jsonresult)
        return ToolResult(structured_content=structured_content)


    @staticmethod
    async def _prepare_upload_files(file_specs: List[Dict[str, Any]]) -> Dict[str, bytes]:
        """Prepare files for upload based on their upload type."""
        files: Dict[str, bytes] = {}
        for f in file_specs:
            uploadtype = f.get("uploadtype", "base64")
            content = f.get("content", "")
            filename = f['filename']

            if uploadtype == "plaintext":
                files[filename] = content.encode() if isinstance(content, str) else content
            elif uploadtype == "base64":
                files[filename] = base64.b64decode(content)
            elif uploadtype == "url":
                files[filename] = await MoodleTool._fetch_file_from_url(content)

        return files


    @staticmethod
    async def _fetch_file_from_url(url: str) -> bytes:
        """Fetch file content from a URL."""
        result = requests.get(url)
        if result.status_code != 200:
            raise ToolError(f"Error fetching file from URL {url}: {result.status_code} {result.text}")
        return result.content


    @staticmethod
    async def _upload_to_moodle(
        baseurl: str,
        wstoken: str,
        arguments: Dict[str, Any],
        files: Dict[str, bytes]
    ) -> Dict[str, Any]:
        """Upload files to Moodle server."""
        return Utils.request_post_json_moodle(
            baseurl + "/webservice/upload.php",
            data={
                "token": wstoken,
                "itemid": arguments.get("itemid"),
                "filepath": arguments.get("filepath", "/"),
            },
            files=files
        )


    @staticmethod
    def _parse_upload_response(jsonresult: Any) -> Dict[str, Any]:
        """Parse Moodle upload response into structured content."""
        structured_content: Dict[str, Any] = {}
        files: List[Dict[str, Any]] = []

        # Moodle returns weird structure that is also inconsistent for successfully uploaded files and files with errors.
        # let's only return important fields and not duplicate itemid/filepath, they can never be different for different successful files.
        if isinstance(jsonresult, list):
            for element in jsonresult:
                if element.get("errortype") is not None:
                    files.append(MoodleTool._create_error_file_info(element))
                else:
                    if "itemid" not in structured_content:
                        structured_content["itemid"] = element.get("itemid")
                        structured_content["filepath"] = element.get("filepath", "")
                    files.append(MoodleTool._create_success_file_info(element))

        structured_content["files"] = files
        return structured_content


    @staticmethod
    def _create_error_file_info(element: Dict[str, Any]) -> Dict[str, Any]:
        """Create error file info dictionary."""
        return {
            "filename": element.get("filename", ""),
            "success": False,
            "errortype": element.get("errortype"),
            "errormessage": element.get("error", ""),
            "filesize": element.get("size", 0),
        }


    @staticmethod
    def _create_success_file_info(element: Dict[str, Any]) -> Dict[str, Any]:
        """Create success file info dictionary."""
        return {
            "filename": element.get("filename", ""),
            "success": True,
            "filesize": element.get("filesize", 0),
        }


    @staticmethod
    async def download_file(arguments: Dict[str, Any]) -> ToolResult:
        """Downloads a file from Moodle given its pluginfile.php URL."""
        baseurl, wstoken = Utils.verify_has_credentials(get_context())
        url = arguments.get("url", "")

        # Check url starts with baseurl/pluginfile.php or is a relative link /pluginfile.php...
        if url.startswith(baseurl + "/"):
            pluginfileurl = url[len(baseurl):]
        elif url.startswith("/"):
            pluginfileurl = url
        else:
            raise ToolError("The URL must either start with a '/' or be a valid Moodle file URL starting with "+ baseurl + "/")

        if pluginfileurl.startswith("/pluginfile.php"):
            pluginfileurl = "/webservice" + pluginfileurl
        elif pluginfileurl.startswith("/webservice/pluginfile.php"):
            pass
        else:
            raise ToolError("The provided URL is not a valid Moodle pluginfile URL. It is possible that you can download the file directly without authentication.")

        file = await DownloadedFile.request_file(baseurl + pluginfileurl, wstoken)
        return ToolResult(content=file)
