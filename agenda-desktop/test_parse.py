import sys
from agenda_app.excel_io import load_clients
clients, wb, sheet, hdr = load_clients("data/Clientes_Vendedor130_por_Departamento_separando personas.xlsx")
print(f"Header row: {hdr}")
print(f"Found clients: {len(clients)}")
