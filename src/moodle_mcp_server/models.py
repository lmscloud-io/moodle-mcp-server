from typing import Dict, Optional
import mcp.types
import requests
from fastmcp.exceptions import ToolError
from fastmcp.utilities.types import File
from mcp.types import Annotations
from typing_extensions import override


class DownloadedFile(File):
    """Represents a file downloaded from Moodle using the download_file tool."""

    def __init__(self, data: bytes, headers: Dict[str, str]):
        filename = self._extract_filename(headers)
        name, format = self._parse_filename(filename)
        mime_type = self._extract_mime_type(headers)

        if format is None and mime_type is not None:
            format = mime_type.split("/")[-1]

        super().__init__(data=data, name=name, format=format)
        self.headers = headers
        self.mime_type_from_headers = mime_type


    @staticmethod
    def _extract_filename(headers: Dict[str, str]) -> Optional[str]:
        """Extract filename from Content-Disposition header."""
        cd = headers.get("Content-Disposition", "").split(";")
        for part in cd:
            part = part.strip()
            if part.startswith("filename="):
                return part.split("=", maxsplit=1)[1].strip().strip('"')
        return None


    @staticmethod
    def _parse_filename(filename: Optional[str]) -> tuple[Optional[str], Optional[str]]:
        """Parse filename into name and extension."""
        if filename is None:
            return None, None

        if "." in filename:
            name = filename.rsplit(".", maxsplit=1)[0]
            format = filename.rsplit(".", maxsplit=1)[1]
            return name, format
        return filename, None


    @staticmethod
    def _extract_mime_type(headers: Dict[str, str]) -> Optional[str]:
        """Extract MIME type from Content-Type header."""
        mime_type = headers.get("Content-Type")
        if mime_type is not None:
            return mime_type.split(";")[0]
        return None


    @override
    def to_resource_content(
        self,
        mime_type: str | None = None,
        annotations: Annotations | None = None,
    ) -> mcp.types.EmbeddedResource:
        mime_type = self.mime_type_from_headers if mime_type is None else mime_type
        return super().to_resource_content(mime_type, annotations)


    @staticmethod
    async def request_file(url: str, wstoken: str) -> "DownloadedFile":
        """Download a file from Moodle using the web service token."""
        result = requests.post(url, params={"token": wstoken}, allow_redirects=True)
        if result.status_code != 200:
            raise ToolError(f"Error downloading file from URL {url}: {result.status_code} {result.text}")

        return DownloadedFile(data=result.content, headers=dict(result.headers))
