import sys
from datetime import date
from agenda_app.excel_io import load_clients, write_agenda_flat_sheet, write_weekly_agenda_sheet, save_workbook
from agenda_app.planner import build_agenda

path = "data/Clientes_Vendedor130_por_Departamento_separando personas.xlsx"
clients, wb, sheet, hdr = load_clients(path)
print(f"Original clients: {len(clients)}")

visits, first_next = build_agenda(clients, date.today(), 7, visits_per_day=3)
write_agenda_flat_sheet(wb, visits)
write_weekly_agenda_sheet(wb, visits)

out_path = "data/agenda_test_output.xlsx"
save_workbook(wb, out_path)

clients2, wb2, sheet2, hdr2 = load_clients(out_path)
print(f"Reloaded clients: {len(clients2)}")
