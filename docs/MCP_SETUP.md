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

## Best practices

- Pin MCP server versions in `.vscode/mcp.json` for team consistency. Avoid `@latest` in shared repos unless you specifically want automatic updates.
- Keep secrets out of source-controlled config. Use environment variables or a local env file (for example, `.vscode/mcp.env`) and keep only placeholders in docs.
- Use least-privilege credentials/tokens for each MCP server.
- Keep one fallback path for critical workflows (for example, direct AWS docs URLs) in case a server is temporarily unavailable.

## Quick smoke tests

Run these in Copilot Chat after startup to verify key servers:

- Filesystem MCP: `List files under docs/ and show README.md`
- GitHub MCP: `List open pull requests for <owner>/<repo>`
- OpenAPI MCP: `Show the upload endpoint from docs/openapi.yaml`
- AWS Documentation MCP: `Find the latest S3 PutObject request syntax`

If all four succeed, your MCP setup is healthy.

## Troubleshooting checklist

- Server does not appear in tools list:
	- Verify `.vscode/mcp.json` is valid JSON/JSONC.
	- Reload VS Code window.
	- Re-approve MCP trust/start prompts.
- Server starts but tools fail:
	- Confirm required environment variables are set in the shell VS Code inherits.
	- Confirm auth tokens are valid and not expired.
- Windows command issues:
	- Prefer full executable paths where appropriate.
	- If using `uv`/`uvx`, ensure they are installed and on `PATH`.
- Slow startup:
	- Avoid `@latest` for every launch.
	- Pin versions and update on a planned cadence.

## Suggested update cadence

- Monthly: bump MCP server versions intentionally and run smoke tests.
- After any server upgrade: re-run smoke tests and capture any prompt/workflow changes in this file.
