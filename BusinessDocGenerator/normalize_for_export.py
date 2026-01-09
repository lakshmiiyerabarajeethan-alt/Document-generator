import base64
import os

def normalize_extension_steps(raw_steps, screenshot_base_path=None):
    """
    Convert raw extension JSON into dictionaries for DOCX/PDF export:
    - 'text': placeholder text (LLM will improve for user guide)
    - 'screenshot': Base64 of screenshot (optional)
    """
    normalized = []

    for step in raw_steps:
        text = ""
        screenshot = step.get("screenshot")

        # Convert screenshot file to Base64
        if screenshot and screenshot_base_path:
            full_path = os.path.join(screenshot_base_path, screenshot)
            if os.path.isfile(full_path):
                with open(full_path, "rb") as f:
                    img_bytes = f.read()
                screenshot = "data:image/png;base64," + base64.b64encode(img_bytes).decode("utf-8")
            else:
                screenshot = None
        else:
            screenshot = None

        action = step.get("action", "").lower()

        if action == "navigate":
            url = step.get("url", "")
            text = f"Navigate to {url}" if url else ""
        elif action == "click":
            t = step.get("text", "").strip()
            text = f"Click {t}" if t else ""
        elif action == "type":
            val = step.get("value", "")
            sel = step.get("selector", "")
            if "pass" in sel.lower():
                text = "Enter your password in the password field."
            elif "user" in sel.lower() or "email" in sel.lower():
                text = "Enter your username or email address."
            elif val:
                text = f"Enter '{val}' in field {sel}"
        else:
            text = ""

        if text:
            normalized.append({
                "text": text,
                "screenshot": screenshot
            })

    return normalized
