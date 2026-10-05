"""
Simple Invoice Generator

"""

from datetime import date
from decimal import Decimal
from pathlib import Path
import sqlite3

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse

app = FastAPI(title="Simple Invoice Generator")

# SQLite database lives alongside this Python file.
DB_FILE = Path(__file__).with_name("invoices.db")
STYLE = open(Path(__file__).with_name("style.txt")).read()
FORM_HTML = open(Path(__file__).with_name("form.html")).read()

def get_db():
    """
    Open a SQLite connection.

    row_factory lets us access columns using row["column_name"].
    """
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Create the minimal invoice table if it doesn't already exist.
    """

    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            organization TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT NOT NULL,
            tax REAL NOT NULL DEFAULT 0,
            consultant_address TEXT NOT NULL,
            invoice_date TEXT NOT NULL,
            place TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


# Create the database/table when the application starts.
init_db()

def money(value):
    """Format a number as Indian-style currency."""

    return f"\u20b9{float(value):,.2f}"

def invoice_html(invoice, saved=False):
    """
    Render the actual invoice.

    The invoice is intentionally plain HTML/CSS so that browser printing
    produces a clean PDF.
    """

    subtotal = float(invoice["amount"])
    tax = float(invoice["tax"])
    total = subtotal + tax

    saved_message = ""

    if saved:
        saved_message = f"""
        <div class="no-print"
             style="max-width:800px; margin:20px auto; text-align:center;">
            <strong>Invoice #{invoice["id"]} saved.</strong>
            &nbsp;
            <a href="/" class="button">New Invoice</a>
            <a href="/invoices" class="button secondary">Saved Invoices</a>
        </div>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Invoice #{invoice["id"]}</title>
        {STYLE}
    </head>

    <body>

        {saved_message}

        <div class="invoice">

            <div class="invoice-header">
                <div>
                    <div class="invoice-title">INVOICE</div>
                    <div>Invoice #{invoice["id"]}</div>
                </div>

                <div class="invoice-meta">
                    <div><strong>Date:</strong> {invoice["invoice_date"]}</div>
                    <div><strong>Place:</strong> {invoice["place"]}</div>
                </div>
            </div>

            <div class="bill-to">
                <strong>Bill To</strong>

                <div style="margin-top:8px;">
                    {invoice["organization"]}
                </div>
            </div>

            <div>
                <strong>Consultant</strong>

                <div style="margin-top:8px; white-space:pre-line;">
                    {invoice["consultant_address"]}
                </div>
            </div>

            <div class="description">
                <strong>Description</strong>

                <p>
                    {invoice["description"]}
                </p>
            </div>

            <div class="totals">

                <div class="total-row">
                    <span>Amount</span>
                    <span>{money(subtotal)}</span>
                </div>

                <div class="total-row">
                    <span>Tax</span>
                    <span>{money(tax)}</span>
                </div>

                <div class="total-row grand-total">
                    <span>Total</span>
                    <span>{money(total)}</span>
                </div>

            </div>

            <div class="invoice-footer">
                Thank you for your business.
            </div>

        </div>

    </body>
    </html>
    """

@app.get("/", response_class=HTMLResponse)
def invoice_form():
    """Display the invoice entry form."""

    return FORM_HTML.format(
        style=STYLE,
        today=date.today().isoformat()
    )


@app.post("/", response_class=HTMLResponse)
def create_invoice(
    organization: str = Form(...),
    amount: float = Form(...),
    description: str = Form(...),
    tax: float = Form(0),
    consultant_address: str = Form(...),
    invoice_date: str = Form(...),
    place: str = Form(...),
    action: str = Form(...)
):
    """
    Generate an invoice.

    'preview' renders it without storing anything.
    'save' stores it in SQLite first.
    """

    # Basic validation.
    if amount < 0 or tax < 0:
        return HTMLResponse(
            "<h2>Amount and tax cannot be negative.</h2>",
            status_code=400
        )

    invoice = {
        "id": "PREVIEW",
        "organization": organization,
        "amount": amount,
        "description": description,
        "tax": tax,
        "consultant_address": consultant_address,
        "invoice_date": invoice_date,
        "place": place,
    }

    # Preview does not touch the database.
    if action == "preview":
        return invoice_html(invoice, saved=False)

    # Save the invoice.
    conn = get_db()

    cursor = conn.execute(
        """
        INSERT INTO invoices (
            organization,
            amount,
            description,
            tax,
            consultant_address,
            invoice_date,
            place
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            organization,
            amount,
            description,
            tax,
            consultant_address,
            invoice_date,
            place,
        )
    )

    invoice_id = cursor.lastrowid

    conn.commit()

    # Fetch the newly-created row so that invoice_html()
    # has exactly the same structure for saved and preview invoices.
    row = conn.execute(
        "SELECT * FROM invoices WHERE id = ?",
        (invoice_id,)
    ).fetchone()

    conn.close()

    return invoice_html(row, saved=True)


# ---------------------------------------------------------------------------
# Saved invoices
# ---------------------------------------------------------------------------

@app.get("/invoices", response_class=HTMLResponse)
def list_invoices():
    """Display previously saved invoices."""

    conn = get_db()

    invoices = conn.execute(
        """
        SELECT id, organization, amount, invoice_date, place
        FROM invoices
        ORDER BY id DESC
        """
    ).fetchall()

    conn.close()

    rows = ""

    for invoice in invoices:
        rows += f"""
        <tr>
            <td>{invoice["id"]}</td>
            <td>{invoice["invoice_date"]}</td>
            <td>{invoice["organization"]}</td>
            <td>{money(invoice["amount"])}</td>
            <td>{invoice["place"]}</td>
            <td>
                <a href="/invoices/{invoice["id"]}">
                    View
                </a>
            </td>
        </tr>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Saved Invoices</title>
        {STYLE}
    </head>

    <body>

    <div class="container">

        <div class="card">

            <h1>Saved Invoices</h1>

            <a href="/" class="button">New Invoice</a>

            <table>
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Date</th>
                        <th>Organization</th>
                        <th>Amount</th>
                        <th>Place</th>
                        <th></th>
                    </tr>
                </thead>

                <tbody>
                    {rows}
                </tbody>
            </table>

        </div>

    </div>

    </body>
    </html>
    """

@app.get("/invoices/{invoice_id}", response_class=HTMLResponse)
def view_invoice(invoice_id: int):
    """Render an existing saved invoice."""

    conn = get_db()

    invoice = conn.execute(
        "SELECT * FROM invoices WHERE id = ?",
        (invoice_id,)
    ).fetchone()

    conn.close()

    if invoice is None:
        return HTMLResponse(
            "<h1>Invoice not found</h1>",
            status_code=404
        )

    return invoice_html(invoice, saved=False)
