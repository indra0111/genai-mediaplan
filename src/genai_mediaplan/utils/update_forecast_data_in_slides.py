from datetime import datetime
import re
from googleapiclient.discovery import build
from google.oauth2 import service_account
from dotenv import load_dotenv
from genai_mediaplan.utils.helper import format_reach_impr
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/drive']
CLIENT_SECRET_FILE = 'client_secret_drive.json'
TOKEN_FILE = 'token.json'

creds = None
if os.path.exists(TOKEN_FILE):
    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
        creds = flow.run_local_server(port=0)
    # Save token for future use
    with open(TOKEN_FILE, 'w') as token:
        token.write(creds.to_json())
        
drive_service = build('drive', 'v3', credentials=creds)
slides_service = build('slides', 'v1', credentials=creds)

def get_non_tabular_forecast_data(audience_forecast):
    data = {
        "cohort_updated_date": f"Audience Media Plan Forecast & Insights for {datetime.now().strftime('%B')} {datetime.now().strftime('%Y')}",
    }
      
    geo_map = {
        "India": "india",
        "United States": "usa",
        "Canada": "canada",
        "GCC": "gcc",
        "Singapore": "singapore",
        "United Arab Emirates": "uae",
        "Saudi Arabia": "saudi_arabia",
        "Malaysia": "malaysia",
        "Indonesia": "indonesia",
        "South Africa": "south_africa",
        "Mauritius": "mauritius",
        "Australia": "australia"
    }
    
    preset_map = {
        "TIL_All_Cluster_RNF": "cluster",
        "TIL_All_Languages_RNF": "languages",
        "TIL_TOI_Only_RNF": "toi",
        "TIL_ET_Only_RNF": "et",
        "TIL_ET_And_TOI_RNF": "combo",
        "TIL_NBT_Only_RNF": "nbt",
    }
    
    for country_key, country_label in geo_map.items():
        for preset_key, preset_label in preset_map.items():
            user = audience_forecast[preset_key][country_key]["user"]
            impr = audience_forecast[preset_key][country_key]["impr"]
            reach, impressions = format_reach_impr(user, impr)
            data[f"{country_label}_reach_{preset_label}"] = reach
            data[f"{country_label}_impressions_{preset_label}"] = impressions
    return data

def replace_table_cell_text(table_element, table_object_id, row_index, col_index, new_text):

    cell = table_element["tableRows"][row_index]["tableCells"][col_index]
    text_elements = cell.get("text", {}).get("textElements", [])

    # Estimate endIndex for deleteText
    end_index = 0
    for el in text_elements:
        end_index = max(end_index, el.get("endIndex", 0))

    requests = []

    if end_index > 0:
        requests.append({
            "deleteText": {
                "objectId": table_object_id,
                "cellLocation": {
                    "rowIndex": row_index,
                    "columnIndex": col_index
                },
                "textRange": {
                    "type": "FIXED_RANGE",
                    "startIndex": 0,
                    "endIndex": end_index-1
                }
            }
        })
    # Step 2: Insert new text at index 0
    requests.append({
        "insertText": {
            "objectId": table_object_id,
            "cellLocation": {
                "rowIndex": row_index,
                "columnIndex": col_index
            },
            "insertionIndex": 0,
            "text": new_text
        }
    })
    return requests

def update_requests_for_tablular_data_in_slides(presentation_id, data_rows, table_alt_text):
    requests = []

    # Get the presentation
    presentation = slides_service.presentations().get(presentationId=presentation_id).execute()

    for slide in presentation['slides']:
        for element in slide.get('pageElements', []):
            if element.get('description') == table_alt_text and 'table' in element:
                table = element['table']
                object_id = element['objectId']
                for row in range(len(data_rows)):
                    for col in range(len(data_rows[row])):
                        requests.extend(replace_table_cell_text(table, object_id, row+1, col, data_rows[row][col]))

    return requests

def get_tabular_data_for_forecast_tables(preset_name, audience_forecast):
    
    city_groups = ["Tier1 Cities", "Tier2 Cities", "Tier3", "Top 8 Metro Cities", "Top 10 Cities"]
    states = ["Maharashtra", "Karnataka", "Telangana", "Tamil Nadu", "Andhra Pradesh"]
    cities = ["Bengaluru", "Delhi", "Mumbai", "Pune", "Hyderabad", "Nagpur", "Ahmedabad", "Vadodara", "Jaipur", "Chandigarh", "Indore","Lucknow","Kolkata","Chennai","Coimbatore","Kochi"]
    countries = ["India", "United States", "GCC", "Canada", "United Arab Emirates"]
    
    forecast_data = audience_forecast[preset_name]
    
    country_tier_state_data = []
    
    country_tier_state_data.append(["Countries", "", ""])
    for country in countries:
        entry = forecast_data.get(country)
        if entry:
            fcap_1 = round(entry["user"], 2)
            fcap_3 = round(min(fcap_1 * 3, entry["impr"]), 2)
            country_tier_state_data.append([country, str(fcap_1), str(fcap_3)])
            
    country_tier_state_data.append(["Geographic Tiers", "", ""])
    for city_group in city_groups:
        entry = forecast_data.get(city_group)
        if entry:
            fcap_1 = round(entry["user"], 2)
            fcap_3 = round(min(fcap_1 * 3, entry["impr"]), 2)
            country_tier_state_data.append([city_group, str(fcap_1), str(fcap_3)])
            
    country_tier_state_data.append(["State", "", ""])
    for state in states:
        entry = forecast_data.get(state)
        if entry:
            fcap_1 = round(entry["user"], 2)
            fcap_3 = round(min(fcap_1 * 3, entry["impr"]), 2)
            country_tier_state_data.append([state, str(fcap_1), str(fcap_3)])
            
    city_data = []
            
    city_data.append(["Cities", "", ""])
    for city in cities:
        entry = forecast_data.get(city)
        if entry:
            fcap_1 = round(entry["user"], 2)
            fcap_3 = round(min(fcap_1 * 3, entry["impr"]), 2)
            city_data.append([city, str(fcap_1), str(fcap_3)])
            
    return country_tier_state_data, city_data

