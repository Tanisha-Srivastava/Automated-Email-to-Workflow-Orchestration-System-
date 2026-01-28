from llm import llm
import re

PROMPT = """
You are given a meeting transcript.

Extract ACTION ITEMS — both explicit and implicit.

An action item is a task that a participant commits to doing
after the meeting, OR a task whose purpose is to schedule,
set up, or arrange a meeting, OR an announcement / notification
task intended to inform a person or group.

The transcript may contain:
- Execution work to be done outside meetings
- Meeting-related actions (scheduling, setting up calls)
- Announcement or notification actions
- Discussion that happens inside meetings
- Or any combination of the above

IMPORTANT INTERPRETATION RULE:
- Implicit action items mean rephrasing or structuring what is
  ALREADY stated in the transcript.
- Implicit does NOT mean inferring new actions, future steps,
  meetings, deadlines, or responsibilities that
  are not explicitly stated.

INSTRUCTIONS:
- Preserve the PERSON NAME in the task text. - very important
- Phrase each action as a clear task.
- Include dates or times ONLY if they are explicitly mentioned.
- Ignore greetings, opinions, or general discussion.
- Treat tentative language ("could", "can", "try", "maybe")
  as lower confidence.
- If an action depends on another, express it using
  natural language ("after", "once", "when").
- Do NOT lower confidence for tasks that are conditional only
  because they depend on another task. Dependency does not
  imply uncertainty.

ANNOUNCEMENT / NOTIFICATION RULES:
- Announcement actions ARE valid action items.
- If a speaker explicitly says they will announce, notify,
  inform, share, update, remind, or send a status update, or makes FYI statements,
  extract it as an action item.
- Such actions may explicitly state that no action is required;
  this does NOT invalidate them as action items. (eg 'this statement is fyi for team, to keep everyone informed, no action required' - still extract as announcement action)
- Do NOT invent recipients, channels, meetings, or follow-ups
  for announcement actions. Use ONLY what is stated.
- When extracting announcement or notification actions,
  include a brief description of WHAT is being announced
  using wording already present elsewhere in the transcript
  (e.g., client feedback, demo acknowledgment, status update). - also include name of person if mentioned
- Do NOT add any details that are not explicitly mentioned.


MEETING-SPECIFIC RULES:
- Actions whose purpose is to SCHEDULE, SET UP, or ARRANGE
  a meeting (e.g., "schedule a meeting", "set up a call",
  "block time") ARE valid action items.
- Statements describing discussion, clarification, alignment,
  or review that will happen INSIDE a meeting are NOT action items.
- If discussion purpose is mentioned alongside an explicit
  scheduling action, include it in the SAME task description.
- Do NOT invent meeting dates, times, or participants.
- If work is stated to happen BEFORE or AFTER a meeting,
  it IS an action item.

NAME PRESERVATION IN DEPENDENCIES (CRITICAL):

- Every extracted task MUST explicitly mention the PERSON NAME(s)
  responsible for the task.
- If a task depends on another task, the dependent task MUST also
  explicitly mention the PERSON NAME of the person performing the
  preceding task.

Examples:
- Correct: "Tanisha will review everything after Surabhi updates the frontend components."
- Incorrect: "Tanisha will review everything after frontend updates are done."

- Correct: "Tanisha will review everything after Surya completes the redesign and Surabhi updates the frontend."
- Incorrect: "Tanisha will review everything after both tasks are done."

- If multiple people are involved in the dependency, include ALL names.
- Do NOT replace people with generic phrases like "the team", "the work", "the tasks", or "the frontend work".

- Avoid using any apostrophes when mentioning any person's name

CRITICAL ANTI-HALLUCINATION RULES:
- Do NOT invent meetings, dates, times, deadlines, assignees,
  recipients, follow-ups, or next steps.
- Do NOT convert future intent ("we'll discuss later",
  "once we receive notes") into action items unless a
  responsible person and concrete action are explicitly stated.
- If the transcript explicitly states "no action required",
  still extract announcement actions, but extract NO execution
  or scheduling tasks.

Assign a confidence score based on commitment strength.

OUTPUT (JSON ONLY):
[
  {{
    "text": "<task>",
    "confidence": <0 to 1>
  }}
]

Transcript:
{transcript}
"""

def fix_utf8_mojibake(text: str) -> str:
    """Repair common UTF-8 mojibake (e.g., â€™ → ’)"""
    try:
        return text.encode('latin1').decode('utf-8')
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text

def normalize_quotes(text: str) -> str:
    """Optional: replace curly quotes with straight ones for robustness"""
    replacements = {"‘": "'", "’": "'", "“": '"', "”": '"'}
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

def extract_actions(lines):
    # 🔧 STEP 1: Clean input transcript
    transcript = "\n".join(lines)
    transcript = fix_utf8_mojibake(transcript)
    transcript = normalize_quotes(transcript)  # optional but recommended

    # 🔧 STEP 2: Send clean transcript to LLM
    response = llm.invoke(PROMPT.format(transcript=transcript))

    # 🔧 STEP 3: Also clean LLM response (in case it echoes corrupted text)
    response = fix_utf8_mojibake(response)

    actions = []
    matches = re.findall(
        r'"text"\s*:\s*"([^"]+)"\s*,\s*"confidence"\s*:\s*([0-9.]+)',
        response
    )

    for text, conf in matches:
        # 🔧 STEP 4: Clean extracted text too
        text = fix_utf8_mojibake(text)
        text = normalize_quotes(text)

        try:
            c = float(conf)
        except:
            c = 0.6

        actions.append({
            "text": text.strip(),
            "confidence": max(0.0, min(1.0, c))
        })

    return actions
