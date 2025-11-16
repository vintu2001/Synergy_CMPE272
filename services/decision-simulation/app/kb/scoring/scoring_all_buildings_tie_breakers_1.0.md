---
doc_id: "SCORING_004"
type: "scoring"
category: "tie_breakers"
building_id: "all_buildings"
effective_date: "2024-01-01"
last_updated: "2025-11-13"
version: "1.0"
keywords: ["tie breaker", "preference", "priority", "equal score", "ranking"]
author: "Operations Manager"
approver: "General Manager"
---

# Tie-Breaker Rules & Preference Order

## When to Apply Tie-Breakers

Use tie-breaker rules when:
- **Two or more options have identical total scores** (within ±0.02 tolerance)
- **Multiple vendors quote identical pricing** for same scope
- **Multiple solutions have same ETA** and similar costs
- **Decision agent cannot differentiate** based on weighted scoring alone

---

## Primary Tie-Breaker Hierarchy (Apply in Order)

### 1. Policy Compliance & Safety First
- **Policy-compliant option always wins** over non-compliant option
- **Safety-certified vendor/solution wins** over non-certified
- **Code-compliant approach wins** over code variance required
- **Licensed/insured vendor wins** over unlicensed (should never reach this, but final safety check)

**Example:** DIY resident repair violates lease policy → choose vendor option even if slightly more expensive

---

### 2. Preferred Vendor Precedence
- **Preferred vendor (contracted rate) wins** over approved vendor
- **Approved vendor wins** over non-approved vendor
- **In-house maintenance team wins** over external vendor (if qualified for task)

**Rationale:** Preferred vendors have established relationships, vetted quality, and known pricing.

**Example:** Preferred HVAC vendor quotes $400, approved vendor quotes $390 → choose preferred vendor

---

### 3. Resident DIY vs. Vendor Decision
- **Policy-compliant DIY wins** if resident capable and work non-critical
- **Vendor visit wins** if:
  - Work requires license/permit
  - Safety risk involved
  - Work >$500 value
  - Resident has no documented skills
  - Warranty implications

**Example:** Resident requests to paint own unit → allow DIY if within policy, saves vendor cost

---

### 4. Faster ETA Wins (Time Sensitivity)
- **Option with shorter ETA wins** if all else equal
- **Same-day service wins** over next-day
- **Business hours completion wins** over after-hours start (lower cost)

**Rationale:** Faster resolution improves resident satisfaction and reduces secondary damage risk.

**Example:** Vendor A arrives in 2 hours @ $200, Vendor B arrives in 4 hours @ $200 → choose Vendor A

---

### 5. Lower Total Cost Wins (Cost Efficiency)
- **Option with lower total cost wins** (labor + parts + fees + travel)
- **Fixed-price option wins** over T&M estimate if similar expected cost (reduces variance)
- **Includes after-hours multipliers** in calculation
- **Includes travel/trip charges** in calculation

**Rationale:** Fiduciary responsibility to minimize costs when quality equal.

**Example:** Option A: $250 fixed, Option B: $220-$280 T&M estimate → choose Option A (certainty)

---

### 6. Parts Availability & Stock Status
- **Parts in-stock wins** over parts requiring order
- **Standard parts win** over specialty parts (future maintenance easier)
- **OEM parts win** over aftermarket if warranty concerns

**Rationale:** Faster completion, less downtime, easier future repairs.

**Example:** HVAC capacitor in-stock @ $350 vs. special order @ $340 → choose in-stock

---

### 7. Fewer Dependencies & Simpler Solution
- **Single-vendor solution wins** over multi-vendor coordination
- **Fewer steps wins** over complex multi-phase approach
- **Fewer resident accommodations required** (e.g., vacation time, moving furniture)

**Rationale:** Reduces coordination overhead and completion risk.

**Example:** One electrician fixes issue vs. electrician + vendor tech → choose single electrician

---

