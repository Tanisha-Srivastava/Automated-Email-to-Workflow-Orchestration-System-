from llm import llm
import json
import re


ROLE_PROMPT = """
Return ONLY valid JSON.
No explanations. No markdown. No extra text.

You are assigning a SEMANTIC ROLE to each action item.

The PERSON NAME in the action text is the owner.
Your task is to label the TYPE OF WORK being performed,
based strictly on WHAT the task does.

Allowed roles:
- UX Designer
- Frontend Engineer
- Backend Engineer
- QA Lead
- Project Manager

ROLE DEFINITIONS AND KEYWORDS:

UX Designer:
Tasks involving user experience or visual design, including:
- redesign, design options, wireframes, mockups
- layout, navigation, usability, user flow
- dashboards, screens, interaction design
- information architecture, visual clarity

Frontend Engineer:
Tasks involving client-side implementation, including:
- frontend, UI, components
- responsiveness, styling, CSS
- rendering, views, React/Vue/Angular
- fixing layout issues in code

Backend Engineer:
Tasks involving server-side or data logic, including:
- backend, API, endpoints
- databases, schemas, queries
- services, authentication, integrations
- business logic, server processing

QA Lead:
Tasks involving validation or testing, including:
- testing, test cases
- verification, validation
- bug fixing, regression checks
- quality assurance, review for defects

Project Manager:
Coordination-only tasks, including:
- reviewing work
- updating or communicating with clients
- scheduling or organizing meetings
- tracking progress or alignment
- approvals and sign-offs

ROLE PRECEDENCE RULES (CRITICAL):
- If a task involves DESIGN work, it MUST be UX Designer.
- If a task involves FRONTEND implementation, it MUST be Frontend Engineer.
- If a task involves BACKEND logic, it MUST be Backend Engineer.
- If a task involves TESTING or VERIFICATION, it MUST be QA Lead.
- Project Manager is ONLY valid when the task is purely
  coordination, communication, review, or scheduling.
- Do NOT assign Project Manager to execution or implementation work.

IMPORTANT CONSTRAINTS:
- Do NOT infer roles from deadlines, ordering, or dependency words
  such as "after", "once", "before".
- Words like "prepare", "by Friday", "options", or "once ready"
  do NOT imply Project Manager by themselves.
- Choose the role based on WHAT work is being done,
  not WHO is doing it or how it is scheduled.

OUTPUT FORMAT (JSON ONLY):
[
  {{
    "action": "<exact action text>",
    "assignee": "<one of the allowed roles>"
  }}
]

Actions:
{actions}
"""


def assign_roles(actions):
    response = llm.invoke(
        ROLE_PROMPT.format(actions=[a["text"] for a in actions])
    )

    print("🧠 RAW ROLE LLM OUTPUT:\n", response)

    # ---- SANITIZE RESPONSE ----
    # Remove lines that clearly don't belong to role JSON
    cleaned_lines = []
    for line in response.splitlines():
        line_strip = line.strip()

        # Drop stray confidence values or leaked strings
        if re.match(r"^[0-9.]+\s*,", line_strip):
            continue
        if line_strip.startswith("'") or line_strip.startswith('"') and "confidence" in line_strip:
            continue

        cleaned_lines.append(line)

    cleaned_response = "\n".join(cleaned_lines).strip()

    # ---- TRY PARSING CLEANED JSON ----
    try:
        return json.loads(cleaned_response)
    except json.JSONDecodeError:
        pass

    # ---- FALLBACK: EXTRACT JSON ARRAY ----
    match = re.search(r"\[\s*\{.*?\}\s*\]", cleaned_response, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # ---- FINAL SAFE FALLBACK ----
    print("⚠️ Role parsing failed. Falling back to Project Manager.")
    return [
        {"action": a["text"], "assignee": "Project Manager"}
        for a in actions
    ]
