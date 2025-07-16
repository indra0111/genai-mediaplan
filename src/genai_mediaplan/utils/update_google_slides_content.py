import json
# from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from genai_mediaplan.utils.update_charts import update_charts_in_slides

# Set up credentials
# SERVICE_ACCOUNT_FILE = 'service_account.json'
SCOPES = ['https://www.googleapis.com/auth/drive']
CLIENT_SECRET_FILE = 'client_secret_drive.json'
TOKEN_FILE = 'token.json'
SOURCE_FILE_ID = '1ruQjp-BGuOYrhvZYoh5_L7OntTjmtQYj6renzsL7aOg'
SOURCE_SHEET_ID = '1zGHhqOw3fsSHqPs4zD1RsFk1H0MTpd5Et65LkK2DZq0'
SHARED_FOLDER_ID = '15Uu1qL-uFFMANn7b2rLlVq7HZG7ytJuH'

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

def get_content_to_replace_in_slides(cohort_name, llm_response_json, audience_forecast):
    def safe_get(lst, index, default=" "):
        try:
            return lst[index]
        except (IndexError, TypeError):
            return default

    def safe_get_data_signals(lst, outer_idx, inner_idx, default=" "):
        try:
            return lst[outer_idx]["data_signals"][inner_idx]
        except (IndexError, KeyError, TypeError):
            return default

    def safe_get_title(lst, idx):
        return safe_get(lst, idx, {}).get("title", " ")

    def safe_get_desc(lst, idx):
        return safe_get(lst, idx, {}).get("description", " ")

    def safe_get_segments(lst, idx):
        no_of_segments = safe_get(lst, idx, {}).get('segments', '')
        if no_of_segments:
            return f"{no_of_segments} Segments"
        else:
            return " "
    data={
        "cohort_title": cohort_name,
        "cohort_updated_date": f"Audience Media Plan Forecast & Insights for {datetime.now().strftime('%B')} {datetime.now().strftime('%Y')}",
        "cohort_definition_title": f"{cohort_name} Cohort Definition",
        "cohort_definition": llm_response_json.get("cohort_definition", " "),
        "reach_cluster": round(audience_forecast["TIL_All_Cluster_RNF"]["India"]["user"],2),
        "impressions_cluster": round(min(audience_forecast["TIL_All_Cluster_RNF"]["India"]["user"] * 3, audience_forecast["TIL_All_Cluster_RNF"]["India"]["impr"]),2),
        "reach_languages": round(audience_forecast["TIL_All_Languages_RNF"]["India"]["user"],2),
        "impressions_languages": round(min(audience_forecast["TIL_All_Languages_RNF"]["India"]["user"] * 3, audience_forecast["TIL_All_Languages_RNF"]["India"]["impr"]),2),
        "reach_toi": round(audience_forecast["TIL_TOI_Only_RNF"]["India"]["user"],2),
        "impressions_toi": round(min(audience_forecast["TIL_TOI_Only_RNF"]["India"]["user"] * 3, audience_forecast["TIL_TOI_Only_RNF"]["India"]["impr"]),2),
        "reach_combo": round(audience_forecast["TIL_ET_And_TOI_RNF"]["India"]["user"],2),
        "impressions_combo": round(min(audience_forecast["TIL_ET_And_TOI_RNF"]["India"]["user"] * 3, audience_forecast["TIL_ET_And_TOI_RNF"]["India"]["impr"]),2),
        "reach_et": round(audience_forecast["TIL_ET_Only_RNF"]["India"]["user"],2),
        "impressions_et": round(min(audience_forecast["TIL_ET_Only_RNF"]["India"]["user"] * 3, audience_forecast["TIL_ET_Only_RNF"]["India"]["impr"]),2),
        "reach_nbt": round(audience_forecast["TIL_NBT_Only_RNF"]["India"]["user"],2),
        "impressions_nbt": round(min(audience_forecast["TIL_NBT_Only_RNF"]["India"]["user"] * 3, audience_forecast["TIL_NBT_Only_RNF"]["India"]["impr"]),2),
        "competitive_advantage": llm_response_json.get("market_edge", " "),
    }
    
    # Add data signals (3 titles, each with 5 signals)
    for i in range(3):
        data[f"data_signal_{i+1}_title"] = safe_get_title(llm_response_json.get("data_signals", []), i)
        for j in range(5):
            key = f"data_signal_{i+1}_{j+1}"
            val = safe_get_data_signals(llm_response_json.get("data_signals", []), i, j)
            data[key] = val

    # Add personas (up to 6)
    for i in range(6):
        data[f"persona_{i+1}_title"] = safe_get_title(llm_response_json.get("personas", []), i)
        data[f"persona_{i+1}_description"] = safe_get_desc(llm_response_json.get("personas", []), i)
        data[f"persona_{i+1}_segments"] = safe_get_segments(llm_response_json.get("personas", []), i)

    # Add insights (up to 3)
    for i in range(3):
        data[f"insight_{i+1}_title"] = safe_get_title(llm_response_json.get("insights", []), i)
        data[f"insight_{i+1}_description"] = safe_get_desc(llm_response_json.get("insights", []), i)

    # Competitive advantage
    data["competitive_advantage"] = llm_response_json.get("market_edge", " ")

    # Add recommendations (up to 4)
    for i in range(4):
        data[f"recommendation_title_{i+1}"] = safe_get_title(llm_response_json.get("recommendations", []), i)
        data[f"recommendation_description_{i+1}"] = safe_get_desc(llm_response_json.get("recommendations", []), i)

    return data

