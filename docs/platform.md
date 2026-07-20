# Backing Platform — Apache Egeria

`egeria-mcp` is a **client** of an Apache Egeria OMAG platform / View Server (OMVS).
This page provides a Docker recipe for deploying one locally to serve as the target
of `EGERIA_PLATFORM_URL`. For production topologies, follow the upstream
[Apache Egeria documentation](https://egeria-project.org/).

!!! note "Backing-system recipe"
    Each connector in the ecosystem follows the same convention — a
    `docs/platform.md` recipe for the system it integrates with, accompanied by a
    sample Compose stack that mirrors [`services/`](https://github.com/Knuckles-Team).
    Systems offered only as a managed service (for example, ServiceNow) have no
    local recipe.

## Single-node deployment (Compose)

Egeria publishes the `egeria/egeria-platform` image. The following stack runs one
OMAG Server Platform on `:9443` with the persistent quick-start runtime:

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

## Connect egeria-mcp

```bash
export EGERIA_PLATFORM_URL=https://egeria.example.invalid:9443
export EGERIA_VIEW_SERVER=qs-view-server
export EGERIA_USER="${EGERIA_USER:?inject a service identity}"
export EGERIA_USER_PASSWORD="${EGERIA_USER_PASSWORD:?inject a runtime secret}"
export EGERIA_TLS_PROFILE=private-pki
export SSL_CERT_FILE=/run/secrets/private-ca-bundle.pem

egeria-mcp --transport streamable-http --host 0.0.0.0 --port 8000
```

## Combined deployment

A combined stack places the platform and the MCP server on one Docker network, so the
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
    image: example/egeria-mcp@sha256:<digest>
    depends_on: [egeria-platform]
    environment:
      - EGERIA_PLATFORM_URL=https://egeria-platform:9443
      - EGERIA_VIEW_SERVER=qs-view-server
      - EGERIA_TLS_PROFILE=private-pki
      - SSL_CERT_FILE=/run/secrets/private-ca-bundle.pem
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

## Populate Egeria from your estate

With the platform running and `EGERIA_ENABLE_WRITE=true`, the
[harvest CLI](usage.md#as-a-harvest-cli) populates Egeria bottom-up from your data
stores, ERPNext, GitLab, and 30+ other sources, then `reconcile` cross-links them
into one lineage/governance graph.
