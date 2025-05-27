import csv
from datetime import datetime

from django.http import HttpResponse

try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill

    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False


def export_transactions_csv(transactions, start_date, end_date):
    """Export transactions to CSV format."""
    response = HttpResponse(content_type="text/csv")
    filename = f"spending_report_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)

    # Write header
    writer.writerow(["Date", "Payee", "Account", "Envelope", "Amount", "Memo"])

    # Write transactions
    for transaction in transactions:
        writer.writerow(
            [
                transaction.date.strftime("%Y-%m-%d"),
                transaction.payee.name if transaction.payee else "",
                transaction.account.name,
                transaction.envelope.name if transaction.envelope else "",
                f"{transaction.amount / 1000:.2f}",
                transaction.memo or "",
            ]
        )

    return response


def export_transactions_xlsx(transactions, start_date, end_date, budget_name):
    """Export transactions to Excel format."""
    if not OPENPYXL_AVAILABLE:
        raise ImportError(
            "openpyxl is required for Excel export. Install it with: pip install openpyxl"
        )

    # Create workbook and worksheet
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Spending Report"

    # Add title and metadata
    ws["A1"] = f"Spending Report - {budget_name}"
    ws["A2"] = (
        f"Period: {start_date.strftime('%B %d, %Y')} - {end_date.strftime('%B %d, %Y')}"
    )
    ws["A3"] = f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"

    # Style the title
    title_font = Font(size=16, bold=True)
    ws["A1"].font = title_font

    # Add headers starting at row 5
    headers = ["Date", "Payee", "Account", "Envelope", "Amount", "Memo"]
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=5, column=col, value=header)
        cell.font = Font(bold=True)
        cell.fill = PatternFill(
            start_color="CCCCCC", end_color="CCCCCC", fill_type="solid"
        )

    # Add transaction data
    for row, transaction in enumerate(transactions, 6):
        ws.cell(row=row, column=1, value=transaction.date.strftime("%Y-%m-%d"))
        ws.cell(
            row=row, column=2, value=transaction.payee.name if transaction.payee else ""
        )
        ws.cell(row=row, column=3, value=transaction.account.name)
        ws.cell(
            row=row,
            column=4,
            value=transaction.envelope.name if transaction.envelope else "",
        )
        ws.cell(row=row, column=5, value=f"{transaction.amount / 1000:.2f}")
        ws.cell(row=row, column=6, value=transaction.memo or "")

    # Auto-adjust column widths
    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except (TypeError, ValueError):
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column_letter].width = adjusted_width

    # Save to response
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    filename = f"spending_report_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.xlsx"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    wb.save(response)
    return response


def export_transactions_markdown(transactions, start_date, end_date, budget_name):
    """Export transactions to Markdown format."""
    response = HttpResponse(content_type="text/markdown")
    filename = f"spending_report_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.md"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    # Calculate totals
    total_income = sum(t.amount for t in transactions if t.amount > 0) / 1000
    total_spent = abs(sum(t.amount for t in transactions if t.amount < 0)) / 1000
    net_amount = (sum(t.amount for t in transactions)) / 1000

    # Generate markdown content
    content = f"""# Spending Report - {budget_name}

**Period:** {start_date.strftime('%B %d, %Y')} - {end_date.strftime('%B %d, %Y')}
**Generated:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}

## Summary

| Metric | Amount |
|--------|--------|
| Total Income | ${total_income:,.2f} |
| Total Spent | ${total_spent:,.2f} |
| Net Amount | ${net_amount:,.2f} |

## Transactions ({len(transactions)} total)

| Date | Payee | Account | Envelope | Amount | Memo |
|------|-------|---------|----------|--------|------|
"""

    for transaction in transactions:
        payee = transaction.payee.name if transaction.payee else "—"
        envelope = transaction.envelope.name if transaction.envelope else "—"
        memo = transaction.memo or "—"
        amount = f"${transaction.amount / 1000:.2f}"

        # Escape pipe characters in content
        payee = payee.replace("|", "\\|")
        envelope = envelope.replace("|", "\\|")
        memo = memo.replace("|", "\\|")

        content += f"| {transaction.date.strftime('%Y-%m-%d')} | {payee} | {transaction.account.name} | {envelope} | {amount} | {memo} |\n"

    response.write(content)
    return response
