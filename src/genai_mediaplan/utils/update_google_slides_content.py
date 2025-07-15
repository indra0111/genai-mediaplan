import json
# from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Set up credentials
# SERVICE_ACCOUNT_FILE = 'service_account.json'
SCOPES = ['https://www.googleapis.com/auth/drive']
CLIENT_SECRET_FILE = 'client_secret_drive.json'
TOKEN_FILE = 'token.json'
SOURCE_FILE_ID = '1ruQjp-BGuOYrhvZYoh5_L7OntTjmtQYj6renzsL7aOg'
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
    data={
        "cohort_title": cohort_name,
        "cohort_updated_date": f"Audience Media Plan Forecast & Insights for {datetime.now().strftime('%B')} {datetime.now().strftime('%Y')}",
        "cohort_definition_title": f"{cohort_name} Cohort Definition",
        "cohort_definition": llm_response_json["cohort_definition"],
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
        
        "data_signal_1_title": llm_response_json["data_signals"][0]["title"],
        "data_signal_1_1": llm_response_json["data_signals"][0]["data_signals"][0],
        "data_signal_1_2": llm_response_json["data_signals"][0]["data_signals"][1],
        "data_signal_1_3": llm_response_json["data_signals"][0]["data_signals"][2],
        "data_signal_1_4": llm_response_json["data_signals"][0]["data_signals"][3],
        "data_signal_1_5": llm_response_json["data_signals"][0]["data_signals"][4],
        "data_signal_2_title": llm_response_json["data_signals"][1]["title"],
        "data_signal_2_1": llm_response_json["data_signals"][1]["data_signals"][0],
        "data_signal_2_2": llm_response_json["data_signals"][1]["data_signals"][1],
        "data_signal_2_3": llm_response_json["data_signals"][1]["data_signals"][2],
        "data_signal_2_4": llm_response_json["data_signals"][1]["data_signals"][3],
        "data_signal_2_5": llm_response_json["data_signals"][1]["data_signals"][4],
        "data_signal_3_title": llm_response_json["data_signals"][2]["title"],
        "data_signal_3_1": llm_response_json["data_signals"][2]["data_signals"][0],
        "data_signal_3_2": llm_response_json["data_signals"][2]["data_signals"][1],
        "data_signal_3_3": llm_response_json["data_signals"][2]["data_signals"][2],
        "data_signal_3_4": llm_response_json["data_signals"][2]["data_signals"][3],
        "data_signal_3_5": llm_response_json["data_signals"][2]["data_signals"][4],
        
        "persona_1_title": llm_response_json["personas"][0]["title"],
        "persona_1_description": llm_response_json["personas"][0]["description"],
        "persona_1_segments": f"{llm_response_json['personas'][0]['segments']} Segments",
        "persona_2_title": llm_response_json["personas"][1]["title"],
        "persona_2_description": llm_response_json["personas"][1]["description"],
        "persona_2_segments": f"{llm_response_json['personas'][1]['segments']} Segments",
        "persona_3_title": llm_response_json["personas"][2]["title"],
        "persona_3_description": llm_response_json["personas"][2]["description"],
        "persona_3_segments": f"{llm_response_json['personas'][2]['segments']} Segments",
        "persona_4_title": llm_response_json["personas"][3]["title"],
        "persona_4_description": llm_response_json["personas"][3]["description"],
        "persona_4_segments": f"{llm_response_json['personas'][3]['segments']} Segments",
        "persona_5_title": llm_response_json["personas"][4]["title"],
        "persona_5_description": llm_response_json["personas"][4]["description"],
        "persona_5_segments": f"{llm_response_json['personas'][4]['segments']} Segments",
        "persona_6_title": llm_response_json["personas"][5]["title"],
        "persona_6_description": llm_response_json["personas"][5]["description"],
        "persona_6_segments": f"{llm_response_json['personas'][5]['segments']} Segments",
        
        "insight_1_title": llm_response_json["insights"][0]["title"],
        "insight_1_description": llm_response_json["insights"][0]["description"],
        "insight_2_title": llm_response_json["insights"][1]["title"],
        "insight_2_description": llm_response_json["insights"][1]["description"],
        "insight_3_title": llm_response_json["insights"][2]["title"],
        "insight_3_description": llm_response_json["insights"][2]["description"],
        
        "recommendation_title_1": llm_response_json["recommendations"][0]["title"],
        "recommendation_description_1": llm_response_json["recommendations"][0]["description"],
        "recommendation_title_2": llm_response_json["recommendations"][1]["title"],
        "recommendation_description_2": llm_response_json["recommendations"][1]["description"],
        "recommendation_title_3": llm_response_json["recommendations"][2]["title"],
        "recommendation_description_3": llm_response_json["recommendations"][2]["description"],
        "recommendation_title_4": llm_response_json["recommendations"][3]["title"],
        "recommendation_description_4": llm_response_json["recommendations"][3]["description"]
    }
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
        print(f"For {preset} city_group_data: {city_group_data}")
        print(f"For {preset} state_data: {state_data}")
        print(f"For {preset} city_data: {city_data}")
        print(f"For {preset} country_data: {country_data}")
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
    print(f"Copy created: https://drive.google.com/file/d/{copied_file['id']}")
    copied_file_id = copied_file['id']
    data = get_content_to_replace_in_slides(cohort_name, llm_response_json, audience_forecast)
    update_requests = update_slides_content(copied_file_id, data)
    update_requests_numerical = get_update_requests_for_numerical_data_in_slides(copied_file_id, audience_forecast)
    print(f"update_requests_numerical: {update_requests_numerical}")
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
    
# def main():
#     cohort_name = "College Students"
#     # Make a copy into that folder

#     # copied_file_id = '1NcRHEWP8k0aDSkDqhs54XQ4w0O2KCJNoxEckOSR8T8g'
#     with open("llm_response.json", "r") as f:
#         llm_response_json = json.load(f)
#     print(f"llm_response_json: {llm_response_json}")
#     with open("cohort_result_table.json", "r") as f:
#         audience_forecast = json.load(f)["results"]
#     print(f"audience_forecast: {audience_forecast}")
#     get_copy_of_presentation(cohort_name, llm_response_json, audience_forecast)

# if __name__ == "__main__":
#     main()