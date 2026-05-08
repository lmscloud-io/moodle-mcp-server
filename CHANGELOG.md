# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.2] - 2026-05-08

### Fixed
- Tool registration no longer passes the `enabled` field, which is rejected by
  strict MCP clients (e.g. mcpo, MCP Inspector) and was removed in fastmcp 3.x [#3]

### Changed
- Upgraded to `fastmcp>=3,<4` (was `>=2.13.1`, unbounded).
- Pinned `requests` upper bound to `<3` to prevent future major-version breakage.
- Added Python 3.13 to the supported versions.
- Marked the project as Production/Stable.

## [1.0.1] - 2025-12-31

Initial public release.
