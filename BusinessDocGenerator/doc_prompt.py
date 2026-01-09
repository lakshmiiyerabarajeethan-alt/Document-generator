import json

def build_business_doc_prompt(app_name, normalized_steps):
    """
    Prompt the LLM to create a full user guide in the exact format you expect.
    """
    steps_json = json.dumps(normalized_steps, indent=2)

    return f"""
You are a technical writer assistant that generates high-quality user guides. Follow the structure and format exactly.

### INSTRUCTIONS
Write a user guide based on the recorded steps provided. The guide must be clear, step-by-step, and easy for non-technical users to follow.

Include screenshots where available using labels like:
**Screenshot label (if available):** <description of the step or page>

### REQUIRED SECTIONS
1. **Title**
2. **1. Purpose**
3. **2. Scope**
4. **3. Prerequisites**
5. **4. Steps** (include screenshots labels)
6. **5. Troubleshooting**
7. **6. Tips (Optional)**
8. **7. Contact Support**

### STYLE GUIDELINES
- Use simple and direct language.
- Number steps for clarity.
- Include screenshot labels.
- Maintain consistent formatting with separators like "________________________________________"

Application: {app_name}

Normalized Steps (with screenshot info):
{steps_json}
"""
