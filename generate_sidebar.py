import requests

ORG = "two-frontiers-project"
EXCLUDE = {"two-frontiers-project.github.io"}
REPO_GROUPS = {
    "Handbook": ["2FP-fieldKitsAndProtocols"],
    "Field Protocols": ["2FP-fieldKitsAndProtocols", "2FP-citSci", "2FP-10sampling-kit", "2FP-fieldworkToolsGeneral"],
    "Lab Protocols": ["2FP-processing", "2FP-extraction-protocols", "2FP-library-preps", "2FP-microscopy"],
    "Hardware": ["2FP-3dPrinting", "2FP-cuvette_holder"],
    "Software": ["2FP-CUAL-ID", "2FP-TFIDlabels", "2FP-XTree", "2FP-MAGUS", "2FP-LILLYPAD"],
    "Templates": ["2FP-expedition-template"]
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
        lines.append(f"## {section}")
        for repo in repo_list:
            if repo in repos:
                title = repo.replace("2FP-", "").replace("-", " ").title()
                lines.append(f"- [{title}](https://raw.githubusercontent.com/{ORG}/{repo}/main/README.md)")
        lines.append("")
    return "\n".join(lines)

if __name__ == "__main__":
    repos = get_all_repos()
    sidebar_content = generate_sidebar(repos)
    with open("_sidebar.md", "w") as f:
        f.write(sidebar_content)
    print("✅ _sidebar.md has been generated.")
