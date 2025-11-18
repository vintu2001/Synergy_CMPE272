import pytest
from unittest.mock import patch, MagicMock
from app.utils.cloudwatch_logger import (
    log_to_cloudwatch,
    setup_cloudwatch_logging,
    ensure_log_stream,
    CLOUDWATCH_ENABLED
)


def test_log_to_cloudwatch_disabled():
    """Test logging when CloudWatch is disabled."""
    with patch('app.utils.cloudwatch_logger.CLOUDWATCH_ENABLED', False):
        # Should not raise
        log_to_cloudwatch('test_event', {'key': 'value'})
        assert True


@patch('app.utils.cloudwatch_logger.ensure_log_stream')
@patch('app.utils.cloudwatch_logger.log_to_cloudwatch')
def test_setup_cloudwatch_logging(mock_log, mock_ensure):
    """Test setting up CloudWatch logging."""
    mock_ensure.return_value = True
    
    with patch('app.utils.cloudwatch_logger.CLOUDWATCH_ENABLED', True):
        setup_cloudwatch_logging()
        
        assert mock_ensure.called
        assert mock_log.called


@patch('app.utils.cloudwatch_logger.CLOUDWATCH_ENABLED', False)
def test_setup_cloudwatch_logging_disabled():
    """Test setting up CloudWatch logging when disabled."""
    # Should not raise
    setup_cloudwatch_logging()
    assert True