def update_slides_content(copied_file_id, data):
    requests = []
    presentation = slides_service.presentations().get(presentationId=copied_file_id).execute()
    for slide in presentation['slides']:
        for element in slide.get('pageElements', []):
            if 'shape' in element:
                alt_text = element.get('description', '')
                if alt_text in data:
                    object_id = element['objectId']
                    shape = element['shape']
                    text_elements = shape.get('text', {}).get('textElements', [])
                    
                    # Skip if empty
                    if not text_elements:
                        continue
                    # Extract text style and paragraph style
                    text_style = {}
                    para_style = {}

                    for elem in text_elements:
                        if 'textRun' in elem and 'style' in elem['textRun']:
                            text_style = elem['textRun']['style']
                            break  # assume consistent style; take first
                    for elem in text_elements:
                        if 'paragraphMarker' in elem and 'style' in elem['paragraphMarker']:
                            para_style = elem['paragraphMarker']['style']
                            break  # assume first paragraph style is good

                    # Clear text
                    requests.append({
                        "deleteText": {
                            "objectId": object_id,
                            "textRange": {"type": "ALL"}
                        }
                    })

                    # Insert new text
                    new_text = str(data[alt_text])
                    requests.append({
                        "insertText": {
                            "objectId": object_id,
                            "insertionIndex": 0,
                            "text": new_text
                        }
                    })

                    # Reapply text style
                    if text_style:
                        requests.append({
                            "updateTextStyle": {
                                "objectId": object_id,
                                "style": text_style,
                                "textRange": {"type": "ALL"},
                                "fields": ",".join(text_style.keys())
                            }
                        })

                    # Reapply paragraph style (like alignment)
                    if para_style:
                        requests.append({
                            "updateParagraphStyle": {
                                "objectId": object_id,
                                "style": para_style,
                                "textRange": {"type": "ALL"},
                                "fields": ",".join(para_style.keys())
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
                print(f"Found table with alt_text: {table_alt_text}")
                table = element['table']
                object_id = element['objectId']

                num_rows = table['rows']
                num_cols = table['columns']

                # Skip header row (row 0), start from row 1
                for row_index, row_data in enumerate(data_rows, start=1):
                    if row_index >= num_rows:
                        print(f"⚠️ Skipping row {row_index}: table only has {num_rows} rows.")
                        break
                    for col_index, value in enumerate(row_data):
                        if col_index >= num_cols:
                            print(f"⚠️ Skipping column {col_index}: table only has {num_cols} columns.")
                            continue

                        # Clear the existing cell text
                        requests.append({
                            "deleteText": {
                                "objectId": object_id,
                                "cellLocation": {
                                    "rowIndex": row_index,
                                    "columnIndex": col_index
                                },
                                "textRange": {"type": "ALL"}
                            }
                        })

                        # Insert new value
                        requests.append({
                            "insertText": {
                                "objectId": object_id,
                                "cellLocation": {
                                    "rowIndex": row_index,
                                    "columnIndex": col_index
                                },
                                "insertionIndex": 0,
                                "text": str(value)
                            }
                        })

    return requests

def get_tabular_data_for_preset(preset_name, audience_forecast):
    
    city_groups = ["Tier1 Cities", "Tier2 Cities", "Tier3", "Top 8 Metro Cities", "Top 10 Cities"]
    states = ["Maharashtra", "Karnataka", "Telangana", "Tamil Nadu", "Andhra Pradesh"]
    cities = ["Bengaluru", "Delhi", "Mumbai", "Pune", "Jaipur"]
    countries = ["India", "United States", "GCC", "Canada", "United Arab Emirates"]
    
    forecast_data = audience_forecast[preset_name]
    
    city_group_data = []
    for city_group in city_groups:
        entry = forecast_data.get(city_group)
        if entry:
            fcap_1 = round(entry["user"], 2)
            fcap_3 = round(fcap_1 * 3, 2)
            city_group_data.append([city_group, str(fcap_1), str(fcap_3)])
            
    state_data = []
    for state in states:
        entry = forecast_data.get(state)
        if entry:
            fcap_1 = round(entry["user"], 2)
            fcap_3 = round(fcap_1 * 3, 2)
            state_data.append([state, str(fcap_1), str(fcap_3)])
            
    city_data = []
    for city in cities:
        entry = forecast_data.get(city)
        if entry:
            fcap_1 = round(entry["user"], 2)
            fcap_3 = round(fcap_1 * 3, 2)
            city_data.append([city, str(fcap_1), str(fcap_3)])
            
    country_data = []
    for country in countries:
        entry = forecast_data.get(country)
        if entry:
            fcap_1 = round(entry["user"], 2)
            fcap_3 = round(fcap_1 * 3, 2)
            country_data.append([country, str(fcap_1), str(fcap_3)])
        
    return city_group_data, state_data, city_data, country_data

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
        city_group_data, state_data, city_data, country_data = get_tabular_data_for_preset(preset, audience_forecast)
        city_group_requests = update_requests_for_tablular_data_in_slides(presentation_id, city_group_data, f"{preset_alt_mapping[preset]}_tier")
        state_requests = update_requests_for_tablular_data_in_slides(presentation_id, state_data, f"{preset_alt_mapping[preset]}_state")
        city_requests = update_requests_for_tablular_data_in_slides(presentation_id, city_data, f"{preset_alt_mapping[preset]}_city")
        country_requests = update_requests_for_tablular_data_in_slides(presentation_id, country_data, f"{preset_alt_mapping[preset]}_country")
        final_requests.extend(city_group_requests + state_requests + city_requests + country_requests)
    return final_requests

def get_copy_of_presentation(cohort_name, llm_response_json, audience_forecast):
    copied_file = drive_service.files().copy(
        fileId=SOURCE_FILE_ID,
        body={
            'name': f'TIL_CohortDashboard_{"".join(cohort_name.split(" "))}_Forecast_{datetime.now().strftime("%B%Y")}',
            'parents': [SHARED_FOLDER_ID]
        }
    ).execute()
    sheet_copy = drive_service.files().copy(
        fileId=SOURCE_SHEET_ID,
        body={
            'name': f'Charts_{"".join(cohort_name.split(" "))}_{datetime.now().strftime("%B%Y")}',
            'parents': [SHARED_FOLDER_ID]
        }
    ).execute()
    print(f"Copy created: https://drive.google.com/file/d/{copied_file['id']}")
    copied_file_id = copied_file['id']
    copied_sheet_id = sheet_copy['id']
    data = get_content_to_replace_in_slides(cohort_name, llm_response_json, audience_forecast)
    update_requests = update_slides_content(copied_file_id, data)
    update_requests_numerical = get_update_requests_for_numerical_data_in_slides(copied_file_id, audience_forecast)
    update_charts_in_slides(copied_file_id, copied_sheet_id, 4, None)
    final_requests = update_requests + update_requests_numerical
    if final_requests:
        slides_service.presentations().batchUpdate(
            presentationId=copied_file_id,
            body={"requests": final_requests}
        ).execute()
        print("✅ Text and paragraph formatting updated successfully.")
    else:
        print("ℹ️ No matching alt_text found.")
    return f"https://drive.google.com/file/d/{copied_file_id}"
    