import mcp.types
import requests
from fastmcp.exceptions import ToolError
from fastmcp.utilities.types import File
from mcp.types import Annotations
from typing_extensions import override


class DownloadedFile(File):
    """Represents a file downloaded from Moodle using the download_file tool."""

    def __init__(self, data: bytes, headers: dict):
        # For each part of Content-Disposition header, check if it starts with filename= and if yes extract the filename
        cd = headers.get("Content-Disposition", "").split(";")
        filename = None
        for part in cd:
            part = part.strip()
            if part.strip().startswith("filename="):
                filename = part.split("=", maxsplit=1)[1].strip().strip('"')

        # extract name and extension from filename
        name = filename.rsplit(".", maxsplit=1)[0] if filename is not None else None
        format = filename.rsplit(".", maxsplit=1)[1] if filename is not None and "." in filename else None

        # get mime type from headers and use it to set format (=extension) if not already set
        mime_type = headers.get("Content-Type", None)
        mime_type = mime_type.split(";")[0] if mime_type is not None else None
        if format is None and mime_type is not None:
            format = mime_type.split("/")[-1]

        super().__init__(data=data, name=name, format=format)
        self.headers = headers
        self.mime_type_from_headers = mime_type


    @override
    def to_resource_content(
        self,
        mime_type: str | None = None,
        annotations: Annotations | None = None,
    ) -> mcp.types.EmbeddedResource:
        mime_type = self.mime_type_from_headers if mime_type is None else mime_type
        return super().to_resource_content(mime_type, annotations)


    @staticmethod
    async def request_file(url: str, wstoken: str) -> bytes:
        result = requests.post(url, params={"token": wstoken}, allow_redirects=True)
        if result.status_code != 200:
            raise ToolError(f"Error downloading file from URL {url}: {result.status_code} {result.text}")

        return DownloadedFile(data=result.content, headers=result.headers)
