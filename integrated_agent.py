
# ===========================================================
# INTEGRATED GMAIL + SLACK + CALENDAR + JIRA AGENT (FINAL FIXED)
# ===========================================================

import os, base64, email, json, re, pickle, requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from jira import JIRA
from slack_sdk import WebClient
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

# ===========================================================
# CONFIG
# ===========================================================
load_dotenv()

MODEL = "llama3.2:1b"
PHI3_ENDPOINT = "http://localhost:11434/api/generate"

GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar"]

GMAIL_TOKEN = "token.pickle"
CALENDAR_TOKEN = "token_calendar.pickle"

MAX_EMAIL_CHARS = 2000
START_DATE_FIELD = "customfield_10015"

SLACK_CHANNEL_ID = "C0A9HAUMWRF"
slack_client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))

# ===========================================================
# LLM
# ===========================================================
import subprocess

import subprocess

import requests
import time
'''def phi3(prompt, temperature=0.2, retries=3, delay=3):
    """
    Calls Ollama API to generate a response.
    Retries up to `retries` times if it fails.
    """
    for attempt in range(1, retries + 1):
        try:
            r = requests.post(PHI3_ENDPOINT, json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": temperature}
            }, timeout=60)  # 60s timeout
            r.raise_for_status()
            return r.json()["response"]
        except requests.exceptions.RequestException as e:
            print(f"❌ Ollama request failed (attempt {attempt}/{retries}): {e}")
            if attempt < retries:
                print(f"⏳ Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                print("⚠️ Ollama request failed after all retries, returning empty string.")
                return ""
'''
def phi3(prompt, temperature=0.2):
    r = requests.post(
        PHI3_ENDPOINT,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_ctx": 2048,     # 🔴 VERY IMPORTANT
                "num_predict": 300   # 🔴 prevents long generations
            }
        },
        timeout=120  # give CPU some breathing room
    )
    r.raise_for_status()
    return r.json()["response"]



def clean_json(text):
    text = re.sub(r"```json|```", "", text)
    return json.loads(re.search(r"\{.*\}", text, re.S).group())

# ===========================================================
# DATE EXTRACTION
# ===========================================================
def extract_due_date(text):
    today = datetime.today()
    text_lower = text.lower()

    if "today" in text_lower:
        return today.strftime("%Y-%m-%d")
    if "tomorrow" in text_lower:
        return (today + timedelta(days=1)).strftime("%Y-%m-%d")

    match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", text)
    if match:
        return match.group(1)

    match = re.search(r"(?:by|before|due on)\s+(\d{1,2})\s+([A-Za-z]+)", text, re.I)
    if match:
        day = int(match.group(1))
        month = match.group(2)[:3].title()
        date = datetime.strptime(f"{day} {month}", "%d %b").replace(year=today.year)
        if date < today:
            date = date.replace(year=today.year + 1)
        return date.strftime("%Y-%m-%d")

    weekdays = {
        "monday":0,"tuesday":1,"wednesday":2,"thursday":3,
        "friday":4,"saturday":5,"sunday":6
    }

    match = re.search(r"(this|next)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)", text_lower)
    if match:
        which, day = match.groups()
        days = (weekdays[day] - today.weekday()) % 7
        if which == "next":
            days += 7
        return (today + timedelta(days=days)).strftime("%Y-%m-%d")

    return None

import re
from datetime import datetime, timedelta

from dateutil import parser

from dateutil import parser
import pytz
from datetime import datetime
import re

from datetime import datetime, timedelta
import pytz
import re

IST = pytz.timezone("Asia/Kolkata")

def extract_due_datetime(text):
    """
    Extracts date + time from email.
    Returns timezone-aware datetime in IST.
    """
    IST = pytz.timezone("Asia/Kolkata")

    # 1️⃣ Try explicit Date + Time fields
    date_match = re.search(
        r"Date:\s*(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)?,?\s*([A-Za-z]+)\s+(\d{1,2}),\s*(\d{4})",
        text,
        re.I
    )
    time_match = re.search(
        r"Time:\s*(\d{1,2}:\d{2})\s*(AM|PM)",
        text,
        re.I
    )

    if date_match and time_match:
        month, day, year = date_match.groups()
        time_str, meridiem = time_match.groups()

        dt_str = f"{month} {day} {year} {time_str} {meridiem}"
        dt = datetime.strptime(dt_str, "%B %d %Y %I:%M %p")
        return IST.localize(dt)

    # 2️⃣ Fallback: natural language parsing
    try:
        dt = parser.parse(text, fuzzy=True)
        if dt.tzinfo is None:
            dt = IST.localize(dt)
        return dt.astimezone(IST)
    except Exception:
        pass

    # 3️⃣ Absolute fallback
    print("⚠️ Could not find date in email, defaulting to today 9 AM")
    return datetime.now(IST).replace(hour=9, minute=0, second=0, microsecond=0)




