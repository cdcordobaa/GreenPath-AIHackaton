## Problem Statement

Environmental Impact Assessments (EIAs) are legally required for infrastructure projects in Colombia, but the current process is highly manual, time-consuming, and fragmented. Project developers and environmental authorities must analyze large amounts of geospatial data (rivers, forests, ecosystems, threatened species, etc.) and cross-reference these intersections with complex regulatory frameworks (Law 99 of 1993, Decree 1076 of 2015, ANLA methodologies, and resolutions such as 126 of 2024).

This process creates three main problems:

1. **Data Complexity** – Environmental and project data are stored in heterogeneous formats (e.g., ArcGIS geodatabases), making it difficult to perform consistent spatial analyses.
2. **Regulatory Complexity** – Each environmental intersection (e.g., a river crossing, forest clearing, or threatened species presence) triggers different permits, compensations, or restrictions under Colombian law. These requirements are spread across multiple legal documents and updated regularly.
3. **Operational Inefficiency** – Manual interpretation leads to delays, higher costs, and potential non-compliance. In practice, this often results in project re-designs, legal disputes, or environmental harm that could have been avoided with earlier, automated detection.

Without an intelligent system to automate spatial analysis and regulatory mapping, both developers and regulators face uncertainty and inefficiency in evaluating project viability and environmental compliance.

---

## Project Description

This project aims to build an **AI-powered tool for Environmental Impact Assessments (EIAs)** that automates the identification of environmental intersections and links them to corresponding Colombian regulations.

The system will:

- **Ingest GIS data** (e.g., project infrastructure layers like towers and transmission lines, and environmental layers such as forests, ecosystems, water bodies, and species distribution).
- **Perform spatial joins and intersections** to detect where projects overlap with sensitive environmental areas.
- **Map intersections to regulatory requirements** by applying a knowledge base of Colombian environmental law (Law 99/1993, Decree 1076/2015, ANLA methodologies, Resolution 126/2024, etc.).
- **Generate structured reports** that outline:
    - Which environmental components are affected (rivers, forests, species, etc.).
    - What permits, concessions, or compensations are required.
    - Which legal documents and sections apply.
    - Potential project risks or mitigation strategies.

### MVP Scope

- Focus on 5–6 key environmental layers (e.g., rivers, lakes, forests, threatened species, ecosystems, land cover).
- Implement rules that connect each type of intersection to specific permits and compensations.
- Prototype reporting system that produces a compliance/viability summary for a given project.

## Executive Summary

Infrastructure projects in Colombia must comply with strict environmental regulations, but today the process of evaluating their impacts is slow, manual, and error-prone. Project developers and authorities need to analyze large volumes of geographic data—such as rivers, forests, ecosystems, and threatened species—and cross-reference them with complex and evolving laws like Law 99 of 1993, Decree 1076 of 2015, and Resolution 126 of 2024. This fragmented approach often delays projects, increases costs, and risks non-compliance with critical environmental safeguards.

Our project addresses this challenge by developing an **AI-powered tool that automates environmental impact assessments (EIAs)**. The system ingests project infrastructure data and environmental GIS layers, identifies where they intersect, and instantly maps those intersections to the permits, compensations, and management measures required by Colombian law. The tool then generates a clear, structured report that highlights potential risks, required approvals, and next steps for compliance.

The initial version will focus on key environmental layers—such as rivers, lakes, forests, and threatened species—and the most relevant regulatory triggers. In the long term, the platform will expand to cover additional environmental data and regulations, offering a scalable solution that reduces uncertainty, saves time, and ensures responsible development in Colombia.

# High‑Level Workflow Architecture (MVP‑first)

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           Orchestrator (LLM + Graph)                     │
│        (LangGraph/agent loop; single shared EIA_State blackboard)        │
└──────────────────────────────────────────────────────────────────────────┘
                 │ ingest project shapefile/geojson + metadata
                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ N1. Project Ingestion + Normalization                                    │
│  • Read: project layers (lines, towers)                                  │
│  • Normalize CRS, simplify geometries                                    │
│  • Update EIA_State.project                                               │
└──────────────────────────────────────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ N2. Geospatial Analysis Loop  ⭯                                          │
│  Orchestrator iterates over target env layers:                           │
│   rivers, lakes, ecosystems, forests, species, land cover, PAs, etc.     │
│    ┌─────────────────────────────────────────────────────────────┐       │
│    │  MCP: Geo MCP (Supabase‑backed)                             │       │
│    │  Tools:                                                     │       │
│    │   • get_layer(<layer_key | iso_code | bbox>)                │       │
│    │   • spatial_join(project_layer, env_layer, predicate, buf)  │       │
│    │   • summarize_intersections(by=feature_type)                │       │
│    └─────────────────────────────────────────────────────────────┘       │
│  • Persist raw intersections + stats to EIA_State.intersections          │
└──────────────────────────────────────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ N3. Intersection Synthesis + Extraction                                   │
│  • Deduplicate/merge overlaps, compute areas/lengths/distances            │
│  • Produce “Affected Features List” + salient attributes                  │
│  • Update EIA_State.affected_features                                     │
└──────────────────────────────────────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ N4. LLM Summarizer + Keyword Elicitation                                  │
│  • Prompted summary of impacts by theme (water, flora/fauna, ecosystems)  │
│  • Extract legal triggers/keywords (e.g., “cruce de cauce”, “PTAR”, etc.) │
│  • Update EIA_State.legal_triggers (concepts, keywords, codes)            │
└──────────────────────────────────────────────────────────────────────────┘
                 │  triggers/keywords
                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ N5. Legal Scope Resolution (KG lookup via MCP)                            │
│   ┌─────────────────────────────────────────────────────────────────┐     │
│   │ MCP: Legal‑KB MCP                                              │     │
│   │  • For MVP: rule_table.csv + resources_index.json              │     │
│   │  • Long‑term: Graph DB (e.g., Neo4j/pgvector graph)            │     │
│   │ Tools:                                                         │     │
│   │  • map_triggers_to_rules(triggers[]) → legal_refs, permits     │     │
│   │  • list_resources(legal_refs[]) → doc URIs                      │     │
│   └─────────────────────────────────────────────────────────────────┘     │
│  • Update EIA_State.legal_scope (rules, permits, authorities)            │
└──────────────────────────────────────────────────────────────────────────┘
                 │  refs & URIs
                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ N6. Legal Analysis (document pull + LLM)                                  │
│  • Fetch legal texts (for MVP: full‑doc chunking or whole‑doc if small)   │
│  • LLM extracts required permits, compensations, mgmt plans, evidence     │
│  • Update EIA_State.compliance (requirements matrix)                       │
└──────────────────────────────────────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ N7. Report Assembly & Export                                              │
│  • Compose Markdown/HTML report                                           │
│  • Tables: intersections, legal mapping, next steps, evidence checklist   │
│  • Attach map snapshots/GeoJSON excerpts                                  │
│  • Store artifacts (Supabase Storage)                                     │
└──────────────────────────────────────────────────────────────────────────┘

```