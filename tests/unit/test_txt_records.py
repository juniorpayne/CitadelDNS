import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import mysql.connector
from src.app import app, get_db_connection

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_db_connection():
    with patch('mysql.connector.connect') as mock_connect:
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
    with patch('requests.put') as mock_put:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_put.return_value = mock_response
        yield mock_put

def test_create_txt_record_new_zone(client, mock_db_connection, mock_requests):
    # Setup mock database responses
    mock_cursor = mock_db_connection['cursor']
    mock_cursor.fetchone.return_value = None  # Zone doesn't exist
    mock_cursor.lastrowid = 1  # New zone ID

    # Test data
    test_data = {
        "name": "verification",
        "content": "google-site-verification=abc123def456",
        "ttl": 3600
    }

    # Make request
    response = client.post("/api/v1/zones/example.com/records/txt", json=test_data)

    # Assert response
    assert response.status_code == 200
    assert response.json() == {"message": "TXT record created successfully"}

    # Verify database calls
    mock_cursor.execute.assert_any_call(
        "SELECT id FROM domains WHERE name = %s",
        ("example.com.",)
    )
    mock_cursor.execute.assert_any_call(
        "INSERT INTO domains (name, type) VALUES (%s, %s)",
        ("example.com.", "NATIVE")
    )
    mock_cursor.execute.assert_any_call(
        "INSERT INTO records (domain_id, name, type, content, ttl) VALUES (%s, %s, %s, %s, %s)",
        (1, "verification.example.com.", "TXT", "google-site-verification=abc123def456", 3600)
    )

def test_create_txt_record_existing_zone(client, mock_db_connection, mock_requests):
    # Setup mock database responses
    mock_cursor = mock_db_connection['cursor']
    mock_cursor.fetchone.return_value = {"id": 1}  # Zone exists

    # Test data
    test_data = {
        "name": "spf",
        "content": "v=spf1 include:_spf.example.com ~all",
        "ttl": 3600
    }

    # Make request
    response = client.post("/api/v1/zones/example.com/records/txt", json=test_data)

    # Assert response
    assert response.status_code == 200
    assert response.json() == {"message": "TXT record created successfully"}

    # Verify database calls
    mock_cursor.execute.assert_any_call(
        "SELECT id FROM domains WHERE name = %s",
        ("example.com.",)
    )
    # Should not try to create zone
    assert not any(
        call[0][0].startswith("INSERT INTO domains")
        for call in mock_cursor.execute.call_args_list
    )
    mock_cursor.execute.assert_any_call(
        "INSERT INTO records (domain_id, name, type, content, ttl) VALUES (%s, %s, %s, %s, %s)",
        (1, "spf.example.com.", "TXT", '"v=spf1 include:_spf.example.com ~all"', 3600)
    )

def test_create_txt_record_invalid_data(client):
    # Test missing required field
    test_data = {
        "name": "spf",
        # Missing content field
        "ttl": 3600
    }

    response = client.post("/api/v1/zones/example.com/records/txt", json=test_data)
    assert response.status_code == 422  # Validation error

def test_create_txt_record_with_quotes(client, mock_db_connection, mock_requests):
    # Setup mock database responses
    mock_cursor = mock_db_connection['cursor']
    mock_cursor.fetchone.return_value = {"id": 1}  # Zone exists

    # Test data with content that should be quoted
    test_data = {
        "name": "test",
        "content": "some text with spaces",
        "ttl": 3600
    }

    # Make request
    response = client.post("/api/v1/zones/example.com/records/txt", json=test_data)

    # Assert response
    assert response.status_code == 200
    assert response.json() == {"message": "TXT record created successfully"}

    # Verify database calls - content should be automatically quoted
    mock_cursor.execute.assert_any_call(
        "INSERT INTO records (domain_id, name, type, content, ttl) VALUES (%s, %s, %s, %s, %s)",
        (1, "test.example.com.", "TXT", '"some text with spaces"', 3600)
    )