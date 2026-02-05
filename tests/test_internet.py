from unittest.mock import patch, MagicMock
import socket
import pytest
from aiautocommit.internet import is_internet_connected, wait_for_internet_connection

@patch("socket.socket")
def test_is_internet_connected_success(mock_socket):
    # Mock successful connection
    instance = mock_socket.return_value.__enter__.return_value
    instance.connect.return_value = None
    
    assert is_internet_connected() is True

@patch("socket.socket")
def test_is_internet_connected_failure(mock_socket):
    # Mock connection failure
    instance = mock_socket.return_value.__enter__.return_value
    instance.connect.side_effect = socket.error("no connection")
    
    assert is_internet_connected() is False

@patch("aiautocommit.internet.is_internet_connected")
def test_wait_for_internet_connection_success(mock_connected):
    mock_connected.return_value = True
    # Should return without raising
    wait_for_internet_connection()
    assert mock_connected.called

@patch("aiautocommit.internet.is_internet_connected")

@patch("aiautocommit.internet.MAX_WAIT_TIME", 0.1)

def test_wait_for_internet_connection_failure(mock_connected):

    mock_connected.return_value = False

    with pytest.raises(Exception) as cm:

        wait_for_internet_connection()

    assert str(cm.value) == "no internet connection"
