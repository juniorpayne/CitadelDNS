import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import mysql.connector
from src.app import app
from src.database.db_operations import DatabaseManager

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_db_connection():
    with patch('src.database.db_operations.mysql.connector.connect') as mock_connect:
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        yield {
            'connection': mock_conn,
            'cursor': mock_cursor,
            'connect': mock_connect
        }

@pytest.fixture
def mock_requests():
    with patch('src.api.pdns_api.requests.put') as mock_put:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_put.return_value = mock_response
        yield mock_put

def test_modify_a_record(client, mock_db_connection, mock_requests):
    # Setup mock database responses
    mock_cursor = mock_db_connection['cursor']
    mock_cursor.rowcount = 1  # Record was updated

    # Test data
    test_data = {
        "name": "www",
        "content": "192.168.1.200",
        "ttl": 7200
    }

    # Make request
    response = client.put("/api/v1/zones/example.com/records/A/www", json=test_data)

    # Assert response
    assert response.status_code == 200
    assert response.json() == {"message": "A record modified successfully"}

    # Verify database calls
    mock_cursor.execute.assert_any_call(
        "UPDATE records r JOIN domains d ON r.domain_id = d.id SET r.content = %s, r.ttl = %s WHERE d.name = %s AND r.name = %s AND r.type = %s",
        ("192.168.1.200", 7200, "example.com.", "www.example.com.", "A")
    )

def test_modify_nonexistent_record(client, mock_db_connection, mock_requests):
    # Setup mock database responses
    mock_cursor = mock_db_connection['cursor']
    mock_cursor.rowcount = 0  # No record was updated

    # Test data
    test_data = {
        "name": "nonexistent",
        "content": "192.168.1.200",
        "ttl": 7200
    }

    # Make request
    response = client.put("/api/v1/zones/example.com/records/A/nonexistent", json=test_data)

    # Assert response
    assert response.status_code == 404
    assert response.json() == {"detail": "Record not found"}

def test_delete_a_record(client, mock_db_connection, mock_requests):
    # Setup mock database responses
    mock_cursor = mock_db_connection['cursor']
    mock_cursor.rowcount = 1  # Record was deleted

    # Make request
    response = client.delete("/api/v1/zones/example.com/records/A/www")

    # Assert response
    assert response.status_code == 200
    assert response.json() == {"message": "A record deleted successfully"}

    # Verify database calls
    mock_cursor.execute.assert_any_call(
        "DELETE r FROM records r JOIN domains d ON r.domain_id = d.id WHERE d.name = %s AND r.name = %s AND r.type = %s",
        ("example.com.", "www.example.com.", "A")
    )

def test_delete_nonexistent_record(client, mock_db_connection, mock_requests):
    # Setup mock database responses
    mock_cursor = mock_db_connection['cursor']
    mock_cursor.rowcount = 0  # No record was deleted

    # Make request
    response = client.delete("/api/v1/zones/example.com/records/A/nonexistent")

    # Assert response
    assert response.status_code == 404
    assert response.json() == {"detail": "Record not found"}

def test_create_aaaa_record(client, mock_db_connection, mock_requests):
    # Setup mock database responses
    mock_cursor = mock_db_connection['cursor']
    mock_cursor.fetchone.return_value = {"id": 1}  # Zone exists

    # Test data
    test_data = {
        "name": "www",
        "content": "2001:db8::1",
        "ttl": 3600
    }

    # Make request
    response = client.post("/api/v1/zones/example.com/records/aaaa", json=test_data)

    # Assert response
    assert response.status_code == 200
    assert response.json() == {"message": "AAAA record created successfully"}

    # Verify database calls
    mock_cursor.execute.assert_any_call(
        "INSERT INTO records (domain_id, name, type, content, ttl) VALUES (%s, %s, %s, %s, %s)",
        (1, "www.example.com.", "AAAA", "2001:db8::1", 3600)
    )

def test_modify_aaaa_record(client, mock_db_connection, mock_requests):
    # Setup mock database responses
    mock_cursor = mock_db_connection['cursor']
    mock_cursor.rowcount = 1  # Record was updated

    # Test data
    test_data = {
        "name": "www",
        "content": "2001:db8::2",
        "ttl": 7200
    }

    # Make request
    response = client.put("/api/v1/zones/example.com/records/AAAA/www", json=test_data)

    # Assert response
    assert response.status_code == 200
    assert response.json() == {"message": "AAAA record modified successfully"}

    # Verify database calls
    mock_cursor.execute.assert_any_call(
        "UPDATE records r JOIN domains d ON r.domain_id = d.id SET r.content = %s, r.ttl = %s WHERE d.name = %s AND r.name = %s AND r.type = %s",
        ("2001:db8::2", 7200, "example.com.", "www.example.com.", "AAAA")
    )

def test_delete_aaaa_record(client, mock_db_connection, mock_requests):
    # Setup mock database responses
    mock_cursor = mock_db_connection['cursor']
    mock_cursor.rowcount = 1  # Record was deleted

    # Make request
    response = client.delete("/api/v1/zones/example.com/records/AAAA/www")

    # Assert response
    assert response.status_code == 200
    assert response.json() == {"message": "AAAA record deleted successfully"}

    # Verify database calls
    mock_cursor.execute.assert_any_call(
        "DELETE r FROM records r JOIN domains d ON r.domain_id = d.id WHERE d.name = %s AND r.name = %s AND r.type = %s",
        ("example.com.", "www.example.com.", "AAAA")
    )