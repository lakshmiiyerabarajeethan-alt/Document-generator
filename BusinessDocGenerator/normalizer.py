from urllib.parse import urlparse

AUTH_KEYWORDS = [
    "openid-connect",
    "protocol",
    "auth",
    "token",
    "realm",
]


def is_auth_redirect(url: str):
    return any(k in url.lower() for k in AUTH_KEYWORDS)


def simplify_url(url):
    try:
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    except Exception:
        return url


def normalize_steps(raw_steps):
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

            # ignore login redirects / OIDC calls
            if is_auth_redirect(url):
                continue

            simple = simplify_url(url)

            # remove duplicate redirects
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

            if "user" in selector:
                field_name = "Username field"

            if "pass" in selector:
                field_name = "Password field"

            normalized.append({
                "type": "input",
                "field": field_name,
                "masked": "Password" in field_name,
                "value": None if "Password" in field_name else step.get("value"),
                "source_step": step.get("id")
            })

        # ----------------------------------
        # CLICK EVENTS
        # ----------------------------------
        elif action == "click":

            text = (step.get("text") or "").strip()
            label = "Click button"

            if text.lower() == "login":
                label = "Click Login button"

            elif "logout" in text.lower():
                label = "Click Logout button"

            normalized.append({
                "type": "click",
                "label": label,
                "text": text,
                "source_step": step.get("id")
            })

    return normalized
