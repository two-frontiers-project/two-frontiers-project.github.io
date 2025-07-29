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
    """Fetch all repositories from the GitHub organization."""
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

def check_readme_exists(repo):
    """Check if a repository has a README.md file."""
    url = f"https://raw.githubusercontent.com/{ORG}/{repo}/main/README.md"
    try:
        response = requests.head(url)
        return response.status_code == 200
    except:
        return False

def generate_sidebar(repos):
    """Generate the sidebar markdown with direct GitHub raw links."""
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
                
                # Check if README exists before adding link
                if check_readme_exists(repo):
                    # Create direct GitHub raw link
                    github_url = f"https://raw.githubusercontent.com/{ORG}/{repo}/main/README.md"
                    lines.append(f"- [{title}]({github_url})")
                else:
                    print(f"⚠️  No README.md found for {repo}")
        lines.append("")
    
    return "\n".join(lines)

def find_uncategorized_repos(repos):
    """Find repos that exist but aren't categorized yet."""
    categorized = set()
    for repo_list in REPO_GROUPS.values():
        categorized.update(repo_list)
    
    uncategorized = set(repos) - categorized
    return sorted(uncategorized)

if __name__ == "__main__":
    print("🔍 Fetching repositories from GitHub organization...")
    repos = get_all_repos()
    print(f"📚 Found {len(repos)} repositories: {repos}")
    
    # Check for uncategorized repos
    uncategorized = find_uncategorized_repos(repos)
    if uncategorized:
        print(f"⚠️  Uncategorized repositories found: {uncategorized}")
        print("   Consider adding these to REPO_GROUPS in the script")
    
    print("\n🔗 Generating sidebar with direct GitHub links...")
    sidebar_content = generate_sidebar(repos)
    
    with open("_sidebar.md", "w") as f:
        f.write(sidebar_content)
    
    print("✅ _sidebar.md has been generated with direct GitHub repository links.")
    print("\n📄 Generated sidebar:")
    print(sidebar_content)
