import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def _make_sample_pdf() -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.setFont("Helvetica", 10)
    # Minimal realistic content
    c.drawString(72, 750, "Bank: Sample Bank")
    c.drawString(72, 735, "Account Holder: John Doe")
    c.drawString(72, 720, "Account Number: 123456789")
    c.drawString(72, 705, "IFSC: SBIN0001234")
    c.drawString(72, 675, "Opening Balance: 1000.00")
    # Transactions (YYYY-MM-DD Description Credit Debit Balance)
    c.drawString(72, 645, "2024-01-01 Salary Credit 1000.00 0.00 2000.00")
    c.drawString(72, 630, "2024-01-05 ATM Withdrawal 0.00 200.00 1800.00")
    c.showPage()
    c.save()
    return buf.getvalue()


def test_upload_pdf():
    pdf_bytes = _make_sample_pdf()
    response = client.post(
        "/upload",
        files={"file": ("sample.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 200, response.text
    assert "statement_id" in response.json()

def test_edit_statement():
    # Upload dynamic PDF
    pdf_bytes = _make_sample_pdf()
    upload_response = client.post(
        "/upload",
        files={"file": ("sample.pdf", pdf_bytes, "application/pdf")},
    )
    assert upload_response.status_code == 200, upload_response.text
    statement_id = upload_response.json()["statement_id"]

    # Then edit
    edit_data = {
        "account_holder": "John Doe",
        "account_number": "123456789",
        "start_date": "2024-01-01",
        "end_date": "2024-01-31",
        "apply_date_sequencing": True,
    }

    response = client.post(f"/edit/{statement_id}", json=edit_data)
    assert response.status_code == 200, response.text
    assert response.json()["message"] == "Statement updated successfully"