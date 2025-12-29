"""Moodle MCP Server - Model Context Protocol server for Moodle LMS integration."""

__version__ = "0.1.0"

from .main import main
from .middleware import MoodleMiddleware
from .models import DownloadedFile
from .tools import MoodleTool
from .utils import Utils

__all__ = ["main", "MoodleMiddleware", "MoodleTool", "DownloadedFile", "Utils"]
