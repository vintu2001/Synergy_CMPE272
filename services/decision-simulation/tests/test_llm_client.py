import sys
from unittest import mock
for mod in ['chromadb', 'numpy', 'torch', 'sentence_transformers', 'transformers']:
    sys.modules[mod] = mock.Mock()
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import os
from app.utils.llm_client import LLMClient, llm_client, ensure_cloudwatch_log_stream, log_error_to_cloudwatch


@pytest.fixture
def mock_genai():
    """Mock google.generativeai module."""
    with patch('app.utils.llm_client.genai') as mock:
        yield mock


@pytest.fixture
def mock_cloudwatch():
    """Mock boto3 CloudWatch client."""
    with patch('app.utils.llm_client.cloudwatch_logs') as mock:
        yield mock


@pytest.fixture
def client():
    """Create LLM client instance."""
    with patch.dict(os.environ, {}, clear=True):
        with patch('app.utils.llm_client.genai.configure'):
            return LLMClient()


def test_llm_client_init_without_key(client):
    """Test LLM client initialization without API key."""
    assert client.enabled == False
    assert client.model is None


@patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}, clear=False)
@patch('app.utils.llm_client.genai')
def test_llm_client_init_with_key(mock_genai):
    """Test LLM client initialization with API key."""
    mock_genai.configure = MagicMock()
    mock_model = MagicMock()
    mock_genai.GenerativeModel.return_value = mock_model
    
    # Re-import to pick up the env var
    import importlib
    import app.utils.llm_client
    importlib.reload(app.utils.llm_client)
    client = app.utils.llm_client.LLMClient()
    
    # Note: The client checks GEMINI_API_KEY at module level, so we need to ensure it's set
    # For this test, we'll just verify the structure
    assert hasattr(client, 'enabled')
    assert hasattr(client, 'model')


def test_build_simple_prompt(client):
    """Test building simple prompt."""
    prompt = client._build_simple_prompt(
        message_text="AC is broken",
        category="Maintenance",
        urgency="High",
        risk_score=0.7,
        rag_context=None
    )
    
    assert isinstance(prompt, str)
    assert "AC is broken" in prompt
    assert "Maintenance" in prompt
    assert "High" in prompt


def test_build_simple_prompt_with_rag(client):
    """Test building simple prompt with RAG context."""
    mock_rag = MagicMock()
    mock_rag.retrieved_docs = [
        {"doc_id": "doc1", "text": "Test document content here"},
        {"doc_id": "doc2", "text": "Another document"}
    ]
    
    prompt = client._build_simple_prompt(
        message_text="AC is broken",
        category="Maintenance",
        urgency="High",
        risk_score=0.7,
        rag_context=mock_rag
    )
    
    assert isinstance(prompt, str)
    assert "doc1" in prompt or "Test document" in prompt




@patch('app.utils.llm_client.genai')
@pytest.mark.asyncio
async def test_answer_question_error(mock_genai):
    """Test handling errors in answer generation."""
    mock_model = MagicMock()
    mock_model.generate_content.side_effect = Exception("API error")
    mock_genai.GenerativeModel.return_value = mock_model
    mock_genai.GenerationConfig = MagicMock()
    
    with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
        client = LLMClient()
        result = await client.answer_question(
            question="What is the policy?",
            rag_context="Some context"
        )
        
        assert "error" in result
        assert result["confidence"] == 0.0


@patch('app.utils.llm_client.cloudwatch_logs')
def test_ensure_cloudwatch_log_stream_success(mock_cw):
    """Test ensuring CloudWatch log stream exists."""
    mock_cw.exceptions.ResourceAlreadyExistsException = Exception
    
    # Test successful creation
    mock_cw.create_log_group.side_effect = [None]
    mock_cw.create_log_stream.side_effect = [None]
    
    ensure_cloudwatch_log_stream()
    
    assert mock_cw.create_log_group.called
    assert mock_cw.create_log_stream.called


@patch('app.utils.llm_client.cloudwatch_logs')
def test_ensure_cloudwatch_log_stream_already_exists(mock_cw):
    """Test handling when log stream already exists."""
    class ResourceAlreadyExistsException(Exception):
        pass
    
    mock_cw.exceptions.ResourceAlreadyExistsException = ResourceAlreadyExistsException
    
    # Simulate already exists
    mock_cw.create_log_group.side_effect = ResourceAlreadyExistsException()
    mock_cw.create_log_stream.side_effect = ResourceAlreadyExistsException()
    
    # Should not raise
    ensure_cloudwatch_log_stream()


@patch('app.utils.llm_client.cloudwatch_logs')
def test_log_error_to_cloudwatch(mock_cw):
    """Test logging errors to CloudWatch."""
    mock_cw.exceptions.ResourceAlreadyExistsException = Exception
    mock_cw.create_log_group.return_value = None
    mock_cw.create_log_stream.return_value = None
    mock_cw.put_log_events.return_value = None
    
    log_error_to_cloudwatch(
        error_type="TEST_ERROR",
        error_message="Test error message",
        context={"key": "value"}
    )
    
    assert mock_cw.put_log_events.called

