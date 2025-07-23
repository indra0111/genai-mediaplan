import re
import json

def extract_json_from_markdown_or_json(final_report_path):
    """
    Extracts a JSON object from a file that could either be:
    1. Markdown with a ```json block
    2. A raw JSON file
    """
    try:
        with open(final_report_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"❌ File not found: {final_report_path}")
        return None
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return None

    # Try case 1: JSON block in markdown
    match = re.search(r"```json\s*(\{.*?\})\s*```", content, re.DOTALL)
    if match:
        json_str = match.group(1)
    else:
        # Case 2: Try parsing the entire content as JSON
        json_str = content

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print("❌ JSON decode error:", e)
        print("⚠️ Offending JSON string (truncated):", json_str[:300])
        return None

def find_object_id_by_alt_description(slides, alt_title):
    for slide in slides:
        for element in slide.get('pageElements', []):
            title = element.get('description')
            if title == alt_title:
                return element['objectId']
    return None