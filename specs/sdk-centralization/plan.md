# CONN-EGERIA-MCP-SDK-CENTRALIZATION — Design and implementation plan

Governing spec: [spec.md](spec.md).

## Existing system and reuse

The connector reused SDK capabilities already: see the cited SDK rows. This spec moves the remaining direct vendor-library use onto the SDK.

## Architecture

- Governed HTTP client: SDK-CENTRALIZED-CAPABILITIES-R001, SDK-CENTRALIZED-CAPABILITIES-R008
- OpenBao token by reference: SDK-CENTRALIZED-CAPABILITIES-R009
- Database driver from the SDK extra: SDK-CENTRALIZED-CAPABILITIES-R040

## Interfaces and data model

No tool, argument or result changes. Only the transport and dependency declarations change.

## Live integration path

The fleet gateway calls a tool. The SDK tool surface calls the client method, which sends through the governed path named above.

## Quality and release gates

Run `pytest` in the repository and the pipelines `spec-status` hook. The change ships as a connector release.

## Risks, alternatives, and decisions

The governed client does not follow redirects and ignores ambient proxy variables. The TLS profile decides proxies.
