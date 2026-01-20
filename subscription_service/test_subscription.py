import pytest
from unittest.mock import MagicMock, patch
from subscription_service.main import SubscriptionService
from proto import subscription_pb2
import etcd3

def test_burn_success():
    # Mock Etcd client
    mock_etcd = MagicMock()

    # Mock transaction success
    mock_etcd.transaction.return_value = (True, [])

    service = SubscriptionService(etcd_client=mock_etcd)

    # We need to mock the etcd3.transactions classes if they are instantiated in the code
    # But since we import them in main.py, they are real classes.
    # The comparison operations on Version() return objects that transaction() consumes.
    # This should be fine as long as transaction() is mocked.

    request = subscription_pb2.BurnRequest(pill_id="test_pill_1")
    response = service.Burn(request, None)

    assert response.success is True
    assert response.message == "Pill burnt"

    mock_etcd.transaction.assert_called_once()

def test_burn_double_spend():
    mock_etcd = MagicMock()
    mock_etcd.transaction.return_value = (False, [])

    service = SubscriptionService(etcd_client=mock_etcd)

    request = subscription_pb2.BurnRequest(pill_id="test_pill_used")
    response = service.Burn(request, None)

    assert response.success is False
    assert response.message == "Double spend detected"

def test_etcd_error():
    mock_etcd = MagicMock()
    mock_etcd.transaction.side_effect = Exception("Connection lost")

    service = SubscriptionService(etcd_client=mock_etcd)

    request = subscription_pb2.BurnRequest(pill_id="test_pill_error")
    response = service.Burn(request, None)

    assert response.success is False
    assert "Connection lost" in response.message