# ===========================================================
# EMAIL
# ===========================================================
def read_latest_email():
    creds = None
    if os.path.exists(GMAIL_TOKEN):
        creds = pickle.load(open(GMAIL_TOKEN, "rb"))

    if not creds or not creds.valid:
        if creds and creds.expired:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", GMAIL_SCOPES)
            creds = flow.run_local_server(port=8080)
        pickle.dump(creds, open(GMAIL_TOKEN, "wb"))

    service = build("gmail", "v1", credentials=creds)
    msg_id = service.users().messages().list(userId="me", maxResults=1).execute()["messages"][0]["id"]
    raw = service.users().messages().get(userId="me", id=msg_id, format="raw").execute()
    msg = email.message_from_bytes(base64.urlsafe_b64decode(raw["raw"]))

    body = ""
    for part in msg.walk():
        if part.get_content_type() == "text/plain":
            body += part.get_payload(decode=True).decode(errors="ignore")

    sender = email.utils.parseaddr(msg["From"])[1]
    assignees = [a for _, a in email.utils.getaddresses(msg.get_all("To", []) + msg.get_all("Cc", []))]
    return body[:MAX_EMAIL_CHARS], sender, assignees

# ===========================================================
# INTENT
# ===========================================================
def is_post_meeting_action_email(text):
    """
    Detects emails that reference a meeting in the past
    and are clearly about action items, not scheduling.
    """
    text_lower = text.lower().strip()

    # Strong start-line patterns
    start_patterns = [
        "from today’s meeting",
        "from today's meeting",
        "following today's meeting",
        "after today's meeting",
        "summary of today's meeting",
        "meeting recap",
        "meeting summary",
        "action items from",
        "action items from today's meeting",
        "notes from today's meeting"
    ]

    # If email starts with any of these → bypass calendar
    for pattern in start_patterns:
        if text_lower.startswith(pattern):
            return True

    # Broader indicators anywhere in mail
    post_meeting_phrases = [
        "action items",
        "next steps",
        "deliverables",
        "tasks assigned",
        "please complete the following",
        "assigned to",
        "ownership"
    ]

    if "meeting" in text_lower and any(p in text_lower for p in post_meeting_phrases):
        return True

    return False


def classify_intent(text):
    # 🔹 Bypass calendar for post-meeting action emails
    if is_post_meeting_action_email(text):
        return "jira_task"

    # 🔹 Ask LLM first
    r = phi3(f"""
Return ONLY one word from the following:
jira_task
slack_notification
calendar_event
none

EMAIL:
{text}
""", 0)

    r_clean = r.lower().strip()
    print(f"🧠 Raw intent output from LLM: '{r_clean}'")

    # Step 1: Trust Jira if LLM says Jira
    if "jira_task" in r_clean:
        print("🧠 Intent detected: jira_task")
        return "jira_task"
    if r_clean == "none":
        return "slack_notification"

    # Step 2: Calendar detection (ONLY future-oriented)
    calendar_keywords = [
        "schedule", "scheduled for", "invite you to",
        "join link", "zoom link", "google meet",
        "teams meeting", "calendar invite"
    ]

    time_indicators = [
        "at ", "on ", "tomorrow", "next", "ist"
    ]

    text_lower = text.lower()

    if (
        any(kw in text_lower for kw in calendar_keywords)
        and any(t in text_lower for t in time_indicators)
    ):
        print("🧠 Intent detected: calendar_event")
        return "calendar_event"

    # Step 3: Default to Slack FYI
    print("🧠 Intent detected: slack_notification")
    return "slack_notification"



