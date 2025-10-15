import pytest
from fastapi.testclient import TestClient
from main import app
from pathlib import Path

client = TestClient(app)

def test_upload_pdf():
    """Test PDF upload"""
    test_file = Path("test_data/sample_statement.pdf")
    
    with open(test_file, "rb") as f:
        response = client.post(
            "/upload",
            files={"file": ("test.pdf", f, "application/pdf")}
        )
    
    assert response.status_code == 200
    assert "statement_id" in response.json()

def test_edit_statement():
    """Test statement editing"""
    # First upload
    with open("test_data/sample_statement.pdf", "rb") as f:
        upload_response = client.post(
            "/upload",
            files={"file": ("test.pdf", f, "application/pdf")}
        )
    
    statement_id = upload_response.json()["statement_id"]
    
    # Then edit
    edit_data = {
        "account_holder": "John Doe",
        "account_number": "123456789",
        "start_date": "2024-01-01",
        "end_date": "2024-01-31",
        "apply_date_sequencing": True
    }
    
    response = client.post(f"/edit/{statement_id}", json=edit_data)
    assert response.status_code == 200
    assert response.json()["message"] == "Statement updated successfully"