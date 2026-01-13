from urllib.parse import urlparse
from typing import List, Dict, Any

AUTH_KEYWORDS = [
    "openid-connect",
    "protocol",
    "auth",
    "token",
    "realm",
    "oauth",
    "saml",
    "sso"
]

UPLOAD_KEYWORDS = [
    "upload",
    "file",
    "select",
    "choose",
    "browse"
]

LOGIN_KEYWORDS = [
    "login",
    "signin",
    "sign-in",
    "log-in"
]

LOGOUT_KEYWORDS = [
    "logout",
    "signout",
    "sign-out",
    "log-out"
]


def is_auth_redirect(url: str):
    """Check if URL is an authentication redirect."""
    return any(k in url.lower() for k in AUTH_KEYWORDS)


def simplify_url(url: str):
    """Simplify URL by removing query parameters and fragments."""
    try:
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    except Exception:
        return url


def detect_workflow_phase(normalized_steps: List[Dict]) -> str:
    """
    Detect the type of workflow based on action patterns.
    Returns: 'login', 'upload', 'data_entry', 'navigation', 'logout', 'mixed'
    """
    has_password = any(step.get("field") == "Password field" for step in normalized_steps if step.get("type") == "input")
    has_username = any(step.get("field") == "Username field" for step in normalized_steps if step.get("type") == "input")
    has_login_click = any("login" in step.get("label", "").lower() for step in normalized_steps if step.get("type") == "click")
    has_logout_click = any("logout" in step.get("label", "").lower() for step in normalized_steps if step.get("type") == "click")
    has_upload = any("upload" in step.get("label", "").lower() or "file" in step.get("label", "").lower() 
                     for step in normalized_steps if step.get("type") == "click")
    
    if has_logout_click:
        return "logout"
    
    if has_password and has_username and has_login_click:
        return "login"
    
    if has_upload:
        return "upload"
    
    input_count = sum(1 for step in normalized_steps if step.get("type") == "input")
    if input_count > 3:
        return "data_entry"
    
    nav_count = sum(1 for step in normalized_steps if step.get("type") == "navigation")
    if nav_count > 2:
        return "navigation"
    
    return "mixed"


def group_into_logical_steps(normalized_steps: List[Dict]) -> List[Dict]:
    """
    Group normalized steps into logical workflow phases.
    Each group represents a major step in the user guide.
    """
    if not normalized_steps:
        return []
    
    logical_groups = []
    current_group = {
        "phase": "Unknown",
        "actions": [],
        "description": ""
    }
    
    for i, step in enumerate(normalized_steps):
        step_type = step.get("type")
        
        # Detect phase transitions
        if step_type == "navigation":
            # Start new group for navigation
            if current_group["actions"]:
                logical_groups.append(current_group)
            
            current_group = {
                "phase": "Navigation",
                "actions": [step],
                "description": f"Navigate to {step.get('url', 'page')}"
            }
        
        elif step_type == "input":
            field = step.get("field", "")
            
            # Check if this is part of login
            if "Username" in field or "Password" in field:
                if current_group["phase"] != "Login":
                    if current_group["actions"]:
                        logical_groups.append(current_group)
                    current_group = {
                        "phase": "Login",
                        "actions": [step],
                        "description": "Enter login credentials"
                    }
                else:
                    current_group["actions"].append(step)
            else:
                # Generic data entry
                if current_group["phase"] not in ["Data Entry", "Form Filling"]:
                    if current_group["actions"]:
                        logical_groups.append(current_group)
                    current_group = {
                        "phase": "Data Entry",
                        "actions": [step],
                        "description": "Enter information"
                    }
                else:
                    current_group["actions"].append(step)
        
        elif step_type == "click":
            label = step.get("label", "").lower()
            text = step.get("text", "").lower()
            
            # Login button click
            if "login" in label or "login" in text:
                current_group["actions"].append(step)
                current_group["phase"] = "Login"
                logical_groups.append(current_group)
                current_group = {"phase": "Unknown", "actions": [], "description": ""}
            
            # Logout button click
            elif "logout" in label or "logout" in text:
                if current_group["actions"]:
                    logical_groups.append(current_group)
                logical_groups.append({
                    "phase": "Logout",
                    "actions": [step],
                    "description": "Log out of the application"
                })
                current_group = {"phase": "Unknown", "actions": [], "description": ""}
            
            # Upload/file related
            elif any(kw in label or kw in text for kw in ["upload", "file", "select", "browse", "submit"]):
                if current_group["phase"] != "Upload":
                    if current_group["actions"]:
                        logical_groups.append(current_group)
                    current_group = {
                        "phase": "Upload",
                        "actions": [step],
                        "description": "Upload files or submit data"
                    }
                else:
                    current_group["actions"].append(step)
            
            # Generic button click
            else:
                if current_group["phase"] in ["Unknown", "Button Click"]:
                    current_group["actions"].append(step)
                    current_group["phase"] = "Button Click"
                else:
                    current_group["actions"].append(step)
    
    # Add final group
    if current_group["actions"]:
        logical_groups.append(current_group)
    
    return logical_groups


