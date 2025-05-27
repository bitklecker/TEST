import os
import requests
import logging

def fetch_filtered_jira_issues():
    domain = os.getenv("JIRA_DOMAIN")
    email = os.getenv("JIRA_EMAIL")
    token = os.getenv("JIRA_API_TOKEN")
    display_name = os.getenv("JIRA_DISPLAY_NAME")
    jql = os.getenv("JIRA_JQL")

    if not all([domain, email, token]):
        raise RuntimeError("Missing required JIRA secrets in environment")

    # Fallback JQL if custom one is not provided
    if not jql and display_name:
        jql = (
            f'project = CFM AND resolution = Unresolved AND created >= "2024-01-01" AND ('
            f'cf[13403] = "{display_name}" OR '  # Designer
            f'cf[13402] = "{display_name}" OR '  # Copywriter
            f'cf[13902] = "{display_name}" OR '  # Brand Lead
            f'cf[13400] = "{display_name}" OR '  # Project Lead
            f'cf[15530] = "{display_name}" OR '  # Print Producer
            f'cf[14200] = "{display_name}") '    # Social Media
            'ORDER BY created DESC'
        )
    elif not jql:
        raise RuntimeError("Neither JIRA_JQL nor JIRA_DISPLAY_NAME was provided")

    logging.info(f"🧠 JQL used: {jql}")

    url = f"https://{domain}/rest/api/3/search"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    auth = (email, token)
    params = {
        "jql": jql,
        "maxResults": 100,
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
