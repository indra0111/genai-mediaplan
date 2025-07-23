import json
# from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from genai_mediaplan.utils.update_charts import update_charts_in_slides
from genai_mediaplan.utils.persona import update_persona_content

# Set up credentials
# SERVICE_ACCOUNT_FILE = 'service_account.json'
SCOPES = ['https://www.googleapis.com/auth/drive']
CLIENT_SECRET_FILE = 'client_secret_drive.json'
TOKEN_FILE = 'token.json'
# SOURCE_FILE_ID = '1ruQjp-BGuOYrhvZYoh5_L7OntTjmtQYj6renzsL7aOg'
SOURCE_FILE_ID = '1f9nJb5rQ1IIulTe4QYvVvJziJxxd8gMDRWyet6_vKpw'
SOURCE_SHEET_ID = '1zGHhqOw3fsSHqPs4zD1RsFk1H0MTpd5Et65LkK2DZq0'
SHARED_FOLDER_ID = '15Uu1qL-uFFMANn7b2rLlVq7HZG7ytJuH'
CHART_SLIDE_INDEX = 4
PERSONA_SLIDE_INDEX_4 = 6
PERSONA_SLIDE_INDEX_6 = 7

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

    def safe_get_target_profiles(lst, idx):
        target_profiles = safe_get(lst, idx, {}).get('target_profiles', [])
        if target_profiles:
            return target_profiles
        else:
            return []
    data={
        "cohort_title": cohort_name,
        "cohort_updated_date": f"Audience Media Plan Forecast & Insights for {datetime.now().strftime('%B')} {datetime.now().strftime('%Y')}",
        "cohort_definition_title": f"{cohort_name} Cohort Definition",
        "cohort_definition": llm_response_json.get("cohort_definition", " "),
        "reach_cluster": f"{round(audience_forecast['TIL_All_Cluster_RNF']['India']['user'],2)}\nUser Reach (Reach fcap-1)",
        "impressions_cluster": f"{round(min(audience_forecast['TIL_All_Cluster_RNF']['India']['user'] * 3, audience_forecast['TIL_All_Cluster_RNF']['India']['impr']),2)}\nTargetable Impressions (Impressions fcap-3)",
        "reach_languages": f"{round(audience_forecast['TIL_All_Languages_RNF']['India']['user'],2)}\nUser Reach (Reach fcap-1)",
        "impressions_languages": f"{round(min(audience_forecast['TIL_All_Languages_RNF']['India']['user'] * 3, audience_forecast['TIL_All_Languages_RNF']['India']['impr']),2)}\nTargetable Impressions (Impressions fcap-3)",
        "reach_toi": f"{round(audience_forecast['TIL_TOI_Only_RNF']['India']['user'],2)}\nUser Reach (Reach fcap-1)",
        "impressions_toi": f"{round(min(audience_forecast['TIL_TOI_Only_RNF']['India']['user'] * 3, audience_forecast['TIL_TOI_Only_RNF']['India']['impr']),2)}\nTargetable Impressions (Impressions fcap-3)",
        "reach_combo": f"{round(audience_forecast['TIL_ET_And_TOI_RNF']['India']['user'],2)}\nUser Reach (Reach fcap-1)",
        "impressions_combo": f"{round(min(audience_forecast['TIL_ET_And_TOI_RNF']['India']['user'] * 3, audience_forecast['TIL_ET_And_TOI_RNF']['India']['impr']),2)}\nTargetable Impressions (Impressions fcap-3)",
        "reach_et": f'{round(audience_forecast["TIL_ET_Only_RNF"]["India"]["user"],2)}\nUser Reach (Reach fcap-1)',
        "impressions_et": f'{round(min(audience_forecast["TIL_ET_Only_RNF"]["India"]["user"] * 3, audience_forecast["TIL_ET_Only_RNF"]["India"]["impr"]),2)}\nTargetable Impressions (Impressions fcap-3)',
        "reach_nbt": f'{round(audience_forecast["TIL_NBT_Only_RNF"]["India"]["user"],2)}\nUser Reach (Reach fcap-1)',
        "impressions_nbt": f'{round(min(audience_forecast["TIL_NBT_Only_RNF"]["India"]["user"] * 3, audience_forecast["TIL_NBT_Only_RNF"]["India"]["impr"]),2)}\nTargetable Impressions (Impressions fcap-3)',
        "competitive_advantage": llm_response_json.get("market_edge", " "),
    }
    
    # Add data signals (3 titles, each with 5 signals)
    for i in range(3):
        data[f"data_signal_{i+1}_title"] = safe_get_title(llm_response_json.get("data_signals", []), i)
        for j in range(5):
            key = f"data_signal_{i+1}_{j+1}"
            val = safe_get_data_signals(llm_response_json.get("data_signals", []), i, j)
            data[key] = val

    persona_data = {}
    # Add personas (up to 6)
    for i in range(6):
        title = safe_get_title(llm_response_json.get("personas", []), i)
        if title:
            parts = title.split(" ")
            emoji = parts[0]
            text = " ".join(parts[1:])
            persona_data[f"persona_{i+1}_title"] = f"{emoji}\n{text}"
        persona_data[f"persona_{i+1}_description"] = safe_get_desc(llm_response_json.get("personas", []), i)
        persona_data[f"persona_{i+1}_target_profiles"] = safe_get_target_profiles(llm_response_json.get("personas", []), i)

    # Add insights (up to 3)
    for i in range(3):
        data[f"insight_{i+1}_title"] = safe_get_title(llm_response_json.get("insights", []), i)
        data[f"insight_{i+1}_description"] = safe_get_desc(llm_response_json.get("insights", []), i)

    # Add recommendations (up to 4)
    for i in range(4):
        data[f"recommendation_title_{i+1}"] = safe_get_title(llm_response_json.get("recommendations", []), i)
        data[f"recommendation_description_{i+1}"] = safe_get_desc(llm_response_json.get("recommendations", []), i)

    return data, persona_data

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
    print(f"Updating table with alt_text: {table_alt_text} with data: {data_rows}")
    requests = []

    # Get the presentation
    presentation = slides_service.presentations().get(presentationId=presentation_id).execute()

    for slide in presentation['slides']:
        for element in slide.get('pageElements', []):
            if element.get('description') == table_alt_text and 'table' in element:
                print(f"Found table with alt_text: {table_alt_text}")
                table = element['table']
                object_id = element['objectId']
                for row in range(len(data_rows)):
                    for col in range(len(data_rows[row])):
                        requests.extend(replace_table_cell_text(table, object_id, row+1, col, data_rows[row][col]))

    return requests