# ===========================================================
# SLACK
# ===========================================================
def send_slack(text):
    summary = phi3(f"Summarize this email in 2-3 lines:\n{text}", temperature=0.2)
    slack_client.chat_postMessage(
        channel=SLACK_CHANNEL_ID,
        text=f"📩 *FYI Email Summary*\n{summary}"
    )
    print("✅ Slack sent (summarised)")


# ===========================================================
# CALENDAR
# ===========================================================
# ===========================================================
# CALENDAR FIXED LOGIC
# ===========================================================
from datetime import timezone, timedelta
import pytz  # pip install pytz
IST = pytz.timezone("Asia/Kolkata")
today = datetime.now(IST)
def calendar_service():
    creds = pickle.load(open(CALENDAR_TOKEN, "rb")) if os.path.exists(CALENDAR_TOKEN) else None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", CALENDAR_SCOPES)
            creds = flow.run_local_server(port=8080)
        pickle.dump(creds, open(CALENDAR_TOKEN, "wb"))

    return build("calendar", "v3", credentials=creds)

def create_calendar_event(summary, due_datetime):
    """
    Creates a Google Calendar event.
    Adjusts +10:30 offset manually for IST.
    """
    svc = calendar_service()
    IST = pytz.timezone("Asia/Kolkata")

    # If naive, assume IST
    if due_datetime.tzinfo is None:
        due_datetime = IST.localize(due_datetime)
    else:
        due_datetime = due_datetime.astimezone(IST)

    # ⚠️ ADD +10:30 HOURS manually
    due_datetime += timedelta(hours=13, minutes=30)

    # Convert to UTC for Calendar API
    start_utc = due_datetime.astimezone(pytz.UTC)
    end_utc = (due_datetime + timedelta(hours=1)).astimezone(pytz.UTC)

    event = {
        "summary": summary,
        "start": {"dateTime": start_utc.isoformat(), "timeZone": "Asia/Kolkata"},
        "end": {"dateTime": end_utc.isoformat(), "timeZone": "Asia/Kolkata"},
        "reminders": {"useDefault": True}
    }

    svc.events().insert(calendarId="primary", body=event).execute()
    print(f"✅ Calendar event '{summary}' created at {due_datetime.isoformat()} (IST)")


# ===========================================================
# JIRA
# ===========================================================
# ===========================================================
# TEXT NORMALIZATION
# ===========================================================
def normalize_text(text):
    """
    Remove markdown bold/italic and extra whitespace from text
    to prevent Jira formatting issues.
    """
    if not text:
        return ""
    # remove bold/italic markers and strip whitespace
    text = text.replace("*", "").replace("_", "").strip()
    return text
def extract_json_array(text):
    """
    Safely extract the first JSON array from LLM response.
    Removes code fences and extra text around JSON.
    """
    # Remove ```json or ``` markers
    text = re.sub(r"```json|```", "", text)
    # Match the first JSON array in the text
    match = re.search(r"\[\s*{.*}\s*\]", text, re.S)
    if match:
        return match.group()
    return "[]"
# ===========================================================
def generate_task_from_email(email_text):
    """
    Converts an email into one or more Jira tasks using the LLM.
    Returns a Python list of task dicts:
    [
        {
            "summary": "...",
            "priority": "High|Medium|Low",
            "description": {
                "context": "...",
                "requirements": [...],
                "acceptance_criteria": [...]
            }
        },
        ...
    ]
    """

    prompt = f"""
Analyze the following email and extract action items.

EMAIL:
\"\"\"{email_text}\"\"\"

Return ONLY valid JSON in this format (no extra text, no explanations):
[
  {{
    "summary": "Short task title (max 12 words)",
    "priority": "High | Medium | Low",
    "description": {{
        "context": "Background or reason for task",
        "requirements": ["Action items or tasks to do"],
        "acceptance_criteria": ["Expected outcomes"]
    }}
  }}
]
"""

    response = phi3(prompt, temperature=0.2)

    # Extract JSON array safely
    json_text = extract_json_array(response)

    try:
        tasks = json.loads(json_text)

        # Normalize summary and description texts to remove bold/italic
        for task in tasks:
            task["summary"] = normalize_text(task.get("summary"))
            desc = task.get("description", {})
            desc["context"] = normalize_text(desc.get("context"))
            desc["requirements"] = [normalize_text(r) for r in desc.get("requirements", [])]
            desc["acceptance_criteria"] = [normalize_text(a) for a in desc.get("acceptance_criteria", [])]

        return tasks

    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse JSON: {e}")
        print("LLM response was:", response)
        return []


