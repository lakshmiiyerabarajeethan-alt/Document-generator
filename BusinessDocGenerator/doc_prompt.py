import json


def build_business_doc_prompt(app_name, normalized_steps):
    """
    Build a prompt that generates structured user guide documentation
    following the exact format specified in requirements.
    """
    
    steps_json = json.dumps(normalized_steps, indent=2)

    return f"""You are a technical writer assistant that generates high-quality user guides. Follow the structure and format below exactly.

### INSTRUCTIONS
Write a user guide based on the recorded user actions provided below. The guide must be clear, step-by-step, and easy for non-technical users to follow.

### REQUIRED SECTIONS

1. **Title**
   - Write a clear descriptive title of the user guide based on the application name and the workflow captured.

2. **1. Purpose**
   - Explain in 1–2 sentences why this guide exists and what it helps the user accomplish.
   - Base this on the sequence of actions recorded.

3. **2. Scope**
   - Describe who can use this guide and in what situations.
   - Consider the application context and user permissions needed.

4. **3. Prerequisites**
   - List all things the user must have or know before starting (requirements, tools, permissions, etc.).
   - Format as bullet points.
   - Include: access credentials, browser requirements, necessary permissions, etc.

5. **4. Steps**
   - Break down the process into major steps based on the recorded workflow.
   - For each step:
     - Provide a Step heading (e.g., "Step 1: Navigate to the Login Page").
     - Provide ordered sub-steps that explain what the user should do.
     - Include details like field names, button labels, and expected outcomes.
     - Add screenshot labels where appropriate (e.g., "![Description](placeholder_image.jpg)").
     - Use clear, action-oriented language (Click, Enter, Select, Navigate, etc.).
   - Group related actions together logically (e.g., all login actions = one major step).

6. **5. Troubleshooting**
   - Create a table with common issues and solutions.
   - Include at least 3–5 rows based on the workflow.
   - Format as:
     | Issue | Solution |
     |-------|----------|
     | Problem description | Step-by-step solution |

7. **6. Tips (Optional)**
   - Provide practical tips, best practices, or warnings related to the task.
   - List as bullet points.
   - Include advice about data validation, security, performance, etc.

8. **7. Contact Support**
   - Provide information on where to get help if steps fail.
   - Include placeholders for support contact information.

### STYLE GUIDELINES
• Use simple and direct language.
• Use numbered steps for clarity.
• Keep each step concise but complete.
• Maintain consistent formatting with separators like "________________________________________" between major sections.
• Write in present tense and imperative mood (e.g., "Click the button", not "You should click the button").
• Explain not just WHAT to do, but also WHAT TO EXPECT after each action.
• For password fields or sensitive data, remind users about security practices.

### INPUT DATA

**Application Name:** {app_name}

**Recorded User Actions:**
{steps_json}

### ANALYSIS INSTRUCTIONS

Before writing the guide, analyze the recorded steps to identify:
1. **Workflow Type**: Is this a login flow? Upload process? Data entry? Navigation?
2. **Major Phases**: Group consecutive actions into logical phases (e.g., Authentication → Navigation → Data Entry → Submission).
3. **Key User Decisions**: Where does the user need to make choices or enter specific data?
4. **Success Indicators**: What confirms each step completed successfully?

### OUTPUT FORMAT

Generate the complete user guide following the exact structure above. Use markdown formatting with:
- Clear section headers with numbers (1. Purpose, 2. Scope, etc.)
- Proper indentation for sub-steps
- Screenshot placeholders where visual guidance would help
- Horizontal lines (________________________________________) between major sections

Begin writing the user guide now:"""


def build_enhanced_business_doc_prompt(app_name, normalized_steps, additional_context=None):
    """
    Enhanced version with optional additional context like:
    - User role information
    - Specific module/feature being documented
    - Known pain points or common errors
    """
    
    steps_json = json.dumps(normalized_steps, indent=2)
    
    context_section = ""
    if additional_context:
        context_section = f"""
### ADDITIONAL CONTEXT
{additional_context}
"""

    return f"""You are a technical writer assistant that generates high-quality user guides. Follow the structure and format below exactly.

### INSTRUCTIONS
Write a user guide based on the recorded user actions provided below. The guide must be clear, step-by-step, and easy for non-technical users to follow.

{context_section}

### REQUIRED SECTIONS

1. **Title**
   - Write a clear descriptive title of the user guide based on the application name and the workflow captured.

2. **1. Purpose**
   - Explain in 1–2 sentences why this guide exists and what it helps the user accomplish.
   - Base this on the sequence of actions recorded.

3. **2. Scope**
   - Describe who can use this guide and in what situations.
   - Consider the application context and user permissions needed.

4. **3. Prerequisites**
   - List all things the user must have or know before starting (requirements, tools, permissions, etc.).
   - Format as bullet points.
   - Include: access credentials, browser requirements, necessary permissions, etc.

5. **4. Steps**
   - Break down the process into major steps based on the recorded workflow.
   - For each step:
     - Provide a Step heading (e.g., "Step 1: Navigate to the Login Page").
     - Provide ordered sub-steps that explain what the user should do.
     - Include details like field names, button labels, and expected outcomes.
     - Add screenshot labels where appropriate (e.g., "![Description](placeholder_image.jpg)").
     - Use clear, action-oriented language (Click, Enter, Select, Navigate, etc.).
   - Group related actions together logically (e.g., all login actions = one major step).

6. **5. Troubleshooting**
   - Create a table with common issues and solutions.
   - Include at least 3–5 rows based on the workflow.
   - Format as markdown table:
   
   | Issue | Solution |
   |-------|----------|
   | Problem description | Step-by-step solution |

7. **6. Tips (Optional)**
   - Provide practical tips, best practices, or warnings related to the task.
   - List as bullet points.
   - Include advice about data validation, security, performance, etc.

8. **7. Contact Support**
   - Provide information on where to get help if steps fail.
   - Include placeholders for support contact information.

### STYLE GUIDELINES
• Use simple and direct language.
• Use numbered steps for clarity.
• Keep each step concise but complete.
• Maintain consistent formatting with separators like "________________________________________" between major sections.
• Write in present tense and imperative mood (e.g., "Click the button", not "You should click the button").
• Explain not just WHAT to do, but also WHAT TO EXPECT after each action.
• For password fields or sensitive data, remind users about security practices.

### INPUT DATA

**Application Name:** {app_name}

**Recorded User Actions:**
{steps_json}

### ANALYSIS INSTRUCTIONS

Before writing the guide, analyze the recorded steps to identify:
1. **Workflow Type**: Is this a login flow? Upload process? Data entry? Navigation?
2. **Major Phases**: Group consecutive actions into logical phases (e.g., Authentication → Navigation → Data Entry → Submission).
3. **Key User Decisions**: Where does the user need to make choices or enter specific data?
4. **Success Indicators**: What confirms each step completed successfully?

### OUTPUT FORMAT

Generate the complete user guide following the exact structure above. Use markdown formatting with:
- Clear section headers with numbers (1. Purpose, 2. Scope, etc.)
- Proper indentation for sub-steps
- Screenshot placeholders where visual guidance would help
- Horizontal lines (________________________________________) between major sections

Begin writing the user guide now:"""