### 8. Lower Rework Risk & Warranty Coverage
- **Longer warranty wins** (e.g., 90-day vs. 30-day)
- **Vendor with lower historical rework rate wins**
- **Permanent fix wins** over temporary patch

**Rationale:** Reduces long-term total cost of ownership.

**Example:** Vendor A: 1-year warranty, Vendor B: 30-day warranty, same price → choose Vendor A

---

### 9. Resident Preference (When Reasonable)
- **Resident's preferred time slot wins** if no cost/schedule impact
- **Resident's preferred vendor wins** if on approved list and price competitive (within 10%)
- **Resident's aesthetic preference wins** for cosmetic work (paint color, fixture style)

**Rationale:** Resident satisfaction and retention.

**Example:** Resident prefers Tuesday vs. Wednesday, no difference → schedule Tuesday

---

### 10. Least Disruptive Option
- **Less intrusive work wins** (e.g., repair vs. replace if functionally equivalent)
- **Shorter duration wins** (2-hour job vs. 4-hour job at same cost)
- **Fewer visits wins** (one 3-hour visit vs. three 1-hour visits)

**Rationale:** Minimizes resident inconvenience.

**Example:** Repair faucet cartridge (1 hour) vs. replace entire faucet (2 hours) same cost → repair

---

### 11. Environmental & Sustainability Preference
- **Energy-efficient option wins** if lifecycle cost similar (e.g., LED vs. incandescent)
- **Water-saving option wins** (low-flow fixtures) if cost neutral
- **Recyclable/sustainable materials win** if performance equivalent

**Rationale:** Corporate sustainability goals and long-term savings.

**Example:** LED bulb $6 vs. incandescent $3, but LED lasts 10× longer → choose LED

---

### 12. Preventative Benefit (Long-Term Value)
- **Option that includes preventative benefit wins**
- **Bundled maintenance wins** (e.g., fix leak + inspect all plumbing)
- **Upgrade that prevents future issues wins** over basic repair

**Rationale:** Proactive maintenance reduces future emergency calls.

**Example:** Fix AC leak + full system inspection vs. just leak repair, same price → choose bundled

---

### 13. Documentation & Transparency Quality
- **Vendor providing detailed quote wins** over vague estimate
- **Vendor with photo documentation practice wins**
- **Vendor with better communication/updates wins**

**Rationale:** Better accountability and quality assurance.

**Example:** Vendor A: detailed line-item quote, Vendor B: verbal estimate → choose Vendor A

---

### 14. Vendor Capacity & Availability
- **Vendor with available crew wins** over vendor at capacity
- **Vendor with backup plan wins** (if tech unavailable, another dispatched)
- **Vendor with 24/7 availability wins** for ongoing needs

**Rationale:** Reduces scheduling risk and delays.

**Example:** Vendor A fully booked next week, Vendor B has availability → choose Vendor B

---

### 15. Geographic Proximity (Travel Time)
- **Closer vendor wins** if reduces response time or travel charges
- **Building-specific vendor wins** if familiar with building systems

**Rationale:** Faster response, better knowledge of building quirks.

**Example:** Vendor 5 miles away vs. Vendor 25 miles away, same price → choose closer vendor

---

## Category-Specific Tie-Breaker Overrides

### HVAC Work
1. EPA-certified technician (required for refrigerant)
2. Vendor familiar with building's HVAC brand
3. Parts availability (in-stock vs. order)
4. Energy-efficiency upgrade option

### Plumbing Work
1. Licensed plumber (required for permitted work)
2. Faster ETA (water damage escalates)
3. Permanent fix over temporary
4. Water-saving fixture option

### Electrical Work
1. Licensed electrician (code requirement)
2. Safety certification (OSHA, etc.)
3. Code compliance (must meet NEC)
4. Parts availability (breakers, outlets)

### Locksmith Services
1. Security clearance/background check
2. Response time (security breach urgent)
3. Key control system compatibility
4. Emergency availability

