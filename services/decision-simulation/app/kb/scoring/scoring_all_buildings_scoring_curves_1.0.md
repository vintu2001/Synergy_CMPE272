---
doc_id: "SCORING_005"
type: "scoring"
category: "scoring_curves"
building_id: "all_buildings"
effective_date: "2024-01-01"
last_updated: "2025-11-13"
version: "1.0"
keywords: ["normalization", "scoring curves", "metrics", "sub-scores", "formula"]
author: "Operations Manager"
approver: "General Manager"
---

# Scoring Curves & Metric Normalization

## Purpose

Convert raw metrics (dollars, hours, satisfaction ratings) into normalized 0.0-1.0 sub-scores for weighted decision scoring. All sub-scores feed into the decision formula:

**Total Score = (w₁ × urgency_score) + (w₂ × time_score) + (w₃ × cost_score) + (w₄ × satisfaction_score) + (w₅ × compliance_score)**

Where all weights sum to 1.0 and all sub-scores range from 0.0 (worst) to 1.0 (best).

---

## 1. Urgency/Risk Score (0.0 - 1.0)

### Input: Urgency Classification + Risk Factors

**Base Urgency Levels:**
- **Emergency (life-safety):** 1.00
- **Urgent (24-48h SLA):** 0.75
- **Standard (72h+ SLA):** 0.50
- **Non-Urgent (scheduled):** 0.25

**Risk Factor Adjustments (Add to Base):**
- **Multi-unit impact (≥4 units):** +0.10
- **Recurring issue (3rd+ occurrence):** +0.10
- **Property damage escalating:** +0.15
- **Weather exacerbating (HVAC in extremes):** +0.10
- **Safety code violation:** +0.15
- **After-hours (10 PM - 7 AM):** +0.05

**Maximum capped at 1.00**

### Example Calculations

**Example 1:** AC not cooling, urgent, single unit, summer heat wave
- Base urgency: 0.75
- Weather factor: +0.10
- **Final urgency_score = 0.85**

**Example 2:** Clogged sink, standard, single unit, no special factors
- Base urgency: 0.50
- No adjustments
- **Final urgency_score = 0.50**

**Example 3:** Water leak, emergency, affecting 5 units, late night
- Base urgency: 1.00
- Multi-unit: (already capped, no add)
- **Final urgency_score = 1.00** (capped)

---

## 2. Time-to-Resolve Score (0.0 - 1.0)

### Input: Estimated Time to Complete (ETA in hours)

**Scoring Formula: Linear Penalty Beyond SLA Target**

- **ETA ≤ SLA target:** 1.00 (perfect score)
- **ETA > SLA target:** Penalty applied

**SLA Targets by Urgency:**
- **Emergency:** 4 hours → penalty starts at >4h
- **Urgent:** 48 hours → penalty starts at >48h
- **Standard:** 168 hours (7 days) → penalty starts at >168h
- **Non-Urgent:** No penalty (scheduled work)

**Penalty Calculation:**

```
If ETA ≤ SLA_target:
    time_score = 1.00

If ETA > SLA_target:
    overage_hours = ETA - SLA_target
    penalty_per_hour = 0.01  (lose 0.01 per hour over)
    time_score = 1.00 - (overage_hours × penalty_per_hour)
    time_score = max(0.00, time_score)  # floor at 0
```

### Example Calculations

**Example 1:** Emergency repair, ETA 3 hours (SLA = 4h)
- ETA ≤ SLA → **time_score = 1.00**

**Example 2:** Emergency repair, ETA 6 hours (SLA = 4h)
- Overage: 6 - 4 = 2 hours
- Penalty: 2 × 0.01 = 0.02
- **time_score = 1.00 - 0.02 = 0.98**

**Example 3:** Urgent repair, ETA 72 hours (SLA = 48h)
- Overage: 72 - 48 = 24 hours
- Penalty: 24 × 0.01 = 0.24
- **time_score = 1.00 - 0.24 = 0.76**

**Example 4:** Standard repair, ETA 240 hours / 10 days (SLA = 168h / 7 days)
- Overage: 240 - 168 = 72 hours
- Penalty: 72 × 0.01 = 0.72
- **time_score = 1.00 - 0.72 = 0.28**

