from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Request
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import shutil
import os
from pathlib import Path
from datetime import date
from typing import Optional
import json

# Import your modules (we'll handle import errors gracefully)
try:
    from parsers.pdf_parser import PDFParser
    from parsers.docx_parser import DOCXParser
    from processors.date_sequencer import DateSequencer
    from processors.balance_calculator import BalanceCalculator
    from processors.column_cleaner import ColumnCleaner
    from processors.page_detector import PageDetector
    from generators.pdf_generator import PDFGenerator
    from generators.docx_generator import DOCXGenerator
    from models.statement_schema import EditRequest, BankStatement
    from utils.audit_logger import AuditLogger
    from config.settings import settings
    IMPORTS_OK = True
except Exception as e:
    print(f"Warning: Some imports failed: {e}")
    IMPORTS_OK = False

# Create FastAPI app
app = FastAPI(
    title="Bank Statement Editor",
    description="AI-powered bank statement analysis and editing tool",
    version="1.0.0"
)

# Setup directories
UPLOAD_DIR = Path("uploads")
TEMP_DIR = Path("temp")
STATIC_DIR = Path("static")
TEMPLATE_DIR = Path("templates")

# Create directories if they don't exist
for directory in [UPLOAD_DIR, TEMP_DIR, STATIC_DIR, TEMPLATE_DIR]:
    directory.mkdir(exist_ok=True)

# Mount static files (CSS, JS, images)
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Setup templates
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))

# In-memory storage (use database in production)
statements_db = {}


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render main UI"""
    try:
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as e:
        # If template not found, return a basic HTML page
        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Bank Statement Editor</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 50px auto;
                    padding: 20px;
                    background: #f5f5f5;
                }}
                .container {{
                    background: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                h1 {{ color: #667eea; }}
                .error {{ color: red; background: #ffe6e6; padding: 10px; border-radius: 5px; }}
                .success {{ color: green; background: #e6ffe6; padding: 10px; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🏦 Bank Statement Editor</h1>
                <div class="error">
                    <strong>Template Error:</strong> {str(e)}<br>
                    <small>Please create templates/index.html</small>
                </div>
                <h3>Quick Test:</h3>
                <p>Visit <a href="/docs">/docs</a> to test the API</p>
                <p>Visit <a href="/health">/health</a> to check system status</p>
            </div>
        </body>
        </html>
        """)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "imports_ok": IMPORTS_OK,
        "uploads_dir": str(UPLOAD_DIR.exists()),
        "templates_dir": str(TEMPLATE_DIR.exists()),
        "template_file_exists": (TEMPLATE_DIR / "index.html").exists()
    }


@app.get("/favicon.ico")
async def favicon():
    """Handle favicon requests"""
    from fastapi.responses import Response
    return Response(status_code=204)


@app.post("/upload")
async def upload_statement(file: UploadFile = File(...)):
    """Upload and parse bank statement"""
    
    if not IMPORTS_OK:
        raise HTTPException(500, "Server modules not properly loaded. Check installation.")
    
    # Validate file type
    if not file.filename.endswith(('.pdf', '.docx')):
        raise HTTPException(400, "Only PDF and DOCX files are supported")
    
    # Save uploaded file
    file_path = UPLOAD_DIR / file.filename
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(500, f"Error saving file: {str(e)}")
    
    # Parse based on file type
    try:
        if file.filename.endswith('.pdf'):
            parser = PDFParser()
        else:
            parser = DOCXParser()
        
        statement = parser.parse(str(file_path))
        
        # Filter pages
        relevant_pages = PageDetector.filter_relevant_pages(statement.original_page_ranges)
        statement.original_page_ranges = relevant_pages
        
        # Calculate initial balances
        statement = BalanceCalculator.recalculate(statement)
        
        # Store in memory with unique ID
        statement_id = file.filename.split('.')[0] + "_" + str(len(statements_db))
        statements_db[statement_id] = statement
        
        return JSONResponse({
            "statement_id": statement_id,
            "data": json.loads(statement.model_dump_json()),
            "message": "Statement parsed successfully"
        })
        
    except Exception as e:
        # Clean up on error
        if file_path.exists():
            os.remove(file_path)
        raise HTTPException(500, f"Error parsing statement: {str(e)}")


