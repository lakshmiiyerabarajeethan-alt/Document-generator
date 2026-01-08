import json


def build_business_doc_prompt(app_name, normalized_steps):

    steps_json = json.dumps(normalized_steps, indent=2)

    return f"""
You are a Senior QA Analyst creating a BUSINESS LEVEL functional test case.

The input is a normalized set of UI actions recorded from a browser session.

Convert these actions into a formal Business Test Case Document.

Follow these rules:

- Use functional business language
- Do not expose CSS selectors or technical details
- Group redirects into meaningful actions
- Treat Login and Logout as major steps
- Mask password values
- Every step MUST have an Expected Result
- Keep steps concise and clear
- Use present tense
- Preserve traceability to source_step ids

Output format MUST be:

Test Name
Business Goal
Application
Preconditions

Test Steps (numbered)
  - Functional Description
  - Expected Result

Postconditions

Traceability Mapping
(table mapping functional step -> source_step ids)

Application: {app_name}

Normalized Steps:
{steps_json}
"""