**Example 5:** Urgent repair, ETA 200 hours (massive overage)
- Overage: 200 - 48 = 152 hours
- Penalty: 152 × 0.01 = 1.52 (exceeds 1.0)
- **time_score = max(0.00, 1.00 - 1.52) = 0.00** (floor)

---

## 3. Direct Cost Score (0.0 - 1.0)

### Input: Total Estimated Cost (USD)

**Scoring Formula: Piecewise Linear with Thresholds**

**Cost Thresholds (Category-Aware):**

| **Cost Range** | **Score** | **Rationale** |
|----------------|-----------|---------------|
| $0 - $100 | 1.00 | Minimal cost, excellent |
| $101 - $300 | 0.90 | Low cost, good |
| $301 - $600 | 0.75 | Moderate cost, acceptable |
| $601 - $1,000 | 0.60 | Higher cost, requires justification |
| $1,001 - $2,000 | 0.45 | Significant cost, supervisor approval |
| $2,001 - $5,000 | 0.30 | Major cost, manager approval |
| $5,001 - $10,000 | 0.15 | Very high cost, regional approval |
| >$10,000 | 0.05 | Extreme cost, executive approval |

**Interpolation Between Thresholds (Linear):**

```python
def cost_score(cost_usd):
    thresholds = [
        (0, 100, 1.00),
        (100, 300, 0.90),
        (300, 600, 0.75),
        (600, 1000, 0.60),
        (1000, 2000, 0.45),
        (2000, 5000, 0.30),
        (5000, 10000, 0.15),
        (10000, float('inf'), 0.05)
    ]
    
    for min_cost, max_cost, score in thresholds:
        if min_cost <= cost_usd <= max_cost:
            return score
    
    return 0.05  # Fallback for extreme costs
```

### Example Calculations

**Example 1:** Filter replacement, $75 cost
- Range: $0-$100 → **cost_score = 1.00**

**Example 2:** Faucet repair, $250 cost
- Range: $101-$300 → **cost_score = 0.90**

**Example 3:** AC capacitor replacement, $400 cost
- Range: $301-$600 → **cost_score = 0.75**

**Example 4:** Water heater replacement, $1,500 cost
- Range: $1,001-$2,000 → **cost_score = 0.45**

**Example 5:** HVAC unit replacement, $6,500 cost
- Range: $5,001-$10,000 → **cost_score = 0.15**

**Example 6:** Major plumbing re-pipe, $18,000 cost
- Range: >$10,000 → **cost_score = 0.05**

---

## 4. Resident Satisfaction Score (0.0 - 1.0)

### Input: Heuristic Based on Multiple Factors

**Satisfaction Formula (Composite Heuristic):**

```
satisfaction_score = 
    (0.40 × speed_factor) +
    (0.30 × disruption_factor) +
    (0.20 × communication_factor) +
    (0.10 × quality_factor)
```

**Sub-Factor Calculations:**

### Speed Factor (0.0 - 1.0)
- **Same-day resolution:** 1.00
- **Next-day resolution:** 0.90
- **2-3 day resolution:** 0.80
- **4-7 day resolution:** 0.60
- **8-14 day resolution:** 0.40
- **>14 day resolution:** 0.20

### Disruption Factor (0.0 - 1.0)
- **No unit access required (DIY instructions):** 1.00
- **Single short visit (<1 hour):** 0.90
- **Single long visit (1-3 hours):** 0.75
- **Multiple visits required:** 0.60
- **Major disruption (moving furniture, shutoff utilities):** 0.40
- **Resident must vacate temporarily:** 0.20

### Communication Factor (0.0 - 1.0)
- **Real-time updates + appointment confirmation:** 1.00
- **Appointment confirmation only:** 0.80
- **Generic "we'll contact you" message:** 0.60
- **No communication, resident must follow up:** 0.30

### Quality Factor (0.0 - 1.0)
- **Permanent fix, warranty included:** 1.00
- **Permanent fix, no explicit warranty:** 0.85
- **Temporary repair, permanent scheduled:** 0.60
- **Temporary patch, no permanent plan:** 0.30

### Example Calculations