### Appliance Repair
1. Brand-certified technician (warranty protection)
2. OEM parts availability
3. Warranty coverage length
4. Same-day service option

---

## Multi-Option Scoring Tie-Breaker Example

**Scenario:** Three options with identical weighted scores (0.72)

| **Criteria** | **Option A: Preferred Vendor** | **Option B: Approved Vendor** | **Option C: DIY Resident** |
|--------------|-------------------------------|------------------------------|---------------------------|
| Policy Compliant | ✓ Yes | ✓ Yes | ✓ Yes (Tie) |
| Preferred Vendor | ✓ **YES** | ✗ No (approved only) | ✗ No |
| ETA | 4 hours | 2 hours | 6 hours |
| Total Cost | $300 | $280 | $50 |

**Tie-Breaker Decision Process:**

1. **Policy Compliance:** All three compliant → TIE, move to next criterion
2. **Preferred Vendor:** **Option A wins preferred vendor status** → **SELECT OPTION A**

Even though Option B has faster ETA and Option C has lower cost, preferred vendor precedence breaks tie.

---

**Scenario 2:** Two preferred vendors, identical scores (0.68)

| **Criteria** | **Vendor X** | **Vendor Y** |
|--------------|-------------|-------------|
| Policy Compliant | ✓ Yes | ✓ Yes |
| Preferred Vendor | ✓ Yes | ✓ Yes (Tie) |
| ETA | 3 hours | 3 hours (Tie) |
| Total Cost | $425 | $440 |
| Parts Status | In-stock | In-stock (Tie) |

**Tie-Breaker Decision Process:**

1-3. Policy, Vendor Status, ETA all tied
4. **Lower Total Cost:** **Vendor X at $425 wins** → **SELECT VENDOR X**

---

## Edge Cases & Special Situations

### Resident-Requested Vendor (Not on Approved List)

- **If vendor meets insurance/licensing requirements:** Resident may hire at own expense
- **If property pays:** Must go through approval process, not automatically selected
- **Tie-breaker:** Resident preference only applies if vendor on approved list

### Warranty Repair (Original Vendor Failed)

- **Original vendor gets first refusal** if warranty period active
- **If original vendor declines or unavailable:** Choose best alternative, original vendor forfeits warranty
- **Tie-breaker:** New vendor with longer warranty wins

### After-Hours Emergency

- **Available vendor wins** over preferred vendor if preferred unavailable
- **Cost becomes secondary** to availability in true emergency
- **Tie-breaker:** Fastest response time wins regardless of vendor status

### Multi-Unit Issue (4+ Units Affected)

- **Vendor capacity wins** (can handle multiple units simultaneously)
- **Bundled discount wins** if offered for multi-unit work
- **Tie-breaker:** Vendor with crew size to complete all units in one visit

### Budget Constraints (Category Near Limit)

- **Lower cost wins** over preferred vendor if budget critical
- **DIY becomes preferred** if policy-compliant and saves significant cost
- **Tie-breaker:** Defer non-critical work to next budget period

---

## Tie-Breaker Documentation

When tie-breaker applied, work order notes must include:

1. **Options considered** (vendor names, costs, ETAs)
2. **Weighted scores** (show all options scored identically)
3. **Tie-breaker rule applied** (e.g., "Preferred vendor precedence")
4. **Final selection rationale** (brief explanation)

**Example Work Order Note:**
```
Options: Vendor A ($350, 4h ETA, preferred) vs Vendor B ($340, 4h ETA, approved)
Weighted scores: Both 0.68
Tie-breaker: Preferred vendor precedence (Rule #2)
Selected: Vendor A - established relationship, known quality
```

---

## Tie-Breaker Override Authority

Maintenance supervisor or property manager may override tie-breaker selection if:

- **Vendor performance issue** known but not yet in system
- **Resident relationship concern** (vendor previously upset resident)
- **Strategic consideration** (training new vendor, testing alternative)
- **Cost savings >15%** despite lower preference ranking

Override requires written justification in work order notes.
