# egeria-mcp Architecture

How the federation fits together: a raw-REST OMVS client, 34 bottom-up harvesters, a
cross-layer reconciliation pass, a completeness audit, and bidirectional federation
with the epistemic-graph knowledge graph.

## The federation pipeline

```mermaid
flowchart LR
    subgraph Sources["34 source systems"]
        direction TB
        S1["infra: hosts, swarm,<br/>DNS, Caddy"]
        S2["data: Postgres, Mongo,<br/>Qdrant, Jena, Kafka"]
        S3["business: ERPNext, Twenty,<br/>Firefly, emerald, Listmonk, ML"]
        S4["governance: Keycloak,<br/>OpenBao, ServiceNow"]
        S5["EA/knowledge: ArchiMate,<br/>LeanIX, Confluence, M365"]
        S6["code/work: GitLab, GitHub,<br/>Camunda, Ansible, Plane/Jira"]
        S7["collab/obs: Mattermost,<br/>Grafana, Uptime Kuma, ..."]
    end

    Sources -->|"harvest_*<br/>(config-driven, tolerant)"| EG[("Apache Egeria<br/>metadata SoR")]
    EG -->|"reconcile()<br/>13 matchers"| EG
    EG -->|"audit()"| RPT["coverage report<br/>+ island assets"]
    EG -->|"list_data_flows()"| KG[("epistemic-graph KG<br/>cognition / orchestration")]
    KG -.->|"governed_route() queries"| EG

    classDef store fill:#dae8fe,stroke:#6c8ebf;
    classDef proc fill:#d5e8d4,stroke:#82b366;
    class EG,KG store;
    class RPT proc;
```

A full run is **harvest → reconcile → audit**; `governed_route` then queries Egeria
governance + the now-cross-linked lineage to return policy-aware decisions.

## Layered client

```mermaid
flowchart TB
    MCP["MCP tools (mcp/mcp_egeria.py)<br/>reads · governed_route · harvest · reconcile · audit"]
    HARV["harvest/* (34 layers) + runner + reconcile + audit"]
    API["EgeriaApi (api/api_client_egeria.py)<br/>tolerant raw-httpx OMVS facade"]
    OMVS["Egeria View Server (OMVS REST)<br/>by-search-string · asset-maker · collection-manager<br/>glossary-manager · classification-explorer · lineage-linker"]
    MCP --> HARV --> API --> OMVS
    MCP --> API
    EXT["agent-utilities KG 'egeria' extractor"] -->|"list_* / list_data_flows"| API
```

No `pyegeria` runtime dependency — the facade speaks REST directly so it runs
identically on Python 3.11–3.14.

## Cross-linked graph (example)

How separately-harvested layers become one graph after `reconcile()`:

```mermaid
flowchart LR
    Repo["Repository::GitLab::app"] -->|deploys| Svc["Service::stack_app"]
    Svc -->|realizes| Store["DataStore::app-db"]
    Node["Node::host-1"] -->|hosts| Store
    Store -->|hosts| DS["Dataset::app-db::app"]
    Route["Route::app.example"] -->|routes-to| Svc
    Mon["Monitor::app"] -->|monitors| Route
    Client["Client::app"] -->|secures| Svc
    EA["ArchiMate::ApplicationComponent::App"] -->|realized-by| Svc
    DSrc["Datasource::Grafana::app-db"] -->|reads| Store
```

`governed_route(DataStore::app-db)` now sees upstream code/ingress and downstream
datasets — cross-layer impact, not an island.

## Bidirectional KG federation

```mermaid
sequenceDiagram
    participant SRC as Source systems
    participant API as EgeriaApi
    participant EG as Egeria (SoR)
    participant EXT as KG 'egeria' extractor
    participant KG as epistemic-graph

    SRC->>API: harvest (read)
    API->>EG: create assets + classifications
    API->>EG: reconcile → DataFlow cross-links
    EXT->>API: list_assets / list_glossary / list_data_flows
    API->>EG: scan catalogue + lineage
    API-->>EXT: nodes + flowsTo/dependsOn edges
    EXT->>KG: ExtractionBatch (domain=egeria, externalToolId=GUID)
    KG->>EG: governed_route() / graph_orchestrate queries
```

**Invariants:** the KG never becomes the lineage store; Egeria never orchestrates.
Federation key = `externalToolId` (Egeria GUID) + `domain="egeria"` on every node.
Edges: `:flowsTo` (data movement) and `:dependsOn` (structural), defined in
`ontology_egeria.ttl`.
