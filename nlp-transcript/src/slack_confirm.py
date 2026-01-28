import requests

SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/XXX/YYY/ZZZ"

def ask_confirmation(task):
    message = {
        "text": (
            f"🤖 *Task detected from meeting*\n"
            f"*Task:* {task['text']}\n"
            f"*Assignee:* {task['assignee']}\n"
            f"*Confidence:* {task['confidence']}\n\n"
            f"Reply YES to create this task."
        )
    }
    requests.post(SLACK_WEBHOOK_URL, json=message)
