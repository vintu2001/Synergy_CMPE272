---
doc_id: "SCORING_002"
type: "scoring"
category: "constraints"
building_id: "all_buildings"
effective_date: "2024-01-01"
last_updated: "2025-11-13"
version: "1.0"
keywords: ["constraints", "caps", "gates", "hard rules", "limits"]
author: "Operations Manager"
approver: "General Manager"
---

# Hard Constraints, Caps & Gates

## Cost Approval Gates (Deterministic Blocks)

### Emergency Urgency

- **SHALL NOT proceed if cost >$1,000** without maintenance supervisor notification
- **SHALL NOT proceed if cost >$2,500** without property manager approval
- **SHALL NOT proceed if cost >$5,000** without regional manager approval
- **Exception:** Life-safety situations proceed immediately, document approval within 2 hours

### Urgent Urgency

- **SHALL NOT proceed if cost >$600** without maintenance supervisor notification
- **SHALL NOT proceed if cost >$1,500** without property manager approval
- **SHALL NOT proceed if cost >$3,500** without regional manager approval
- **No exceptions:** All urgent work must follow approval chain

### Standard Urgency

- **SHALL NOT proceed if cost >$300** without maintenance supervisor notification
- **SHALL NOT proceed if cost >$800** without property manager approval
- **SHALL NOT proceed if cost >$2,000** without regional manager approval
- **No exceptions:** All standard work must follow approval chain

### Non-Urgent

- **SHALL NOT proceed if cost >$150** without maintenance supervisor notification
- **SHALL NOT proceed if cost >$500** without property manager approval
- **SHALL NOT proceed if cost >$1,500** without regional manager approval
- **No exceptions:** All non-urgent work must follow approval chain

---

## Time-of-Day Gates (Business Hours Restrictions)

### After-Hours Work Restrictions (10:00 PM - 7:00 AM)

- **SHALL NOT perform non-emergency work** between 10:00 PM and 7:00 AM
- **SHALL NOT perform noisy work** (drilling, hammering, vacuuming) between 10:00 PM and 7:00 AM
- **Exception:** Emergency work (water leak, no heat/AC in extremes, security breach, electrical hazard)
- **Partial exception:** Quiet work (leak inspection, temporary repairs) allowed with resident consent

### Weekend Restrictions (Saturday-Sunday)

- **SHALL NOT perform non-emergency work** before 9:00 AM or after 7:00 PM on weekends
- **SHOULD minimize** routine maintenance on Sundays unless resident-requested
- **Exception:** Emergency work proceeds 24/7
- **Standard work:** Requires resident appointment confirmation for weekend scheduling

### Holiday Restrictions

- **SHALL NOT perform non-emergency work** on major holidays: New Year's Day, Memorial Day, July 4th, Labor Day, Thanksgiving, Christmas
- **Emergency work only** with double holiday rate (2.0× multiplier)
- **Vendor availability:** Limited to on-call emergency vendors only

---

## Safety & Compliance Gates (Must/Shall Clauses)

### Immediate Escalation Required (Human Override)

- **MUST escalate if gas smell detected:** Immediate evacuation, utility company notification, fire department alert
- **MUST escalate if structural damage:** Building engineer inspection required before proceeding
- **MUST escalate if active flooding >2 units:** Property manager notification, water mitigation company dispatch
- **MUST escalate if electrical fire hazard:** Main breaker shutoff, fire department notification, licensed electrician
- **MUST escalate if mold >10 sq ft:** Environmental assessment required before remediation
- **MUST escalate if asbestos suspected:** Work stoppage, certified inspector required
- **MUST escalate if lead paint suspected:** EPA RRP compliance required for pre-1978 buildings

### Code Compliance Requirements

- **SHALL NOT proceed with electrical work** without licensed electrician if work requires permit
- **SHALL NOT proceed with gas work** without licensed gas fitter
- **SHALL NOT proceed with plumbing work** if requires permit without licensed plumber
- **SHALL obtain permit** for: HVAC unit replacement, water heater replacement, electrical panel work, structural changes
- **SHALL complete inspection** within 48 hours of permit closure for all permitted work
- **SHALL document all safety violations** found during work with photos and written report

### Insurance & Liability Requirements

- **SHALL verify insurance** before work begins if vendor not on preferred list
- **SHALL NOT proceed** if vendor insurance expired or coverage <$1 million
- **SHALL NOT allow resident DIY** for: electrical, plumbing, gas, HVAC, structural, anything requiring permit
- **SHALL photograph pre-existing damage** before work begins if potential for dispute
- **SHALL obtain signed damage waiver** if work requires accessing resident belongings

