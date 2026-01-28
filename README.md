# Automated Email-to-Workflow Orchestration System

## Overview
This project automates converting emails into actionable workflows across Slack, Google Calendar, and Jira. Using a large language model (LLM), the system:

- Reads and summarizes incoming emails.
- Determines whether the email triggers a Slack notification, calendar event, or Jira task.
- Handles date extraction, including natural language parsing.
- Generates structured Jira tasks with summaries, requirements, and acceptance criteria.
- Integrates Slack and Google Calendar APIs for notifications and scheduling.
- Maintains a privacy-first, real-time workflow for enterprise use.

## Features

- Email Reading: Fetches the latest Gmail email.
- Intent Classification: Detects if an email is a Jira task, calendar event, or Slack notification using a LLM.
- Task Generation: Converts emails into structured Jira tasks with priority, context, requirements, and acceptance criteria.
- Slack Integration: Sends summarized notifications to a Slack channel.
- Calendar Integration: Creates Google Calendar events with timezone-aware due dates.
- Date Handling: Extracts due dates from text using regex and natural language parsing with `dateutil`.

## Installation

1. Clone the repository:
git clone https://github.com/Tanisha-Srivastava/Automated-Email-to-Workflow-Orchestration-System-.git
cd email-workflow-automation


2. Install dependencies:
pip install -r requirements.txt


3. Set up credentials:
- Gmail: `credentials.json` from Google Cloud Console
- Google Calendar: `credentials.json` (can be same as Gmail project)
- Jira: API token from Atlassian
- Slack: Bot token from Slack App

4. Create a `.env` file (see below).

## .env Specification

SLACK_BOT_TOKEN=<your-slack-bot-token>
SLACK_CHANNEL_ID=<your-slack-channel-id>
GOOGLE_CLIENT_SECRET_FILE=credentials.json
JIRA_URL=<your-jira-instance-url>
JIRA_EMAIL=<your-jira-email>
JIRA_API_TOKEN=<your-jira-api-token>
JIRA_PROJECT_KEY=<jira-project-key>

## Run the workflow:
python integrated_agent.py
