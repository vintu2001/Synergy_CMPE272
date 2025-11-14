# Knowledge Base Directory

This directory contains the organization's knowledge base documents for RAG retrieval.

## Directory Structure

```
kb/
├── policies/       # Apartment policies (noise, pets, parking, etc.)
├── sops/          # Standard Operating Procedures for staff
├── catalogs/      # Service catalogs (vendors, repair services, etc.)
├── slas/          # Service Level Agreements for maintenance
├── costs/         # Cost data (labor rates, parts, pricing, surcharges)
└── scoring/       # Decision scoring rules (weights, constraints, escalation)
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
- **type**: Document type (`policy`, `sop`, `catalog`, `sla`, `cost`, `scoring`)
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

### Costs
- Labor rates with hourly pricing and multipliers
- Parts catalogs with SKU, pricing, lead times
- Fixed-price SOP bundles
- Surcharges and credits (emergency, after-hours, SLA penalties)
- Approval thresholds and spending caps
- One rule or price per line for optimal retrieval

### Scoring
- Decision weights (normalized to sum 1.0)
- Hard constraints (SHALL/MUST rules, approval gates)
- Escalation triggers (human_escalation conditions)
- Tie-breaker preferences (vendor selection order)
- Scoring curves (metric normalization formulas)

## Ingestion (LangChain-Based)

The knowledge base uses a **LangChain-based ingestion pipeline** with frontmatter pre-processing, optimized text chunking, and ChromaDB vector storage.

### Quick Start

**Full ingestion (rebuild vector store):**
```bash
cd backend
python -c "from kb.langchain_ingest import ingest_kb_documents, print_ingestion_summary; \
stats = ingest_kb_documents(kb_dir='kb', persist_directory='./vector_stores/chroma_db', \
collection_name='apartment_kb', force_rebuild=True); print_ingestion_summary(stats)"
```

**Incremental ingestion (add new documents):**
```bash
python -c "from kb.langchain_ingest import ingest_kb_documents, print_ingestion_summary; \
stats = ingest_kb_documents(kb_dir='kb', persist_directory='./vector_stores/chroma_db', \
collection_name='apartment_kb', force_rebuild=False); print_ingestion_summary(stats)"
```

### Pipeline Architecture

The ingestion pipeline consists of three phases:

#### Phase 1: Frontmatter Pre-Processing
- Extracts YAML frontmatter from Markdown and CSV files
- Validates required metadata fields (doc_id, type, category, building_id, version)
- Sanitizes metadata for JSON-serializability
- Creates LangChain Documents with **clean, YAML-free bodies**

#### Phase 2: LangChain Pipeline
- **Text Splitting**: RecursiveCharacterTextSplitter with ~700 token target (2800 chars, 480 overlap)
- **Embeddings**: HuggingFaceEmbeddings with `sentence-transformers/all-MiniLM-L6-v2` (384-dim)
- **Vector Store**: ChromaDB with persistence at `./vector_stores/chroma_db`
- **Metadata**: Each chunk includes doc_id, type, category, building_id, version, chunk_id, chunk_index, total_chunks

#### Phase 3: Validation
- Chunk size validation (token estimates)
- Metadata coverage validation (100% required fields)
- Spot-check retrieval testing with known queries

### Testing

**Test Phase 1 (Frontmatter Extraction):**
```bash
python kb/test_phase1_frontmatter.py --kb-dir kb
```

**Test Phase 2 (Ingestion Pipeline):**
```bash
python kb/test_phase2_ingestion.py --kb-dir kb --persist-dir ./test_vector_stores/chroma_db
```

**Test Phase 3 (Validation):**
```bash
# Test all validations
python kb/test_phase3_validation.py --kb-dir kb --persist-dir ./vector_stores/chroma_db --collection-name apartment_kb

