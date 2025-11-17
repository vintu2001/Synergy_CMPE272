"""
Tests for CloudWatch Logger
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from app.utils.cloudwatch_logger import (
    log_to_cloudwatch,
    setup_cloudwatch_logging,
    ensure_log_stream,
    convert_decimal
)


def test_convert_decimal_simple():
    result = convert_decimal(Decimal("10.5"))
    assert result == 10.5
    assert isinstance(result, float)


def test_convert_decimal_dict():
    data = {
        "cost": Decimal("150.75"),
        "tax": Decimal("12.50"),
        "name": "test"
    }
    
    result = convert_decimal(data)
    
    assert result["cost"] == 150.75
    assert result["tax"] == 12.50
    assert result["name"] == "test"


def test_convert_decimal_nested():
    data = {
        "request": {
            "cost": Decimal("100.00"),
            "items": [
                {"price": Decimal("25.50")},
                {"price": Decimal("74.50")}
            ]
        }
    }
    
    result = convert_decimal(data)
    
    assert result["request"]["cost"] == 100.0
    assert result["request"]["items"][0]["price"] == 25.5
    assert result["request"]["items"][1]["price"] == 74.5


def test_convert_decimal_list():
    data = [Decimal("10.5"), Decimal("20.3"), "text", 100]
    
    result = convert_decimal(data)
    
    assert result[0] == 10.5
    assert result[1] == 20.3
    assert result[2] == "text"
    assert result[3] == 100


@patch('app.utils.cloudwatch_logger.cloudwatch_logs')
@patch('app.utils.cloudwatch_logger.CLOUDWATCH_ENABLED', True)
def test_ensure_log_stream_creates_group_and_stream(mock_cw):
    mock_cw.create_log_group = Mock()
    mock_cw.create_log_stream = Mock()
    
    result = ensure_log_stream()
    
    assert result is True
    mock_cw.create_log_group.assert_called_once()
    mock_cw.create_log_stream.assert_called_once()


@patch('app.utils.cloudwatch_logger.cloudwatch_logs')
@patch('app.utils.cloudwatch_logger.CLOUDWATCH_ENABLED', True)
def test_ensure_log_stream_handles_existing_resources(mock_cw):
    from botocore.exceptions import ClientError
    
    mock_cw.exceptions.ResourceAlreadyExistsException = Exception
    mock_cw.create_log_group.side_effect = mock_cw.exceptions.ResourceAlreadyExistsException()
    mock_cw.create_log_stream.side_effect = mock_cw.exceptions.ResourceAlreadyExistsException()
    
    result = ensure_log_stream()
    
    assert result is True


@patch('app.utils.cloudwatch_logger.cloudwatch_logs')
@patch('app.utils.cloudwatch_logger.CLOUDWATCH_ENABLED', True)
def test_log_to_cloudwatch_success(mock_cw):
    mock_cw.put_log_events.return_value = {"nextSequenceToken": "token123"}
    
    log_to_cloudwatch('test_event', {'key': 'value', 'cost': Decimal('50.00')})
    
    mock_cw.put_log_events.assert_called_once()
    call_args = mock_cw.put_log_events.call_args[1]
    assert 'logEvents' in call_args
    assert len(call_args['logEvents']) == 1


@patch('app.utils.cloudwatch_logger.CLOUDWATCH_ENABLED', False)
def test_log_to_cloudwatch_disabled():
    with patch('app.utils.cloudwatch_logger.logger') as mock_logger:
        log_to_cloudwatch('test_event', {'key': 'value'})
        
        mock_logger.debug.assert_called_once()


@patch('app.utils.cloudwatch_logger.cloudwatch_logs')
@patch('app.utils.cloudwatch_logger.CLOUDWATCH_ENABLED', True)
def test_log_to_cloudwatch_with_decimal_conversion(mock_cw):
    mock_cw.put_log_events.return_value = {"nextSequenceToken": "token123"}
    
    data = {
        "request_id": "REQ123",
        "cost": Decimal("150.50"),
        "items": [
            {"price": Decimal("75.25")},
            {"price": Decimal("75.25")}
        ]
    }
    
    log_to_cloudwatch('request_completed', data)
    
    call_args = mock_cw.put_log_events.call_args[1]
    message = call_args['logEvents'][0]['message']
    
    assert 'Decimal' not in message


@patch('app.utils.cloudwatch_logger.cloudwatch_logs')
@patch('app.utils.cloudwatch_logger.CLOUDWATCH_ENABLED', True)
def test_setup_cloudwatch_logging(mock_cw):
    mock_cw.create_log_group = Mock()
    mock_cw.create_log_stream = Mock()
    mock_cw.put_log_events.return_value = {"nextSequenceToken": "token123"}
    
    setup_cloudwatch_logging()
    
    assert mock_cw.put_log_events.called


def test_log_event_structure():
    with patch('app.utils.cloudwatch_logger.cloudwatch_logs') as mock_cw:
        with patch('app.utils.cloudwatch_logger.CLOUDWATCH_ENABLED', True):
            mock_cw.put_log_events.return_value = {"nextSequenceToken": "token123"}
            
            log_to_cloudwatch('test_event', {
                'resident_id': 'RES123',
                'category': 'Maintenance',
                'cost': 100.5
            })
            
            call_args = mock_cw.put_log_events.call_args[1]
            import json
            message = json.loads(call_args['logEvents'][0]['message'])
            
            assert message['event_type'] == 'test_event'
            assert message['resident_id'] == 'RES123'
            assert message['category'] == 'Maintenance'
            assert 'timestamp' in message
            assert 'service' in message
