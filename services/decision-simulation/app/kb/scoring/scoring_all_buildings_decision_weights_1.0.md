---
doc_id: "SCORING_001"
type: "scoring"
category: "decision_weights"
building_id: "all_buildings"
effective_date: "2024-01-01"
last_updated: "2025-11-13"
version: "1.0"
keywords: ["weights", "scoring", "priority", "decision", "algorithm"]
author: "Operations Manager"
approver: "General Manager"
---

# Decision Scoring Weights

## Global Decision Formula

**Total Score = (urgency_weight × urgency_score) + (time_weight × time_score) + (cost_weight × cost_score) + (satisfaction_weight × satisfaction_score) + (compliance_weight × compliance_score)**

All weights sum to **1.0** for normalized scoring across all categories.

---

## Standard Weight Distribution (Default)

**Use for:** General maintenance requests, routine repairs, standard service calls

- **Urgency/Risk Weight:** 0.30 (30%)
- **Time-to-Resolve Weight:** 0.25 (25%)
- **Direct Cost Weight:** 0.20 (20%)
- **Resident Satisfaction Weight:** 0.15 (15%)
- **Policy Compliance Weight:** 0.10 (10%)

**Sum = 1.0** ✓

**Rationale:** Balanced approach prioritizing urgency and speed while keeping cost reasonable.

---

## Emergency Category Override

**Use for:** Active leaks, electrical hazards, gas leaks, security breaches, structural issues

- **Urgency/Risk Weight:** 0.50 (50%)
- **Time-to-Resolve Weight:** 0.30 (30%)
- **Direct Cost Weight:** 0.05 (5%)
- **Resident Satisfaction Weight:** 0.10 (10%)
- **Policy Compliance Weight:** 0.05 (5%)

**Sum = 1.0** ✓

**Rationale:** Safety and speed are paramount. Cost is nearly irrelevant in life-safety situations.

---

## HVAC Category Override (Temperature Extremes)

**Use for:** HVAC failures when outdoor temp <40°F or >90°F, affecting habitability

- **Urgency/Risk Weight:** 0.35 (35%)
- **Time-to-Resolve Weight:** 0.35 (35%)
- **Direct Cost Weight:** 0.15 (15%)
- **Resident Satisfaction Weight:** 0.10 (10%)
- **Policy Compliance Weight:** 0.05 (5%)

**Sum = 1.0** ✓

**Rationale:** HVAC in extreme weather is urgent for health/safety. Time and urgency equally weighted.

---

## Plumbing Category Override (Water Issues)

**Use for:** Water leaks, sewage backups, no water service, flooding risks

- **Urgency/Risk Weight:** 0.40 (40%)
- **Time-to-Resolve Weight:** 0.30 (30%)
- **Direct Cost Weight:** 0.10 (10%)
- **Resident Satisfaction Weight:** 0.15 (15%)
- **Policy Compliance Weight:** 0.05 (5%)

**Sum = 1.0** ✓

**Rationale:** Water damage escalates quickly. Resident satisfaction high due to habitability impact.

---

## Electrical Category Override

**Use for:** Electrical hazards, power outages (single unit), exposed wiring, smoking outlets

- **Urgency/Risk Weight:** 0.45 (45%)
- **Time-to-Resolve Weight:** 0.25 (25%)
- **Direct Cost Weight:** 0.10 (10%)
- **Resident Satisfaction Weight:** 0.10 (10%)
- **Policy Compliance Weight:** 0.10 (10%)

**Sum = 1.0** ✓

**Rationale:** Electrical issues are fire hazards. Code compliance important for inspection liability.

---

## Security Category Override

**Use for:** Broken locks, door damage, security breaches, forced entry aftermath

- **Urgency/Risk Weight:** 0.45 (45%)
- **Time-to-Resolve Weight:** 0.40 (40%)
- **Direct Cost Weight:** 0.05 (5%)
- **Resident Satisfaction Weight:** 0.05 (5%)
- **Policy Compliance Weight:** 0.05 (5%)

