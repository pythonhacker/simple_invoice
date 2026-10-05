## About

This project contains a simple invoice generator application written in Fast API.
The project is contained in a single file "invoice_app.py". Upon running it
shows a form for creating an invoice. Some simple defaults are set.

After creating, one can preview and save the invoice. The application expects
that the user can print PDF of invoice via the browser's "Print->Save PDF" path,
so doesn't expose any PDF export.

There is no authentication for the application. It uses a SQlite database,
by default called invoices.db. The database is created automatically on first startup.

All code written in Python 3. Tested in Python 3.11. No unit tests yet.

## Running

    pip install fastapi uvicorn
    uvicorn invoice_app:app --reload

Visit http://127.0.0.1:8000/



