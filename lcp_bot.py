import os
import json
import requests
from github import Github

# Environment variables
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = os.getenv("GITHUB_REPOSITORY")
PR_NUMBER = int(os.getenv("PR_NUMBER"))

# Mock LCP agreement database
LCP_AGREEMENTS = {
    "whateverventures": {"signed": True, "date": "2025-07-11"}
}

# Supported licenses
ALLOWED_LICENSES = ["MIT", "Apache-2.0", "GPL-3.0"]

# Value weights
VALUE_WEIGHTS = {
    ".py": 2,
    ".js": 1.5,
    ".md": 0.5,
    ".txt": 0.5
}

def check_lcp_agreement(username):
    return LCP_AGREEMENTS.get(username, {"signed": False})["signed"]

def check_license_compatibility(pr_files):
    for file in pr_files:
        if file.filename == "LICENSE" or file.filename.endswith(".md"):
            try:
                content = requests.get(file.raw_url).text
                for license in ALLOWED_LICENSES:
                    if license in content:
                        return True, license
            except:
                continue
    return False, None

def calculate_contribution_value(pr):
    total_value = 0
    for file in pr.get_files():
        extension = os.path.splitext(file.filename)[1]
        weight = VALUE_WEIGHTS.get(extension, 1.0)
        total_value += file.additions * weight
    return round(total_value, 2)

def save_contribution_data(contributor, pr_number, license_type, value):
    contribution = {
        "contributor": contributor,
        "pr_number": pr_number,
        "license": license_type,
        "value": value,
        "date": "2025-07-11"
    }
    try:
        with open("contributions.json", "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = []
    data.append(contribution)
    with open("contributions.json", "w") as f:
        json.dump(data, f, indent=2)
    return contribution

def main():
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
    pr = repo.get_pull(PR_NUMBER)
    contributor = pr.user.login

    if not check_lcp_agreement(contributor):
        pr.create_issue_comment(
            f"@{contributor}, please sign the LCP agreement at lcp.org/sign to proceed."
        )
        exit(1)

    pr_files = pr.get_files()
    is_licensed, license_type = check_license_compatibility(pr_files)
    if not is_licensed:
        pr.create_issue_comment(
            f"@{contributor}, your PR lacks a compatible license (e.g., MIT, Apache-2.0). Please add one."
        )
        exit(1)

    value = calculate_contribution_value(pr)
    contribution = save_contribution_data(contributor, PR_NUMBER, license_type, value)
    pr.create_issue_comment(
        f"@{contributor}, your PR is LCP-compliant! License: {license_type}. Contribution value: {value} points."
    )
    print(f"Contribution logged: {json.dumps(contribution)}")

if __name__ == "__main__":
    main()
