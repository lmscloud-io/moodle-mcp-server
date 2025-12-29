import base64
from urllib.parse import urlencode

import requests
from fastmcp.exceptions import ToolError
from fastmcp.server.dependencies import get_context
from fastmcp.tools.tool import ToolResult

from .models import DownloadedFile
from .utils import Utils

class MoodleTool:
    """Communication with Moodle web services."""

    # @staticmethod
    # def urlencode_flat(l: dict):
    #     """Same as urlencode but encodes nulls as "" instead of "None"."""
    #     def _encode_value(k, v):
    #         return urlencode({k: ("" if v is None else v)}, safe='[]')
    #     return '&'.join([_encode_value(k, l[k]) for k in l.keys()])


    @staticmethod
    def urlencode_dict(d: dict):
        def _flatten(list_of_dicts):
            return {key: val for k in list_of_dicts for key, val in k.items()}
        def _append_prefix(arg, prefix):
            if (isinstance(arg, list)):
                return _flatten([_append_prefix(value, f"{prefix}[{index}]") for index, value in enumerate(arg)])
            elif (isinstance(arg, dict)):
                return _flatten([_append_prefix(value, f"{prefix}[{index}]") for index, value in arg.items()])
            elif arg is None:
                return {prefix: ""}
            else:
                return {prefix: arg}

        return urlencode(_flatten([_append_prefix(value, index) for index, value in d.items()]), safe='[]')


    @staticmethod
    async def run_moodle_tool(name: str, arguments: dict, output_schema) -> ToolResult:
        """Executes the tool by making a call to Moodle web service."""
        baseurl, wstoken = Utils.verify_has_credentials(get_context())

        data = {**arguments, "wstoken": wstoken, "wsfunction": name}
        jsonresult = Utils.request_post_json_moodle(f"{baseurl}/webservice/rest/server.php?moodlewsrestformat=json",
                               data=MoodleTool.urlencode_dict(data),
                               allow_redirects=True,
                               headers={'Content-Type': 'application/x-www-form-urlencoded'})

        return ToolResult(structured_content=MoodleTool.fix_empty_arrays({"result": jsonresult}, output_schema))


    @staticmethod
    def fix_empty_arrays(result, schema):
        """Since JSON was encoded with PHP, empty objects may appear as empty arrays. This causes schema validation errors."""
        if schema is None or not isinstance(schema, dict) or schema.get("type", None) is None:
            return result

        # Fix empty arrays that should be objects
        if schema["type"] == "object" and isinstance(result, list) and len(result) == 0:
            return {}

        # Recursively fix nested elements
        if schema["type"] == "array" and isinstance(result, list) and schema.get("items", None) is not None:
            return [MoodleTool.fix_empty_arrays(item, schema["items"]) for item in result]
        if schema["type"] == "object" and isinstance(result, dict) and isinstance(schema.get("properties", None), dict):
            return {k: MoodleTool.fix_empty_arrays(v, schema["properties"].get(k, None)) for k, v in result.items()}
        return result


    @staticmethod
    async def run_moodle_tool_upload(arguments: dict) -> ToolResult:
        """Uploads one or more files to Moodle draft file area"""
        ctx = get_context()
        baseurl, wstoken = Utils.verify_has_credentials(ctx)

        itemid = arguments.get("itemid")

        files = {}
        for f in arguments.get("files", []):
            uploadtype = f.get("uploadtype", "base64")
            content = f.get("content", "")
            if uploadtype == "plaintext":
                files[f['filename']] = content
            elif uploadtype == "base64":
                files[f['filename']] = base64.b64decode(content)
            elif uploadtype == "url":
                # fetch the file from the URL
                result = requests.get(content)
                if result.status_code != 200:
                    raise ToolError(f"Error fetching file from URL {content}: {result.status_code} {result.text}")
                files[f['filename']] = result.content

        jsonresult = Utils.request_post_json_moodle(baseurl + "/webservice/upload.php",
                      data={
                          "token": wstoken,
                          "itemid": itemid,
                          "filepath": arguments.get("filepath", "/"),
                      },
                      files=files)

        structured_content = {}
        files = []

        # Moodle returns weird structure that is also inconsistent for successfully uploaded files and files with errors.
        # let's only return important fields and not duplicate itemid/filepath, they can never be different for different successful files.
        if (isinstance(jsonresult, list)):
            for element in jsonresult:
                if element.get("errortype", None) is not None:
                    files.append({
                        "filename": element.get("filename", ""),
                        "success": False,
                        "errortype": element.get("errortype"),
                        "errormessage": element.get("error", ""),
                        "filesize": element.get("size", 0),
                    })
                else:
                    structured_content["itemid"] = element.get("itemid", None)
                    structured_content["filepath"] = element.get("filepath", "")
                    files.append({
                        "filename": element.get("filename", ""),
                        "success": True,
                        "filesize": element.get("filesize", 0),
                    })

        structured_content["files"] = files
        return ToolResult(structured_content=structured_content)


    @staticmethod
    async def run_moodle_tool_download(arguments: dict) -> ToolResult:
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

        #return File(data=result.content, name="Sun behind the Heel Stone", format="jpg")  # TODO extract name and format (=extension) from the headers

        # async with aiohttp.ClientSession() as session:
        #     async with session.get(url) as response:
        #         pdf_data = await response.read()
        #         return File(data=pdf_data, format="pdf")