**Sum = 1.0** ✓

**Rationale:** Security must be restored immediately. Speed is critical, cost is secondary.

---

## Cosmetic/Aesthetic Category Override

**Use for:** Painting, minor drywall, non-critical repairs, aesthetic improvements

- **Urgency/Risk Weight:** 0.10 (10%)
- **Time-to-Resolve Weight:** 0.15 (15%)
- **Direct Cost Weight:** 0.40 (40%)
- **Resident Satisfaction Weight:** 0.25 (25%)
- **Policy Compliance Weight:** 0.10 (10%)

**Sum = 1.0** ✓

**Rationale:** Cost-effectiveness is key for non-urgent work. Resident satisfaction matters for retention.

---

## Preventative Maintenance Override

**Use for:** Scheduled inspections, filter changes, routine service, seasonal prep

- **Urgency/Risk Weight:** 0.15 (15%)
- **Time-to-Resolve Weight:** 0.20 (20%)
- **Direct Cost Weight:** 0.35 (35%)
- **Resident Satisfaction Weight:** 0.10 (10%)
- **Policy Compliance Weight:** 0.20 (20%)

**Sum = 1.0** ✓

**Rationale:** Preventative work should be cost-effective and policy-compliant to avoid future issues.

---

## Resident-Caused Damage Override

**Use for:** Lockouts, resident negligence, abuse, intentional damage (billable work)

- **Urgency/Risk Weight:** 0.25 (25%)
- **Time-to-Resolve Weight:** 0.20 (20%)
- **Direct Cost Weight:** 0.30 (30%)
- **Resident Satisfaction Weight:** 0.05 (5%)
- **Policy Compliance Weight:** 0.20 (20%)

**Sum = 1.0** ✓

**Rationale:** Cost recovery important since billable. Compliance ensures proper billing documentation.

---

## Multi-Unit Impact Override

**Use for:** Issues affecting 4+ units, building-wide problems, systemic failures

- **Urgency/Risk Weight:** 0.35 (35%)
- **Time-to-Resolve Weight:** 0.30 (30%)
- **Direct Cost Weight:** 0.10 (10%)
- **Resident Satisfaction Weight:** 0.20 (20%)
- **Policy Compliance Weight:** 0.05 (5%)

**Sum = 1.0** ✓

**Rationale:** Multiple residents affected increases urgency and satisfaction impact significantly.

---

## After-Hours Service Override

**Use for:** Work requested or required outside business hours (5 PM - 7 AM, weekends)

- **Urgency/Risk Weight:** 0.40 (40%)
- **Time-to-Resolve Weight:** 0.25 (25%)
- **Direct Cost Weight:** 0.25 (25%)
- **Resident Satisfaction Weight:** 0.05 (5%)
- **Policy Compliance Weight:** 0.05 (5%)

**Sum = 1.0** ✓

**Rationale:** After-hours multipliers are expensive. Cost becomes more important unless truly urgent.

---

## Budget-Constrained Period Override

**Use for:** End of quarter/year, over-budget categories, cost reduction initiatives

- **Urgency/Risk Weight:** 0.25 (25%)
- **Time-to-Resolve Weight:** 0.15 (15%)
- **Direct Cost Weight:** 0.40 (40%)
- **Resident Satisfaction Weight:** 0.10 (10%)
- **Policy Compliance Weight:** 0.10 (10%)

**Sum = 1.0** ✓

**Rationale:** Financial constraints require cost optimization while maintaining safety standards.

---

## Warranty/Insurance Claim Override

**Use for:** Work covered by warranty or insurance, third-party liability

- **Urgency/Risk Weight:** 0.20 (20%)
- **Time-to-Resolve Weight:** 0.25 (25%)
- **Direct Cost Weight:** 0.10 (10%)
- **Resident Satisfaction Weight:** 0.15 (15%)
- **Policy Compliance Weight:** 0.30 (30%)

