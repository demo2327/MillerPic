# MCP Setup in VS Code

This workspace includes MCP server config at `.vscode/mcp.json`.

## Installed MCP servers

- Filesystem: `@modelcontextprotocol/server-filesystem`
- GitHub: `mcp-github-server`
- HTTP: `@waleedyousaf07/mcp-http`
- OpenAPI: `mcp-openapi-schema-explorer`
- Playwright: `@playwright/mcp`

## One-time auth/env setup

In PowerShell, set required environment variables before using MCP servers:

```powershell
$env:GITHUB_TOKEN = "<your-github-token>"
```

You can use `.vscode/mcp.env.example` as a reference.

## Notes

- OpenAPI MCP reads from `docs/openapi.yaml`.
- GitHub MCP requires `GITHUB_TOKEN`.
- If VS Code asks to trust/start MCP servers, approve those prompts.
