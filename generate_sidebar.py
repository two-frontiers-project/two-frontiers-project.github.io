import requests
import os
import shutil
import re
import argparse
from pathlib import Path

ORG = "two-frontiers-project"
EXCLUDE = {"two-frontiers-project.github.io"}
EXTERNAL_DIR = "external"

# Custom names for repos that don't follow the standard pattern
CUSTOM_NAMES = {
    "2FP-fieldKitsAndProtocols": "Speciality Kits",
    "2FP-fieldworkToolsGeneral": "General Field Tools",
    "2FP-expedition-template": "Expedition Template",
    "2FP-PUMA": "PUMA Scope",
    "2FP-3dPrinting": "General 3D Printing",
    "2FP-cuvette_holder": "Cuvette Holder",
    "2FP-open_colorimeter": "Open Colorimeter",
    "2FP-XTree": "XTree",
    "2FP_MAGUS": "MAGUS"
}

# Simple categorization function
def categorize_repo(repo):
    """Categorize repositories based on their names."""
    if repo in ["2FP-fieldKitsAndProtocols"]:
        return "Speciality Kits"
    elif repo in ["2FP-fieldworkToolsGeneral", "2FP-PUMA", "2FP-cuvette_holder", "2FP-open_colorimeter", "2FP-3dPrinting"]:
        return "Hardware"
    elif repo in ["2FP-XTree", "2FP_MAGUS"]:
        return "Software"
    elif repo in ["2FP-expedition-template"]:
        return "Templates"
    else:
        return "Other"

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

def get_repo_structure(repo, branch='main'):
    """Get the directory structure of a repository."""
    try:
        # Try main branch first, then master
        branches_to_try = ['main', 'master'] if branch == 'main' else [branch]
        
        for br in branches_to_try:
            url = f"https://api.github.com/repos/{ORG}/{repo}/contents?ref={br}"
            response = requests.get(url)
            if response.status_code == 200:
                contents = response.json()
                
                # Find directories and check if they have READMEs
                subdirs = []
                for item in contents:
                    if item['type'] == 'dir':
                        # Check if this directory has a README
                        readme_url = f"https://api.github.com/repos/{ORG}/{repo}/contents/{item['name']}/README.md?ref={br}"
                        readme_response = requests.get(readme_url)
                        if readme_response.status_code == 200:
                            subdirs.append({
                                'name': item['name'],
                                'branch': br
                            })
                
                return {'branch': br, 'subdirs': subdirs}
        
        return {'branch': 'main', 'subdirs': []}
        
    except Exception as e:
        print(f"⚠️  Could not get structure for {repo}: {e}")
        return {'branch': 'main', 'subdirs': []}

def download_readme(repo, subdir=None, branch='main'):
    """Download and process README from a repository or subdirectory."""
    # Build the URL path
    if subdir:
        path = f"{subdir}/README.md"
        display_path = f"{repo}/{subdir}"
    else:
        path = "README.md"
        display_path = repo
    
    url = f"https://raw.githubusercontent.com/{ORG}/{repo}/{branch}/{path}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        # Process the markdown to fix relative links
        content = response.text
        
        # Fix image links to point to GitHub raw content
        if subdir:
            # For subdirectory READMEs, images might be relative to the subdir
            content = re.sub(
                r'!\[([^\]]*)\]\((?!https?://)([^)]+)\)',
                f'![\\1](https://raw.githubusercontent.com/{ORG}/{repo}/{branch}/{subdir}/\\2)',
                content
            )
            # Fix relative links to point to GitHub repository subdir
            content = re.sub(
                r'\[([^\]]+)\]\((?!https?://|mailto:|#)([^)]+)\)',
                f'[\\1](https://github.com/{ORG}/{repo}/blob/{branch}/{subdir}/\\2)',
                content
            )
        else:
            # For main READMEs, standard processing
            content = re.sub(
                r'!\[([^\]]*)\]\((?!https?://)([^)]+)\)',
                f'![\\1](https://raw.githubusercontent.com/{ORG}/{repo}/{branch}/\\2)',
                content
            )
            content = re.sub(
                r'\[([^\]]+)\]\((?!https?://|mailto:|#)([^)]+)\)',
                f'[\\1](https://github.com/{ORG}/{repo}/blob/{branch}/\\2)',
                content
            )
        
        # Add repository header
        if subdir:
            display_name = f"{CUSTOM_NAMES.get(repo, repo.replace('2FP-', '').replace('2FP_', '').replace('-', ' ').replace('_', ' ').title())} - {subdir.replace('-', ' ').replace('_', ' ').title()}"
            header = f"""# {display_name}

> **Repository:** [{repo}](https://github.com/{ORG}/{repo})  
> **Subdirectory:** [{subdir}](https://github.com/{ORG}/{repo}/tree/{branch}/{subdir})

---

"""
        else:
            display_name = CUSTOM_NAMES.get(repo, repo.replace("2FP-", "").replace("2FP_", "").replace("-", " ").replace("_", " ").title())
            header = f"""# {display_name}

> **Repository:** [{repo}](https://github.com/{ORG}/{repo})

---

"""
        
        return header + content
        
    except requests.RequestException as e:
        print(f"⚠️  Could not download README for {display_path}: {e}")
        return None

