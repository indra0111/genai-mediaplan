import mysql.connector
import json
import requests
import os
def get_audience_data(abvr):
    final_data = {}
    url=f"{os.getenv('AUDIENCE_INFO_URL')}/getAudienceInfo"
    try:
        response = requests.post(url, data=abvr)
        data = response.json()
        for item in data:
            final_data[item["abvr"]] = {"name": item["audience_name"], "description": item["description"]}
    except Exception as e:
        print(f"Error in getting audience data: {e}")
        return {}
    return final_data
    
def process_forecast_data(data):
    final_output = {"results": {}, "abvr": {}}
    abvrs=""
    for entry in data:
        result_dict = json.loads(entry["result"])
        parent_data_dict = json.loads(entry["parent_data"])
        preset_name = parent_data_dict["inventoryPresets"]
        abvrs = parent_data_dict["abvr"]
        final_output["results"][preset_name] = result_dict
        
    final_output["abvr"] = get_audience_data(abvrs)
    return final_output
    
def export_table_as_json(cohort_id):
    connection = mysql.connector.connect(
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        database=os.getenv('DB_NAME')
    )

    try:
        with connection.cursor() as cursor:
            sql = """
            SELECT dfp_runs.result, dfp_runs.parent_data,
                   SUBSTRING_INDEX(template_cohort_report.name, ' ', 1) AS preset
            FROM dfp_runs
            JOIN template_cohort_report ON dfp_runs.report_id = template_cohort_report.report_id
            WHERE template_cohort_report.cohort_id = (
                SELECT id FROM mediaplan_cohorts WHERE name = %s AND is_deleted=0
            );
            """
            cursor.execute(sql, (cohort_id,))
            rows = cursor.fetchall()

            if not rows:
                print(f" No rows returned for cohort ID {cohort_id}")
                return

            columns = [desc[0] for desc in cursor.description]
            result_table = [dict(zip(columns, row)) for row in rows]
            final_output = process_forecast_data(result_table)
            return final_output
    finally:
        connection.close()