# Test specific validation
python kb/test_phase3_validation.py --test chunk-size     # Chunk size validation only
python kb/test_phase3_validation.py --test metadata       # Metadata coverage only
python kb/test_phase3_validation.py --test retrieval --collection-name apartment_kb    # Retrieval testing only
```

### Expected Results

- **Documents Loaded**: ~46 documents (excluding README.md)
- **Chunks Created**: ~97 chunks
- **Average Chunk Size**: ~196 tokens (acceptable for concise KB documents)
- **Metadata Coverage**: 100% (all chunks have required fields)
- **Vector Store Size**: ~1.7MB
- **Ingestion Time**: ~8 seconds

### Document Distribution

- **catalog**: 7% (service catalogs, vendor lists)
- **cost**: 23% (labor rates, parts, pricing)
- **policy**: 21% (apartment policies)
- **scoring**: 30% (decision weights, constraints)
- **sla**: 7% (service level agreements)
- **sop**: 12% (standard operating procedures)

---

## Cost Documents (kb/costs/)

### Purpose
Cost documents provide pricing data, billing rules, and financial thresholds for the Decision and Simulation agents to estimate expenses and enforce budget constraints.

### Document Types

#### 1. Labor & Billing Rules
- **Format:** CSV with YAML frontmatter
- **Content:** Hourly rates per trade (plumber, HVAC, electrician, locksmith, etc.)
- **Required fields:** Trade, skill level, hourly rate, minimum billable hours, billing increments, after-hours multipliers
- **Example:** `cost_all_buildings_labor_rates_1.0.csv`

#### 2. Parts & Materials Catalog
- **Format:** CSV with YAML frontmatter
- **Content:** SKU, part name, unit price, quantity, lead time, stock status
- **Target:** 20+ common parts per category (HVAC, plumbing, electrical, locksmith, appliance)
- **Bundles:** Common kits (AC leak detection, toilet repair, etc.)
- **Example:** `cost_all_buildings_parts_catalog_1.0.csv`

#### 3. Fixed-Price SOP Bundles
- **Format:** CSV with YAML frontmatter
- **Content:** Mapping of frequent SOPs to fixed price ranges
- **Includes:** Service name, category, urgency, fixed price, duration, parts included, exclusions
- **Example:** `cost_all_buildings_sop_bundles_1.0.csv`

#### 4. Surcharges & Credits
- **Format:** Markdown with YAML frontmatter
- **Content:** Emergency response fees, after-hours multipliers, distance charges, SLA penalties/credits
- **Style:** One rule per bullet point for optimal chunking
- **Example:** `cost_all_buildings_surcharges_1.0.md`

#### 5. Approval Thresholds
- **Format:** Markdown with YAML frontmatter
- **Content:** Spending limits by urgency level, category-specific caps, vendor requirements
- **Example:** `cost_all_buildings_approval_thresholds_1.0.md`

### Cost Document Acceptance Criteria
- ✅ Coverage: Labor rates + after-hours rules + 20+ common parts per target category
- ✅ Completeness: Every price has currency + unit, all chunks have required metadata
- ✅ Specificity: Building-specific docs exist OR functional all_buildings fallback
- ✅ Retrievability: Seeded query like "after-hours AC leak cost" returns relevant chunk with doc_id, rate, multiplier
- ✅ Freshness: effective_date and version are set, superseded prices marked or replaced

---

## Scoring Documents (kb/scoring/)

### Purpose
Scoring documents define the decision-making logic: how to weight factors, enforce constraints, trigger escalations, and normalize metrics for the Decision agent.

### Document Types

#### 1. Decision Weights
- **Format:** Markdown with YAML frontmatter
- **Content:** Normalized weights summing to 1.0 for: urgency/risk, time-to-resolve, direct cost, resident satisfaction, policy compliance
- **Includes:** Category-specific overrides (HVAC, plumbing, electrical, security, etc.)
- **Formula:** `Total Score = (w₁ × urgency) + (w₂ × time) + (w₃ × cost) + (w₄ × satisfaction) + (w₅ × compliance)`
- **Example:** `scoring_all_buildings_decision_weights_1.0.md`

#### 2. Constraints & Gates
- **Format:** Markdown with YAML frontmatter
- **Content:** Hard rules (SHALL/MUST clauses), cost approval gates, time-of-day restrictions, safety compliance requirements
- **Style:** Deterministic rules that bypass scoring (e.g., "SHALL NOT proceed if cost >$1,000 without approval")
- **Example:** `scoring_all_buildings_constraints_1.0.md`

#### 3. Escalation Matrix
- **Format:** Markdown with YAML frontmatter
- **Content:** Triggers for human_escalation=true (gas smell, structural damage, active flooding, etc.)
- **Minimum:** 3 clear triggers including time-based (after-hours + urgent)
- **Includes:** Escalation contact hierarchy, notification methods, documentation requirements
- **Example:** `scoring_all_buildings_escalation_matrix_1.0.md`

#### 4. Tie-Breakers & Preferences
- **Format:** Markdown with YAML frontmatter
- **Content:** Preference order when scores tie: policy-compliant DIY > vendor visit, preferred vendor > non-preferred
- **Secondary criteria:** Parts in stock, fewer dependencies, lower rework risk
- **Example:** `scoring_all_buildings_tie_breakers_1.0.md`

#### 5. Scoring Curves
- **Format:** Markdown with YAML frontmatter
- **Content:** Mapping raw metrics to 0.0-1.0 normalized sub-scores
- **Curves:** Cost penalty (piecewise), ETA thresholds (SLA-based), satisfaction heuristic (composite)
- **Example:** `scoring_all_buildings_scoring_curves_1.0.md`

### Scoring Document Acceptance Criteria
- ✅ Weights: Present and sum to 1.0 for each category/urgency demonstrated
- ✅ Caps/Gates: At least one explicit max_cost and one SHALL rule per critical category
- ✅ Escalation: At least 3 clear triggers including one time-based (after-hours)
- ✅ Determinism: With fixed Simulation metrics, Decision step picks same option every run
- ✅ Traceability: Every chosen option can cite both option sources (Simulation) and rules sources (Scoring KB) by doc_id

---

## Document Metadata Example (Cost Document)

```yaml
---
doc_id: "COST_001"
type: "cost"
category: "labor_rates"
building_id: "all_buildings"
effective_date: "2024-01-01"
last_updated: "2025-11-13"
version: "1.0"
keywords: ["labor", "hourly rate", "billing", "trade"]
author: "Property Management"
approver: "Finance Director"
---
```

## Document Metadata Example (Scoring Document)

```yaml
---
doc_id: "SCORING_001"
type: "scoring"
category: "decision_weights"
building_id: "all_buildings"
effective_date: "2024-01-01"
last_updated: "2025-11-13"
version: "1.0"
keywords: ["weights", "scoring", "priority", "decision"]
author: "Operations Manager"
approver: "General Manager"
---
```
