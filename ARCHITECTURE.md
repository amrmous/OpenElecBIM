# OpenElecBIM Architecture

## 1. Project Purpose

OpenElecBIM is an open-source engineering knowledge platform focused on
electrical engineering, BIM, design, documentation, and engineering
knowledge reuse.

The platform is designed so that engineers can contribute engineering
knowledge from multiple file types and multiple storage providers.

Examples include:

- PDF
- DOCX
- XLSX
- PPTX
- TXT
- Markdown
- Revit
- AutoCAD
- IFC
- BIM exchange formats
- Images
- Engineering project archives
- Future supported formats

The project must not depend on a single engineer, a single computer,
or a single cloud storage account.

---

## 2. High-Level Architecture

Contributor
    |
    +-- Contributor Identity
    |
    +-- Storage Profile(s)
    |       |
    |       +-- Local Storage
    |       +-- Google Drive
    |       +-- Future Providers
    |
    +-- Knowledge Contributions
            |
            +-- Knowledge Objects
            +-- Metadata
            +-- Provenance
            +-- Versions
            +-- Replicas
            +-- Contribution Ledger

Knowledge Objects
    |
    +-- Storage Layer
    |
    +-- Ingestion
    |
    +-- Parsing / Extraction
    |
    +-- Knowledge Engine
    |
    +-- Retrieval / Study / AI

---

## 3. Decentralized Storage Pool

OpenElecBIM uses a decentralized contributor-oriented storage model.

A Contributor may have:

- multiple storage profiles
- multiple Google Drive accounts
- multiple local storage locations
- multiple providers
- multiple replicas of the same Knowledge Object

The architecture must never assume:

"one contributor = one storage account"

or:

"the project = one central drive"

Storage providers are replaceable infrastructure.

---

## 4. Public and Private Configuration

Public project configuration is stored in Git and may be shared publicly.

Examples:

- storage provider definitions
- public storage metadata
- project-level schemas
- public manifests
- architecture and documentation

Private configuration remains local and must never be committed.

Examples:

- credentials
- OAuth configuration
- access tokens
- private account identifiers
- private filesystem paths
- local machine state

The current separation is:

- storage/config/storage_registry.json
- storage/config/storage_profile_registry.json
- storage/config/knowledge_object_registry.json
- storage/config/replica_registry.json
- storage/config/contribution_ledger.json

Private provider credentials and OAuth tokens remain outside the public registry architecture.

Private provider credentials and OAuth tokens remain outside Git and outside the public storage metadata architecture.

---

## 5. Knowledge Objects

A physical file is not the complete identity of engineering knowledge.

OpenElecBIM treats contributed data as Knowledge Objects.

A Knowledge Object should eventually contain concepts such as:

- object_id
- content_hash
- original_name
- source_type
- contributor
- storage references
- version
- creation/ingestion timestamps
- provenance
- parser/adapter information
- processing status
- replica information

The content hash provides stable content identity independent of the
physical storage location.

---

## 6. Storage References and Replicas

A Knowledge Object may exist in more than one physical location.

Example:

Knowledge Object
    |
    +-- Replica A -> Contributor local storage
    |
    +-- Replica B -> Google Drive
    |
    +-- Replica C -> Future provider

The loss or replacement of one storage provider must not invalidate
the logical Knowledge Object.

Storage references therefore describe where the object can be found,
while the Knowledge Object identity remains independent of the provider.

---

## 7. Provenance

Engineering knowledge must preserve its origin.

The system should be able to answer:

- Who contributed the object?
- Where did it originate?
- What was the original filename?
- When was it ingested?
- Which adapter/parser processed it?
- What is its content hash?
- Which versions exist?
- Where are replicas stored?

Provenance is a core requirement because engineering knowledge must
remain traceable.

---

## 8. Contribution Ledger

OpenElecBIM will maintain a verifiable contribution history.

The Contribution Ledger is intended to record contribution events such as:

- contributor identity
- contributed Knowledge Object
- contribution timestamp
- storage contribution
- version/event information
- verification information

The ledger is a project-level accountability mechanism and is separate
from private credentials.

---

## 9. Storage Contribution Model

The first project user is Contributor #001.

Contributor #001 will provide approximately 50 GB of local storage
capacity from the F: drive as a controlled test storage contribution.

This storage is initially intended for:

- integration testing
- storage pool testing
- ingestion testing
- retrieval testing
- replication testing
- hash verification
- metadata verification
- failure/recovery testing

The 50 GB test contribution is not considered the permanent central
storage of the project.

It is a real contributor storage profile used to validate the
decentralized architecture.

---

## 10. GitHub and External Storage

GitHub is intended primarily for:

- source code
- schemas
- documentation
- manifests
- configuration examples
- metadata required for reproducibility

Large engineering datasets should normally remain outside GitHub.

External storage may contain:

- engineering projects
- Revit files
- CAD files
- reference books
- datasets
- processed knowledge
- other large engineering assets

GitHub should retain durable references/manifests necessary to locate
and understand externally stored project data without exposing private
credentials.

---

## 11. Security Boundary

Credentials and private access information must remain outside the
public repository.

Examples:

- OAuth client secrets
- refresh tokens
- private storage configuration
- private account information
- machine-specific paths
- local state

Public registry data must never be used as a credential store.

---

## 12. Current Implementation

The current storage layer provides:

- public storage registry
- local/private storage configuration
- multiple local storage profiles
- provider abstraction
- Google Drive adapter
- storage manager
- direct dependency declaration
- Git-safe private configuration separation

The architecture is intentionally being implemented incrementally.

---

## 13. Next Implementation Stage

The next storage milestones are:

1. Register Contributor #001.
2. Create the 50 GB test storage profile on F:.
3. Define the storage pool data model.
4. Define Knowledge Object schema.
5. Implement object hashing.
6. Implement storage references.
7. Implement upload/store operations.
8. Implement retrieval operations.
9. Verify content hashes after retrieval.
10. Add replica tracking.
11. Add contribution events.
12. Test failure and recovery scenarios.
13. Document the complete storage workflow.

---

## 14. Design Principle

No single computer, drive, provider, or contributor should become a
single point of failure for the logical knowledge system.

The storage layer is infrastructure.

Knowledge identity, provenance, contribution history, and metadata must
remain independent from any individual storage provider.
