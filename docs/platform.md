# Backing Platform — Apache Egeria

`egeria-mcp` is a **client** of an Apache Egeria OMAG platform / View Server (OMVS).
This page is a recipe for standing one up locally with Docker so you have something
to point `EGERIA_PLATFORM_URL` at. For production topologies, follow the upstream
[Apache Egeria docs](https://egeria-project.org/).

!!! note "This is a backing-system recipe"
    Other packages in the ecosystem follow the same pattern — a
    `docs/platform.md` recipe for the system the connector talks to, with a sample
    Compose stack mirroring [`services/`](https://github.com/Knuckles-Team). Some
    backing systems are SaaS-only (e.g. ServiceNow) and have no local recipe.

## Quick start (single-node Compose)

Egeria publishes the `egeria/egeria-platform` image. This stack brings up one OMAG
Server Platform on `:9443` with the persistent quick-start runtime:

```yaml
# docker/egeria-platform.compose.yml
services:
  egeria-platform:
    image: docker.io/egeria/egeria-platform:5.3
    container_name: egeria-platform
    hostname: egeria-platform
    restart: unless-stopped
    ports:
      - "9443:9443"            # OMAG platform / View Server (HTTPS, self-signed)
    environment:
      - JAVA_DEBUG=false
      # Pre-load the quick-start config documents on boot
      - STARTUP_SERVERS=qs-metadata-store,qs-view-server
    volumes:
      - egeria_data:/deployments/data
    healthcheck:
      test: ["CMD", "curl", "-kfsS", "https://localhost:9443/open-metadata/platform-services/users/garygeeke/server-platform/origin"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 40s

volumes:
  egeria_data:
```

```bash
docker compose -f docker/egeria-platform.compose.yml up -d

# Wait for the platform origin to answer (self-signed TLS → -k)
curl -k https://localhost:9443/open-metadata/platform-services/users/garygeeke/server-platform/origin
```

## Point egeria-mcp at it

```bash
export EGERIA_PLATFORM_URL=https://localhost:9443
export EGERIA_VIEW_SERVER=qs-view-server
export EGERIA_USER=erinoverview
export EGERIA_USER_PASSWORD=secret
export EGERIA_VERIFY_SSL=False          # self-signed quick-start cert

egeria-mcp --transport streamable-http --host 0.0.0.0 --port 8000
```

## Run both together

A combined stack puts the platform and the MCP server on one Docker network so the
server reaches Egeria by container name:

```yaml
# docker/stack.compose.yml
services:
  egeria-platform:
    image: docker.io/egeria/egeria-platform:5.3
    hostname: egeria-platform
    ports: ["9443:9443"]
    environment:
      - STARTUP_SERVERS=qs-metadata-store,qs-view-server
    volumes: ["egeria_data:/deployments/data"]

  egeria-mcp:
    image: knucklessg1/egeria-mcp:latest
    depends_on: [egeria-platform]
    environment:
      - EGERIA_PLATFORM_URL=https://egeria-platform:9443
      - EGERIA_VIEW_SERVER=qs-view-server
      - EGERIA_VERIFY_SSL=False
      - TRANSPORT=streamable-http
      - HOST=0.0.0.0
      - PORT=8000
    ports: ["8000:8000"]

volumes:
  egeria_data:
```

```bash
docker compose -f docker/stack.compose.yml up -d
```

## Seed it from your estate

With the platform up and `EGERIA_ENABLE_WRITE=true`, the
[harvest CLI](usage.md#as-a-harvest-cli) populates Egeria bottom-up from your data
stores, ERPNext, GitLab, and 30+ other sources, then `reconcile` cross-links them
into one lineage/governance graph.