def normalize_steps(raw_steps: List[Dict]) -> List[Dict]:
    """
    Convert technical browser recording into semantic actions
    suitable for business documentation.
    """
    normalized = []
    last_url = None

    for step in raw_steps:
        action = step.get("action", "")

        # ----------------------------------
        # NAVIGATION EVENTS
        # ----------------------------------
        if action == "navigate":
            url = step.get("url", "")

            # Ignore login redirects / OIDC calls
            if is_auth_redirect(url):
                continue

            simple = simplify_url(url)

            # Remove duplicate redirects
            if simple == last_url:
                continue

            last_url = simple

            normalized.append({
                "type": "navigation",
                "label": "Navigate to page",
                "url": simple,
                "source_step": step.get("id")
            })

        # ----------------------------------
        # INPUT EVENTS
        # ----------------------------------
        elif action == "type":
            field_name = "Input field"
            selector = (step.get("selector") or "").lower()
            placeholder = (step.get("placeholder") or "").lower()

            # Detect username fields
            if any(kw in selector or kw in placeholder for kw in ["user", "email", "username"]):
                field_name = "Username field"

            # Detect password fields
            if any(kw in selector or kw in placeholder for kw in ["pass", "password", "pwd"]):
                field_name = "Password field"
            
            # Detect other common fields
            elif "name" in selector or "name" in placeholder:
                field_name = "Name field"
            elif "description" in selector or "description" in placeholder:
                field_name = "Description field"
            elif "tag" in selector or "tag" in placeholder:
                field_name = "Tag field"
            elif "search" in selector or "search" in placeholder:
                field_name = "Search field"

            normalized.append({
                "type": "input",
                "field": field_name,
                "masked": "Password" in field_name,
                "value": None if "Password" in field_name else step.get("value"),
                "placeholder": step.get("placeholder", ""),
                "source_step": step.get("id")
            })

        # ----------------------------------
        # CLICK EVENTS
        # ----------------------------------
        elif action == "click":
            text = (step.get("text") or "").strip()
            label = "Click button"

            text_lower = text.lower()

            # Login button
            if any(kw in text_lower for kw in LOGIN_KEYWORDS):
                label = "Click Login button"
            
            # Logout button
            elif any(kw in text_lower for kw in LOGOUT_KEYWORDS):
                label = "Click Logout button"
            
            # Upload/File buttons
            elif any(kw in text_lower for kw in UPLOAD_KEYWORDS):
                label = f"Click '{text}' button"
            
            # Submit button
            elif "submit" in text_lower:
                label = "Click Submit button"
            
            # Save button
            elif "save" in text_lower:
                label = "Click Save button"
            
            # Cancel/Close
            elif "cancel" in text_lower or "close" in text_lower:
                label = f"Click '{text}' button"
            
            # Generic button with text
            elif text:
                label = f"Click '{text}' button"

            normalized.append({
                "type": "click",
                "label": label,
                "text": text,
                "source_step": step.get("id")
            })

    return normalized


def normalize_steps_with_grouping(raw_steps: List[Dict]) -> Dict[str, Any]:
    """
    Enhanced normalization that includes workflow analysis and logical grouping.
    Returns both normalized steps and grouped steps for better documentation.
    """
    normalized = normalize_steps(raw_steps)
    workflow_type = detect_workflow_phase(normalized)
    logical_groups = group_into_logical_steps(normalized)
    
    return {
        "normalized_steps": normalized,
        "workflow_type": workflow_type,
        "logical_groups": logical_groups,
        "total_steps": len(normalized),
        "step_counts": {
            "navigation": sum(1 for s in normalized if s.get("type") == "navigation"),
            "input": sum(1 for s in normalized if s.get("type") == "input"),
            "click": sum(1 for s in normalized if s.get("type") == "click")
        }
    }