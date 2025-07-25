import os
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

def get_chart_ids(copied_sheet_id, sheets_service):
    response = sheets_service.spreadsheets().get(
        spreadsheetId=copied_sheet_id,
        includeGridData=False
    ).execute()
    chart_map = {}
    sheets = response.get('sheets', [])
    for sheet in sheets:
        sheet_title = sheet['properties']['title']
        charts = sheet.get('charts', [])
        if charts:
            for chart in charts:
                chart_map[sheet_title] = chart['chartId']
    return chart_map

def update_charts_preserving_position(copied_slide_id, slides_service, copied_sheet_id, chart_map, target_slide_index=1):
    presentation = slides_service.presentations().get(presentationId=copied_slide_id).execute()
    slides = presentation.get('slides')

    if target_slide_index >= len(slides):
        print(f"❌ Slide index {target_slide_index} does not exist in presentation.")
        return

    target_slide = slides[target_slide_index]
    page_id = target_slide['objectId']
    requests = []

    # Step 1: Collect old chart object details
    chart_elements = []
    for element in target_slide.get('pageElements', []):
        if 'sheetsChart' in element:
            chart_elements.append({
                'objectId': element['objectId'],
                'transform': element['transform'],
                'size': element.get('size', {
                    'height': {'magnitude': 250, 'unit': 'PT'},
                    'width': {'magnitude': 300, 'unit': 'PT'}
                })
            })

    if not chart_elements:
        print("⚠️ No existing charts to replace.")
        return

    # Step 2: Replace charts using saved positions
    for (sheet_name, chart_id), chart_info in zip(chart_map.items(), chart_elements):
        requests.append({
            'deleteObject': {
                'objectId': chart_info['objectId']
            }
        })
        requests.append({
            'createSheetsChart': {
                'spreadsheetId': copied_sheet_id,
                'chartId': chart_id,
                'linkingMode': 'LINKED',
                'elementProperties': {
                    'pageObjectId': page_id,
                    'size': chart_info['size'],
                    'transform': chart_info['transform']
                }
            }
        })

    # Step 3: Execute batch update
    if requests:
        slides_service.presentations().batchUpdate(
            presentationId=copied_slide_id,
            body={'requests': requests}
        ).execute()
        print(f"✅ {len(requests)//2} charts replaced in slide {target_slide_index + 1}.")
    else:
        print("⚠️ No charts replaced.")
        
def update_chart_data_in_sheets(spreadsheet_id, sheets_service, chart_data):
    requests = []

    for sheet_name, values in chart_data.items():
        range_notation = f"{sheet_name}!A2:B{len(values) + 1}"

        requests.append({
            "range": range_notation,
            "values": values
        })

    if not requests:
        print("⚠️ No data to update.")
        return

    body = {
        "valueInputOption": "RAW",
        "data": requests
    }

    response = sheets_service.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=body
    ).execute()

    print(f"✅ Updated data in {len(chart_data)} sheet(s): {list(chart_data.keys())}")
    
def update_charts_in_slides(copied_slide_id, slides_service, copied_sheet_id, sheets_service, target_slide_index, chart_data=None):
    chart_ids_map = get_chart_ids(copied_sheet_id, sheets_service)
    update_charts_preserving_position(copied_slide_id, slides_service, copied_sheet_id, chart_ids_map, target_slide_index)
    if chart_data:
        update_chart_data_in_sheets(copied_sheet_id, sheets_service, chart_data)
    
    