---

## Vendor Selection Gates

### Preferred Vendor Requirements

- **MUST use preferred vendor** unless unavailable or cost >20% lower with approved alternative
- **Preferred vendor unavailable defined as:** >4 hour response for emergency, >24 hour for urgent, >72 hour for standard
- **Cost comparison:** Alternative vendor quote required if not using preferred vendor for cost reasons

### Non-Approved Vendor Restrictions

- **SHALL NOT use non-approved vendor** for non-emergency work without property manager exception
- **Emergency exception:** May use any available vendor if preferred/approved unavailable and emergency status confirmed
- **Vetting required:** W-9, insurance verification, background check within 48 hours of emergency use
- **One-time use:** Non-approved vendor cannot be used again without full approval process

### Resident-Requested Vendor

- **SHALL NOT use resident-requested vendor** unless vendor meets approval criteria
- **Exception:** Resident may hire own vendor for resident-caused damage if resident pays 100% directly
- **Property not liable:** If resident hires vendor, property assumes no liability for quality or outcome
- **Inspection required:** Property reserves right to inspect work completed by resident's vendor

---

## Resident Impact Gates

### Unit Access Requirements

- **SHALL NOT enter unit** without 24-hour notice unless emergency or resident-requested same-day
- **Emergency access allowed** for: active leak, gas smell, fire/smoke, security breach, no heat <55°F, no AC >85°F
- **SHALL attempt contact** resident 3 times (call, text, email) before emergency entry if possible
- **SHALL leave entry notice** immediately after emergency entry with timestamp and reason

### Occupied Unit Restrictions

- **SHALL NOT perform work >30 minutes** in occupied unit without resident consent
- **SHALL NOT access bedroom** unless resident present or written consent obtained
- **SHALL NOT move resident belongings** unless necessary for work and documented with photos
- **SHALL provide resident option** to reschedule if work estimated >2 hours during occupied hours

### Vacant Unit Priorities

- **MUST prioritize vacant unit turnover** over occupied non-urgent work
- **Turnover timeline:** 3 business days for make-ready after move-out inspection
- **Exception:** Emergency work in occupied unit takes priority over turnover work

---

## Quality & Rework Gates

### Warranty Work Requirements

- **SHALL NOT charge resident** if work is warranty repair within 30 days of original service
- **SHALL use same vendor** for warranty work if vendor error caused rework
- **SHALL escalate to property manager** if vendor refuses warranty service
- **SHALL document warranty terms** on all work orders: parts warranty, labor warranty, callback policy

### Recurring Issue Thresholds

- **SHALL escalate to maintenance supervisor** if same issue in same unit within 30 days
- **SHALL escalate to property manager** if third occurrence of same issue in same unit within 90 days
- **SHALL perform root cause analysis** if fourth occurrence within 12 months
- **SHALL consider capital improvement** instead of repeated repairs if cost >$2,000 in 12 months for same issue

### Quality Inspection Requirements

- **SHALL photograph completed work** for: all permitted work, all water damage repairs, all electrical panel work, all HVAC replacements
- **SHALL obtain resident sign-off** for: all work >$500, all emergency work, all resident-caused billable work
- **SHALL perform post-completion inspection** for: all vendor work >$1,000, all multi-day projects, all water damage remediation

---

## Weather & Environmental Gates

### Temperature-Based Restrictions

- **SHALL NOT perform exterior painting** if temperature <50°F or >95°F
- **SHALL NOT pour concrete** if temperature <40°F without cold-weather additives
- **SHALL NOT perform roof work** if temperature <32°F (ice hazard)
- **SHALL NOT perform HVAC refrigerant work** if outdoor temperature <32°F (inaccurate charging)

### Precipitation Restrictions

- **SHALL NOT perform exterior electrical work** during rain or within 2 hours of rain cessation
- **SHALL NOT perform roof work** during rain or if rain forecast within 4 hours
- **SHALL NOT perform exterior painting** if rain forecast within 8 hours
- **SHALL delay landscaping** if ground saturated (equipment damage risk)

### Seasonal Restrictions

- **SHALL complete all exterior painting** before November 1st (winter weather)
- **SHALL complete all roof work** before December 15th (ice/snow risk)
- **SHALL prioritize HVAC preventative** by May 31st (cooling season) and October 31st (heating season)
- **SHALL complete all irrigation system winterization** by November 15th (freeze protection)

