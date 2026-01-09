from urllib.parse import urlparse

AUTH_KEYWORDS = [
    "openid-connect",
    "protocol",
    "auth",
    "token",
    "realm",
]


def is_auth_redirect(url: str) -> bool:
    return any(k in url.lower() for k in AUTH_KEYWORDS)


def simplify_url(url: str) -> str:
    try:
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    except Exception:
        return url


def normalize_steps(raw_steps):
    """
    Convert browser recordings into plain,
    user-action instructions suitable for
    a customer-facing user guide.
    """

    normalized = []
    last_url = None

    for step in raw_steps:
        if not isinstance(step, dict):
            continue

        action = step.get("action", "").lower()

        # ----------------------------
        # NAVIGATION
        # ----------------------------
        if action == "navigate":
            url = step.get("url", "")

            if is_auth_redirect(url):
                continue

            simple = simplify_url(url)

            if simple == last_url:
                continue

            last_url = simple

            normalized.append(
                f"Navigate to the page at {simple}."
            )

        # ----------------------------
        # INPUT
        # ----------------------------
        elif action == "type":
            selector = (step.get("selector") or "").lower()

            if "pass" in selector:
                normalized.append(
                    "Enter your password in the password field."
                )
            elif "user" in selector or "email" in selector:
                normalized.append(
                    "Enter your username or email address in the username field."
                )
            else:
                normalized.append(
                    "Enter the required information in the input field."
                )

        # ----------------------------
        # CLICK
        # ----------------------------
        elif action == "click":
            text = (step.get("text") or "").strip()

            if text.lower() == "login":
                normalized.append(
                    "Click the Login button to sign in."
                )
            elif "logout" in text.lower():
                normalized.append(
                    "Click the Logout option to sign out."
                )
            elif text:
                normalized.append(
                    f"Click {text} to continue."
                )
            else:
                normalized.append(
                    "Click the highlighted button to proceed."
                )

    return normalized
