Automated Email-to-Workflow Orchestration System
Overview

This project automates converting emails into actionable workflows across Slack, Google Calendar, and Jira. Using a large language model (LLM), the system:

Reads and summarizes incoming emails.

Determines whether the email triggers a Slack notification, calendar event, or Jira task.

Handles date extraction, including natural language parsing.

Generates structured Jira tasks with summaries, requirements, and acceptance criteria.

Integrates Slack and Google Calendar APIs for notifications and scheduling.

Maintains a privacy-first, real-time workflow for enterprise use.

Features

Email Reading: Fetches the latest Gmail email.

Intent Classification: Detects if an email is a Jira task, calendar event, or Slack notification using a LLM.

Task Generation: Converts emails into structured Jira tasks with priority, context, requirements, and acceptance criteria.

Slack Integration: Sends summarized notifications to a Slack channel.

Calendar Integration: Creates Google Calendar events with timezone-aware due dates.

Date Handling: Extracts due dates from text using regex and natural language parsing with dateutil.

Installation

Clone the repo:

git clone https://github.com/<your-username>/email-workflow-automation.git
cd email-workflow-automation


Install dependencies:

pip install -r requirements.txt


Set up credentials:

Gmail: credentials.json from Google Cloud Console

Google Calendar: credentials.json (same as Gmail project)

Jira: API token from Atlassian

Slack: Bot token from Slack App

Create a .env file (see below).

.env Specification
# Slack
SLACK_BOT_TOKEN=<your-slack-bot-token>
SLACK_CHANNEL_ID=<your-slack-channel-id>

# Jira
JIRA_URL=<your-jira-instance-url>
JIRA_EMAIL=<your-jira-email>
JIRA_API_TOKEN=<your-jira-api-token>
JIRA_PROJECT_KEY=<jira-project-key>

# LLM / Phi3
PHI3_ENDPOINT=<your-local-or-remote-llm-endpoint>
MODEL=<your-llm-model-name>


⚠️ Never commit real secrets. Use .env.example with placeholders.

Usage

Run the workflow:
python integrated_agent.py
