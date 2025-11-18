import pytest
from unittest.mock import patch, MagicMock
from app.utils.cloudwatch_logger import log_to_cloudwatch, ensure_log_stream


@patch('app.utils.cloudwatch_logger.CLOUDWATCH_ENABLED', True)
@patch('app.utils.cloudwatch_logger.cloudwatch_logs')
def test_log_to_cloudwatch_success(mock_logs):
    # Mock successful put_log_events
    mock_logs.put_log_events.return_value = {'nextSequenceToken': 'token123'}
    
    # Should not raise exception
    log_to_cloudwatch('test_event', {'key': 'value'})
    
    # Verify put_log_events was called
    assert mock_logs.put_log_events.called


@patch('boto3.client')
def test_log_to_cloudwatch_error_handling(mock_boto_client):
    mock_boto_client.side_effect = Exception("AWS Error")
    
    log_to_cloudwatch('test_event', {'key': 'value'})


@patch('app.utils.cloudwatch_logger.CLOUDWATCH_ENABLED', True)
@patch('app.utils.cloudwatch_logger.cloudwatch_logs')
def test_ensure_log_stream_creates_resources(mock_logs):
    # Mock that resources don't exist yet
    mock_logs.exceptions.ResourceAlreadyExistsException = Exception
    
    result = ensure_log_stream()
    
    # Should attempt to create log group and stream
    assert mock_logs.create_log_group.called
    assert mock_logs.create_log_stream.called


@patch('app.utils.cloudwatch_logger.CLOUDWATCH_ENABLED', True)
@patch('app.utils.cloudwatch_logger.cloudwatch_logs')
def test_ensure_log_stream_handles_existing(mock_logs):
    # Mock that resources already exist
    class ResourceExists(Exception):
        pass
    
    mock_logs.exceptions.ResourceAlreadyExistsException = ResourceExists
    mock_logs.create_log_group.side_effect = ResourceExists()
    mock_logs.create_log_stream.side_effect = ResourceExists()
    
    result = ensure_log_stream()
    
    # Should still return True
    assert result is True


@patch('app.utils.cloudwatch_logger.CLOUDWATCH_ENABLED', False)
def test_log_to_cloudwatch_disabled():
    # Should handle disabled CloudWatch gracefully
    log_to_cloudwatch('test_event', {'key': 'value'})
    # No assertion needed - just shouldn't crash


@patch('app.utils.cloudwatch_logger.CLOUDWATCH_ENABLED', False)
def test_ensure_log_stream_disabled():
    result = ensure_log_stream()
    assert result is False
