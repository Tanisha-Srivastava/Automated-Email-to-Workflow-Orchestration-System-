from llm import llm
import json
import re

PROMPT = """
You must output ONLY valid JSON.
No explanations. No text.

Return execution dependencies as a JSON array.

Format:
[
  ["task_0", "task_1"],
  ["task_0", "task_2"]
]

Rules:
- Only include true dependencies
- Do NOT connect tasks that can run in parallel
- If no dependencies exist, return []

Actions:
{actions}
"""

def extract_first_json_array(text: str):
    matches = re.findall(r"\[[\s\S]*?\]", text)
    for m in matches:
        try:
            return json.loads(m)
        except json.JSONDecodeError:
            continue
    return []

def build_dag(tasks):
    edges = []

    def is_admin(text):
        return any(k in text.lower() for k in ["meeting", "schedule", "agreed to a follow-up"])

    assignees = {t["id"]: t["text"].split()[0] for t in tasks}

    for t in tasks:
        t_text = t["text"].lower()
        current_assignee = assignees[t["id"]].lower()

        # Rule 1: Single dependencies
        temporal_single = ["after", "once", "when", "following", "upon", "as soon as", "next"]
        if any(trigger in t_text for trigger in temporal_single):
            for other in tasks:
                if other["id"] == t["id"]:
                    continue
                if is_admin(other["text"]):
                    continue

                other_assignee = assignees[other["id"]].lower()

                # ✅ CRITICAL: Skip same assignee to avoid self-matching
                if other_assignee == current_assignee:
                    # BUT: allow one exception: if this is a COMM task mentioning "review"
                    # and the other is a REVIEW task by the same person
                    if ("review" in t_text and 
                        "review" in other["text"].lower() and
                        "client" in t_text):
                        # Allow: review task → client update by same person
                        pass
                    else:
                        continue

                if other_assignee in t_text:
                    edges.append({
                        "from": other["id"],
                        "to": t["id"],
                        "relation": "temporal_after"
                    })
                elif (other_assignee == current_assignee and 
                      "review" in other["text"].lower() and 
                      "review" in t_text):
                    # Fallback: if same person and both mention "review", link
                    edges.append({
                        "from": other["id"],
                        "to": t["id"],
                        "relation": "temporal_after"
                    })

        # Rule 2: Group dependencies
        group_triggers = [
            "after both", "once both", "when both",
            "after all", "once all", "when all",
            "after everything", "once everything", "when everything",
            "after all tasks", "once all tasks", "when all tasks",
            "after all of them", "once all of them", "when all of them",
            "conditional on"
        ]
        if any(trigger in t_text for trigger in group_triggers):
            for other in tasks:
                if other["id"] == t["id"]:
                    continue
                if is_admin(other["text"]):
                    continue
                other_assignee = assignees[other["id"]].lower()
                if other_assignee == current_assignee:
                    continue  # keep this for group deps
                edges.append({
                    "from": other["id"],
                    "to": t["id"],
                    "relation": "group_dependency"
                })

    # Deduplicate
    seen = set()
    final_edges = []
    for e in edges:
        key = (e["from"], e["to"])
        if key not in seen:
            seen.add(key)
            final_edges.append(e)

    return final_edges