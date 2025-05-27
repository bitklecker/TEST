import os
import requests
import logging
from datetime import datetime
import pytz
import json

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
NOTION_TEXT_BLOCK_ID = os.getenv("NOTION_TEXT_BLOCK_ID")
NOTION_BASE_URL = "https://api.notion.com/v1"
NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}

# Mapping: Notion property → (Jira field, type)
FIELD_MAP = {
    "Name": ("summary", "title"),
    "Designer": ("customfield_13403", "select"),
    "Copy due date": ("customfield_13406", "date"),
    "CR3": ("customfield_15039", "date"),
    "Ideal go-live date": ("customfield_13607", "date"),
    "Brand lead": ("customfield_13902", "select"),
    "Brief date": ("customfield_15011", "date"),
    "Due date": ("customfield_13408", "date"),
    "Design due date": ("customfield_13607", "date"),
    "Copywriter": ("customfield_13402", "select"),
    "Sizing (brand)": ("customfield_15159", "select"),
    "Illustration due date": ("customfield_13407", "date"),
    "Project lead": ("customfield_13400", "select"),
    "Head of Brand Design Review": ("customfield_14610", "select"),
    "Video due date": ("customfield_15100", "date"),
    "Illustration": ("customfield_14110", "select"),
    "CR2": ("customfield_14112", "date"),
    "CR1": ("customfield_14111", "date"),
    "Social media due date": ("customfield_14201", "date"),
    "Print producer": ("customfield_15530", "select"),
    "Social media": ("customfield_14200", "select"),
}

def get_existing_ticket_ids():
    url = f"{NOTION_BASE_URL}/databases/{NOTION_DATABASE_ID}/query"
    ticket_ids = set()
    has_more = True
    payload = {"page_size": 100}
    while has_more:
        res = requests.post(url, headers=NOTION_HEADERS, json=payload)
        res.raise_for_status()
        data = res.json()
        for result in data.get("results", []):
            props = result.get("properties", {})
            ticket_field = props.get("Ticket ID", {}).get("rich_text", [])
            if ticket_field:
                text = ticket_field[0]["text"]["content"]
                ticket_ids.add(text)
        has_more = data.get("has_more", False)
        if has_more:
            payload["start_cursor"] = data["next_cursor"]
    return ticket_ids

def format_property(value, field_type):
    if not value:
        return None
    if field_type == "select":
        return {"select": {"name": str(value).strip()}}
    if field_type == "date":
        return {"date": {"start": value[:10]}}
    if field_type == "title":
        return {"title": [{"text": {"content": str(value)}}]}
    if field_type == "rich_text":
        return {"rich_text": [{"text": {"content": str(value)}}]}
    return None

def add_or_update_ticket(issue, existing_ids, dry_run=False):
    key = issue["key"]
    props = {}

    for notion_field, (jira_field, field_type) in FIELD_MAP.items():
        raw = issue["fields"].get(jira_field)
        if isinstance(raw, dict) and "displayName" in raw:
            value = raw["displayName"]
        elif isinstance(raw, list) and raw and isinstance(raw[0], dict) and "displayName" in raw[0]:
            value = raw[0]["displayName"]
        elif isinstance(raw, str):
            value = raw
        elif raw and field_type == "date":
            value = raw
        else:
            value = None
        formatted = format_property(value, field_type)
        if formatted:
            props[notion_field] = formatted

    # Add Jira ticket ID as a rich text link
    jira_domain = os.getenv("JIRA_DOMAIN")
    jira_url = f"https://{jira_domain}/browse/{key}"
    props["Ticket ID"] = {
        "rich_text": [{
            "text": {
                "content": key,
                "link": {"url": jira_url}
            }
        }]
    }

    changes = {}

    if key not in existing_ids:
        props["Status"] = {"status": {"name": "Not started"}}

        if dry_run:
            logging.info(f"[DRY RUN] Would create ticket: {key}")
            return key, {"created": True}

        payload = {
            "parent": {"database_id": NOTION_DATABASE_ID},
            "properties": props,
        }

        res = requests.post(f"{NOTION_BASE_URL}/pages", headers=NOTION_HEADERS, json=payload)

        if res.status_code != 200:
            print(f"\n❌ Failed to create ticket {key} in Notion.")
            print(f"Status code: {res.status_code}")
            print(f"Response: {res.text}")
            print("Payload:")
            print(json.dumps(payload, indent=2))
            raise Exception(f"Failed to create ticket {key} in Notion")

        logging.info(f"✅ Created ticket {key} in Notion")
        changes["created"] = True
    else:
        logging.info(f"➖ Ticket {key} already exists. Skipping create.")

    return key, changes

def update_last_synced():
    if not NOTION_TEXT_BLOCK_ID:
        logging.info("ℹ️ No NOTION_TEXT_BLOCK_ID set — skipping timestamp update.")
        return

    now = datetime.now(pytz.timezone("America/New_York"))
    timestamp = now.strftime("%A, %B %d at %I:%M %p ET")
    text = f"✅ Last synced: {timestamp}"

    payload = {
        "paragraph": {
            "rich_text": [{
                "type": "text",
                "text": {"content": text}
            }]
        }
    }

    url = f"{NOTION_BASE_URL}/blocks/{NOTION_TEXT_BLOCK_ID}"
    res = requests.patch(url, headers=NOTION_HEADERS, json=payload)

    if res.status_code == 200:
        logging.info(f"🕒 Updated Notion timestamp block: {text}")
    else:
        logging.warning(f"❌ Failed to update Notion timestamp block: {res.status_code} — {res.text}")