**Example 1:** Emergency lockout, locksmith arrives in 45 minutes
- Speed: Same-day → 1.00
- Disruption: Single short visit → 0.90
- Communication: Real-time updates → 1.00
- Quality: Permanent fix → 1.00
- **satisfaction_score = (0.40×1.00) + (0.30×0.90) + (0.20×1.00) + (0.10×1.00) = 0.97**

**Example 2:** AC repair, 2-day turnaround, 2-hour visit, good communication
- Speed: 2-3 day → 0.80
- Disruption: Single long visit → 0.75
- Communication: Confirmation → 0.80
- Quality: Permanent + warranty → 1.00
- **satisfaction_score = (0.40×0.80) + (0.30×0.75) + (0.20×0.80) + (0.10×1.00) = 0.795**

**Example 3:** Leak repair, 10-day wait, multiple visits, poor communication, temporary patch
- Speed: 8-14 day → 0.40
- Disruption: Multiple visits → 0.60
- Communication: No updates → 0.30
- Quality: Temporary patch → 0.30
- **satisfaction_score = (0.40×0.40) + (0.30×0.60) + (0.20×0.30) + (0.10×0.30) = 0.43**

---

## 5. Policy Compliance Score (0.0 - 1.0)

### Input: Compliance Checklist (Binary Yes/No)

**Compliance Factors (Equal Weight):**

1. **Licensed contractor (if required by work type):** Required for permit work
2. **Insurance verified (≥$1M coverage):** All vendors
3. **Background check completed (if building access):** Within 24 months
4. **Permit obtained (if required by jurisdiction):** Electrical panel, gas, structural
5. **Code compliant (meets NEC, UPC, IBC standards):** All work
6. **Safety protocols followed (OSHA, EPA):** Refrigerant, asbestos, lead paint
7. **Documentation complete (work order, photos, sign-off):** All work >$300
8. **Warranty provided (if standard for work type):** Parts + labor terms
9. **Resident notification (if unit access required):** 24h notice unless emergency
10. **Approval chain followed (if cost threshold exceeded):** Per approval matrix

**Scoring Formula:**

```
compliance_score = (number_of_yes) / (total_applicable_factors)

Example: 8 out of 10 factors met → compliance_score = 8/10 = 0.80
```

**Hard Fail Conditions (compliance_score = 0.00):**
- **Unlicensed work requiring license** (electrical, plumbing, gas)
- **No insurance for vendor work** (liability exposure)
- **Code violation** (building inspector red tag risk)

### Example Calculations

**Example 1:** DIY filter replacement (resident-performed, policy-compliant)
- Applicable factors: 3 (code compliant, resident notification, documentation)
- Factors met: 3
- **compliance_score = 3/3 = 1.00**

**Example 2:** Standard plumbing repair by preferred vendor
- Applicable factors: 10 (all)
- Factors met: 9 (missing: permit not required)
- **compliance_score = 9/10 = 0.90**

**Example 3:** Emergency electrical work, licensed electrician, permit waived due to emergency
- Applicable factors: 10
- Factors met: 9 (permit waived but documented)
- **compliance_score = 9/10 = 0.90**

**Example 4:** Non-licensed handyman performing electrical panel work (VIOLATION)
- **compliance_score = 0.00** (hard fail - unlicensed work)

---

## Complete Decision Scoring Example

**Scenario:** AC not cooling, urgent, summer heat wave (outdoor temp 95°F)

### Option A: Preferred Vendor, $380 cost, 4-hour ETA

**Sub-Score Calculations:**

1. **Urgency Score:**
   - Base urgent: 0.75
   - Weather factor: +0.10
   - **urgency_score = 0.85**

2. **Time Score:**
   - ETA 4 hours, SLA 48 hours
   - Well under SLA
   - **time_score = 1.00**

3. **Cost Score:**
   - $380 cost
   - Range: $301-$600
   - **cost_score = 0.75**

4. **Satisfaction Score:**
   - Speed: Same-day (1.00)
   - Disruption: 2-hour visit (0.75)
   - Communication: Real-time updates (1.00)
   - Quality: Permanent fix + warranty (1.00)
   - **satisfaction_score = (0.40×1.00) + (0.30×0.75) + (0.20×1.00) + (0.10×1.00) = 0.925**

