"""
Classification Agent
Categorizes messages, detects urgency, and identifies resident intent.
Hybrid approach: Rule-based (fast) + Gemini fallback (accurate)
"""
from fastapi import APIRouter
from app.models.schemas import MessageRequest, ClassificationResponse, IssueCategory, Urgency, Intent
import os
import re
from typing import Tuple, Optional
import json
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

# Rule-based classification keywords
URGENCY_KEYWORDS = {
    'HIGH': [
        'leak', 'leaking', 'water damage', 'flood', 'flooding',
        'fire', 'smoke', 'emergency', 'urgent', 'immediately',
        'broken', 'danger', 'dangerous', 'no power', 'no electricity',
        'gas leak', 'gas smell', 'break-in', 'theft', 'stolen',
        'injury', 'hurt', 'unsafe', 'critical'
    ],
    'MEDIUM': [
        'not working', 'issue', 'problem', 'repair', 'fix',
        'stopped working', 'malfunction', 'broken down'
    ],
    'LOW': [
        'question', 'when', 'schedule', 'inquire', 'wondering',
        'information', 'can you', 'would like'
    ]
}

CATEGORY_KEYWORDS = {
    'Maintenance': [
        'leak', 'plumbing', 'pipe', 'faucet', 'toilet', 'shower', 'sink',
        'hvac', 'heating', 'cooling', 'air conditioning', 'ac',
        'appliance', 'refrigerator', 'stove', 'oven', 'dishwasher',
        'electrical', 'light', 'outlet', 'switch', 'power',
        'door', 'window', 'lock', 'broken', 'repair', 'fix'
    ],
    'Billing': [
        'bill', 'billing', 'charge', 'charged', 'payment', 'pay',
        'invoice', 'rent', 'fee', 'cost', 'price', 'late fee',
        'balance', 'account', 'refund'
    ],
    'Security': [
        'lock', 'key', 'keys', 'lost key', 'locked out',
        'alarm', 'security', 'camera', 'break-in', 'theft',
        'stolen', 'suspicious', 'trespassing', 'access card'
    ],
    'Deliveries': [
        'package', 'delivery', 'mail', 'courier', 'ups', 'fedex',
        'amazon', 'delivered', 'missing package', 'parcel'
    ],
    'Amenities': [
        'gym', 'fitness', 'pool', 'swimming', 'laundry', 'washer',
        'dryer', 'parking', 'garage', 'elevator', 'common area',
        'clubhouse', 'amenity'
    ]
}

ESCALATION_KEYWORDS = [
    'manager', 'speak to', 'talk to', 'complaint', 'complain',
    'supervisor', 'unacceptable', 'dissatisfied', 'disappointed',
    'formal complaint', 'report', 'escalate', 'higher up',
    'not happy', 'frustrated'
]


def rule_based_classification(message_text: str) -> Tuple[Optional[IssueCategory], Optional[Urgency], Intent, float]:
    """
    Fast rule-based classification using keyword matching.
    Returns (category, urgency, intent, confidence)
    """
    text_lower = message_text.lower()
    
    # Check for human escalation intent
    intent = Intent.SOLVE_PROBLEM
    for keyword in ESCALATION_KEYWORDS:
        if keyword in text_lower:
            intent = Intent.HUMAN_ESCALATION
            break
    
    # Detect urgency
    urgency_score = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
    for level, keywords in URGENCY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                urgency_score[level] += 1
    
    urgency = None
    if urgency_score['HIGH'] > 0:
        urgency = Urgency.HIGH
    elif urgency_score['MEDIUM'] > 0:
        urgency = Urgency.MEDIUM
    elif urgency_score['LOW'] > 0:
        urgency = Urgency.LOW
    
    # Detect category
    category_score = {cat: 0 for cat in CATEGORY_KEYWORDS.keys()}
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                category_score[category] += 1
    
    category = None
    max_score = max(category_score.values())
    if max_score > 0:
        category_name = max(category_score, key=category_score.get)
        category = getattr(IssueCategory, category_name.upper())
    
    # Calculate confidence based on keyword matches
    urgency_key = urgency.name if urgency else 'LOW'
    total_matches = max_score + urgency_score[urgency_key]
    confidence = min(0.9, 0.5 + (total_matches * 0.1))
    
    return category, urgency, intent, confidence


async def gemini_classification(message_text: str) -> ClassificationResponse:
    """
    Use Google Gemini for intelligent classification when rules are uncertain.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        import google.generativeai as genai
        
        api_key = os.getenv('GEMINI_API_KEY')
        logger.info(f"[GEMINI] API Key present: {bool(api_key)}")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment")
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        prompt = f"""You are an apartment management assistant. Classify this resident message into structured data.

Message: "{message_text}"

Return ONLY a valid JSON object (no markdown, no explanations) with these EXACT fields and values:

{{
  "category": one of ["Maintenance", "Billing", "Security", "Deliveries", "Amenities"],
  "urgency": one of ["High", "Medium", "Low"],
  "intent": one of ["solve_problem", "human_escalation"],
  "confidence": a number between 0.0 and 1.0
}}

CRITICAL RULES - FOLLOW EXACTLY:
1. category MUST be EXACTLY one of: Maintenance, Billing, Security, Deliveries, Amenities
   - NEVER use "General", "Other", "Unknown" or any other category
   - If unsure, pick the closest match from the 5 allowed categories
   
2. urgency MUST be EXACTLY one of: High, Medium, Low (capitalize first letter only)

3. intent MUST be EXACTLY: solve_problem OR human_escalation (all lowercase with underscore)

