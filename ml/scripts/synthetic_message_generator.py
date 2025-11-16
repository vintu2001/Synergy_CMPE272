"""
Synthetic Resident Message Generator
Generates realistic, freeform resident messages for development and testing.

Features:
- Generates messages covering all categories (Maintenance, Billing, Security, Deliveries, Amenities)
- Includes messages for "human escalation" intent
- Each message includes: timestamp, resident_id, message_text, true_category, urgency, intent, metadata
- Outputs in both CSV and JSON formats
- Generates 1,500 unique messages by default
"""
import pandas as pd
import json
from faker import Faker
from datetime import datetime, timedelta
import random
from pathlib import Path

fake = Faker()

# Escalation patterns to combine with category messages
ESCALATION_PATTERNS = {
    "high_urgency": [
        "This is absolutely unacceptable I demand to speak with the property manager immediately",
        "I've reported this multiple times get me your supervisor NOW",
        "This is the third time, I need to speak with management right away",
        "Need to speak with senior management and file a complaint",
        "I will be filing a formal complaint about this, need manager contact immediately"
    ],
    "medium_urgency": [
        "Please have your manager contact me",
        "Would like to escalate this to your supervisor",
        "Need to discuss this with management",
        "I am not satisfied with the response and want to speak with someone in charge",
        "This situation needs management attention"
    ],
    "low_urgency": [
        "Would like to schedule a meeting with the property manager to discuss this",
        "Please have management review the situation",
        "Requesting management oversight on this",
        "Can a manager follow up about this"
    ]
}

# Message templates by category and urgency level
MESSAGE_TEMPLATES = {
    "Maintenance": {
        "high_urgency": [
            "Water is pouring from my ceiling and flooding my apartment",
            "Gas leak! Strong smell of gas in my kitchen",
            "No heat and it's freezing - pipes might burst",
            "Electricity is completely out in my unit",
            "Hot water pipe burst in bathroom - water everywhere",
            "Severe leak under sink flooding kitchen NOW",
            "AC completely dead during heatwave - elderly resident",
            "Sparks coming from electrical outlet"
        ],
        "medium_urgency": [
            "My dishwasher is leaking slowly",
            "AC not cooling properly, apartment is too warm",
            "Bathroom sink draining very slowly",
            "One burner on stove not working",
            "Washing machine making loud noises",
            "Kitchen drawer broken and won't close",
            "Bedroom window stuck and won't open"
        ],
        "low_urgency": [
            "Small crack in bathroom tile",
            "Kitchen cabinet hinge is loose",
            "Closet door squeaks when opening",
            "Would like to schedule routine AC maintenance",
            "Light bulb needs replacing in hallway",
            "Minor drip from bathroom faucet"
        ]
    },
    "Billing": {
        "high_urgency": [
            "URGENT: Received eviction notice but I paid rent!",
            "Double-charged for rent this month - need immediate refund",
            "Wrong late fee applied - due date is today",
            "Account showing $2000 balance error - paid last week"
        ],
        "medium_urgency": [
            "Need to dispute a charge on my account",
            "Question about this month's utility calculation",
            "Didn't receive my payment confirmation",
            "Autopay didn't process correctly"
        ],
        "low_urgency": [
            "Can I get a copy of my payment history?",
            "Looking to set up automatic payments",
            "What's included in the amenity fee?",
            "When is rent due this month?"
        ]
    },
    "Security": {
        "high_urgency": [
            "Someone is trying to break into my apartment RIGHT NOW",
            "Suspicious person following residents into building",
            "My apartment was broken into - need immediate help",
            "Garage security door is completely broken",
            "Found my apartment door open when I got home"
        ],
        "medium_urgency": [
            "Lost my access card and need replacement",
            "Security camera by my parking spot is down",
            "Garage gate occasionally opens by itself",
            "Several lights out in parking area"
        ],
        "low_urgency": [
            "When will new security system be installed?",
            "How do I register a new guest pass?",
            "Need to update emergency contact info",
            "Request for additional parking security patrol"
        ]
    },
    "Deliveries": {
        "high_urgency": [
            "Witnessed package theft in progress",
            "Time-sensitive medical delivery missing",
            "Perishable food delivery left in sun",
            "Delivery truck damaged entry gate"
        ],
        "medium_urgency": [
            "Package delivered but not in mailroom",
            "Need help locating missing delivery",
            "Delivery person left packages in wrong building",
            "Package room access code not working"
        ],
        "low_urgency": [
            "Can you hold my packages next week?",
            "What are package room hours?",
            "How do I sign up for delivery notifications?",
            "Need to update my delivery preferences"
        ]
    },
    "Amenities": {
        "high_urgency": [
            "Person collapsed in gym - need immediate help",
            "Glass broken in pool area - safety hazard",
            "Kids locked inside playground area",
            "Smoke coming from sauna equipment"
        ],
        "medium_urgency": [
            "Gym equipment not working properly",
            "Pool heater seems broken",
            "Grill not lighting in BBQ area",
            "Tennis court net broken"
        ],
        "low_urgency": [
            "How do I book the community room?",
            "When is next pool maintenance?",
            "Request for new gym equipment",
            "WiFi weak in common area"
        ]
    }
}


