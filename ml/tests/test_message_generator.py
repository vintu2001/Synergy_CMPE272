"""
Unit tests for the synthetic message generator
"""
import pytest
from pathlib import Path
import pandas as pd
import json
from scripts.synthetic_message_generator import generate_synthetic_messages

@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary directory for test outputs."""
    return tmp_path

def test_message_count():
    """Verify the generator produces at least 1000 messages."""
    df = generate_synthetic_messages(num_messages=1000)
    assert len(df) >= 1000

def test_required_fields():
    """Verify all required fields are present in generated messages."""
    df = generate_synthetic_messages(num_messages=100)
    required_fields = {
        'resident_id', 'message_text', 'true_category',
        'true_urgency', 'intent', 'timestamp', 'metadata'
    }
    assert all(field in df.columns for field in required_fields)

def test_category_coverage():
    """Verify all categories are represented in the output."""
    df = generate_synthetic_messages(num_messages=1000)
    categories = {
        'Maintenance', 'Billing', 'Security',
        'Deliveries', 'Amenities', 'Human_Escalation'
    }
    assert set(df['true_category'].unique()) == categories

def test_urgency_distribution():
    """Verify reasonable distribution of urgency levels."""
    df = generate_synthetic_messages(num_messages=1000)
    urgency_counts = df['true_urgency'].value_counts()
    
    # Check all urgency levels present
    assert set(urgency_counts.index) == {'High', 'Medium', 'Low'}
    
    # Medium should be most common
    assert urgency_counts['Medium'] > urgency_counts['High']
    assert urgency_counts['Medium'] > urgency_counts['Low']

def test_file_outputs(temp_output_dir):
    """Verify both CSV and JSON files are created with correct content."""
    df = generate_synthetic_messages(num_messages=100, output_dir=temp_output_dir)
    
    # Check CSV file
    csv_path = temp_output_dir / "synthetic_messages.csv"
    assert csv_path.exists()
    df_csv = pd.read_csv(csv_path)
    assert len(df_csv) == len(df)
    
    # Check JSON file
    json_path = temp_output_dir / "synthetic_messages.json"
    assert json_path.exists()
    with open(json_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    assert len(json_data) == len(df)

def test_message_uniqueness():
    """Verify sufficient variety in generated messages."""
    df = generate_synthetic_messages(num_messages=1000)
    unique_messages = df['message_text'].nunique()
    # At least 80% should be unique (allowing for some intentional duplication)
    assert unique_messages >= 800

def test_timestamp_range():
    """Verify timestamps are within the expected 90-day range."""
    df = generate_synthetic_messages(num_messages=100)
    timestamps = pd.to_datetime(df['timestamp'])
    time_range = timestamps.max() - timestamps.min()
    assert time_range.days <= 90

def test_metadata_structure():
    """Verify metadata contains all expected fields."""
    df = generate_synthetic_messages(num_messages=100)
    required_metadata = {
        'time_of_day', 'day_of_week', 'is_business_hours',
        'is_weekend', 'message_length', 'contains_urgent_keywords'
    }
    
    # Get first row's metadata
    metadata = df.iloc[0]['metadata']
    assert isinstance(metadata, dict)
    assert all(field in metadata for field in required_metadata)

def test_resident_id_format():
    """Verify resident IDs follow the expected format."""
    df = generate_synthetic_messages(num_messages=100)
    assert all(df['resident_id'].str.match(r'RES_\d{4}'))