CATEGORY GUIDELINES:
- "Maintenance" = repairs, appliances, plumbing, HVAC, electrical, water, heating, AC, broken items, physical issues
- "Billing" = payments, charges, invoices, refunds, rent, fees, money matters
- "Security" = locks, keys, access cards, break-ins, theft, alarms, suspicious activity
- "Deliveries" = packages, mail, courier, lost/stolen packages
- "Amenities" = gym, pool, parking, laundry, clubhouse, common areas, facilities

URGENCY RULES:
- "High" = emergency, leak, fire, danger, injury, no power, gas leak, severe issue
- "Medium" = not working properly, repair needed, issue that can wait 24-48 hours
- "Low" = questions, inquiries, scheduling, non-urgent matters

INTENT RULES:
- "human_escalation" = wants manager, complaint, dissatisfied, supervisor, escalate
- "solve_problem" = all other cases (default)

EXAMPLES:
- "weird noise in walls" → {{"category": "Maintenance", "urgency": "Medium", "intent": "solve_problem", "confidence": 0.7}}
- "I was double charged" → {{"category": "Billing", "urgency": "Medium", "intent": "solve_problem", "confidence": 0.9}}

Return ONLY the JSON object. DO NOT use categories outside the 5 allowed ones."""

        logger.info(f"[GEMINI] Calling Gemini API for: '{message_text[:50]}...'")
        response = model.generate_content(prompt)
        result_text = response.text.strip()
        logger.info(f"[GEMINI] Raw response: {result_text[:100]}...")
        
        # Remove markdown code blocks if present
        result_text = re.sub(r'^```json\s*', '', result_text)
        result_text = re.sub(r'^```\s*', '', result_text)
        result_text = re.sub(r'\s*```$', '', result_text)
        
        result = json.loads(result_text)
        logger.info(f"[GEMINI] Parsed result: {result}")
        
        # Validate and map category
        category_map = {
            'MAINTENANCE': IssueCategory.MAINTENANCE,
            'BILLING': IssueCategory.BILLING,
            'SECURITY': IssueCategory.SECURITY,
            'DELIVERIES': IssueCategory.DELIVERIES,
            'AMENITIES': IssueCategory.AMENITIES,
        }
        category_key = result['category'].upper()
        if category_key not in category_map:
            logger.warning(f"[GEMINI] Unknown category '{result['category']}' returned by Gemini. Defaulting to Maintenance. Full response: {result}")
        category = category_map.get(category_key, IssueCategory.MAINTENANCE)
        
        # Validate urgency
        urgency_map = {
            'HIGH': Urgency.HIGH,
            'MEDIUM': Urgency.MEDIUM,
            'LOW': Urgency.LOW
        }
        urgency = urgency_map.get(result['urgency'].upper(), Urgency.MEDIUM)
        
        # Validate intent
        intent_map = {
            'SOLVE_PROBLEM': Intent.SOLVE_PROBLEM,
            'HUMAN_ESCALATION': Intent.HUMAN_ESCALATION
        }
        intent = intent_map.get(result['intent'].upper(), Intent.SOLVE_PROBLEM)
        
        return ClassificationResponse(
            category=category,
            urgency=urgency,
            intent=intent,
            confidence=float(result['confidence'])
        )
        
    except Exception as e:
        logger.error(f"[GEMINI] Error: {type(e).__name__}: {e}")
        import traceback
        logger.error(f"[GEMINI] Traceback: {traceback.format_exc()}")
        # Fallback to default safe classification
        return ClassificationResponse(
            category=IssueCategory.MAINTENANCE,
            urgency=Urgency.MEDIUM,
            intent=Intent.SOLVE_PROBLEM,
            confidence=0.5
        )


@router.post("/classify", response_model=ClassificationResponse)
async def classify_message(request: MessageRequest) -> ClassificationResponse:
    """
    Hybrid classification: Rule-based first, Gemini fallback for low confidence.
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    
    # Phase 1: Try rule-based classification (fast)
    category, urgency, intent, confidence = rule_based_classification(request.message_text)
    
    logger.info(f"[CLASSIFY] Message: '{request.message_text[:50]}...'")
    logger.info(f"[CLASSIFY] Rule-based: category={category}, urgency={urgency}, intent={intent}, confidence={confidence}")
    
    # Phase 2: If confidence is low or missing critical info, use Gemini
    if confidence < 0.7 or category is None or urgency is None:
        logger.info(f"[CLASSIFY] Confidence {confidence} < 0.7 - Triggering Gemini fallback")
        try:
            gemini_result = await gemini_classification(request.message_text)
            logger.info(f"[CLASSIFY] Gemini returned: {gemini_result}")
            return gemini_result
        except Exception as e:
            logger.error(f"[CLASSIFY] Gemini failed: {e}")
            # Fallback to rule-based if Gemini fails
            if category and urgency:
                return ClassificationResponse(
                    category=category,
                    urgency=urgency,
                    intent=intent,
                    confidence=confidence
                )
            # Ultimate fallback
            return ClassificationResponse(
                category=IssueCategory.MAINTENANCE,
                urgency=Urgency.MEDIUM,
                intent=Intent.SOLVE_PROBLEM,
                confidence=0.5
            )
    
    # Phase 3: Return rule-based result with high confidence
    logger.info(f"[CLASSIFY] Using rule-based result (confidence={confidence} >= 0.7)")
    return ClassificationResponse(
        category=category,
        urgency=urgency,
        intent=intent,
        confidence=confidence
    )
