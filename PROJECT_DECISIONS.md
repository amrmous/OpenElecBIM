# OpenElecBIM Project Decisions

## Decision 001 - Decentralized Contributor Storage

OpenElecBIM will use a contributor-oriented storage architecture.

A contributor can have multiple storage profiles and multiple providers.

Status: Accepted

---

## Decision 002 - Public Registry vs Private Configuration

Public storage metadata is maintained through dedicated registries under
storage/config/.

Core public registries include:
- storage_registry.json for contributor authority
- storage_profile_registry.json for storage profiles
- knowledge_object_registry.json for canonical knowledge objects
- replica_registry.json for storage replicas
- contribution_ledger.json for contribution history and verification

Private authentication credentials and provider access tokens must remain
outside Git and outside the public storage metadata model.

The active storage architecture must not depend on a legacy local-profile
configuration file.

Status: Accepted

---

## Decision 003 - Multiple Storage Providers

The system must not assume Google Drive is the only provider.

Google Drive is an initial adapter.

The architecture must allow additional providers later.

Status: Accepted

---

## Decision 004 - Knowledge Object Identity

Knowledge Objects will have logical identity independent of their
physical storage location.

Content hashing will be used as a core mechanism for content identity
and integrity verification.

Status: Accepted

---

## Decision 005 - Replication

A Knowledge Object may have multiple replicas.

Replica information belongs to the storage/metadata layer and does not
change the logical identity of the Knowledge Object.

Status: Accepted

---

## Decision 006 - Provenance

Engineering knowledge must preserve provenance.

Source, contributor, ingestion information, parser/adapter information,
hashes, and version information are part of the long-term design.

Status: Accepted

---

## Decision 007 - Contribution Ledger

Contribution events will be recorded separately from private credentials.

The ledger is intended to make contributions traceable and verifiable.

Status: Accepted

---

## Decision 008 - First Test Contributor

Contributor #001 will provide approximately 50 GB of local F: drive
capacity for controlled project testing.

This is a test contribution and is not defined as permanent central
project storage.

Status: Accepted

---

## Decision 009 - GitHub vs Large Data

GitHub will contain source code, schemas, documentation, manifests,
examples, and reproducibility metadata.

Large engineering datasets should normally remain in external storage.

Status: Accepted

---

## Decision 010 - No Single Storage Dependency

The logical OpenElecBIM knowledge system must not depend on one machine,
one drive, one provider, or one contributor.

Status: Accepted
