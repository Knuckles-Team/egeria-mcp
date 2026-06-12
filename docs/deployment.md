# Deployment

<!-- BEGIN GENERATED: deployment-options -->
## Deployment Options

`egeria-mcp` exposes its MCP server (console script `egeria-mcp`) four ways. Pick the row that
matches where the server runs relative to your MCP client, then copy the matching
`mcp_config.json` below. Replace the `<your-…>` placeholders with the values from the **Configuration / Environment Variables** section.

| # | Option | Transport | Where it runs | `mcp_config.json` key |
|---|--------|-----------|---------------|------------------------|
| 1 | stdio | `stdio` | client launches a subprocess | `command` |
| 2 | Streamable-HTTP (local) | `streamable-http` | a local network port | `command` or `url` |
| 3 | Local container / uv | `stdio` or `streamable-http` | Docker / Podman / uv on this host | `command` or `url` |
| 4 | Remote URL | `streamable-http` | a remote host behind Caddy | `url` |

### 1. stdio (local subprocess)

The client launches the server over stdio via `uvx` — best for local IDEs
(Cursor, Claude Desktop, VS Code):

```json
{
  "mcpServers": {
    "egeria-mcp": {
      "command": "uvx",
      "args": ["--from", "egeria-mcp", "egeria-mcp"],
      "env": {
        "EGERIA_PLATFORM_URL": "<your-egeria_platform_url>",
        "LANGFUSE_BASE_URL": "<your-langfuse_base_url>",
        "ANSIBLE_TOWER_URL": "<your-ansible_tower_url>"
      }
    }
  }
}
```

### 2. Streamable-HTTP (local process)

Run the server as a long-lived HTTP process:

```bash
uvx --from egeria-mcp egeria-mcp --transport streamable-http --host 0.0.0.0 --port 8000
curl -s http://localhost:8000/health        # {"status":"OK"}
```

Then either let the client launch it:

```json
{
  "mcpServers": {
    "egeria-mcp": {
      "command": "uvx",
      "args": ["--from", "egeria-mcp", "egeria-mcp", "--transport", "streamable-http", "--port", "8000"],
      "env": {
        "TRANSPORT": "streamable-http",
        "HOST": "0.0.0.0",
        "PORT": "8000",
        "EGERIA_PLATFORM_URL": "<your-egeria_platform_url>",
        "LANGFUSE_BASE_URL": "<your-langfuse_base_url>",
        "ANSIBLE_TOWER_URL": "<your-ansible_tower_url>"
      }
    }
  }
}
```

…or connect to the already-running process by URL:

```json
{
  "mcpServers": {
    "egeria-mcp": { "url": "http://localhost:8000/mcp" }
  }
}
```

### 3. Local container / uv

**(a) Launch a container directly from `mcp_config.json`** (stdio over the container —
no ports to manage). Swap `docker` for `podman` for a daemonless runtime:

```json
{
  "mcpServers": {
    "egeria-mcp": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "TRANSPORT=stdio",
        "-e", "EGERIA_PLATFORM_URL=<your-egeria_platform_url>",
        "-e", "LANGFUSE_BASE_URL=<your-langfuse_base_url>",
        "-e", "ANSIBLE_TOWER_URL=<your-ansible_tower_url>",
        "knucklessg1/egeria-mcp:latest"
      ]
    }
  }
}
```

**(b) Run a local streamable-http container, then connect by URL:**

```bash
docker run -d --name egeria-mcp -p 8000:8000 \
  -e TRANSPORT=streamable-http \
  -e PORT=8000 \
  -e EGERIA_PLATFORM_URL="<your-egeria_platform_url>" \
  -e LANGFUSE_BASE_URL="<your-langfuse_base_url>" \
  -e ANSIBLE_TOWER_URL="<your-ansible_tower_url>" \
  knucklessg1/egeria-mcp:latest
# or, from a clone of this repo:
docker compose -f docker/mcp.compose.yml up -d
```

```json
{
  "mcpServers": {
    "egeria-mcp": { "url": "http://localhost:8000/mcp" }
  }
}
```

**(c) From a local checkout with `uv`:**

```bash
uv run egeria-mcp --transport streamable-http --port 8000
```

### 4. Remote URL (deployed behind Caddy)

When the server is deployed remotely (e.g. as a Docker service) and published through
Caddy on the internal `*.arpa` zone, connect with the `"url"` key — no local process or
image required:

```json
{
  "mcpServers": {
    "egeria-mcp": { "url": "http://egeria-mcp.arpa/mcp" }
  }
}
```

Caddy reverse-proxies `http://egeria-mcp.arpa` to the container's `:8000`
streamable-http listener; `http://egeria-mcp.arpa/health` returns
`{"status":"OK"}` when the service is live.
<!-- END GENERATED: deployment-options -->

This page covers running `egeria-mcp` as a long-lived server: the transports, a
Docker Compose stack, putting it behind a Caddy reverse proxy, and giving it a DNS
name with Technitium. To provision the **Egeria platform** it connects to, see
[Backing Platform](platform.md).

