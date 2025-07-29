import requests
import os
import shutil
import re
from pathlib import Path

ORG = "two-frontiers-project"
EXCLUDE = {"two-frontiers-project.github.io"}
EXTERNAL_DIR = "external"

# Map actual existing repositories to sections
REPO_GROUPS = {
    "Handbook": [],
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

def download_readme(repo):
    """Download and process README from a repository."""
    # Try both main and master branches
    branches = ['main', 'master']
    
    for branch in branches:
        url = f"https://raw.githubusercontent.com/{ORG}/{repo}/{branch}/README.md"
        try:
            response = requests.get(url)
            response.raise_for_status()
            
            # Process the markdown to fix relative links
            content = response.text
            
            # Fix image links to point to GitHub raw content
            content = re.sub(
                r'!\[([^\]]*)\]\((?!https?://)([^)]+)\)',
                f'![\\1](https://raw.githubusercontent.com/{ORG}/{repo}/{branch}/\\2)',
                content
            )
            
            # Fix relative links to point to GitHub repository
            # Fix markdown links that aren't already absolute URLs
            content = re.sub(
                r'\[([^\]]+)\]\((?!https?://|mailto:|#)([^)]+)\)',
                f'[\\1](https://github.com/{ORG}/{repo}/blob/{branch}/\\2)',
                content
            )
            
            # Add repository header
            display_name = CUSTOM_NAMES.get(repo, repo.replace("2FP-", "").replace("2FP_", "").replace("-", " ").replace("_", " ").title())
            header = f"""# {display_name}

> **Repository:** [{repo}](https://github.com/{ORG}/{repo})  
> **Edit on GitHub:** [README.md](https://github.com/{ORG}/{repo}/edit/{branch}/README.md)

---

"""
            
            print(f"✅ Found README for {repo} on {branch} branch")
            return header + content
            
        except requests.RequestException as e:
            continue  # Try next branch
    
    print(f"⚠️  Could not download README for {repo}: No README.md found on main or master branch")
    return None

def create_external_structure():
    """Create the external directory structure and download READMEs."""
    # Remove existing external directory
    if os.path.exists(EXTERNAL_DIR):
        shutil.rmtree(EXTERNAL_DIR)
    
    # Create external directory
    os.makedirs(EXTERNAL_DIR, exist_ok=True)
    
    repos = get_all_repos()
    downloaded_repos = []
    
    for repo in repos:
        print(f"📥 Downloading README for {repo}...")
        content = download_readme(repo)
        
        if content:
            # Create repo directory
            repo_dir = os.path.join(EXTERNAL_DIR, repo)
            os.makedirs(repo_dir, exist_ok=True)
            
            # Write README.md
            readme_path = os.path.join(repo_dir, "README.md")
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            downloaded_repos.append(repo)
            print(f"✅ Downloaded README for {repo}")
        else:
            print(f"❌ Failed to download README for {repo}")
    
    return downloaded_repos

def generate_sidebar(downloaded_repos):
    """Generate the sidebar markdown with direct relative paths to README.md files."""
    lines = ["# 2FP Open Tools", "", "## Overview", "- [Home](/README.md)", ""]
    
    for section, repo_list in REPO_GROUPS.items():
        if not repo_list:  # Skip empty sections
            continue
            
        lines.append(f"## {section}")
        for repo in repo_list:
            if repo in downloaded_repos:
                # Use custom name if available, otherwise generate from repo name
                if repo in CUSTOM_NAMES:
                    title = CUSTOM_NAMES[repo]
                else:
                    title = repo.replace("2FP-", "").replace("2FP_", "").replace("-", " ").replace("_", " ").title()
                
                # Create direct relative path to README.md file
                lines.append(f"- [{title}](external/{repo}/README.md)")
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
    
    print(f"\n📁 Creating external directory structure...")
    downloaded_repos = create_external_structure()
    
    print(f"\n🔗 Generating sidebar with local external links...")
    sidebar_content = generate_sidebar(downloaded_repos)
    
    with open("_sidebar.md", "w") as f:
        f.write(sidebar_content)
    
    print("✅ _sidebar.md has been generated with local repository links.")
    print(f"✅ Downloaded {len(downloaded_repos)} repository READMEs to {EXTERNAL_DIR}/ directory.")
    print("\n📄 Generated sidebar:")
    print(sidebar_content)
