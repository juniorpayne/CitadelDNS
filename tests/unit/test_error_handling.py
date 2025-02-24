import pytest
from fastapi import HTTPException
import requests
import mysql.connector
from src.app import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_create_a_record_powerdns_connection_error(mocker):
    # Mock database operations to succeed
    mock_db = mocker.patch('mysql.connector.connect')
    mock_cursor = mock_db.return_value.cursor.return_value
    mock_cursor.fetchone.return_value = None
    
    # Mock requests to raise connection error
    mocker.patch('requests.put', side_effect=requests.exceptions.ConnectionError("Failed to connect to PowerDNS"))
    
    response = client.post(
        "/api/v1/zones/example.com/records/a",
        json={"name": "test", "content": "192.168.1.1", "ttl": 3600}
    )
    
    assert response.status_code == 500
    assert "PowerDNS API error" in response.json()["detail"]

def test_create_txt_record_database_error(mocker):
    # Mock database to raise error
    mock_db = mocker.patch('mysql.connector.connect')
    mock_cursor = mock_db.return_value.cursor.return_value
    mock_cursor.execute.side_effect = mysql.connector.Error("Database connection failed")
    
    response = client.post(
        "/api/v1/zones/example.com/records/txt",
        json={"name": "test", "content": "v=spf1 ~all", "ttl": 3600}
    )
    
    assert response.status_code == 500
    assert "Database error" in response.json()["detail"]

def test_create_txt_record_powerdns_api_error(mocker):
    # Mock database operations to succeed
    mock_db = mocker.patch('mysql.connector.connect')
    mock_cursor = mock_db.return_value.cursor.return_value
    mock_cursor.fetchone.return_value = None
    
    # Mock PowerDNS API to return error
    mock_response = mocker.Mock()
    mock_response.status_code = 500
    mock_response.text = "Internal server error"
    mocker.patch('requests.put', return_value=mock_response)
    
    response = client.post(
        "/api/v1/zones/example.com/records/txt",
        json={"name": "test", "content": "v=spf1 ~all", "ttl": 3600}
    )
    
    assert response.status_code == 500
    assert "PowerDNS API error" in response.json()["detail"]