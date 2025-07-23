import os
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

def find_object_ids_by_alt_description(slides_service, presentation_id, slide_index):
    presentation = slides_service.presentations().get(presentationId=presentation_id).execute()
    slides = presentation.get('slides', [])
    
    if slide_index >= len(slides):
        raise IndexError(f"Slide index {slide_index} out of range.")
    
    slide_id = slides[slide_index]['objectId']
    
    response = slides_service.presentations().pages().get(
        presentationId=presentation_id,
        pageObjectId=slide_id
    ).execute()
    
    elements = response.get('pageElements', [])
    
    alt_descriptions=[f"persona_{i+1}" for i in range(6)]
    alt_descriptions.extend([f"persona_{i+1}_title" for i in range(6)])
    alt_descriptions.extend([f"persona_{i+1}_description" for i in range(6)])
    alt_descriptions.extend([f"persona_{i+1}_target_profiles" for i in range(6)])
    object_ids = {}
    styles = {}
    for element in elements:
        description = element.get('description')
        if description in alt_descriptions:
            object_ids[description] = element.get('objectId')
            shape = element['shape']
            text_elements = shape.get('text', {}).get('textElements', [])
            text_style = {}
            para_style = {}
            emoji_style = {}
            for elem in text_elements:
                if 'paragraphMarker' in elem and 'style' in elem['paragraphMarker']:
                    para_style = elem['paragraphMarker']['style']
                    break  # assume first paragraph style is good
                
            if description.endswith('_title'):
                emoji_found = False
                for elem in text_elements:
                    if 'textRun' in elem:
                        text = elem['textRun'].get('content', '')
                        style = elem['textRun'].get('style', {})

                        if not emoji_found and '\n' in text:
                            emoji_char = text.split('\n')[0]
                            if emoji_char.strip():
                                emoji_style = style
                                emoji_found = True

                                # If there’s text after the emoji in the same textRun
                                after_emoji = text.split('\n', 1)[1]
                                if after_emoji.strip():
                                    text_style = style  # same style assumed
                                continue
                        elif emoji_found:
                            # First non-emoji style run
                            if style:
                                text_style = style
                                break
                        else:
                            # Might be an emoji in its own run
                            if text.strip() and not emoji_found:
                                emoji_style = style
                                emoji_found = True
            else:
                for elem in text_elements:
                    if 'textRun' in elem and 'style' in elem['textRun']:
                        text_style = elem['textRun']['style']
                        break
                    
            styles[description] = {
                "text_style": text_style,
                "para_style": para_style
            }
            if emoji_style:
                styles[description]["emoji_style"] = emoji_style
    return object_ids, styles

def utf16_len(text):
    return len(text.encode('utf-16-le')) // 2

def update_textboxes(slides_service, presentation_id, textbox_ids, styles, desired_count, data):
    requests = []

    for i in range(desired_count):
        title_key = f"persona_{i+1}_title"
        description_key = f"persona_{i+1}_description"
        target_profiles_key = f"persona_{i+1}_target_profiles"

        title_id = textbox_ids[title_key]
        description_id = textbox_ids[description_key]
        target_profiles_id = textbox_ids[target_profiles_key]

        # --- Handle Title: {emoji}\n{content} ---
        title_text = data[title_key]
        emoji_part = title_text.split("\n", 1)[0]
        emoji_len = utf16_len(emoji_part)

        requests.append({
            "deleteText": {
                "objectId": title_id,
                "textRange": {"type": "ALL"}
            }
        })
        requests.append({
            "insertText": {
                "objectId": title_id,
                "text": title_text
            }
        })

        # Style for emoji (assumes first character is emoji and is followed by \n)
        emoji_style = styles.get(title_key, {}).get("emoji_style")
        content_style = styles.get(title_key, {}).get("text_style")
        para_style = styles.get(title_key, {}).get("para_style")

        if emoji_style:
            requests.append({
                "updateTextStyle": {
                    "objectId": title_id,
                    "style": emoji_style,
                    "textRange": {"type": "FIXED_RANGE", "startIndex": 0, "endIndex": emoji_len},
                    "fields": ",".join(emoji_style.keys())
                }
            })

        emoji_and_newline = title_text.split("\n", 1)[0] + "\n"
        content_start_index = utf16_len(emoji_and_newline)

        if content_style and content_start_index < utf16_len(title_text):
            requests.append({
                "updateTextStyle": {
                    "objectId": title_id,
                    "style": content_style,
                    "textRange": {
                        "type": "FIXED_RANGE",
                        "startIndex": content_start_index,
                        "endIndex": utf16_len(title_text)
                    },
                    "fields": ",".join(content_style.keys())
                }
            })


        if para_style:
            requests.append({
                "updateParagraphStyle": {
                    "objectId": title_id,
                    "style": para_style,
                    "textRange": {"type": "ALL"},
                    "fields": ",".join(para_style.keys())
                }
            })

        # --- Handle Description ---
        description_text = data[description_key]
        requests.append({
            "deleteText": {"objectId": description_id, "textRange": {"type": "ALL"}}
        })
        requests.append({
            "insertText": {"objectId": description_id, "text": description_text}
        })
        if styles.get(description_key, {}).get("text_style"):
            requests.append({
                "updateTextStyle": {
                    "objectId": description_id,
                    "style": styles[description_key]["text_style"],
                    "textRange": {"type": "ALL"},
                    "fields": ",".join(styles[description_key]["text_style"].keys())
                }
            })
        if styles.get(description_key, {}).get("para_style"):
            requests.append({
                "updateParagraphStyle": {
                    "objectId": description_id,
                    "style": styles[description_key]["para_style"],
                    "textRange": {"type": "ALL"},
                    "fields": ",".join(styles[description_key]["para_style"].keys())
                }
            })

        # --- Handle Target Profiles with Bullets ---
        profile_lines = "\n".join(data[target_profiles_key])
        requests.append({
            "deleteText": {"objectId": target_profiles_id, "textRange": {"type": "ALL"}}
        })
        requests.append({
            "insertText": {"objectId": target_profiles_id, "text": profile_lines}
        })
        requests.append({
            "createParagraphBullets": {
                "objectId": target_profiles_id,
                "textRange": {"type": "ALL"},
                "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE"
            }
        })

        if styles.get(target_profiles_key, {}).get("text_style"):
            requests.append({
                "updateTextStyle": {
                    "objectId": target_profiles_id,
                    "style": styles[target_profiles_key]["text_style"],
                    "textRange": {"type": "ALL"},
                    "fields": ",".join(styles[target_profiles_key]["text_style"].keys())
                }
            })
        if styles.get(target_profiles_key, {}).get("para_style"):
            requests.append({
                "updateParagraphStyle": {
                    "objectId": target_profiles_id,
                    "style": styles[target_profiles_key]["para_style"],
                    "textRange": {"type": "ALL"},
                    "fields": ",".join(styles[target_profiles_key]["para_style"].keys())
                }
            })

    # Execute batch request
    slides_service.presentations().batchUpdate(
        presentationId=presentation_id,
        body={"requests": requests}
    ).execute()


def update_persona_content(slides_service, presentation_id, slide_index, data):
    desired_count = 6
    for i in range(6):
        if data.get(f"persona_{i+1}_title", {}).strip() == "":
            desired_count = i
            break
    textbox_ids, styles = find_object_ids_by_alt_description(slides_service, presentation_id, slide_index)
    print(f"desired_count: {desired_count}")
    update_textboxes(slides_service, presentation_id, textbox_ids, styles, desired_count, data)