def create_external_structure(repos, no_download=False):
    """Create the external directory structure and download READMEs."""
    # Remove existing external directory
    if os.path.exists(EXTERNAL_DIR):
        shutil.rmtree(EXTERNAL_DIR)
    
    # Create external directory
    os.makedirs(EXTERNAL_DIR, exist_ok=True)
    
    downloaded_content = {}
    
    for repo in repos:
        if no_download:
            print(f"📥 Processing {repo} (no download mode)...")
            # Try to download only the main README without API calls
            main_content = download_readme(repo, branch='main')
            if not main_content:
                # Try master branch if main fails
                main_content = download_readme(repo, branch='master')
            
            if main_content:
                # Create repo directory
                repo_dir = os.path.join(EXTERNAL_DIR, repo)
                os.makedirs(repo_dir, exist_ok=True)
                
                # Write main README.md
                readme_path = os.path.join(repo_dir, "README.md")
                with open(readme_path, 'w', encoding='utf-8') as f:
                    f.write(main_content)
                
                downloaded_content[repo] = {'main': True, 'subdirs': []}
                print(f"✅ Downloaded main README for {repo}")
            else:
                print(f"❌ Failed to download main README for {repo}")
        else:
            print(f"📥 Analyzing repository structure for {repo}...")
            
            # Get repository structure
            structure = get_repo_structure(repo)
            branch = structure['branch']
            subdirs = structure['subdirs']
            
            # Download main README
            print(f"📥 Downloading main README for {repo}...")
            main_content = download_readme(repo, branch=branch)
            
            if main_content:
                # Create repo directory
                repo_dir = os.path.join(EXTERNAL_DIR, repo)
                os.makedirs(repo_dir, exist_ok=True)
                
                # Write main README.md
                readme_path = os.path.join(repo_dir, "README.md")
                with open(readme_path, 'w', encoding='utf-8') as f:
                    f.write(main_content)
                
                downloaded_content[repo] = {'main': True, 'subdirs': []}
                print(f"✅ Downloaded main README for {repo}")
                
                # Download subdirectory READMEs
                for subdir_info in subdirs:
                    subdir = subdir_info['name']
                    print(f"📥 Downloading README for {repo}/{subdir}...")
                    
                    subdir_content = download_readme(repo, subdir, branch)
                    if subdir_content:
                        # Create subdirectory
                        subdir_path = os.path.join(repo_dir, subdir)
                        os.makedirs(subdir_path, exist_ok=True)
                        
                        # Write subdirectory README.md
                        subdir_readme_path = os.path.join(subdir_path, "README.md")
                        with open(subdir_readme_path, 'w', encoding='utf-8') as f:
                            f.write(subdir_content)
                        
                        downloaded_content[repo]['subdirs'].append(subdir)
                        print(f"✅ Downloaded README for {repo}/{subdir}")
                    else:
                        print(f"❌ Failed to download README for {repo}/{subdir}")
            else:
                print(f"❌ Failed to download main README for {repo}")
    
    return downloaded_content

def generate_sidebar(downloaded_content):
    """Generate the sidebar markdown with simple categorization."""
    lines = ["## Overview", "- [Home](/README.md)", ""]
    
    # Group repositories by category
    categories = {}
    for repo in downloaded_content.keys():
        category = categorize_repo(repo)
        if category not in categories:
            categories[category] = []
        categories[category].append(repo)
    
    # Define the order of categories
    category_order = ["Speciality Kits", "Hardware", "Software", "Templates", "Other"]
    
    for category in category_order:
        if category in categories and categories[category]:
            lines.append(f"## {category}")
            
            # Sort repos within category alphabetically
            for repo in sorted(categories[category]):
                if repo in downloaded_content:
                    # Use custom name if available, otherwise generate from repo name
                    if repo in CUSTOM_NAMES:
                        title = CUSTOM_NAMES[repo]
                    else:
                        title = repo.replace("2FP-", "").replace("2FP_", "").replace("-", " ").replace("_", " ").title()
                    
                    # Add main repository link
                    lines.append(f"- [{title}](external/{repo}/README.md)")
                    
                    # Add subdirectory links if they exist
                    if downloaded_content[repo]['subdirs']:
                        for subdir in downloaded_content[repo]['subdirs']:
                            subdir_title = subdir.replace('-', ' ').replace('_', ' ').title()
                            lines.append(f"  - [{subdir_title}](external/{repo}/{subdir}/README.md)")
            
            lines.append("")
    
    return "\n".join(lines)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate sidebar for 2FP documentation site')
    parser.add_argument('--no-download', action='store_true', 
                       help='Skip subdirectory discovery to avoid GitHub API rate limits')
    args = parser.parse_args()
    
    print("🔍 Fetching repositories from GitHub organization...")
    repos = get_all_repos()
    print(f"📚 Found {len(repos)} repositories: {repos}")
    
    if args.no_download:
        print(f"\n📁 Creating external directory structure (no subdirectory discovery)...")
    else:
        print(f"\n📁 Creating external directory structure with subdirectories...")
    
    downloaded_content = create_external_structure(repos, no_download=args.no_download)
    
    print(f"\n🔗 Generating categorized sidebar...")
    sidebar_content = generate_sidebar(downloaded_content)
    
    with open("_sidebar.md", "w") as f:
        f.write(sidebar_content)
    
    # Count total downloaded files
    total_files = 0
    for repo, content in downloaded_content.items():
        if content['main']:
            total_files += 1
        total_files += len(content['subdirs'])
    
    print("✅ _sidebar.md has been generated with categorized repository listing.")
    print(f"✅ Downloaded {total_files} README files from {len(downloaded_content)} repositories.")
    
    if args.no_download:
        print("ℹ️  Ran in no-download mode - subdirectories were not discovered.")
        print("ℹ️  Run without --no-download flag to discover subdirectories when API limits reset.")
    
    print("\n📄 Generated sidebar:")
    print(sidebar_content)
