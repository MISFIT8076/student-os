"""Student OS MCP servers.

Each subpackage is an independent Model Context Protocol server that wraps
one student platform (GitHub, Gmail, Calendar, ...) and exposes a small set
of standardized, read-only tools. Servers are launched by the orchestrator
over stdio (see backend/servers.json).
"""
