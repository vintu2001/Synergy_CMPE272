# Knowledge Base Directory

This directory contains the organization's knowledge base documents for RAG retrieval.

## Directory Structure

```
kb/
├── policies/       # Apartment policies (noise, pets, parking, etc.)
├── sops/          # Standard Operating Procedures for staff
├── catalogs/      # Service catalogs (vendors, repair services, etc.)
└── slas/          # Service Level Agreements for maintenance
```

## Document Metadata Standards

All documents must include YAML frontmatter with the following metadata:

```yaml
---
doc_id: "POLICY_001"
type: "policy"
category: "noise_complaint"
building_id: "building_a"
effective_date: "2024-01-01"
last_updated: "2024-11-10"
version: "1.0"
keywords: ["noise", "quiet hours", "enforcement"]
---
```

### Required Fields

- **doc_id**: Unique identifier (format: TYPE_NNN)
- **type**: Document type (`policy`, `sop`, `catalog`, `sla`)
- **category**: Primary category matching classification taxonomy
- **building_id**: Building identifier (use `all_buildings` for universal docs)
- **effective_date**: When the document takes effect (YYYY-MM-DD)
- **last_updated**: Last modification date (YYYY-MM-DD)
- **version**: Semantic version number

### Optional Fields

- **keywords**: List of searchable terms
- **priority**: Priority level (`high`, `medium`, `low`)
- **tags**: Additional classification tags
- **author**: Document creator
- **approver**: Document approver

## Document Naming Convention

Format: `{type}_{building_id}_{category}_{version}.md`

Examples:
- `policy_building_a_noise_1.0.md`
- `sop_all_buildings_emergency_2.1.md`
- `catalog_building_b_vendors_1.0.csv`
- `sla_all_buildings_hvac_maintenance_1.0.md`

## Document Content Guidelines

### Policies
- Clear statement of rules and expectations
- Consequences for violations
- Reference to relevant regulations
- Escalation procedures

### SOPs
- Step-by-step procedures
- Required tools/resources
- Safety considerations
- Quality checks

### Catalogs
- Structured data (CSV preferred)
- Complete vendor/service information
- Contact details
- Pricing/timing information

### SLAs
- Response time commitments
- Service scope
- Performance metrics
- Escalation paths

## Validation

Run the validation script before committing new documents:

```bash
python -m app.rag.ingest.validate_kb
```

## Ingestion

To ingest documents into the vector store:

```bash
python -m app.rag.ingest.ingest_documents --full-rebuild
```

For incremental updates:

```bash
python -m app.rag.ingest.ingest_documents --incremental
```
