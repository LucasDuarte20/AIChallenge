import sys
import openpyxl
from agenda_app.excel_io import load_clients
try:
    clients, wb, sheet, hdr = load_clients("data/agenda_jonha_2026-04-09.xlsx")
    print(f"Header row: {hdr}")
    print(f"Found clients: {len(clients)}")
except Exception as e:
    print(e)
