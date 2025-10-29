# MCP Publish & Deploy

Denne workflowen bygger Docker image, pusher til GHCR og genererer MCP-manifest for enkel publisering i MCP-kataloger.

## Bruk
- Automatisk kjøring ved push til `main`
- Manuell kjøring via "Run workflow" for deploy-instruksjoner til Docker Desktop MCP Toolkit

## Outputs
- Docker image: `ghcr.io/${owner}/${repo}:main`
- Artefakt: `mcp-server.json` (manifest)
