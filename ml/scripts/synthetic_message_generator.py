"""
Synthetic Resident Message Generator - Ticket 2
Generates realistic, freeform resident messages for development and testing.

TODO (Ticket 2):
- Generate messages covering all categories (Maintenance, Billing, Security, Deliveries, Amenities)
- Include messages for "human escalation" intent
- Each message includes: timestamp, resident_id, message_text, true_category
- Output in both CSV and JSON formats
- Generate at least 1,000 unique messages
"""
import pandas as pd
import json
from faker import Faker
from datetime import datetime, timedelta
import random
from pathlib import Path

fake = Faker()

# Message templates by category
MESSAGE_TEMPLATES = {
    "Maintenance": [
        "My sink is leaking and water is everywhere",
        "The air conditioning is not working in my apartment",
        "The toilet won't flush properly",
        "There's a strange smell coming from the vents",
        "My door lock is broken and I can't get in",
        "Water leak in the ceiling",
        "The garbage disposal is broken",
        "Need someone to fix my broken window"
    ],
    "Billing": [
        "I was charged twice for this month's rent",
        "I need to understand my utility bill",
        "Why is there a late fee on my account?",
        "I never received a bill this month",
        "Can you explain the parking fee on my statement?",
        "I think there's an error in my billing",
        "I need to set up automatic payments"
    ],
    "Security": [
        "I saw a suspicious person near the building",
        "The front door lock is broken",
        "My apartment was broken into",
        "The security cameras aren't working",
        "I lost my access card",
        "Someone is trying to enter my apartment"
    ],
    "Deliveries": [
        "I never received my package",
        "My package was stolen from my door",
        "Can you reroute my delivery to the office?",
        "I'm not home, where is my package?",
        "The delivery person left my package in the wrong apartment"
    ],
    "Amenities": [
        "The gym equipment is broken",
        "The pool is dirty",
        "Can I reserve the party room?",
        "The WiFi in the common area isn't working",
        "The laundry machines are out of order"
    ],
    "Human_Escalation": [
        "I need to speak to a manager immediately",
        "This is unacceptable, I want to talk to someone in charge",
        "Please connect me with the property manager",
        "I need to file a formal complaint",
        "This is an emergency and I need human assistance now"
    ]
}


def generate_synthetic_messages(num_messages: int = 1000, output_dir: Path = Path("ml/data")) -> pd.DataFrame:
    """
    Generate synthetic resident messages.
    
    Args:
        num_messages: Number of messages to generate
        output_dir: Directory to save output files
        
    Returns:
        DataFrame with generated messages
    """
    messages = []
    start_date = datetime.now() - timedelta(days=90)  # Last 90 days
    
    for i in range(num_messages):
        # Select category
        if random.random() < 0.05:  # 5% human escalation
            category = "Human_Escalation"
            intent = "human_escalation"
        else:
            category = random.choice(list(MESSAGE_TEMPLATES.keys())[:-1])  # Exclude Human_Escalation
            intent = "solve_problem"
        
        # Get message text
        base_message = random.choice(MESSAGE_TEMPLATES[category])
        
        # Add variations
        variations = [
            base_message,
            base_message + " Can you help?",
            base_message + " This is urgent!",
            "Hi, " + base_message.lower(),
            base_message + " Please fix this as soon as possible."
        ]
        message_text = random.choice(variations)
        
        # Generate timestamp
        random_days = random.randint(0, 90)
        random_hours = random.randint(0, 23)
        timestamp = start_date + timedelta(days=random_days, hours=random_hours)
        
        messages.append({
            "resident_id": f"RES_{random.randint(1000, 9999)}",
            "message_text": message_text,
            "true_category": category,
            "intent": intent,
            "timestamp": timestamp.isoformat()
        })
    
    df = pd.DataFrame(messages)
    
    # Save to CSV
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "synthetic_messages.csv"
    df.to_csv(csv_path, index=False)
    print(f"Generated {num_messages} messages saved to {csv_path}")
    
    # Save to JSON
    json_path = output_dir / "synthetic_messages.json"
    df.to_json(json_path, orient="records", date_format="iso")
    print(f"Generated {num_messages} messages saved to {json_path}")
    
    return df


if __name__ == "__main__":
    # Generate messages
    df = generate_synthetic_messages(num_messages=1000)
    print(f"\nCategory distribution:")
    print(df["true_category"].value_counts())

