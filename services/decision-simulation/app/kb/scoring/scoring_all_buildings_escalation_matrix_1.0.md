---
doc_id: "SCORING_003"
type: "scoring"
category: "escalation"
building_id: "all_buildings"
effective_date: "2024-01-01"
last_updated: "2025-11-13"
version: "1.0"
keywords: ["escalation", "human review", "override", "emergency", "triggers"]
author: "Operations Manager"
approver: "General Manager"
---

# Escalation Matrix & Human Override Triggers

## Automatic Escalation Triggers (Set `human_escalation = true`)

### Life-Safety Escalation Triggers

1. **Gas leak or gas smell detected**
   - **Action:** Immediate escalation to on-call property manager + maintenance supervisor
   - **Protocol:** Evacuate building if necessary, call utility company, call fire department
   - **Estimated response:** <15 minutes notification, <60 minutes on-site assessment

2. **Structural damage or collapse risk**
   - **Action:** Immediate escalation to property manager + building engineer/structural inspector
   - **Protocol:** Evacuate affected area, secure perimeter, building code enforcement notification
   - **Estimated response:** <30 minutes notification, <2 hours structural assessment

3. **Active flooding affecting multiple units (≥2 units)**
   - **Action:** Immediate escalation to property manager + water mitigation company
   - **Protocol:** Main water shutoff, containment, resident relocation if necessary
   - **Estimated response:** <20 minutes notification, <90 minutes mitigation start

4. **Electrical fire hazard (smoking outlet, burning smell, sparking)**
   - **Action:** Immediate escalation to property manager + fire department if active fire
   - **Protocol:** Circuit breaker shutoff, evacuate if necessary, licensed electrician dispatch
   - **Estimated response:** <15 minutes notification, <60 minutes emergency electrician

5. **Active fire or smoke (not cooking-related)**
   - **Action:** BYPASS all systems, call 911 immediately, evacuate building
   - **Protocol:** Fire alarm activation, full building evacuation, fire department response
   - **Estimated response:** Immediate 911 call, <10 minutes fire department arrival

6. **Carbon monoxide alarm activation**
   - **Action:** Immediate escalation + resident evacuation
   - **Protocol:** Evacuate unit, ventilate building, utility company + fire department notification
   - **Estimated response:** <10 minutes evacuation, <30 minutes fire department assessment

7. **Sewage backup affecting living spaces**
   - **Action:** Escalation to property manager + emergency plumber
   - **Protocol:** Water shutoff if applicable, containment, biohazard cleanup protocol
   - **Estimated response:** <30 minutes notification, <2 hours emergency plumber on-site

---

### Security & Safety Escalation Triggers

8. **Forced entry or security breach**
   - **Action:** Escalation to property manager + locksmith + police department (if crime suspected)
   - **Protocol:** Secure premises, lock replacement, incident report
   - **Estimated response:** <30 minutes locksmith dispatch, <2 hours lock replacement

9. **Domestic disturbance or violence reported**
   - **Action:** BYPASS all systems, call 911 immediately, notify property manager after
   - **Protocol:** Police response, incident documentation, potential restraining order coordination
   - **Estimated response:** Immediate 911 call, document after resolution

10. **Illegal activity suspected (drug manufacturing, etc.)**
    - **Action:** Escalation to property manager + legal counsel, police notification if warranted
    - **Protocol:** Evidence preservation, lease violation process, potential eviction
    - **Estimated response:** <1 hour legal consultation, coordinate with law enforcement

---

### Environmental Hazard Escalation Triggers

11. **Mold growth >10 square feet**
    - **Action:** Escalation to property manager + environmental assessment company
    - **Protocol:** Work stoppage, air quality testing, certified remediation plan
    - **Estimated response:** <24 hours environmental assessment appointment

12. **Asbestos disturbance suspected (pre-1980 buildings)**
    - **Action:** Immediate work stoppage + escalation to property manager + certified asbestos inspector
    - **Protocol:** Area containment, air monitoring, EPA RRP compliance
    - **Estimated response:** <4 hours work stoppage, <48 hours inspector appointment

13. **Lead paint disturbance (pre-1978 buildings)**
    - **Action:** Work stoppage + escalation to property manager + EPA RRP certified contractor
    - **Protocol:** Area containment, EPA notification if required, certified cleanup
    - **Estimated response:** <4 hours work stoppage, <48 hours certified contractor

14. **Refrigerant leak (large quantity, HVAC system)**
    - **Action:** Escalation to maintenance supervisor + EPA-certified HVAC technician
    - **Protocol:** Ventilate area, evacuate if necessary, EPA reporting if threshold exceeded
    - **Estimated response:** <2 hours EPA-certified technician dispatch

