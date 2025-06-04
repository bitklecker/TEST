import os
import requests
import logging

# Supported roles and their custom field IDs
ROLE_FIELD_IDS = {
    "designer":       "cf[13403]",
    "copywriter":     "cf[13402]",
    "brand_lead":     "cf[13902]",
    "project_lead":   "cf[13400]",
    "print_producer": "cf[15530]",
    "social_media":   "cf[14200]",
}

def fetch_filtered_jira_issues():
    domain = os.getenv("JIRA_DOMAIN")
    email = os.getenv("JIRA_EMAIL")
    token = os.getenv("JIRA_API_TOKEN")
    jql = os.getenv("JIRA_JQL")
    display_name = os.getenv("JIRA_DISPLAY_NAME")
    role = os.getenv("JIRA_ROLE")

    if not all([domain, email, token]):
        raise RuntimeError("Missing required JIRA secrets in environment")

    # Fallback JQL construction
    if not jql:
        if not display_name or not role:
            raise RuntimeError("Either JIRA_JQL must be provided, or both JIRA_DISPLAY_NAME and JIRA_ROLE must be set.")

        field_id = ROLE_FIELD_IDS.get(role.lower())
        if not field_id:
            raise RuntimeError(f"Unsupported JIRA_ROLE: {role}. Must be one of: {', '.join(ROLE_FIELD_IDS)}")

        jql = (
            f'project = CFM AND status != Resolved AND created >= "2024-01-01" '
            f'AND {field_id} = "{display_name}" '
            f'ORDER BY created DESC'
        )

    logging.info(f"🧠 JQL used: {jql}")

    url = f"https://{domain}/rest/api/3/search"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    auth = (email, token)
    params = {
        "jql": jql,
        "maxResults": 1000,
        "fields": "*all",
    }

    issues = []
    start_at = 0

    logging.info(f"📡 Fetching Jira issues for: {display_name or 'custom JQL'}")
    while True:
        params["startAt"] = start_at
        response = requests.get(url, headers=headers, params=params, auth=auth)

        if response.status_code != 200:
            logging.error(f"⚠️ Jira API error: {response.status_code} — {response.text}")
            raise Exception(f"Failed to fetch Jira issues: {response.text}")

        data = response.json()
        issues.extend(data.get("issues", []))
        if start_at + data.get("maxResults", 0) >= data.get("total", 0):
            break
        start_at += data["maxResults"]

    return issues
