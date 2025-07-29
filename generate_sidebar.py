import requests

ORG = "two-frontiers-project"
EXCLUDE = {"two-frontiers-project.github.io"}

# Map actual existing repositories to sections
REPO_GROUPS = {
    "Handbook": ["2FP-fieldKitsAndProtocols"],
    "Field Protocols": ["2FP-fieldKitsAndProtocols", "2FP-fieldworkToolsGeneral"],
    "Lab Protocols": [],  # No lab protocol repos exist yet
    "Hardware": ["2FP-PUMA", "2FP-cuvette_holder", "2FP-open_colorimeter"],
    "Software": ["2FP-XTree", "2FP_MAGUS"],
    "Templates": ["2FP-expedition-template"]
}

# Custom names for repos that don't follow the standard pattern
CUSTOM_NAMES = {
    "2FP-fieldKitsAndProtocols": "Field Kits & Protocols",
    "2FP-fieldworkToolsGeneral": "In-Field Geochemistry Tools",
    "2FP-expedition-template": "Expedition Template",
    "2FP-PUMA": "PUMA Scope",
    "2FP-cuvette_holder": "Cuvette Holder",
    "2FP-open_colorimeter": "Open Colorimeter",
    "2FP-XTree": "XTree",
    "2FP_MAGUS": "MAGUS"
}

def get_all_repos():
    repos = []
    page = 1
    while True:
        r = requests.get(f"https://api.github.com/orgs/{ORG}/repos?page={page}&per_page=100")
        r.raise_for_status()
        page_repos = r.json()
        if not page_repos:
            break
        repos.extend([repo["name"] for repo in page_repos])
        page += 1
    return sorted([r for r in repos if r not in EXCLUDE])

def generate_sidebar(repos):
    lines = ["# 2FP Open Tools", "", "## Overview", "- [Home](/README.md)", ""]
    
    for section, repo_list in REPO_GROUPS.items():
        if not repo_list:  # Skip empty sections
            continue
            
        lines.append(f"## {section}")
        for repo in repo_list:
            if repo in repos:
                # Use custom name if available, otherwise generate from repo name
                if repo in CUSTOM_NAMES:
                    title = CUSTOM_NAMES[repo]
                else:
                    title = repo.replace("2FP-", "").replace("2FP_", "").replace("-", " ").replace("_", " ").title()
                
                # Create local route for external content
                lines.append(f"- [{title}](/external/{repo}/)")
        lines.append("")
    
    return "\n".join(lines)

if __name__ == "__main__":
    repos = get_all_repos()
    print("Found repositories:", repos)
    sidebar_content = generate_sidebar(repos)
    with open("_sidebar.md", "w") as f:
        f.write(sidebar_content)
    print("✅ _sidebar.md has been generated with external content routing.")
    print("Generated sidebar:")
    print(sidebar_content)
