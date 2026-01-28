from name_extractor import extract_names

with open("data/trans4.txt") as f:
    lines = [l.strip() for l in f if l.strip()]

names = extract_names(lines)
print("👥 Detected participants:", names)

import json, os
from action_extractor import extract_actions
from role_assigner import assign_roles
from dag_builder import build_dag
from email_sender import send_email
from slack_confirm import ask_confirmation
import glob


# ---------- Load transcript ----------
with open("data/trans4.txt") as f:
    lines = [l.strip() for l in f if l.strip()]

actions = extract_actions(lines)
roles = assign_roles(actions)

tasks = []
for i, (a, r) in enumerate(zip(actions, roles)):
    tasks.append({
        "id": f"task_{i}",
        "text": a["text"],
        "role": r["assignee"],
        "confidence": a["confidence"]
    })

edges = build_dag(tasks)

with open("output/workflow.json", "w") as f:
    json.dump({
        "tasks": tasks,
        "edges": edges
    }, f, indent=2)


# ---------- Load participants from Downloads ----------


downloads = os.path.join(os.path.expanduser("~"), "Downloads")

files = glob.glob(os.path.join(downloads, "participants*.json"))
if not files:
    raise FileNotFoundError("No participants.json found in Downloads")

# Pick the most recently modified file
participants_path = max(files, key=os.path.getmtime)

with open(participants_path) as f:
    participants = json.load(f)

print(f"✅ Using participants file: {os.path.basename(participants_path)}")


# ---------- Resolve owners ----------
def resolve_owners(task):
    text = task["text"].lower()
    owners = []

    # 1️⃣ Name-based matching (supports multiple people)
    for p in participants:
        if p["name"].lower() in text:
            owners.append(p)

    # 2️⃣ Role-based fallback ONLY if no names matched
    if not owners:
        for p in participants:
            if p["role"] == task["role"]:
                owners.append(p)

    return owners


# ---------- Group tasks by person ----------
tasks_by_person = {}

for t in tasks:
    owners = resolve_owners(t)
    if not owners:
        continue

    for owner in owners:
        tasks_by_person.setdefault(owner["email"], {
            "name": owner["name"],
            "email": owner["email"],
            "tasks": []
        })["tasks"].append(t)


# ---------- Email + confirmation logic ----------
for person in tasks_by_person.values():
    high = [t for t in person["tasks"] if t["confidence"] >= 0.75]
    medium = [t for t in person["tasks"] if 0.5 <= t["confidence"] < 0.75]
    low = [t for t in person["tasks"] if t["confidence"] < 0.5]

    if high or medium:
        body = [
            f"Hi {person['name']},",
            "",
            "From today’s meeting, here are your action items:",
            ""
        ]

        for t in high:
            body.append(f"• {t['text']}")

        for t in medium:
            body.append(f"• {t['text']} (tentative)")

        body.extend([
            "",
            "Please reply if anything looks incorrect."
        ])

        send_email(
            person["email"],
            "Your action items from today’s meeting",
            "\n".join(body)
        )

    for t in medium+low:
        ask_confirmation(t, person)


# ---------- Save workflow ----------
with open("output/workflow.json", "w") as f:
    json.dump({"tasks": tasks, "edges": edges}, f, indent=2)

print("✅ Workflow generated and emails processed")
