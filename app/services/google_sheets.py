import gspread
from app.config import settings

def get_sheets_client() -> gspread.Client:
    return gspread.service_account_from_dict(settings.google_creds_json)

def sync_order_to_sheet(order_id: int, status: str, total: float, phone: str, delivery: str, items_str: str, admin: str = ""):
    client = get_sheets_client()
    sheet = client.open_by_key(settings.google_sheets_id).sheet1
    
    cell = sheet.find(str(order_id), in_column=1)
    if cell:
        sheet.update_cell(cell.row, 2, status)
        sheet.update_cell(cell.row, 7, admin)
    else:
        sheet.append_row([str(order_id), status, str(total), phone, delivery, items_str, admin])