def format_description(desc, sender_name, assignee_names):
    """
    Formats the Jira task description with context, requirements, acceptance criteria, and notes.
    """
    return f"""
*Context:*
{desc.get("context", "")}

*Requirements:*
""" + "\n".join(f"- {r}" for r in desc.get("requirements", [])) + f"""

*Acceptance Criteria:*
""" + "\n".join(f"- {a}" for a in desc.get("acceptance_criteria", [])) + f"""

*Notes:*
- Parent (Email Sender): {sender_name}
- Assignees: {', '.join(assignee_names)}
""".strip()

def create_jira_task(task, sender, assignees, email_text):
    jira = JIRA(
        server=os.getenv("JIRA_URL"),
        basic_auth=(os.getenv("JIRA_EMAIL"), os.getenv("JIRA_API_TOKEN"))
    )

    sender_name = sender.split("@")[0]
    assignee_names = assignees

    due_date = extract_due_date(email_text)
    VALID_PRIORITIES = ["High", "Medium", "Low"]
    priority = task.get("priority", "Medium").title()  # fallback to Medium
    if priority not in VALID_PRIORITIES:
        priority = "Medium"  # default if invalid
    fields = {
        "project": {"key": os.getenv("JIRA_PROJECT_KEY")},
        "summary": task["summary"],
        "description": format_description(task["description"], sender_name, assignee_names),
        "issuetype": {"name": "Task"},
        "priority": {"name": priority},
        "duedate": due_date
    }

    issue = jira.create_issue(fields=fields)

    for email_id in assignees:
        users = jira.search_users(query=email_id)
        for user in users:
            try:
                jira.assign_issue(issue.key, user.accountId)
                print(f"✅ Assigned {user.displayName} to {issue.key}")
            except Exception as e:
                print(f"❌ Failed to assign {user.displayName}: {e}")


    print("✅ Jira created:", issue.key)
    return issue.key, due_date

def has_future_meeting(text):
    text_lower = text.lower()

    meeting_keywords = [
        "meeting",
        "follow-up",
        "sync",
        "call"
    ]

    time_patterns = [
        r"\b\d{1,2}\s?(am|pm)\b",
        r"\b\d{1,2}:\d{2}\s?(am|pm)\b",
        r"tomorrow",
        r"next\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)"
    ]

    if not any(k in text_lower for k in meeting_keywords):
        return False

    for pattern in time_patterns:
        if re.search(pattern, text_lower):
            return True

    return False

# ===========================================================
# MAIN
# ===========================================================
if __name__ == "__main__":
    print("🚀 Starting workflow...")

    print("📧 Step 1: Reading latest email...")
    email_text, sender, assignees = read_latest_email()
    print(f"✅ Email read. Sender: {sender}, Assignees: {assignees}")
    print(f"Email snippet: {email_text[:100]}...")  # first 100 chars

    print("🧠 Step 2: Classifying intent...")
    intent = classify_intent(email_text)
    print(f"✅ Intent classified: {intent}")

    if intent == "slack_notification":
        print("💬 Step 3: Sending Slack notification...")
        send_slack(email_text)
        print("✅ Slack workflow done")

    elif intent == "calendar_event":
        print("📅 Step 3: Extracting due datetime...")
        due = extract_due_datetime(email_text)
        print(f"✅ Due datetime extracted: {due}")
        print("📅 Step 4: Creating Calendar event...")
        create_calendar_event("Email Event", due)
        print("✅ Calendar workflow done")


    elif intent == "jira_task":
        print("📝 Step 3: Generating Jira task from email...")
        tasks = generate_task_from_email(email_text)

        if not tasks:
            print("⚠️ No tasks found in email, skipping Jira creation.")
        else:
            for task in tasks:
                print(f"✅ Task generated: {task.get('summary')}")
                create_jira_task(task, sender, assignees, email_text)
            if has_future_meeting(email_text):
                print("📅 Future meeting detected inside Jira email")
                due = extract_due_datetime(email_text)
                create_calendar_event("Follow-up Meeting", due)
                print("✅ Calendar workflow done")


            print("✅ Jira workflow done")
    print("🎯 Workflow finished")