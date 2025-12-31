"""Moodle MCP Server - Model Context Protocol server for Moodle LMS integration."""

from importlib.metadata import version

try:
    __version__ = version("moodle-mcp-server")
except Exception:
    __version__ = "0.0.0"  # Fallback for development

from .main import main
from .middleware import MoodleMiddleware
from .models import DownloadedFile
from .tools import MoodleTool
from .utils import Utils

__all__ = ["main", "MoodleMiddleware", "MoodleTool", "DownloadedFile", "Utils"]