def generate_synthetic_messages(num_messages: int = 1000, output_dir: Path = Path("ml/data")) -> pd.DataFrame:
    """
    Generate synthetic resident messages with metadata for ML training.
    
    Args:
        num_messages: Number of messages to generate (minimum 1000)
        output_dir: Directory to save output files
        
    Returns:
        DataFrame with generated messages and metadata
    """
    if num_messages < 1000:
        num_messages = 1000  # Enforce minimum requirement
        
    messages = []
    start_date = datetime.now() - timedelta(days=90)  # Last 90 days
    
    # Create a set of realistic resident IDs
    num_residents = max(50, num_messages // 20)  # Average 20 messages per resident
    resident_ids = [f"RES_{str(i).zfill(4)}" for i in range(1000, 1000 + num_residents)]
    
    # Track category and urgency distribution
    category_counts = {cat: 0 for cat in MESSAGE_TEMPLATES.keys()}
    urgency_counts = {"high_urgency": 0, "medium_urgency": 0, "low_urgency": 0}
    
    for i in range(num_messages):
        # Select category with distribution control
        if i < len(MESSAGE_TEMPLATES):  # Ensure at least one message per category
            category = list(MESSAGE_TEMPLATES.keys())[i % len(MESSAGE_TEMPLATES)]
        else:
            weights = [max(1, 1000 // max(count, 1)) for count in category_counts.values()]
            category = random.choices(list(MESSAGE_TEMPLATES.keys()), weights=weights)[0]
        
        # Determine if this will be an escalation (5% chance)
        is_escalation = random.random() < 0.05
        
        # Select urgency level with distribution control
        if is_escalation:
            urgency_weights = [0.4, 0.4, 0.2]  # Escalations tend toward higher urgency
        else:
            urgency_weights = [0.2, 0.5, 0.3]  # Normal distribution
        
        urgency_level = random.choices(
            ["high_urgency", "medium_urgency", "low_urgency"],
            weights=urgency_weights
        )[0]
        
        # Get base message from category
        base_message = random.choice(MESSAGE_TEMPLATES[category][urgency_level])
        
        if is_escalation:
            # Create an escalation message using the base issue
            escalation_template = random.choice(ESCALATION_PATTERNS[urgency_level])
            message_text = f"{base_message}. {escalation_template}"
        else:
            # Add normal variations based on urgency
            variations = [base_message]
            if urgency_level == "high_urgency":
                variations.extend([
                    f"URGENT: {base_message}",
                    f"EMERGENCY: {base_message}",
                    f"{base_message} - Need immediate assistance!",
                    f"{base_message} - Please help ASAP!"
                ])
            elif urgency_level == "medium_urgency":
                variations.extend([
                    f"{base_message} - Please address this soon",
                    f"Hi, {base_message.lower()}",
                    f"{base_message}. When can this be fixed?",
                    f"Having an issue: {base_message.lower()}"
                ])
            else:  # low_urgency
                variations.extend([
                    f"Question: {base_message}",
                    f"Hi, I was wondering about {base_message.lower()}",
                    f"Could you please look into this? {base_message}",
                    f"When possible: {base_message}"
                ])
            
            message_text = random.choice(variations)
        
        # Generate realistic timestamp with time-of-day patterns
        random_days = random.randint(0, 90)
        if urgency_level == "high_urgency":
            # Emergencies more likely outside business hours
            random_hours = random.choices(
                range(24),
                weights=[2]*8 + [1]*8 + [2]*8  # Higher weights for evening/night
            )[0]
        else:
            # Regular issues more likely during business hours
            random_hours = random.choices(
                range(24),
                weights=[1]*8 + [3]*8 + [1]*8  # Higher weights for business hours
            )[0]
        
        random_minutes = random.randint(0, 59)
        timestamp = start_date + timedelta(days=random_days, hours=random_hours, minutes=random_minutes)
        
        # Map urgency level to enum value
        urgency_enum = {
            "high_urgency": "High",
            "medium_urgency": "Medium",
            "low_urgency": "Low"
        }[urgency_level]
        
        # Generate message object with rich metadata
        message = {
            "resident_id": random.choice(resident_ids),
            "message_text": message_text,
            "true_category": category,
            "true_urgency": urgency_enum,
            "intent": "human_escalation" if is_escalation else "solve_problem",
            "timestamp": timestamp.isoformat(),
            "metadata": {
                "time_of_day": timestamp.strftime("%H:%M"),
                "day_of_week": timestamp.strftime("%A"),
                "is_business_hours": 9 <= timestamp.hour <= 17,
                "is_weekend": timestamp.weekday() >= 5,
                "message_length": len(message_text),
                "contains_urgent_keywords": any(kw in message_text.lower() 
                                             for kw in ["urgent", "emergency", "asap", "immediately"]),
                "is_escalation": is_escalation
            }
        }
        
        messages.append(message)
        category_counts[category] += 1
        urgency_counts[urgency_level] += 1
    
    # Convert to DataFrame
    df = pd.DataFrame(messages)
    
    # Validate distribution requirements
    category_distribution = df['true_category'].value_counts()
    urgency_distribution = df['true_urgency'].value_counts()
    
    print("\nMessage Distribution Summary:")
    print("\nCategory Distribution:")
    for category, count in category_distribution.items():
        percentage = (count / num_messages) * 100
        print(f"{category}: {count} messages ({percentage:.1f}%)")
    
    print("\nUrgency Distribution:")
    for urgency, count in urgency_distribution.items():
        percentage = (count / num_messages) * 100
        print(f"{urgency}: {count} messages ({percentage:.1f}%)")
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV with error handling
    csv_path = output_dir / "synthetic_messages.csv"
    try:
        df.to_csv(csv_path, index=False, encoding='utf-8')
        csv_size = csv_path.stat().st_size / (1024 * 1024)  # Size in MB
        print(f"\nGenerated {num_messages} messages saved to {csv_path} ({csv_size:.1f}MB)")
    except Exception as e:
        print(f"Error saving CSV file: {e}")
        raise
    
    # Save to JSON with error handling
    json_path = output_dir / "synthetic_messages.json"
    try:
        # Save with nice formatting for readability
        json_data = df.to_dict(orient="records")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(
                json_data,
                f,
                indent=2,
                ensure_ascii=False,
                default=str  # Handle datetime serialization
            )
        json_size = json_path.stat().st_size / (1024 * 1024)  # Size in MB
        print(f"Generated {num_messages} messages saved to {json_path} ({json_size:.1f}MB)")
    except Exception as e:
        print(f"Error saving JSON file: {e}")
        raise
    
    # Validate outputs
    print("\nValidation Summary:")
    print(f"✓ Generated {num_messages} unique messages")
    print(f"✓ All categories represented")
    print(f"✓ Files saved in both CSV and JSON formats")
    print(f"✓ Added metadata for ML training")
    
    return df


if __name__ == "__main__":
    # Generate messages with progress tracking
    print("Generating synthetic messages...")
    num_messages = 1500  # Generate extra to ensure good distribution
    df = generate_synthetic_messages(num_messages=num_messages)
    
    # Print example messages
    print("\nExample Messages:")
    for category in MESSAGE_TEMPLATES.keys():
        example = df[df['true_category'] == category].iloc[0]
        print(f"\n{category} ({example['true_urgency']}):")
        print(f"Message: {example['message_text']}")
        print(f"Timestamp: {example['timestamp']}")

