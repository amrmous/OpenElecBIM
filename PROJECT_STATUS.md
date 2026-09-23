# OpenElecBIM Project Status

## Current Phase

Storage architecture and project portability.

## Completed

- Project repository established.
- Git/GitHub synchronization established.
- Large/local-only directories excluded from Git.
- Public storage metadata is separated into contributor, profile, object, replica, and contribution registries.
- Multiple local storage profiles supported.
- Google Drive adapter dependencies installed.
- Google Drive adapter import tested successfully.
- Legacy StorageManager retired after migration to StorageProfileRegistry, ProviderResolver, ProviderManager, and StorageService.
- Legacy storage example/local-profile schema retired.
- Storage direct dependencies documented.
- Storage refactor committed and pushed to GitHub.

Current storage commit:

41e7efd - Repair stale Google Drive replica

## Current Git State

The local main branch is synchronized with origin/main.

## In Progress

The decentralized Storage Pool implementation is not yet complete.

The next milestone is to register Contributor #001 and create a
controlled 50 GB local test storage profile on the F: drive.

## Upcoming

- Contributor model
- 50 GB test storage profile
- Knowledge Object schema
- content hashing
- storage references
- upload/retrieval workflow
- replica tracking
- provenance
- contribution ledger
- storage integrity tests
- failure/recovery tests
- complete Knowledge Engine integration
- open-source readiness audit

## Important Boundary

The F: drive is a test environment and must not be treated as the
permanent or sole storage location for OpenElecBIM knowledge.

Important project metadata, source code, schemas, and reproducibility
information must remain durable outside the test machine.

## Definition of Storage Completion

The storage layer should not be considered complete until the system
can demonstrably:

1. register a contributor;
2. register multiple storage profiles;
3. store a Knowledge Object;
4. calculate and preserve its content hash;
5. retrieve it;
6. verify its hash;
7. track its storage reference;
8. track replicas;
9. preserve provenance;
10. record contribution events;
11. recover from a failed storage location.