> `egeria-mcp` ships an **MCP server** (console script `egeria-mcp`). It does not
> include a separate A2A agent server — it is a typed, deterministic tool surface a
> policy router / agent calls. (Ecosystem packages that *do* ship an agent server
> expose a second `*-agent` console script and an `agent.compose.yml`.)

## Run the MCP server

The transport is selected with `--transport` (or the `TRANSPORT` env var):

=== "stdio (default)"

    ```bash
    egeria-mcp
    ```
    For IDE / desktop MCP clients that launch the server as a subprocess.

=== "streamable-http"

    ```bash
    egeria-mcp --transport streamable-http --host 0.0.0.0 --port 8000
    ```
    A network server with a `/health` endpoint and `/mcp` route.

=== "sse"

    ```bash
    egeria-mcp --transport sse --host 0.0.0.0 --port 8000
    ```

Health check (HTTP transports):

```bash
curl -s http://localhost:8000/health        # {"status":"OK"}
```

## Configuration (environment)

`egeria-mcp` is configured entirely from the environment. The **required** set:

| Var | Default | Meaning |
|---|---|---|
| `EGERIA_PLATFORM_URL` | `https://localhost:9443` | OMAG platform URL |
| `EGERIA_VIEW_SERVER` | `qs-view-server` | View server name |
| `EGERIA_USER` | `erinoverview` | User id |
| `EGERIA_USER_PASSWORD` | `secret` | Password / token |
| `EGERIA_VERIFY_SSL` | `False` | Verify TLS (self-signed homelab) |
| `EGERIA_ENABLE_WRITE` | `False` | Gate every write/harvest tool |
| `EGERIATOOL` | `True` | Register the Egeria tool set |

Plus `HOST` / `PORT` / `TRANSPORT` for HTTP transports. Every **optional** harvest
connector (ServiceNow, ERPNext, GitLab, …) reads its own credentials — the full set,
grouped by source system, is documented in
[`.env.example`](https://github.com/Knuckles-Team/egeria-mcp/blob/main/.env.example).
Copy it to `.env` and fill in only what you use.

## Docker Compose

The repo ships [`docker/mcp.compose.yml`](https://github.com/Knuckles-Team/egeria-mcp/blob/main/docker/mcp.compose.yml).
It reads a sibling `.env` and publishes the HTTP server on `:8000`:

```yaml
services:
  egeria-mcp:
    image: knucklessg1/egeria-mcp:latest
    container_name: egeria-mcp
    hostname: egeria-mcp
    restart: always
    env_file:
      - .env
    environment:
      - PYTHONUNBUFFERED=1
      - HOST=0.0.0.0
      - PORT=8000
      - TRANSPORT=streamable-http
    ports:
      - "8000:8000"
    healthcheck:
      test: ["CMD", "python3", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
```

```bash
cp .env.example .env          # then edit EGERIA_* values
docker compose -f docker/mcp.compose.yml up -d
docker compose -f docker/mcp.compose.yml logs -f
```

## Behind a Caddy reverse proxy

Expose the HTTP server on a hostname with automatic TLS. Add to your `Caddyfile`:

```caddy
# Internal (self-signed) — homelab .arpa zone
egeria-mcp.arpa {
    tls internal
    reverse_proxy egeria-mcp:8000
}
```

```caddy
# Public — automatic Let's Encrypt
egeria-mcp.example.com {
    reverse_proxy egeria-mcp:8000
}
```

Reload Caddy:

```bash
docker compose -f services/caddy/compose.yml exec caddy caddy reload --config /etc/caddy/Caddyfile
```

## DNS with Technitium

Point the hostname at the host running Caddy. Via the Technitium API:

```bash
curl -s "http://technitium.arpa:5380/api/zones/records/add" \
  --data-urlencode "token=$TECHNITIUM_DNS_TOKEN" \
  --data-urlencode "domain=egeria-mcp.arpa" \
  --data-urlencode "zone=arpa" \
  --data-urlencode "type=A" \
  --data-urlencode "ipAddress=10.0.0.10" \
  --data-urlencode "ttl=3600"
```

…or add an **A record** `egeria-mcp.arpa → <caddy-host-ip>` in the Technitium web
console (`http://technitium.arpa:5380`). The ecosystem
[`technitium-dns-mcp`](https://knuckles-team.github.io/technitium-dns-mcp/) automates
this as a tool.

## Register with an MCP client

Add to your client's `mcp_config.json` (multiplexer nickname `eg`):

```json
{
  "mcpServers": {
    "egeria-mcp": {
      "command": "uv",
      "args": ["run", "egeria-mcp"],
      "env": {
        "EGERIA_PLATFORM_URL": "https://your-egeria:9443",
        "EGERIA_VIEW_SERVER": "qs-view-server",
        "EGERIA_USER": "erinoverview",
        "EGERIA_USER_PASSWORD": "secret"
      }
    }
  }
}
```

For a remote HTTP server, point the client at `http://egeria-mcp.arpa/mcp` instead.
