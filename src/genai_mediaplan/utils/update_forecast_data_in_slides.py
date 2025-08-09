from googleapiclient.discovery import build
from google.oauth2 import service_account
from dotenv import load_dotenv

load_dotenv()

SERVICE_ACCOUNT_FILE = 'service_account.json'
SCOPES = ['https://www.googleapis.com/auth/drive']
credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
slides_service = build('slides', 'v1', credentials=credentials)

def get_non_tabular_forecast_data(audience_forecast):
    return {
        "reach_cluster": f"{round(audience_forecast['TIL_All_Cluster_RNF']['India']['user'],2)}\nUser Reach",
        "impressions_cluster": f"{round(min(audience_forecast['TIL_All_Cluster_RNF']['India']['user'] * 3, audience_forecast['TIL_All_Cluster_RNF']['India']['impr']),2)}\nTargetable Impressions",
        "reach_languages": f"{round(audience_forecast['TIL_All_Languages_RNF']['India']['user'],2)}\nUser Reach",
        "impressions_languages": f"{round(min(audience_forecast['TIL_All_Languages_RNF']['India']['user'] * 3, audience_forecast['TIL_All_Languages_RNF']['India']['impr']),2)}\nTargetable Impressions",
        "reach_toi": f"{round(audience_forecast['TIL_TOI_Only_RNF']['India']['user'],2)}\nUser Reach",
        "impressions_toi": f"{round(min(audience_forecast['TIL_TOI_Only_RNF']['India']['user'] * 3, audience_forecast['TIL_TOI_Only_RNF']['India']['impr']),2)}\nTargetable Impressions",
        "reach_combo": f"{round(audience_forecast['TIL_ET_And_TOI_RNF']['India']['user'],2)}\nUser Reach",
        "impressions_combo": f"{round(min(audience_forecast['TIL_ET_And_TOI_RNF']['India']['user'] * 3, audience_forecast['TIL_ET_And_TOI_RNF']['India']['impr']),2)}\nTargetable Impressions",
        "reach_et": f'{round(audience_forecast["TIL_ET_Only_RNF"]["India"]["user"],2)}\nUser Reach',
        "impressions_et": f'{round(min(audience_forecast["TIL_ET_Only_RNF"]["India"]["user"] * 3, audience_forecast["TIL_ET_Only_RNF"]["India"]["impr"]),2)}\nTargetable Impressions',
        "reach_nbt": f'{round(audience_forecast["TIL_NBT_Only_RNF"]["India"]["user"],2)}\nUser Reach',
        "impressions_nbt": f'{round(min(audience_forecast["TIL_NBT_Only_RNF"]["India"]["user"] * 3, audience_forecast["TIL_NBT_Only_RNF"]["India"]["impr"]),2)}\nTargetable Impressions'
    }

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

def update_forecast_data_for_cohort(forecast_data, presentation_id):
    non_tabular_forecast_data = get_non_tabular_forecast_data(forecast_data)
    update_requests_based_on_alt_text = get_update_requests_for_non_tabular_forecast_data(presentation_id, non_tabular_forecast_data)
    update_requests_for_numerical_data = get_update_requests_for_numerical_data_in_slides(presentation_id, forecast_data)
    all_requests = update_requests_based_on_alt_text + update_requests_for_numerical_data
    slides_service.presentations().batchUpdate(presentationId=presentation_id, body={"requests": all_requests}).execute()
    return all_requests