def get_tabular_data_for_preset(preset_name, audience_forecast):
    
    city_groups = ["Tier1 Cities", "Tier2 Cities", "Tier3", "Top 8 Metro Cities", "Top 10 Cities"]
    states = ["Maharashtra", "Karnataka", "Telangana", "Tamil Nadu", "Andhra Pradesh"]
    cities = ["Bengaluru", "Delhi", "Mumbai", "Pune", "Hyderabad", "Jaipur", "Chennai", "Indore", "Kochi"]
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
            fcap_3 = round(fcap_1 * 3, 2)
            country_tier_state_data.append([country, str(fcap_1), str(fcap_3)])
            
    country_tier_state_data.append(["Geographic Tiers", "", ""])
    for city_group in city_groups:
        entry = forecast_data.get(city_group)
        if entry:
            fcap_1 = round(entry["user"], 2)
            fcap_3 = round(fcap_1 * 3, 2)
            country_tier_state_data.append([city_group, str(fcap_1), str(fcap_3)])
            
    country_tier_state_data.append(["State", "", ""])
    for state in states:
        entry = forecast_data.get(state)
        if entry:
            fcap_1 = round(entry["user"], 2)
            fcap_3 = round(fcap_1 * 3, 2)
            country_tier_state_data.append([state, str(fcap_1), str(fcap_3)])
            
    city_data = []
            
    city_data.append(["Cities", "", ""])
    for city in cities:
        entry = forecast_data.get(city)
        if entry:
            fcap_1 = round(entry["user"], 2)
            fcap_3 = round(fcap_1 * 3, 2)
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

def delete_slides_requests(presentation_id, persona_slide_index):
    requests = []
    slide_indexes_to_delete = [2, 3, persona_slide_index]
    presentation = slides_service.presentations().get(presentationId=presentation_id).execute()
    slides = presentation['slides']
    for idx, slide in enumerate(slides):
        if idx in slide_indexes_to_delete:
            slide_id = slide['objectId']
            requests.append({
                "deleteObject": {"objectId": slide_id}
            })
    return requests

def get_persona_slide_index(data):
    desired_count = 6
    for i in range(6):
        if data.get(f"persona_{i+1}_title", {}).strip() == "":
            desired_count = i
            break
    return (PERSONA_SLIDE_INDEX_4, PERSONA_SLIDE_INDEX_6) if desired_count == 4 else (PERSONA_SLIDE_INDEX_6, PERSONA_SLIDE_INDEX_4)

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
    data, persona_data = get_content_to_replace_in_slides(cohort_name, llm_response_json, audience_forecast)
    persona_slide_index_to_keep, persona_slide_index_to_discard = get_persona_slide_index(persona_data)
    update_persona_content(slides_service, copied_file_id, persona_slide_index_to_keep, persona_data)
    delete_requests = delete_slides_requests(copied_file_id, persona_slide_index_to_discard)
    update_requests = update_slides_content(copied_file_id, data)
    update_requests_numerical = get_update_requests_for_numerical_data_in_slides(copied_file_id, audience_forecast)
    update_charts_in_slides(copied_file_id, copied_sheet_id, CHART_SLIDE_INDEX, None)
    final_requests = update_requests + update_requests_numerical + delete_requests
    if final_requests:
        slides_service.presentations().batchUpdate(
            presentationId=copied_file_id,
            body={"requests": final_requests}
        ).execute()
        print("✅ Text and paragraph formatting updated successfully.")
    else:
        print("ℹ️ No matching alt_text found.")
    return f"https://drive.google.com/file/d/{copied_file_id}"
    