**Sum = 1.0** ✓

**Rationale:** Documentation and compliance critical for claim approval. Cost less relevant if covered.

---

## Recurring Issue Override (3rd+ Occurrence)

**Use for:** Same problem in same unit within 90 days, pattern of failures

- **Urgency/Risk Weight:** 0.25 (25%)
- **Time-to-Resolve Weight:** 0.20 (20%)
- **Direct Cost Weight:** 0.20 (20%)
- **Resident Satisfaction Weight:** 0.25 (25%)
- **Policy Compliance Weight:** 0.10 (10%)

**Sum = 1.0** ✓

**Rationale:** Resident frustration is high. May need root cause fix vs. repeated band-aids.

---

## Inspection/Audit Period Override

**Use for:** City inspections, insurance audits, compliance reviews, licensing renewals

- **Urgency/Risk Weight:** 0.20 (20%)
- **Time-to-Resolve Weight:** 0.25 (25%)
- **Direct Cost Weight:** 0.15 (15%)
- **Resident Satisfaction Weight:** 0.05 (5%)
- **Policy Compliance Weight:** 0.35 (35%)

**Sum = 1.0** ✓

**Rationale:** Code compliance and documentation critical during official inspections.

---

## Seasonal Priority Adjustments

### Winter (December - February)

- **HVAC heating failures:** +0.10 to urgency weight (from standard baseline)
- **Frozen pipe prevention:** +0.10 to urgency weight
- **Snow removal/ice:** +0.10 to time weight
- **Heating system preventative:** +0.05 to compliance weight

### Summer (June - August)

- **HVAC cooling failures:** +0.10 to urgency weight (from standard baseline)
- **Water leak detection:** +0.05 to urgency weight (landscaping/exterior)
- **AC preventative maintenance:** +0.05 to compliance weight
- **Pool safety (if applicable):** +0.10 to compliance weight

### Spring (March - May)

- **Exterior maintenance:** +0.05 to satisfaction weight (curb appeal)
- **Turnover season:** +0.05 to time weight (faster unit turnaround)
- **Landscaping:** +0.05 to satisfaction weight
- **Roof inspections:** +0.05 to compliance weight (storm season prep)

### Fall (September - November)

- **Heating system prep:** +0.05 to compliance weight (winter readiness)
- **Gutter cleaning:** +0.05 to compliance weight (water damage prevention)
- **Weather sealing:** +0.05 to cost weight (energy efficiency)
- **Fire safety inspection:** +0.10 to compliance weight (heating season)

---

## Score Interpretation Guidelines

### High Priority (Total Score ≥ 0.75)

- **Action:** Immediate dispatch, same-day response target
- **Escalation:** Notify property manager if score ≥ 0.85
- **Documentation:** Full incident report required

### Medium Priority (Total Score 0.50 - 0.74)

- **Action:** Next available appointment, 24-48 hour target
- **Escalation:** Notify maintenance supervisor
- **Documentation:** Standard work order

### Standard Priority (Total Score 0.30 - 0.49)

- **Action:** Scheduled within 72 hours
- **Escalation:** None required
- **Documentation:** Standard work order

### Low Priority (Total Score < 0.30)

- **Action:** Scheduled maintenance batch, 5-7 day target
- **Escalation:** None required
- **Documentation:** Basic work order note

---

## Weight Selection Logic for Decision Agent

1. **Check for life-safety keywords:** Use Emergency override if detected
2. **Check category:** Apply category-specific override if applicable
3. **Check time of day:** Apply after-hours override if outside business hours
4. **Check multi-unit impact:** Apply multi-unit override if ≥4 units affected
5. **Check seasonal factors:** Apply seasonal adjustments if applicable
6. **Default:** Use Standard weight distribution if no overrides match