5. **Compliance Score:**
   - 10/10 factors met (preferred vendor, all docs, licensed, insured)
   - **compliance_score = 1.00**

**Weighted Total Score (Using HVAC Category Weights):**
- Urgency weight: 0.35
- Time weight: 0.35
- Cost weight: 0.15
- Satisfaction weight: 0.10
- Compliance weight: 0.05

```
Total Score = (0.35 × 0.85) + (0.35 × 1.00) + (0.15 × 0.75) + (0.10 × 0.925) + (0.05 × 1.00)
            = 0.2975 + 0.35 + 0.1125 + 0.0925 + 0.05
            = 0.9025
```

**Option A Total Score: 0.90** (High Priority)

---

### Option B: Approved Vendor, $290 cost, 24-hour ETA

**Sub-Score Calculations:**

1. **urgency_score = 0.85** (same as Option A)

2. **Time Score:**
   - ETA 24 hours, SLA 48 hours
   - Under SLA
   - **time_score = 1.00**

3. **Cost Score:**
   - $290 cost
   - Range: $101-$300
   - **cost_score = 0.90**

4. **Satisfaction Score:**
   - Speed: Next-day (0.90)
   - Disruption: 2-hour visit (0.75)
   - Communication: Confirmation only (0.80)
   - Quality: Permanent fix, no warranty (0.85)
   - **satisfaction_score = (0.40×0.90) + (0.30×0.75) + (0.20×0.80) + (0.10×0.85) = 0.850**

5. **Compliance Score:**
   - 9/10 factors met (no warranty provided)
   - **compliance_score = 0.90**

**Weighted Total Score:**
```
Total Score = (0.35 × 0.85) + (0.35 × 1.00) + (0.15 × 0.90) + (0.10 × 0.85) + (0.05 × 0.90)
            = 0.2975 + 0.35 + 0.135 + 0.085 + 0.045
            = 0.9125
```

**Option B Total Score: 0.91** (High Priority)

---

### Decision: Option B Wins (0.91 > 0.90)

Despite Option A being preferred vendor with better communication, Option B scores slightly higher due to better cost score (0.90 vs. 0.75) which compensates for slightly lower satisfaction.

**If Scores Were Tied:** Apply tie-breaker rules (preferred vendor precedence would choose Option A).

---

## Scoring Adjustment Guidelines

### When to Adjust Curves

- **Budget constraints:** Increase cost weight from standard distribution
- **Resident complaints trending up:** Increase satisfaction weight
- **SLA misses frequent:** Increase time weight
- **Safety incidents:** Increase urgency and compliance weights

### Seasonal Adjustments

- **Summer HVAC season:** Decrease cost weight, increase urgency weight for AC issues
- **Winter heating season:** Decrease cost weight, increase urgency weight for heating issues
- **Spring turnover season:** Increase time weight for vacant unit work

### Building-Specific Adjustments

- **High-occupancy building:** Increase satisfaction weight (more residents affected)
- **Budget-constrained property:** Increase cost weight
- **Inspection period:** Increase compliance weight

---

## Scoring Transparency for Explainability

All decision agent outputs should include:

1. **Raw inputs:** ETA hours, cost USD, urgency classification
2. **Sub-scores:** All five normalized scores (0.0-1.0)
3. **Weights applied:** Which weight distribution used
4. **Total score:** Final weighted sum
5. **Threshold interpretation:** High/Medium/Standard/Low priority
6. **Source doc_ids:** Which KB documents informed scoring rules

**Example Output:**
```json
{
  "option_id": "vendor_a_ac_repair",
  "raw_inputs": {
    "cost_usd": 380,
    "eta_hours": 4,
    "urgency": "urgent"
  },
  "sub_scores": {
    "urgency_score": 0.85,
    "time_score": 1.00,
    "cost_score": 0.75,
    "satisfaction_score": 0.925,
    "compliance_score": 1.00
  },
  "weights": {
    "distribution": "HVAC_category_override",
    "urgency_weight": 0.35,
    "time_weight": 0.35,
    "cost_weight": 0.15,
    "satisfaction_weight": 0.10,
    "compliance_weight": 0.05
  },
  "total_score": 0.9025,
  "priority_level": "high",
  "source_docs": ["SCORING_001", "SCORING_005"]
}
```
