#!/usr/bin/env python3
"""
Test script for the GenAI Mediaplan API
"""
import requests
import json
import time
import os
from dotenv import load_dotenv

load_dotenv()


# API base URL
BASE_URL = "http://localhost:8000"
MEDIAPLAN_URL = os.getenv("MEDIAPLAN_URL")

def get_all_cohorts():
    url = f"{MEDIAPLAN_URL}/get-all-mediaplan-cohorts"
    response = requests.get(url)
    data = response.json()
    return [item["name"] for item in data]

def main():
    cohorts = get_all_cohorts()
    print(cohorts)
    
    responses = {}

    for cohort in cohorts:
        print(cohort)
        url = f"{BASE_URL}/generate-mediaplan"
        try:
            response = requests.post(url, json={"cohort_name": cohort})
            data = response.json()
            print(data)
            responses[cohort] = {
                "status": data.get("status"),
                "message": data.get("message"),
                "google_slides_url": data.get("google_slides_url", None),
            }
        except Exception as e:
            error_msg = f"Error generating mediaplan for {cohort}: {e}"
            print(error_msg)
            responses[cohort] = {
                "status": "error",
                "message": error_msg
            }

        # Write all collected responses to a JSON file
        with open("mediaplan_responses.json", "w", encoding="utf-8") as json_file:
            json.dump(responses, json_file, indent=4)
        
if __name__ == "__main__":
    main() 