15. **Pest infestation (bed bugs, roaches, rodents affecting >3 units)**
    - **Action:** Escalation to property manager + licensed pest control company
    - **Protocol:** Building-wide inspection, treatment plan, resident notification
    - **Estimated response:** <48 hours inspection, <7 days treatment plan

---

### Cost & Budget Escalation Triggers

16. **Estimated cost >$1,000 for emergency work**
    - **Action:** Escalation to maintenance supervisor for approval before proceeding
    - **Protocol:** Verbal approval acceptable, document within 2 hours
    - **Estimated response:** <30 minutes approval for true emergency

17. **Estimated cost >$2,500 for any work**
    - **Action:** Escalation to property manager for written approval
    - **Protocol:** Written quote required, email/text approval acceptable
    - **Estimated response:** <2 hours approval for emergency, <24 hours for urgent

18. **Estimated cost >$5,000 for any work**
    - **Action:** Escalation to regional manager for written approval
    - **Protocol:** Detailed scope + multiple quotes preferred
    - **Estimated response:** <4 hours approval for emergency, <48 hours for standard

19. **Category budget exceeded by >20%**
    - **Action:** Escalation to property manager + finance director
    - **Protocol:** Budget reallocation request or expense freeze on non-emergency work
    - **Estimated response:** <5 business days budget review and decision

---

### Time & Urgency Escalation Triggers

20. **After-hours urgent request (10 PM - 7 AM)**
    - **Action:** Escalation to on-call maintenance supervisor for approval
    - **Protocol:** Confirm true urgency vs. can wait until morning
    - **Estimated response:** <20 minutes callback from on-call supervisor

21. **Emergency SLA missed (>2 hours response time)**
    - **Action:** Escalation to property manager + maintenance supervisor
    - **Protocol:** Immediate alternative vendor dispatch, root cause analysis
    - **Estimated response:** <15 minutes alternative dispatch authorization

22. **Urgent SLA missed (>24 hours response time)**
    - **Action:** Escalation to property manager
    - **Protocol:** Vendor escalation, alternative vendor consideration
    - **Estimated response:** <2 hours escalation decision

23. **Work incomplete after 3+ scheduled appointments**
    - **Action:** Escalation to maintenance supervisor + property manager
    - **Protocol:** Vendor replacement consideration, resident credit discussion
    - **Estimated response:** <24 hours vendor performance review

---

### Multi-Unit & Systemic Issue Escalation Triggers

24. **Same issue affecting 4+ units in same building**
    - **Action:** Escalation to property manager + maintenance supervisor
    - **Protocol:** Root cause analysis, systemic fix vs. individual repairs
    - **Estimated response:** <4 hours investigation start

25. **Building-wide utility failure (water, electric, heat)**
    - **Action:** Escalation to property manager + utility company + regional manager
    - **Protocol:** Resident notification, temporary accommodations if extended outage
    - **Estimated response:** <30 minutes notification, coordinate with utility ETA

26. **Recurring issue (4th occurrence in same unit within 12 months)**
    - **Action:** Escalation to property manager for root cause analysis
    - **Protocol:** Engineering inspection, capital improvement consideration
    - **Estimated response:** <48 hours engineering assessment

---

### Resident & Legal Escalation Triggers

27. **Resident threatens legal action or files complaint**
    - **Action:** Immediate escalation to property manager + legal counsel
    - **Protocol:** Cease direct communication, document everything, legal team handles
    - **Estimated response:** <2 hours legal notification, <24 hours legal guidance

28. **Fair Housing complaint or discrimination allegation**
    - **Action:** Immediate escalation to regional manager + legal counsel + HR
    - **Protocol:** Investigation, document preservation, compliance review
    - **Estimated response:** <1 hour notification, <4 hours initial legal consultation

29. **Injury to resident or guest on property**
    - **Action:** Immediate escalation to property manager + insurance company
    - **Protocol:** Incident report, witness statements, medical attention offered, claim filed
    - **Estimated response:** <30 minutes notification, <2 hours incident documentation

30. **Media inquiry or social media complaint going viral**
    - **Action:** Escalation to regional manager + corporate communications
    - **Protocol:** No staff comments, official response from communications team
    - **Estimated response:** <1 hour communications team notification

---

### Vendor & Quality Escalation Triggers

31. **Vendor causes property damage**
    - **Action:** Escalation to property manager + vendor's insurance company
    - **Protocol:** Photo documentation, written damage report, insurance claim
    - **Estimated response:** <24 hours insurance claim filed

32. **Vendor no-show without 2-hour advance notice**
    - **Action:** Escalation to maintenance supervisor + alternative vendor dispatch
    - **Protocol:** Vendor performance warning, alternative vendor consideration
    - **Estimated response:** <1 hour alternative vendor dispatch

