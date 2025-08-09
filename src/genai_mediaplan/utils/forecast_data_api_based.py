import json
import requests
import os
from genai_mediaplan.utils.logger import get_logger

logger = get_logger(__name__)

def get_audience_data(abvr):
    final_data = {}
    url=f"{os.getenv('AUDIENCE_INFO_URL')}/getAudienceInfo"
    try:
        response = requests.post(url, data=abvr)
        data = response.json()
        for item in data:
            final_data[item["abvr"]] = {"name": item["audience_name"], "description": item["description"]}
    except Exception as e:
        logger.error(f"Error in getting audience data: {e}")
        return {}
    return final_data
    
def export_table_as_json(cohort_name):
    final_output = {"results": {}, "abvr": {}}
    try:
        all_cohorts = requests.get(f"{os.getenv('MEDIAPLAN_URL')}/get-all-mediaplan-cohorts").json()
        cohort = next((c for c in all_cohorts if c["name"] == cohort_name), None)
        if not cohort:
            raise ValueError(f"Cohort '{cohort_name}' not found.")
    
        abvrs = cohort["abvrs"]
        final_output["abvr"] = get_audience_data(abvrs)
        cohort_id = cohort["id"]
        
        cohort_details = requests.get(f"{os.getenv('MEDIAPLAN_URL')}/get-mediaplan-cohort-by-id/{cohort_id}").json()
        parent_info = cohort_details["parentTemplatesInfo"]
        if not parent_info:
            raise ValueError(f"No parentTemplatesInfo found for cohort '{cohort_name}'.")
        for _, value in parent_info.items():
            preset_data = json.loads(value["result"])
            preset_name = value["name"].split()[0].strip()
            final_output["results"][preset_name] = preset_data
        
        return final_output
    
    except Exception as e:
        logger.error(f"Error in getting forecast data: {e}")
        return {}