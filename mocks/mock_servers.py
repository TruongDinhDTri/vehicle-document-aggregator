"""Mock Sales + Service external APIs for local development and demos.

Run:  python mocks/mock_servers.py
  - Sales   System API -> http://localhost:9001/documents?vin=...
  - Service System API -> http://localhost:9002/documents?vin=...

Two things worth noting:
  1. Each source speaks its own field language (docId/docName... vs recordId/name...),
     which is exactly why the backend uses per-source adapters to normalize them.
  2. Each source filters by `vin`: an unknown VIN returns an empty list, like a real API.
"""
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

DEMO_VIN = "WDB4631234567890X"

# Sales field language: docId / docName / category / createdDate / fileUrl
SALES_DOCS_BY_VIN = {
    DEMO_VIN: [
        {"docId": "S-1001", "docName": "Sales Invoice", "category": "INVOICE",
         "createdDate": "2024-03-12", "fileUrl": "https://sales.local/s-1001.pdf"},
        {"docId": "S-1002", "docName": "Purchase Agreement", "category": "CONTRACT",
         "createdDate": "2024-03-10", "fileUrl": "https://sales.local/s-1002.pdf"},
    ],
}

# Service field language: recordId / name / type / serviceDate / link
SERVICE_DOCS_BY_VIN = {
    DEMO_VIN: [
        {"recordId": "SV-77", "name": "Oil Change Report", "type": "SERVICE_REPORT",
         "serviceDate": "2024-06-01", "link": "https://service.local/sv-77.pdf"},
        {"recordId": "SV-78", "name": "Brake Inspection", "type": "SERVICE_REPORT",
         "serviceDate": "2024-07-15", "link": "https://service.local/sv-78.pdf"},
    ],
}


def make_handler(docs_by_vin):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            # Filter by ?vin=...; unknown VIN -> empty list.
            query = parse_qs(urlparse(self.path).query)
            vin = query.get("vin", [""])[0]
            docs = docs_by_vin.get(vin, [])

            body = json.dumps({"documents": docs}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):  # keep the console quiet
            pass

    return Handler


def serve(port, docs_by_vin, name):
    print(f"  - {name} -> http://localhost:{port}/documents?vin=...")
    HTTPServer(("localhost", port), make_handler(docs_by_vin)).serve_forever()


if __name__ == "__main__":
    print("Mock external APIs running:")
    threading.Thread(target=serve, args=(9001, SALES_DOCS_BY_VIN, "Sales  "), daemon=True).start()
    threading.Thread(target=serve, args=(9002, SERVICE_DOCS_BY_VIN, "Service"), daemon=True).start()
    print(f"  (VIN with seeded data: {DEMO_VIN})")
    print("Press Ctrl+C to stop.\n")
    threading.Event().wait()
