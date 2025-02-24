import pytest
from unittest.mock import Mock, patch
import mysql.connector
from src.database.db_operations import DatabaseManager

@pytest.fixture
def db_manager():
    return DatabaseManager()

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

def test_ensure_zone_exists_new_zone(db_manager, mock_db_connection):
    mock_cursor = mock_db_connection['cursor']
    mock_cursor.fetchone.return_value = None
    mock_cursor.lastrowid = 1

    zone_id = db_manager.ensure_zone_exists(mock_cursor, "example.com.")

    assert zone_id == 1
    mock_cursor.execute.assert_any_call(
        "SELECT id FROM domains WHERE name = %s",
        ("example.com.",)
    )
    mock_cursor.execute.assert_any_call(
        "INSERT INTO domains (name, type) VALUES (%s, %s)",
        ("example.com.", "NATIVE")
    )

def test_ensure_zone_exists_existing_zone(db_manager, mock_db_connection):
    mock_cursor = mock_db_connection['cursor']
    mock_cursor.fetchone.return_value = {"id": 1}

    zone_id = db_manager.ensure_zone_exists(mock_cursor, "example.com.")

    assert zone_id == 1
    mock_cursor.execute.assert_called_once_with(
        "SELECT id FROM domains WHERE name = %s",
        ("example.com.",)
    )

def test_get_record_exists(db_manager, mock_db_connection):
    mock_cursor = mock_db_connection['cursor']
    expected_record = {
        "id": 1,
        "name": "www.example.com.",
        "type": "A",
        "content": "192.168.1.100",
        "ttl": 3600
    }
    mock_cursor.fetchone.return_value = expected_record

    record = db_manager.get_record("example.com.", "www.example.com.", "A")

    assert record == expected_record
    mock_cursor.execute.assert_called_once_with(
        "SELECT r.* FROM records r JOIN domains d ON r.domain_id = d.id WHERE d.name = %s AND r.name = %s AND r.type = %s",
        ("example.com.", "www.example.com.", "A")
    )

def test_get_record_not_exists(db_manager, mock_db_connection):
    mock_cursor = mock_db_connection['cursor']
    mock_cursor.fetchone.return_value = None

    record = db_manager.get_record("example.com.", "nonexistent.example.com.", "A")

    assert record is None
    mock_cursor.execute.assert_called_once_with(
        "SELECT r.* FROM records r JOIN domains d ON r.domain_id = d.id WHERE d.name = %s AND r.name = %s AND r.type = %s",
        ("example.com.", "nonexistent.example.com.", "A")
    )

def test_modify_record_success(db_manager, mock_db_connection):
    mock_cursor = mock_db_connection['cursor']
    mock_cursor.rowcount = 1

    result = db_manager.modify_record(
        "example.com.",
        "www.example.com.",
        "A",
        "192.168.1.200",
        7200
    )

    assert result is True
    mock_cursor.execute.assert_called_once_with(
        "UPDATE records r JOIN domains d ON r.domain_id = d.id SET r.content = %s, r.ttl = %s WHERE d.name = %s AND r.name = %s AND r.type = %s",
        ("192.168.1.200", 7200, "example.com.", "www.example.com.", "A")
    )

def test_modify_record_no_ttl(db_manager, mock_db_connection):
    mock_cursor = mock_db_connection['cursor']
    mock_cursor.rowcount = 1

    result = db_manager.modify_record(
        "example.com.",
        "www.example.com.",
        "A",
        "192.168.1.200"
    )

    assert result is True
    mock_cursor.execute.assert_called_once_with(
        "UPDATE records r JOIN domains d ON r.domain_id = d.id SET r.content = %s WHERE d.name = %s AND r.name = %s AND r.type = %s",
        ("192.168.1.200", "example.com.", "www.example.com.", "A")
    )

def test_modify_record_not_found(db_manager, mock_db_connection):
    mock_cursor = mock_db_connection['cursor']
    mock_cursor.rowcount = 0

    result = db_manager.modify_record(
        "example.com.",
        "nonexistent.example.com.",
        "A",
        "192.168.1.200"
    )

    assert result is False

def test_delete_record_success(db_manager, mock_db_connection):
    mock_cursor = mock_db_connection['cursor']
    mock_cursor.rowcount = 1

    result = db_manager.delete_record(
        "example.com.",
        "www.example.com.",
        "A"
    )

    assert result is True
    mock_cursor.execute.assert_called_once_with(
        "DELETE r FROM records r JOIN domains d ON r.domain_id = d.id WHERE d.name = %s AND r.name = %s AND r.type = %s",
        ("example.com.", "www.example.com.", "A")
    )

def test_delete_record_not_found(db_manager, mock_db_connection):
    mock_cursor = mock_db_connection['cursor']
    mock_cursor.rowcount = 0

    result = db_manager.delete_record(
        "example.com.",
        "nonexistent.example.com.",
        "A"
    )

    assert result is False

def test_database_connection_error(db_manager):
    with patch('src.database.db_operations.mysql.connector.connect') as mock_connect:
        mock_connect.side_effect = mysql.connector.Error("Connection error")
        
        with pytest.raises(mysql.connector.Error) as exc_info:
            db_manager.get_record("example.com.", "www.example.com.", "A")
        
        assert str(exc_info.value) == "Connection error"

def test_database_query_error(db_manager, mock_db_connection):
    mock_cursor = mock_db_connection['cursor']
    mock_cursor.execute.side_effect = mysql.connector.Error("Query error")

    with pytest.raises(mysql.connector.Error) as exc_info:
        db_manager.get_record("example.com.", "www.example.com.", "A")

    assert str(exc_info.value) == "Query error"