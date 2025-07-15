import re
import json

def extract_json_from_markdown(final_report_path):
    """
    Reads a markdown file and extracts the first JSON block found within triple backticks.
    """
    try:
        with open(final_report_path, 'r', encoding='utf-8') as f:
            markdown_text = f.read()
    except FileNotFoundError:
        print(f"File not found: {final_report_path}")
        return None
    except Exception as e:
        print(f"Error reading file: {e}")
        return None

    match = re.search(r"```json\s*(\{.*?\})\s*```", markdown_text, re.DOTALL)
    if match:
        json_str = match.group(1)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            print("JSON decode error:", e)
            print("Offending JSON string:", json_str)
    else:
        print("No JSON block found.")
    return None
