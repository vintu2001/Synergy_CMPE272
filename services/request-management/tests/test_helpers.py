import pytest
from app.utils.helpers import generate_request_id


def test_generate_request_id():
    request_id = generate_request_id()
    
    assert request_id.startswith("REQ_")
    assert len(request_id) > 10


def test_generate_request_id_unique():
    id1 = generate_request_id()
    id2 = generate_request_id()
    
    assert id1 != id2

