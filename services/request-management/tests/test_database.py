import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.database import (
    get_table,
    create_request,
    get_request_by_id,
    get_all_requests,
    convert_floats_to_decimal
)
from app.models.schemas import ResidentRequest, Status
from decimal import Decimal


@pytest.fixture
def mock_dynamodb_table():
    table = MagicMock()
    table.put_item = Mock()
    table.get_item = Mock()
    table.scan = Mock()
    table.update_item = Mock()
    return table


@patch('boto3.resource')
def test_get_table(mock_boto_resource):
    mock_dynamodb = MagicMock()
    mock_boto_resource.return_value = mock_dynamodb
    
    from importlib import reload
    import app.services.database as db_module
    reload(db_module)
    
    assert mock_boto_resource.called


@patch('app.services.database.get_table')
def test_create_request(mock_get_table):
    from datetime import datetime
    mock_table = MagicMock()
    mock_get_table.return_value = mock_table
    
    request = ResidentRequest(
        request_id="REQ123",
        resident_id="R001",
        resident_name="John Doe",
        message_text="Test message",
        category="Maintenance",
        urgency="High",
        intent="solve_problem",
        status=Status.SUBMITTED,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    result = create_request(request)
    
    mock_table.put_item.assert_called_once()


@patch('app.services.database.get_table')
def test_get_request_by_id(mock_get_table):
    mock_table = MagicMock()
    mock_get_table.return_value = mock_table
    mock_table.get_item.return_value = {
        'Item': {'request_id': 'REQ123', 'status': 'Submitted'}
    }
    
    result = get_request_by_id("REQ123")
    
    assert result['request_id'] == 'REQ123'
    mock_table.get_item.assert_called_once()


@patch('app.services.database.get_table')
def test_get_request_by_id_not_found(mock_get_table):
    mock_table = MagicMock()
    mock_get_table.return_value = mock_table
    mock_table.get_item.return_value = {}
    
    result = get_request_by_id("NONEXISTENT")
    
    assert result is None


@patch('app.services.database.get_table')
def test_get_all_requests(mock_get_table):
    from datetime import datetime
    mock_table = MagicMock()
    mock_get_table.return_value = mock_table
    mock_table.scan.return_value = {
        'Items': [
            {
                'request_id': 'REQ1',
                'resident_id': 'R001',
                'message_text': 'Test',
                'category': 'Maintenance',
                'urgency': 'High',
                'intent': 'solve_problem',
                'status': 'Submitted',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
        ]
    }
    
    result = get_all_requests()
    
    assert len(result) == 1
    mock_table.scan.assert_called_once()


def test_convert_floats_to_decimal():
    data = {
        "float_value": 3.14,
        "nested": {
            "another_float": 2.71
        },
        "list": [1.1, 2.2],
        "string": "test"
    }
    
    result = convert_floats_to_decimal(data)
    
    assert isinstance(result["float_value"], Decimal)
    assert isinstance(result["nested"]["another_float"], Decimal)
    assert isinstance(result["list"][0], Decimal)


@patch('app.services.database.get_table')
def test_get_request(mock_get_table):
    from datetime import datetime
    from app.services.database import get_request
    mock_table = MagicMock()
    mock_get_table.return_value = mock_table
    mock_table.get_item.return_value = {
        'Item': {
            'request_id': 'REQ123',
            'resident_id': 'R001',
            'message_text': 'Test',
            'category': 'Maintenance',
            'urgency': 'High',
            'intent': 'solve_problem',
            'status': 'Submitted',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
    }
    
    result = get_request('REQ123')
    
    assert result is not None
    assert result.request_id == 'REQ123'


@patch('app.services.database.get_table')
def test_get_request_not_found(mock_get_table):
    from app.services.database import get_request
    mock_table = MagicMock()
    mock_get_table.return_value = mock_table
    mock_table.get_item.return_value = {}
    
    result = get_request('NONEXISTENT')
    
    assert result is None


@patch('app.services.database.get_table')
def test_get_request_error(mock_get_table):
    from botocore.exceptions import ClientError
    from app.services.database import get_request
    mock_table = MagicMock()
    mock_get_table.return_value = mock_table
    mock_table.get_item.side_effect = ClientError({'Error': {'Code': 'ServiceError'}}, 'GetItem')
    
    result = get_request('REQ123')
    
    assert result is None


@patch('app.services.database.get_table')
def test_get_requests_by_resident(mock_get_table):
    from datetime import datetime
    from app.services.database import get_requests_by_resident
    mock_table = MagicMock()
    mock_get_table.return_value = mock_table
    mock_table.scan.return_value = {
        'Items': [
            {
                'request_id': 'REQ1',
                'resident_id': 'R001',
                'message_text': 'Test 1',
                'category': 'Maintenance',
                'urgency': 'High',
                'intent': 'solve_problem',
                'status': 'Submitted',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
        ]
    }
    
    result = get_requests_by_resident('R001')
    
    assert len(result) == 1
    assert result[0].resident_id == 'R001'


@patch('app.services.database.get_table')
def test_get_requests_by_resident_error(mock_get_table):
    from botocore.exceptions import ClientError
    from app.services.database import get_requests_by_resident
    mock_table = MagicMock()
    mock_get_table.return_value = mock_table
    mock_table.scan.side_effect = ClientError({'Error': {'Code': 'ServiceError'}}, 'Scan')
    
    result = get_requests_by_resident('R001')
    
    assert result == []


@patch('app.services.database.get_table')
def test_create_request_error(mock_get_table):
    from datetime import datetime
    from botocore.exceptions import ClientError
    mock_table = MagicMock()
    mock_get_table.return_value = mock_table
    mock_table.put_item.side_effect = ClientError({'Error': {'Code': 'ServiceError'}}, 'PutItem')
    
    request = ResidentRequest(
        request_id="REQ123",
        resident_id="R001",
        resident_name="John Doe",
        message_text="Test message",
        category="Maintenance",
        urgency="High",
        intent="solve_problem",
        status=Status.SUBMITTED,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    result = create_request(request)
    
    assert result is False


@patch('app.services.database.get_table')
def test_get_all_requests_error(mock_get_table):
    from botocore.exceptions import ClientError
    mock_table = MagicMock()
    mock_get_table.return_value = mock_table
    mock_table.scan.side_effect = ClientError({'Error': {'Code': 'ServiceError'}}, 'Scan')
    
    result = get_all_requests()
    
    assert result == []


@patch('app.services.database.get_table')
def test_get_request_by_id_error(mock_get_table):
    from botocore.exceptions import ClientError
    mock_table = MagicMock()
    mock_get_table.return_value = mock_table
    mock_table.get_item.side_effect = ClientError({'Error': {'Code': 'ServiceError'}}, 'GetItem')
    
    result = get_request_by_id('REQ123')
    
    assert result is None


@pytest.mark.asyncio
@patch('app.services.database.get_table')
async def test_update_request_status(mock_get_table):
    from app.services.database import update_request_status
    mock_table = MagicMock()
    mock_get_table.return_value = mock_table
    
    result = await update_request_status('REQ123', Status.PROCESSING)
    
    assert result is True
    mock_table.update_item.assert_called_once()


@pytest.mark.asyncio
@patch('app.services.database.get_table')
async def test_update_request_status_error(mock_get_table):
    from botocore.exceptions import ClientError
    from app.services.database import update_request_status
    mock_table = MagicMock()
    mock_get_table.return_value = mock_table
    mock_table.update_item.side_effect = ClientError({'Error': {'Code': 'ServiceError'}}, 'UpdateItem')
    
    result = await update_request_status('REQ123', Status.PROCESSING)
    
    assert result is False
