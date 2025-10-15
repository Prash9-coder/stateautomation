let currentStatementId = null;
let statementData = null;

async function uploadFile() {
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];

    if (!file) {
        alert('Please select a file');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    document.getElementById('uploadStatus').innerHTML = '<div class="spinner-border" role="status"></div> Parsing...';

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (response.ok) {
            currentStatementId = result.statement_id;
            statementData = result.data;

            document.getElementById('uploadStatus').innerHTML =
                '<div class="alert alert-success">✅ Statement parsed successfully!</div>';

            loadStatementData();
            document.getElementById('statementSection').style.display = 'block';
        } else {
            throw new Error(result.detail);
        }
    } catch (error) {
        document.getElementById('uploadStatus').innerHTML =
            `<div class="alert alert-danger">❌ Error: ${error.message}</div>`;
    }
}

function loadStatementData() {
    // Load header
    document.getElementById('accountHolder').value = statementData.header.account_holder || '';
    document.getElementById('accountNumber').value = statementData.header.account_number || '';
    document.getElementById('ifsc').value = statementData.header.ifsc || '';
    document.getElementById('micr').value = statementData.header.micr || '';
    document.getElementById('branch').value = statementData.header.branch || '';

    // Load transactions
    const tbody = document.getElementById('transactionsBody');
    tbody.innerHTML = '';

    statementData.transactions.forEach((txn, idx) => {
        const row = tbody.insertRow();
        row.innerHTML = `
            <td>${txn.date}</td>
            <td>${txn.description}</td>
            <td>₹${txn.credit.toFixed(2)}</td>
            <td>₹${txn.debit.toFixed(2)}</td>
            <td>₹${txn.balance.toFixed(2)}</td>
        `;
    });
}

async function applyEdits() {
    const editRequest = {
        account_holder: document.getElementById('accountHolder').value,
        account_number: document.getElementById('accountNumber').value,
        ifsc: document.getElementById('ifsc').value,
        micr: document.getElementById('micr').value,
        branch: document.getElementById('branch').value,
        apply_date_sequencing: document.getElementById('applyDateSequencing').checked,
        date_distribution_method: document.getElementById('dateMethod').value
    };

    if (editRequest.apply_date_sequencing) {
        editRequest.start_date = document.getElementById('startDate').value;
        editRequest.end_date = document.getElementById('endDate').value;
    }

    const salaryAmount = parseFloat(document.getElementById('salaryAmount').value);
    if (salaryAmount) {
        editRequest.salary_amount = salaryAmount;
        editRequest.salary_date = document.getElementById('salaryDate').value;
        editRequest.salary_description = document.getElementById('salaryDesc').value;
    }

    try {
        const response = await fetch(`/edit/${currentStatementId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(editRequest)
        });

        const result = await response.json();

        if (response.ok) {
            statementData = result.updated_data;
            loadStatementData();
            alert('✅ Changes applied successfully!\n\n' +
                `Total changes: ${result.audit_summary.total_changes}`);
            document.getElementById('exportSection').style.display = 'block';
        } else {
            throw new Error(result.detail);
        }
    } catch (error) {
        alert(`❌ Error: ${error.message}`);
    }
}

async function exportStatement(format) {
    window.location.href = `/export/${currentStatementId}?format=${format}`;
}

async function viewAuditLog() {
    try {
        const response = await fetch(`/audit/${currentStatementId}`);
        const result = await response.json();

        document.getElementById('auditLogContent').textContent =
            JSON.stringify(result.audit_log, null, 2);

        const modal = new bootstrap.Modal(document.getElementById('auditModal'));
        modal.show();
    } catch (error) {
        alert(`❌ Error loading audit log: ${error.message}`);
    }
}