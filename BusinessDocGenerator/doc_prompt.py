import json


def build_business_doc_prompt(app_name: str, normalized_steps: list) -> str:
    """
    Build a prompt describing the recorded workflow.

    The LLM's SYSTEM_PROMPT (in llm_client.py) already instructs the model
    to return structured JSON with: title, purpose, steps[], and help_section.
    This function only supplies the WHAT — not the formatting rules.

    Args:
        app_name (str): Name of the application being documented
        normalized_steps (list): Normalized step dicts from normalizer.py

    Returns:
        str: Prompt text to pass to call_llm()
    """
    steps_json = json.dumps(normalized_steps, indent=2)

    return f"""Generate a step-by-step user guide for the following recorded workflow.

**Application:** {app_name}

**Recorded User Actions:**
{steps_json}

Using these actions, produce a clear user guide that:
- Groups related actions into logical steps (e.g. login, navigation, upload, logout)
- Names each step clearly (e.g. "Step 1: Sign In to Your Account")
- Writes 2-5 concise bullet instructions per step using action-oriented language
  (Click, Enter, Select, Navigate)
- Bolds key UI element names in instructions using **double asterisks**
  (e.g. "Click the **Upload** button")
- Writes a purpose sentence explaining what this workflow accomplishes
- Ends with a help_section inviting users to contact support if needed
"""


def build_enhanced_business_doc_prompt(
    app_name: str,
    normalized_steps: list,
    additional_context: str | None = None
) -> str:
    """
    Enhanced version that accepts optional additional context such as:
    - User role information
    - Specific module/feature being documented
    - Known pain points or common errors

    Args:
        app_name (str): Name of the application being documented
        normalized_steps (list): Normalized step dicts from normalizer.py
        additional_context (str | None): Optional extra context for the guide

    Returns:
        str: Prompt text to pass to call_llm()
    """
    steps_json = json.dumps(normalized_steps, indent=2)

    context_section = (
        f"\n**Additional Context:**\n{additional_context}\n"
        if additional_context
        else ""
    )

    return f"""Generate a step-by-step user guide for the following recorded workflow.

**Application:** {app_name}
{context_section}
**Recorded User Actions:**
{steps_json}

Using these actions, produce a clear user guide that:
- Groups related actions into logical steps (e.g. login, navigation, upload, logout)
- Names each step clearly (e.g. "Step 1: Sign In to Your Account")
- Writes 2-5 concise bullet instructions per step using action-oriented language
  (Click, Enter, Select, Navigate)
- Bolds key UI element names in instructions using **double asterisks**
  (e.g. "Click the **Upload** button")
- Writes a purpose sentence explaining what this workflow accomplishes
- Ends with a help_section inviting users to contact support if needed
"""
