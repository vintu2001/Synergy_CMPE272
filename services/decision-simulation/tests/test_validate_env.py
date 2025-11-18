import sys
from unittest import mock
for mod in ['chromadb', 'numpy', 'torch', 'sentence_transformers', 'transformers']:
    sys.modules[mod] = mock.Mock()
import pytest
import os
from unittest.mock import patch, mock_open
from pathlib import Path
from app.utils.validate_env import EnvValidator


@pytest.fixture
def validator():
    """Create a validator instance for testing."""
    with patch('app.utils.validate_env.load_dotenv'):
        with patch('pathlib.Path.exists', return_value=False):
            return EnvValidator(env_file=".env.test")


def test_convert_value_bool(validator):
    """Test value conversion for boolean types."""
    assert validator._convert_value("true", bool) == True
    assert validator._convert_value("True", bool) == True
    assert validator._convert_value("1", bool) == True
    assert validator._convert_value("yes", bool) == True
    assert validator._convert_value("false", bool) == False
    assert validator._convert_value("0", bool) == False
    assert validator._convert_value("no", bool) == False


def test_convert_value_int(validator):
    """Test value conversion for integer types."""
    assert validator._convert_value("123", int) == 123
    assert validator._convert_value("0", int) == 0
    assert validator._convert_value("-5", int) == -5


def test_convert_value_float(validator):
    """Test value conversion for float types."""
    assert validator._convert_value("123.45", float) == 123.45
    assert validator._convert_value("0.5", float) == 0.5


def test_convert_value_string(validator):
    """Test value conversion for string types."""
    assert validator._convert_value("test", str) == "test"
    assert validator._convert_value("123", str) == "123"


@patch.dict(os.environ, {
    "RAG_ENABLED": "true",
    "EMBEDDING_MODEL": "test-model",
    "EMBEDDING_DIMENSION": "384",
    "VECTOR_STORE_TYPE": "chroma",
    "VECTOR_STORE_PATH": "./test_path",
    "KB_BASE_PATH": "./kb",
    "RAG_TOP_K": "5",
    "RAG_SIMILARITY_THRESHOLD": "0.7"
})
def test_validate_required_all_present(validator):
    """Test validation when all required variables are present."""
    success, errors = validator.validate_required()
    assert success == True
    assert len(errors) == 0


@patch.dict(os.environ, {}, clear=True)
def test_validate_required_missing(validator):
    """Test validation when required variables are missing."""
    success, errors = validator.validate_required()
    assert success == False
    assert len(errors) > 0
    assert any("RAG_ENABLED" in error for error in errors)


@patch.dict(os.environ, {
    "RAG_ENABLED": "invalid",
    "EMBEDDING_DIMENSION": "not_a_number"
})
def test_validate_required_invalid_types(validator):
    """Test validation with invalid value types."""
    success, errors = validator.validate_required()
    assert success == False
    assert len(errors) > 0




@patch.dict(os.environ, {
    "KB_BASE_PATH": "./nonexistent",
    "VECTOR_STORE_PATH": "./nonexistent/chroma_db"
})
@patch('pathlib.Path.exists', return_value=False)
def test_validate_paths_missing(mock_exists, validator):
    """Test path validation when paths don't exist."""
    success, errors = validator.validate_paths()
    assert success == False
    assert len(errors) > 0


@patch.dict(os.environ, {
    "RAG_SIMILARITY_THRESHOLD": "0.5",
    "RAG_TOP_K": "5",
    "EMBEDDING_DIMENSION": "384"
})
def test_validate_ranges_valid(validator):
    """Test range validation with valid values."""
    success, errors = validator.validate_ranges()
    assert success == True
    assert len(errors) == 0


@patch.dict(os.environ, {
    "RAG_SIMILARITY_THRESHOLD": "1.5",  # Invalid: > 1.0
    "RAG_TOP_K": "-1",  # Invalid: <= 0
    "EMBEDDING_DIMENSION": "50"  # Invalid: < 100
})
def test_validate_ranges_invalid(validator):
    """Test range validation with invalid values."""
    success, errors = validator.validate_ranges()
    assert success == False
    assert len(errors) > 0


@patch.dict(os.environ, {
    "RAG_ENABLED": "true",
    "EMBEDDING_MODEL": "test-model",
    "EMBEDDING_DIMENSION": "384",
    "VECTOR_STORE_TYPE": "chroma",
    "VECTOR_STORE_PATH": "./test_path",
    "KB_BASE_PATH": "./kb",
    "RAG_TOP_K": "5",
    "RAG_SIMILARITY_THRESHOLD": "0.7",
    "EMBEDDING_DEVICE": "cpu",
    "CHROMA_COLLECTION_NAME": "test_collection"
})
def test_get_config_summary(validator):
    """Test getting configuration summary."""
    config = validator.get_config_summary()
    
    assert isinstance(config, dict)
    assert "RAG_ENABLED" in config
    assert "EMBEDDING_MODEL" in config
    assert config["RAG_ENABLED"] == True
    assert config["EMBEDDING_MODEL"] == "test-model"


@patch.dict(os.environ, {
    "RAG_ENABLED": "true",
    "EMBEDDING_MODEL": "test-model",
    "EMBEDDING_DIMENSION": "384",
    "VECTOR_STORE_TYPE": "chroma",
    "VECTOR_STORE_PATH": "./test_path",
    "KB_BASE_PATH": "./kb",
    "RAG_TOP_K": "5",
    "RAG_SIMILARITY_THRESHOLD": "0.7"
})
@patch('pathlib.Path.exists', return_value=True)
@patch('builtins.print')
def test_validate_all_success(mock_print, mock_exists, validator):
    """Test full validation when everything is valid."""
    result = validator.validate_all()
    assert result == True
    assert mock_print.called


@patch.dict(os.environ, {}, clear=True)
@patch('pathlib.Path.exists', return_value=False)
@patch('builtins.print')
def test_validate_all_failure(mock_print, mock_exists, validator):
    """Test full validation when there are errors."""
    result = validator.validate_all()
    assert result == False
    assert mock_print.called

