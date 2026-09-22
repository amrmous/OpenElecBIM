# OpenElecBIM

Open-source infrastructure for building structured, traceable engineering knowledge for Electrical BIM.

## Vision

OpenElecBIM is intended to provide a reusable foundation where electrical engineers and developers can contribute books, standards, electrical codes, previous projects, shop drawings, Revit/AutoCAD material, examples, and other supported engineering documents.

The long-term goal is to connect structured engineering knowledge with retrieval, reasoning, and BIM/CAD tools such as Revit and AutoCAD.

## Current Status

This repository contains the initial **Study Engine** foundation.

The current pipeline is:

# Engineering Document
# ↓ Docling
# ↓ Structured source representation
# ↓ hierarchical chunks
# ↑ knowledge.jsonl
# ↓ implementation manifest

The current implementation is a Phase 1 prototype focused on document ingestion, extraction, chunking, provenance, and traceable processed outputs.

The current system does not yet claim full semantic understanding, autonomous engineering design, or autonomous Revit/AutoCAD operation.

## Knowledge Library

Large engineering source files and processed knowledge datasets are intentionally kept outside this Git repository.

The external library can contain books, standards, codes, previous projects, shop drawings, Revit, AutoCAD, and other engineering examples.

## Configuration

Copy knowledge-engine/config/settings.example.json to settings.json and replace the placeholder paths with the local library path.

The local settings.json is intentionally ignored by Git because it contains machine-specific paths.

## Development

The project is being developed incrementally with focus on traceability, reproducibility, modular architecture, engineering-domain extensibility, and open contribution.

## Roadmap

Planned areas include multi-format document ingestion, improved OCR and multilingual processing, knowledge schemas, retrieval, engineering-aware retrieval and reasoning, standards and code modules, Revit and AutoCAD connectors, MCP/tool integrations, and testing and evaluation.
