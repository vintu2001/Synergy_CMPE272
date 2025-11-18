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

    # Detect if message is a question (for answer_question intent)
    question_words = [
        'what', 'how', 'when', 'where', 'why', 'who', 'which', 'whom', 'whose', 'does', 'do', 'is', 'are', 'can', 'could', 'would', 'should', 'will', 'did', 'may', 'might', 'shall'
    ]
    # Only set to ANSWER_QUESTION if not escalation
    if intent != Intent.HUMAN_ESCALATION:
        if text_lower.strip().endswith('?') or any(text_lower.strip().startswith(qw + ' ') for qw in question_words):
            intent = Intent.ANSWER_QUESTION
    
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
    First checks intent, then only does full classification if intent is solve_problem.
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
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # STAGE 1: Intent Classification Only
        intent_prompt = f"""You are an apartment management assistant. Determine the user's intent from this message.

Message: "{message_text}"

Return ONLY a valid JSON object (no markdown, no explanations) with these EXACT fields:

{{
  "intent": one of ["solve_problem", "human_escalation", "answer_question"],
  "confidence": a number between 0.0 and 1.0
}}

INTENT RULES:
- "answer_question" = user is asking for information, policy, hours, procedures, general questions (no action needed)
- "human_escalation" = wants manager, complaint, dissatisfied, supervisor, escalate, speak to someone, talk to human
- "solve_problem" = user has an issue that needs fixing/resolution (default)

EXAMPLES:
- "What are the pool hours?" → {{"intent": "answer_question", "confidence": 0.95}}
- "I want to speak to a manager" → {{"intent": "human_escalation", "confidence": 0.95}}
- "My AC is broken" → {{"intent": "solve_problem", "confidence": 0.9}}
- "How do I pay my rent?" → {{"intent": "answer_question", "confidence": 0.9}}
- "This is unacceptable, get me your supervisor" → {{"intent": "human_escalation", "confidence": 0.98}}

Return ONLY the JSON object."""

        logger.info(f"[GEMINI] Stage 1: Checking intent for: '{message_text[:50]}...'")
        intent_response = model.generate_content(intent_prompt)
        intent_text = intent_response.text.strip()
        logger.info(f"[GEMINI] Stage 1 raw response: {intent_text}")
        
        intent_text = re.sub(r'^```json\s*', '', intent_text)
        intent_text = re.sub(r'^```\s*', '', intent_text)
        intent_text = re.sub(r'\s*```$', '', intent_text)
        
        intent_result = json.loads(intent_text)
        logger.info(f"[GEMINI] Stage 1 parsed result: {intent_result}")
        
        # Validate intent
        intent_map = {
            'SOLVE_PROBLEM': Intent.SOLVE_PROBLEM,
            'HUMAN_ESCALATION': Intent.HUMAN_ESCALATION,
            'ANSWER_QUESTION': Intent.ANSWER_QUESTION
        }
        intent = intent_map.get(intent_result['intent'].upper(), Intent.SOLVE_PROBLEM)
        confidence = float(intent_result['confidence'])
        
        # STAGE 2: Classify category (for all intents, including questions)
        # Even questions need proper categorization for RAG retrieval
        logger.info(f"[GEMINI] Stage 2: Classifying category for intent={intent.value}")
        
        category_prompt = f"""You are an apartment management assistant. Classify this message's category.

Message: "{message_text}"

Return ONLY a valid JSON object (no markdown, no explanations) with these EXACT fields:

{{
  "category": one of ["Maintenance", "Billing", "Security", "Deliveries", "Amenities"],
  "confidence": a number between 0.0 and 1.0
}}

CATEGORY GUIDELINES:
- "Maintenance" = repairs, appliances, plumbing, HVAC, electrical, water, heating, AC, broken items, physical issues
- "Billing" = payments, charges, invoices, refunds, rent, fees, money matters
- "Security" = locks, keys, access cards, break-ins, theft, alarms, suspicious activity
- "Deliveries" = packages, mail, courier, lost/stolen packages
- "Amenities" = gym, pool, parking, laundry, clubhouse, common areas, facilities

EXAMPLES:
- "What are the pool hours?" → {{"category": "Amenities", "confidence": 0.95}}
- "How do I pay my rent?" → {{"category": "Billing", "confidence": 0.95}}
- "When does maintenance fix AC?" → {{"category": "Maintenance", "confidence": 0.9}}
- "Where is my package?" → {{"category": "Deliveries", "confidence": 0.9}}

Return ONLY the JSON object."""

        category_response = model.generate_content(category_prompt)
        category_text = category_response.text.strip()
        logger.info(f"[GEMINI] Stage 2 raw response: {category_text}")
        
        category_text = re.sub(r'^```json\s*', '', category_text)
        category_text = re.sub(r'^```\s*', '', category_text)
        category_text = re.sub(r'\s*```$', '', category_text)
        
        category_result = json.loads(category_text)
        logger.info(f"[GEMINI] Stage 2 parsed result: {category_result}")
        
        # Validate and map category
        category_map = {
            'MAINTENANCE': IssueCategory.MAINTENANCE,
            'BILLING': IssueCategory.BILLING,
            'SECURITY': IssueCategory.SECURITY,
            'DELIVERIES': IssueCategory.DELIVERIES,
            'AMENITIES': IssueCategory.AMENITIES,
        }
        category_key = category_result['category'].upper()
        if category_key not in category_map:
            logger.warning(f"[GEMINI] Unknown category '{category_result['category']}' returned. Defaulting to Maintenance.")
        category = category_map.get(category_key, IssueCategory.MAINTENANCE)
        category_confidence = float(category_result.get('confidence', 0.8))
        
        if intent == Intent.ANSWER_QUESTION:
            logger.info(f"[GEMINI] Intent is answer_question with category={category.value}")
            return ClassificationResponse(
                category=category,
                urgency=Urgency.LOW,  # Questions are typically low urgency
                intent=Intent.ANSWER_QUESTION,
                confidence=min(confidence, category_confidence)  # Use lower of the two confidences
            )
        
        # STAGE 3: Full Classification (only if intent is solve_problem or human_escalation)
        logger.info(f"[GEMINI] Stage 3: Getting urgency for solve_problem/escalation")
        
        urgency_prompt = f"""You are an apartment management assistant. Classify this message's urgency level.

Message: "{message_text}"

Return ONLY a valid JSON object (no markdown, no explanations) with these EXACT fields and values:

{{
  "category": one of ["Maintenance", "Billing", "Security", "Deliveries", "Amenities"],
  "urgency": one of ["High", "Medium", "Low"],
  "confidence": a number between 0.0 and 1.0
}}

CRITICAL RULES - FOLLOW EXACTLY:
1. category MUST be EXACTLY one of: Maintenance, Billing, Security, Deliveries, Amenities
   - NEVER use "General", "Other", "Unknown" or any other category
   - If unsure, pick the closest match from the 5 allowed categories
   
2. urgency MUST be EXACTLY one of: High, Medium, Low (capitalize first letter only)

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

EXAMPLES:
- "weird noise in walls" → {{"category": "Maintenance", "urgency": "Medium", "confidence": 0.7}}
- "I was double charged" → {{"category": "Billing", "urgency": "Medium", "confidence": 0.9}}

Return ONLY the JSON object. DO NOT use categories outside the 5 allowed ones."""

        logger.info(f"[GEMINI] Stage 3: Calling Gemini API for urgency classification")
        urgency_response = model.generate_content(urgency_prompt)
        result_text = urgency_response.text.strip()
        logger.info(f"[GEMINI] Stage 3 raw response: {result_text[:100]}...")
        
        result_text = re.sub(r'^```json\s*', '', result_text)
        result_text = re.sub(r'^```\s*', '', result_text)
        result_text = re.sub(r'\s*```$', '', result_text)
        
        result = json.loads(result_text)
        logger.info(f"[GEMINI] Stage 3 parsed result: {result}")
        
        # Validate urgency
        urgency_map = {
            'HIGH': Urgency.HIGH,
            'MEDIUM': Urgency.MEDIUM,
            'LOW': Urgency.LOW
        }
        urgency = urgency_map.get(result['urgency'].upper(), Urgency.MEDIUM)
        
        # Use category from Stage 2, but can use Stage 3's category if Stage 2 failed
        final_category = category
        
        return ClassificationResponse(
            category=final_category,
            urgency=urgency,
            intent=intent,  # Use the intent from Stage 1
            confidence=float(result.get('confidence', 0.8))
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
    
    category, urgency, intent, confidence = rule_based_classification(request.message_text)
    
    logger.info(f"[CLASSIFY] Message: '{request.message_text[:50]}...'")
    logger.info(f"[CLASSIFY] Rule-based: category={category}, urgency={urgency}, intent={intent}, confidence={confidence}")
    
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
            return ClassificationResponse(
                category=IssueCategory.MAINTENANCE,
                urgency=Urgency.MEDIUM,
                intent=Intent.SOLVE_PROBLEM,
                confidence=0.5
            )
    
    logger.info(f"[CLASSIFY] Using rule-based result (confidence={confidence} >= 0.7)")
    return ClassificationResponse(
        category=category,
        urgency=urgency,
        intent=intent,
        confidence=confidence
    )