---

## Budget & Financial Gates

### Category Budget Caps

- **SHALL NOT exceed category annual budget** by >20% without regional manager approval
- **SHALL flag to property manager** when category reaches 75% of annual budget
- **SHALL propose budget increase** or cost reduction plan when category reaches 85% of annual budget
- **SHALL freeze non-emergency work** in category if annual budget reached (pending approval)

### Cash Flow Gates

- **SHALL NOT approve work >$5,000** in final week of month without CFO approval (cash flow protection)
- **SHALL batch small repairs** when possible to reduce vendor trip charges
- **SHALL delay non-urgent cosmetic work** if property occupancy <90% (revenue priority)
- **SHALL prioritize revenue-generating work** (vacant unit turnover) over non-urgent discretionary work

### Resident Billing Gates

- **SHALL NOT bill resident** for any amount <$25 (administrative cost exceeds recovery)
- **SHALL obtain property manager approval** before billing resident for any amount >$500
- **SHALL provide itemized invoice** for any resident billing >$100
- **SHALL allow resident 30-day payment period** before late fees apply

---

## Documentation Gates

### Mandatory Photo Documentation

- **SHALL photograph** before and after: all water damage repairs, all appliance replacements, all flooring work, all painting work >1 room
- **SHALL photograph resident-caused damage** within 24 hours of discovery
- **SHALL photograph warranty work** before and during repair to document issue
- **SHALL photograph safety violations** immediately upon discovery

### Mandatory Written Documentation

- **SHALL complete incident report** for: all emergency work, all injuries, all resident complaints, all escalations
- **SHALL document approval** for: all work >$300, all non-preferred vendors, all after-hours work, all warranty disputes
- **SHALL provide written estimate** to resident for: all billable work, all work >$500, all cosmetic/optional work
- **SHALL maintain work order notes** with: start time, end time, materials used, labor hours, completion status

### Mandatory Resident Communication

- **SHALL notify resident within 1 hour** after emergency entry
- **SHALL provide completion notice** within 24 hours of work completion
- **SHALL follow up** within 48 hours for all emergency work to confirm resolution
- **SHALL obtain feedback** for all work >$500 or multi-day projects

---

## Penalty & Consequence Gates

### Vendor Performance Standards

- **SHALL remove from preferred list** if: insurance lapses, 3+ complaints in 6 months, 2+ missed SLA targets, safety violation
- **SHALL issue written warning** if: missed appointment without 2-hour notice, incomplete work, unprofessional conduct
- **SHALL require quality audit** if: 2+ warranty callbacks in 30 days, resident complaint severity level ≥3

### Resident Violation Thresholds

- **SHALL issue warning** on first verified policy violation (noise, pet, smoking)
- **SHALL issue fine** on second verified policy violation within 12 months
- **SHALL begin eviction process** on third verified policy violation within 12 months (legal review required)
- **SHALL bill resident** for all resident-caused damage >$50 beyond normal wear

### SLA Penalty Application

- **SHALL apply credit** automatically if SLA missed (no resident request required)
- **SHALL escalate to property manager** if same vendor misses SLA 3+ times in 90 days
- **SHALL document SLA miss** with timestamps and root cause analysis
- **SHALL adjust future SLA targets** if category consistently misses (SLA may be unrealistic)

---

## Technology & System Gates

### Work Order System Requirements

- **SHALL create work order** for all maintenance work (no verbal-only requests)
- **SHALL assign priority level** at work order creation (emergency/urgent/standard/non-urgent)
- **SHALL update status** within 4 hours of any status change
- **SHALL close work order** within 24 hours of completion with final costs and notes

### Approval Workflow Gates

- **SHALL route to supervisor** if cost threshold exceeded (automatic system gate)
- **SHALL timeout and escalate** if approval not received within: 2 hours (emergency), 8 hours (urgent), 24 hours (standard)
- **SHALL notify requester** if work order rejected with reason code
- **SHALL track approval timestamp** for all approvals (audit trail)

### Inventory Management Gates

- **SHALL check inventory** before ordering parts if part cost >$100
- **SHALL update inventory** within 24 hours of parts use
- **SHALL trigger reorder** automatically when inventory below minimum threshold
- **SHALL conduct quarterly inventory audit** for high-value parts (>$200 each)