33. **Unprofessional conduct by vendor (verified complaint)**
    - **Action:** Escalation to property manager + vendor management
    - **Protocol:** Formal complaint, vendor removal from site, performance review
    - **Estimated response:** <4 hours vendor performance review

34. **Warranty dispute (vendor refuses warranty service)**
    - **Action:** Escalation to property manager + vendor management + legal if necessary
    - **Protocol:** Review original work order, review warranty terms, enforce or escalate
    - **Estimated response:** <48 hours dispute resolution

---

## Escalation Matrix by Time of Day

| **Time Period** | **Urgency** | **Cost Threshold** | **First Escalation** | **Response Time** |
|-----------------|-------------|-------------------|---------------------|-------------------|
| Business Hours (7 AM - 5 PM Mon-Fri) | Emergency | Any | Maintenance Supervisor | <15 minutes |
| Business Hours | Urgent | >$600 | Maintenance Supervisor | <30 minutes |
| Business Hours | Standard | >$300 | Maintenance Supervisor | <2 hours |
| After-Hours (5 PM - 10 PM Mon-Fri) | Emergency | >$1,000 | On-Call Supervisor | <20 minutes |
| After-Hours | Urgent | Any | On-Call Supervisor | <30 minutes |
| After-Hours | Standard | N/A | Wait until morning | Next business day |
| Late Night (10 PM - 7 AM) | Emergency | >$1,000 | On-Call Supervisor + Property Manager | <30 minutes |
| Late Night | Urgent | N/A | Wait until morning unless HVAC extreme | Next business day |
| Late Night | Standard | N/A | Wait until morning | Next business day |
| Weekends | Emergency | >$1,000 | On-Call Supervisor | <30 minutes |
| Weekends | Urgent | >$600 | On-Call Supervisor | <1 hour |
| Weekends | Standard | N/A | Wait until Monday | Monday morning |
| Holidays | Emergency Only | Any | On-Call Supervisor + Property Manager | <1 hour |

---

## Escalation Contact Hierarchy

### Level 1: Maintenance Technician / Work Order System
- **Handles:** Auto-approved work (<$300 standard, <$600 urgent, <$1,000 emergency)
- **Escalates to:** Maintenance Supervisor

### Level 2: Maintenance Supervisor
- **Handles:** Work up to $2,500 (emergency), $1,500 (urgent), $800 (standard)
- **Escalates to:** Property Manager

### Level 3: Property Manager
- **Handles:** Work up to $5,000 (emergency), $3,500 (urgent), $2,000 (standard)
- **Escalates to:** Regional Manager

### Level 4: Regional Manager
- **Handles:** Work up to $10,000 (emergency), $7,500 (urgent), $5,000 (standard)
- **Escalates to:** Executive Team (VP Operations, CFO)

### Level 5: Executive Team
- **Handles:** Work >$10,000 any urgency, legal issues, media issues, major incidents
- **Final authority:** CEO approval required for work >$25,000 or major legal matters

---

## Escalation Notification Methods

### Emergency (Life-Safety)
- **Method:** Phone call (do not leave voicemail, escalate to next level if no answer within 5 minutes)
- **Backup:** Text message with "EMERGENCY" prefix + brief description
- **Documentation:** Email follow-up within 1 hour with full details

### Urgent (24-48 Hour SLA)
- **Method:** Phone call during business hours, text message after-hours
- **Backup:** Email if no response within 30 minutes
- **Documentation:** Work order notes updated in real-time

### Standard (72+ Hour SLA)
- **Method:** Email during business hours
- **Backup:** Phone call if no response within 4 hours
- **Documentation:** Work order notes + email trail

---

## Escalation Documentation Requirements

All escalations must include:

1. **Work order ID** and original request details
2. **Escalation reason** (cost, urgency, safety, legal, etc.)
3. **Escalation timestamp** (when escalation initiated)
4. **Who escalated** (name, role)
5. **Who approved/responded** (name, role, timestamp)
6. **Decision made** (approve, deny, modify scope, etc.)
7. **Estimated cost** if cost-related escalation
8. **Photos** if safety or damage-related
9. **Resident notification** (if applicable, when notified)
10. **Resolution plan** and timeline

---

## De-Escalation Criteria

Escalation can be cancelled/downgraded if:

- **Resident changes mind** (non-emergency work no longer needed)
- **Temporary fix sufficient** (full repair can be scheduled standard timeline)
- **Duplicate request** (work already scheduled or completed)
- **Resident-caused resolved** (resident fixed issue themselves)
- **False alarm** (no actual problem found upon inspection)

De-escalation requires:
- **Maintenance supervisor approval** to downgrade urgency level
- **Resident confirmation** if work no longer needed
- **Photo documentation** if "no problem found"
- **Work order notes** explaining de-escalation reason