@app.post("/edit/{statement_id}")
async def edit_statement(statement_id: str, edit_request: EditRequest):
    """Apply edits to statement"""
    
    if statement_id not in statements_db:
        raise HTTPException(404, "Statement not found")
    
    statement = statements_db[statement_id]
    audit_logger = AuditLogger(log_file=f"audit_{statement_id}.jsonl")
    
    try:
        # Edit header fields
        for field in ['account_holder', 'account_number', 'ifsc', 'micr', 'branch']:
            new_value = getattr(edit_request, field)
            if new_value:
                old_value = getattr(statement.header, field)
                setattr(statement.header, field, new_value)
                audit_logger.log_change(field, old_value, new_value, "header")
        
        # Apply transaction edits
        if edit_request.transaction_edits:
            for edit in edit_request.transaction_edits:
                idx = edit['index']
                if idx < len(statement.transactions):
                    txn = statement.transactions[idx]
                    for key, value in edit.items():
                        if key != 'index' and hasattr(txn, key):
                            old_val = getattr(txn, key)
                            setattr(txn, key, value)
                            audit_logger.log_change(key, old_val, value, "transaction", idx)
        
        # Apply date sequencing
        if edit_request.apply_date_sequencing and edit_request.start_date and edit_request.end_date:
            statement.transactions = DateSequencer.sequence_dates(
                statement.transactions,
                edit_request.start_date,
                edit_request.end_date,
                edit_request.date_distribution_method
            )
            
            for i, txn in enumerate(statement.transactions):
                if txn.original_date and txn.original_date != txn.date:
                    audit_logger.log_change("date", txn.original_date, txn.date, "transaction", i)
        
        # Add salary entry
        if edit_request.salary_amount and edit_request.salary_date:
            from models.statement_schema import Transaction
            salary_txn = Transaction(
                date=edit_request.salary_date,
                description=edit_request.salary_description,
                credit=edit_request.salary_amount,
                debit=0.0,
                balance=0.0
            )
            statement.transactions.append(salary_txn)
            statement.transactions.sort(key=lambda x: x.date)
            audit_logger.log_change("salary", None, edit_request.salary_amount, "transaction")
        
        # Recalculate balances
        statement = BalanceCalculator.recalculate(statement)
        
        # Save audit log
        audit_logger.save()
        
        # Update stored statement
        statements_db[statement_id] = statement
        
        return JSONResponse({
            "message": "Statement updated successfully",
            "audit_summary": audit_logger.get_summary(),
            "updated_data": json.loads(statement.model_dump_json())
        })
        
    except Exception as e:
        raise HTTPException(500, f"Error editing statement: {str(e)}")


@app.get("/export/{statement_id}")
async def export_statement(statement_id: str, format: str = "pdf"):
    """Export edited statement"""
    
    if statement_id not in statements_db:
        raise HTTPException(404, "Statement not found")
    
    if format not in ['pdf', 'docx']:
        raise HTTPException(400, "Format must be 'pdf' or 'docx'")
    
    statement = statements_db[statement_id]
    output_path = TEMP_DIR / f"{statement_id}_edited.{format}"
    
    try:
        if format == "pdf":
            generator = PDFGenerator()
        else:
            generator = DOCXGenerator()
        
        generator.generate(statement, str(output_path))
        
        return FileResponse(
            path=str(output_path),
            filename=f"{statement_id}_edited.{format}",
            media_type='application/pdf' if format == 'pdf' else 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        
    except Exception as e:
        raise HTTPException(500, f"Error generating output: {str(e)}")


@app.get("/audit/{statement_id}")
async def get_audit_log(statement_id: str):
    """Retrieve audit log for a statement"""
    
    log_file = f"audit_{statement_id}.jsonl"
    if not os.path.exists(log_file):
        return JSONResponse({"audit_log": [], "message": "No audit log found"})
    
    entries = []
    try:
        with open(log_file, 'r') as f:
            for line in f:
                entries.append(json.loads(line))
    except Exception as e:
        raise HTTPException(500, f"Error reading audit log: {str(e)}")
    
    return JSONResponse({"audit_log": entries})


# Run with: uvicorn main:app --reload
if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Bank Statement Editor...")
    print("📍 Access at: http://127.0.0.1:8000")
    print("📚 API Docs: http://127.0.0.1:8000/docs")
    uvicorn.run(app, host="127.0.0.1", port=8000)