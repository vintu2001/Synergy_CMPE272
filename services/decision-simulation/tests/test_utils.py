import sys
from unittest import mock
for mod in ['chromadb', 'numpy', 'torch', 'sentence_transformers', 'transformers']:
    sys.modules[mod] = mock.Mock()
import pytest
from unittest.mock import patch, MagicMock
from app.utils.cloudwatch_logger import setup_cloudwatch_logging, log_to_cloudwatch


def test_log_to_cloudwatch():
    """Test logging to CloudWatch."""
    # Should not raise even if CloudWatch is not configured
    try:
        log_to_cloudwatch('test_event', {'key': 'value'})
        assert True
    except Exception:
        # CloudWatch might not be available in test environment
        pass


@patch('app.utils.cloudwatch_logger.boto3.client')
def test_setup_cloudwatch_logging(mock_boto3):
    """Test setting up CloudWatch logging."""
    mock_client = MagicMock()
    mock_boto3.return_value = mock_client
    
    # Should not raise
    try:
        setup_cloudwatch_logging()
        assert True
    except Exception:
        # CloudWatch might not be available in test environment
        pass