def get_update_requests_for_numerical_data_in_slides(presentation_id, audience_forecast):
    final_requests = []
    preset_alt_mapping={
        "TIL_All_Cluster_RNF": "cluster",
        "TIL_All_Languages_RNF": "language",
        "TIL_TOI_Only_RNF": "TOI",
        "TIL_ET_Only_RNF": "ET",
        "TIL_ET_And_TOI_RNF": "combo",
        "TIL_NBT_Only_RNF": "NBT",
    }
    for preset in ["TIL_All_Cluster_RNF", "TIL_All_Languages_RNF", "TIL_TOI_Only_RNF", "TIL_ET_Only_RNF", "TIL_ET_And_TOI_RNF", "TIL_NBT_Only_RNF"]:
        country_tier_state_data, city_data= get_tabular_data_for_forecast_tables(preset, audience_forecast)
        country_tier_state_requests = update_requests_for_tablular_data_in_slides(presentation_id, country_tier_state_data, f"{preset_alt_mapping[preset]}_country_tier_state")
        city_requests = update_requests_for_tablular_data_in_slides(presentation_id, city_data, f"{preset_alt_mapping[preset]}_city")
        final_requests.extend(country_tier_state_requests + city_requests)
    return final_requests


def get_update_requests_for_non_tabular_forecast_data(presentation_id, data):
    requests = []
    presentation = slides_service.presentations().get(presentationId=presentation_id).execute()
    
    for slide in presentation['slides']:
        for element in slide.get('pageElements', []):
            if 'shape' in element:
                alt_text = element.get('description', '')
                if alt_text in data:
                    object_id = element['objectId']
                    shape = element['shape']
                    text_elements = shape.get('text', {}).get('textElements', [])
                    
                    if not text_elements:
                        continue
                    
                    # Extract original styles line by line
                    lines = []
                    current_line = ""
                    current_style = None
                    index = 0

                    for elem in text_elements:
                        if 'textRun' in elem:
                            content = elem['textRun'].get('content', '')
                            style = elem['textRun'].get('style', {})
                            for char in content:
                                if char == '\n':
                                    lines.append((current_line, current_style))
                                    current_line = ""
                                else:
                                    if current_line == "":
                                        current_style = style
                                    current_line += char
                        elif 'paragraphMarker' in elem:
                            if current_line:
                                lines.append((current_line, current_style))
                                current_line = ""

                    if current_line:
                        lines.append((current_line, current_style))

                    # Delete existing text
                    requests.append({
                        "deleteText": {
                            "objectId": object_id,
                            "textRange": {"type": "ALL"}
                        }
                    })

                    # Insert new text
                    new_text = str(data[alt_text])  # should include `\n` if multi-line
                    requests.append({
                        "insertText": {
                            "objectId": object_id,
                            "insertionIndex": 0,
                            "text": new_text
                        }
                    })

                    # Reapply text styles per line
                    char_index = 0
                    new_lines = new_text.split('\n')

                    for i, line_text in enumerate(new_lines):
                        if i < len(lines):
                            _, line_style = lines[i]
                            if line_style and len(line_text) > 0:
                                requests.append({
                                    "updateTextStyle": {
                                        "objectId": object_id,
                                        "style": line_style,
                                        "textRange": {
                                            "type": "FIXED_RANGE",
                                            "startIndex": char_index,
                                            "endIndex": char_index + len(line_text)+1
                                        },
                                        "fields": ",".join(line_style.keys())
                                    }
                                })
                        char_index += len(line_text) + 1  # account for `\n`

                    # Reapply paragraph style (alignment)
                    for elem in text_elements:
                        if 'paragraphMarker' in elem and 'style' in elem['paragraphMarker']:
                            para_style = elem['paragraphMarker']['style']
                            requests.append({
                                "updateParagraphStyle": {
                                    "objectId": object_id,
                                    "style": para_style,
                                    "textRange": {"type": "ALL"},
                                    "fields": ",".join(para_style.keys())
                                }
                            })
                            break  # Only need first one

    return requests

def update_presentation_title(presentation_id):
    file_metadata = drive_service.files().get(
        fileId=presentation_id,
        fields="name"
    ).execute()
    current_name = file_metadata["name"]
    current_month_year = datetime.now().strftime("%B%Y")
    new_name = re.sub(r"[A-Za-z]+[0-9]{4}$", current_month_year, current_name)
    drive_service.files().update(
        fileId=presentation_id,
        body={"name": new_name}
    ).execute()
    return new_name

def update_forecast_data_for_cohort(forecast_data, presentation_id):
    non_tabular_forecast_data = get_non_tabular_forecast_data(forecast_data)
    update_requests_based_on_alt_text = get_update_requests_for_non_tabular_forecast_data(presentation_id, non_tabular_forecast_data)
    update_requests_for_numerical_data = get_update_requests_for_numerical_data_in_slides(presentation_id, forecast_data)
    all_requests = update_requests_based_on_alt_text + update_requests_for_numerical_data
    slides_service.presentations().batchUpdate(presentationId=presentation_id, body={"requests": all_requests}).execute()
    update_presentation_title(presentation_id)
    return all_requests