from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from models.statement_schema import BankStatement
import io

class PDFGenerator:
    def generate(self, statement: BankStatement, output_path: str):
        """Generate formatted PDF from BankStatement"""
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        # Header Section
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=1  # Center
        )
        
        story.append(Paragraph(statement.header.bank_name or "Bank Statement", title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Account Details
        account_data = [
            ["Account Holder:", statement.header.account_holder],
            ["Account Number:", statement.header.account_number],
            ["IFSC Code:", statement.header.ifsc or "N/A"],
            ["MICR Code:", statement.header.micr or "N/A"],
            ["Branch:", statement.header.branch or "N/A"],
        ]
        
        account_table = Table(account_data, colWidths=[2*inch, 4*inch])
        account_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        story.append(account_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Transaction Table
        story.append(Paragraph("Transaction Details", styles['Heading2']))
        story.append(Spacer(1, 0.1*inch))
        
        txn_data = [["Date", "Description", "Credit", "Debit", "Balance"]]
        
        for txn in statement.transactions:
            txn_data.append([
                txn.date.strftime("%d-%m-%Y"),
                txn.description[:40],  # Truncate long descriptions
                f"₹{txn.credit:.2f}" if txn.credit > 0 else "-",
                f"₹{txn.debit:.2f}" if txn.debit > 0 else "-",
                f"₹{txn.balance:.2f}"
            ])
        
        # Summary row
        txn_data.append([
            "TOTAL",
            "",
            f"₹{statement.total_credits:.2f}",
            f"₹{statement.total_debits:.2f}",
            f"₹{statement.closing_balance:.2f}"
        ])
        
        txn_table = Table(txn_data, colWidths=[1*inch, 2.5*inch, 1*inch, 1*inch, 1.2*inch])
        txn_table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4CAF50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            
            # Data rows
            ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -2), 9),
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 1), (1, -1), 'LEFT'),
            
            # Summary row
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f0f0f0')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 10),
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f9f9f9')]),
        ]))
        
        story.append(txn_table)
        
        # Build PDF
        doc.build(story)