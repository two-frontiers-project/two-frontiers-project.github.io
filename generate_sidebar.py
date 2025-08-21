import requests
import os
import shutil
import re
import argparse
from pathlib import Path
from urllib.parse import urljoin, urlparse

ORG = "two-frontiers-project"
EXCLUDE = {"two-frontiers-project.github.io"}
EXTERNAL_DIR = "external"

# GitHub API token for higher rate limits
GITHUB_TOKEN = None  # Will be set from command line argument

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
    "2FP_MAGUS": "MAGUS",
    "2FP-Field-Handbook": "The Two Frontiers Handbook"
}

# Simple categorization function
def categorize_repo(repo):
    """Categorize repositories based on their names."""
    if repo in ["2FP-Field-Handbook"]:
        return "The Two Frontiers Handbook"
    elif repo in ["2FP-fieldKitsAndProtocols"]:
        return "Speciality Kits"
    elif repo in ["2FP-fieldworkToolsGeneral", "2FP-PUMA", "2FP-cuvette_holder", "2FP-open_colorimeter", "2FP-3dPrinting"]:
        return "Hardware"
    elif repo in ["2FP-XTree", "2FP_MAGUS"]:
        return "Software"
    elif repo in ["2FP-expedition-template"]:
        return "Templates"
    else:
        return "Other"

def fix_readme_image_paths(readme_path, repo, subdir=None):
    """Fix image paths in an existing README file to use full paths from root."""
    try:
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        if subdir:
            # Fix markdown images
            image_pattern = r'!\[([^\]]*)\]\((?!https?://)([^)]+)\)'
            images = re.findall(image_pattern, content)
            for alt_text, image_path in images:
                # Always use full path from root
                full_path = f"{EXTERNAL_DIR}/{repo}/{subdir}/{os.path.basename(image_path)}"
                old_pattern = f'![{re.escape(alt_text)}]({re.escape(image_path)})'
                new_pattern = f'![{alt_text}]({full_path})'
                content = content.replace(old_pattern, new_pattern)
            
            # Fix HTML img tags
            html_img_pattern = r'<img\s+src="(?!https?://)([^"]+)"'
            html_images = re.findall(html_img_pattern, content)
            for image_path in html_images:
                full_path = f"{EXTERNAL_DIR}/{repo}/{subdir}/{os.path.basename(image_path)}"
                old_pattern = f'src="{re.escape(image_path)}"'
                new_pattern = f'src="{full_path}"'
                content = content.replace(old_pattern, new_pattern)
        
        # Only write if content changed
        if content != original_content:
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"🔧 Fixed image paths in {readme_path}")
        
    except Exception as e:
        print(f"⚠️  Could not fix image paths in {readme_path}: {e}")

def get_subdirectory_files(repo, subdir, branch='main'):
    """Get all files in a repository subdirectory."""
    try:
        url = f"https://api.github.com/repos/{ORG}/{repo}/contents/{subdir}"
        params = {'ref': branch}
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        files = []
        for item in response.json():
            if item['type'] == 'file':
                files.append(item['name'])
        return files
    except Exception as e:
        print(f"⚠️  Could not get files for {repo}/{subdir}: {e}")
        return []

def download_image(repo, image_path, local_dir, branch='main'):
    """Download an image from GitHub to local directory."""
    try:
        image_url = f"https://raw.githubusercontent.com/{ORG}/{repo}/{branch}/{image_path}"
        response = requests.get(image_url)
        if response.status_code == 200:
            # Create subdirectories if needed
            local_image_path = os.path.join(local_dir, os.path.basename(image_path))
            os.makedirs(os.path.dirname(local_image_path) if os.path.dirname(local_image_path) else local_dir, exist_ok=True)
            
            with open(local_image_path, 'wb') as f:
                f.write(response.content)
            print(f"📷 Downloaded image: {os.path.basename(image_path)}")
            return True
        else:
            print(f"❌ Failed to download image: {image_path} (status: {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Error downloading image {image_path}: {e}")
        return False

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
            # Get all files in the subdirectory to download ALL images
            local_subdir = os.path.join(EXTERNAL_DIR, repo, subdir)
            all_files = get_subdirectory_files(repo, subdir, branch)
            
            # Download all image files (png, jpg, jpeg, gif, svg, etc.)
            image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.bmp', '.webp'}
            for filename in all_files:
                if any(filename.lower().endswith(ext) for ext in image_extensions):
                    full_image_path = f"{subdir}/{filename}"
                    download_image(repo, full_image_path, local_subdir, branch)
            
            # Find all image references in the content and fix paths
            image_pattern = r'!\[([^\]]*)\]\((?!https?://)([^)]+)\)'
            images = re.findall(image_pattern, content)
            
            # Update image paths in content to use local files
            for alt_text, image_path in images:
                # Check if this image was downloaded locally
                local_image_file = os.path.join(local_subdir, os.path.basename(image_path))
                if os.path.exists(local_image_file):
                    # Update to use full path from root (for Docsify)
                    full_local_path = f"{EXTERNAL_DIR}/{repo}/{subdir}/{os.path.basename(image_path)}"
                    old_pattern = f'![{re.escape(alt_text)}]({re.escape(image_path)})'
                    new_pattern = f'![{alt_text}]({full_local_path})'
                    content = content.replace(old_pattern, new_pattern)
                else:
                    # Fallback to GitHub URL if not downloaded
                    old_pattern = f'![{re.escape(alt_text)}]({re.escape(image_path)})'
                    new_pattern = f'![{alt_text}](https://raw.githubusercontent.com/{ORG}/{repo}/{branch}/{subdir}/{image_path})'
                    content = content.replace(old_pattern, new_pattern)
            
            # Also fix HTML img tags
            html_img_pattern = r'<img\s+src="(?!https?://)([^"]+)"'
            html_images = re.findall(html_img_pattern, content)
            for image_path in html_images:
                local_image_file = os.path.join(local_subdir, os.path.basename(image_path))
                if os.path.exists(local_image_file):
                    full_local_path = f"{EXTERNAL_DIR}/{repo}/{subdir}/{os.path.basename(image_path)}"
                    old_pattern = f'src="{re.escape(image_path)}"'
                    new_pattern = f'src="{full_local_path}"'
                    content = content.replace(old_pattern, new_pattern)
            
            # Fix other relative links (non-images) to point to GitHub
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

def download_field_handbook_files(repo, branch='main'):
    """Download all markdown files from the Field Handbook repository."""
    try:
        # Get the repository contents
        url = f"https://api.github.com/repos/{ORG}/{repo}/contents?ref={branch}"
        headers = {}
        if GITHUB_TOKEN:
            headers['Authorization'] = f'token {GITHUB_TOKEN}'
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        contents = response.json()
        downloaded_files = []
        
        for item in contents:
            if item['type'] == 'file' and item['name'].endswith('.md') and item['name'] != 'README.md':
                # Download the markdown file
                file_url = f"https://raw.githubusercontent.com/{ORG}/{repo}/{branch}/{item['name']}"
                file_response = requests.get(file_url)
                if file_response.status_code == 200:
                    # Create repo directory
                    repo_dir = os.path.join(EXTERNAL_DIR, repo)
                    os.makedirs(repo_dir, exist_ok=True)
                    
                    # Write the markdown file
                    file_path = os.path.join(repo_dir, item['name'])
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(file_response.text)
                    
                    downloaded_files.append(item['name'])
                    print(f"📄 Downloaded: {item['name']}")
        
        return downloaded_files
        
    except Exception as e:
        print(f"⚠️  Could not download Field Handbook files for {repo}: {e}")
        return []

def create_external_structure(repos, no_download=False):
    """Create the external directory structure and download READMEs."""
    # Remove existing external directory (ONLY if not in no-download mode)
    if os.path.exists(EXTERNAL_DIR) and not no_download:
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
                
                # Special handling for Field Handbook - download all markdown files
                if repo == "2FP-Field-Handbook":
                    print(f"📥 Downloading all markdown files for {repo}...")
                    downloaded_files = download_field_handbook_files(repo, branch='main')
                    downloaded_content[repo] = {'main': True, 'subdirs': [], 'flat_markdown': True, 'markdown_files': downloaded_files}
                    print(f"✅ Downloaded {len(downloaded_files)} markdown files for {repo}")
                else:
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

def get_flat_markdown_files(repo_path):
    """Get all markdown files from a repository root directory for flat-structured repos."""
    markdown_files = []
    if os.path.exists(repo_path):
        for item in os.listdir(repo_path):
            if item.endswith('.md') and item != 'README.md':
                # Remove the .md extension for display
                title = item.replace('.md', '').replace('-', ' ').replace('_', ' ')
                # Convert numbered prefixes to more readable titles
                if title.startswith('01 '):
                    title = title.replace('01 ', 'About This Handbook - ')
                elif title.startswith('02 '):
                    title = title.replace('02 ', 'Expedition Planning - ')
                elif title.startswith('03 '):
                    title = title.replace('03 ', 'Sample Identifiers - ')
                elif title.startswith('04 '):
                    title = title.replace('04 ', 'Preparation - ')
                elif title.startswith('05 '):
                    title = title.replace('05 ', 'Field Lab Setup - ')
                elif title.startswith('06 '):
                    title = title.replace('06 ', 'Sample Collection - ')
                elif title.startswith('07 '):
                    title = title.replace('07 ', 'Sample Check-in - ')
                elif title.startswith('08 '):
                    title = title.replace('08 ', 'Sample Processing - ')
                elif title.startswith('09 '):
                    title = title.replace('09 ', 'Sample Transportation - ')
                elif title.startswith('10 '):
                    title = title.replace('10 ', 'Post-Sampling - ')
                
                markdown_files.append({
                    'filename': item,
                    'title': title.title()
                })
    return sorted(markdown_files, key=lambda x: x['filename'])

def generate_sidebar(downloaded_content):
    """Generate the sidebar markdown with simple categorization."""
    lines = [
        '<img src="images/2FP-Logo-MainLogo-COLOR-2063x500.png" alt="Two Frontiers Project" width="1032" />',
        "",
        "## Overview", 
        "- [Home](/README.md)", 
        ""
    ]
    
    # Group repositories by category
    categories = {}
    for repo in downloaded_content.keys():
        category = categorize_repo(repo)
        if category not in categories:
            categories[category] = []
        categories[category].append(repo)
    
    # Define the order of categories
    category_order = ["The Two Frontiers Handbook", "Speciality Kits", "Hardware", "Software", "Templates", "Other"]
    
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
                    
                    # Special handling for Field Handbook - it has flat markdown structure
                    if repo == "2FP-Field-Handbook" or (repo in downloaded_content and downloaded_content[repo].get('flat_markdown', False)):
                        lines.append(f"- [{title}](external/{repo}/README.md)")
                        # Get all the individual markdown files
                        repo_path = os.path.join(EXTERNAL_DIR, repo)
                        markdown_files = get_flat_markdown_files(repo_path)
                        for md_file in markdown_files:
                            lines.append(f"  - [{md_file['title']}](external/{repo}/{md_file['filename']})")
                    else:
                        # Standard handling for other repos
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
    parser.add_argument('--handbook', action='store_true',
                       help='Download only the Field Handbook repository')
    parser.add_argument('--token', type=str, help='GitHub personal access token for higher rate limits')
    args = parser.parse_args()
    
    # Set GitHub token if provided
    if args.token:
        GITHUB_TOKEN = args.token
        print("🔑 Using provided GitHub token for higher rate limits")
    
    if args.handbook:
        print("📚 Handbook-only mode: Downloading only the Field Handbook...")
        # Create external directory if it doesn't exist
        os.makedirs(EXTERNAL_DIR, exist_ok=True)
        
        # Download only the Field Handbook
        handbook_repo = "2FP-Field-Handbook"
        downloaded_content = {}
        
        # Download main README
        main_content = download_readme(handbook_repo, branch='main')
        if not main_content:
            main_content = download_readme(handbook_repo, branch='master')
        
        if main_content:
            # Create repo directory
            repo_dir = os.path.join(EXTERNAL_DIR, handbook_repo)
            os.makedirs(repo_dir, exist_ok=True)
            
            # Write main README.md
            readme_path = os.path.join(repo_dir, "README.md")
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(main_content)
            
            # Download all markdown files
            print(f"📥 Downloading all markdown files for {handbook_repo}...")
            downloaded_files = download_field_handbook_files(handbook_repo, branch='main')
            downloaded_content[handbook_repo] = {'main': True, 'subdirs': [], 'flat_markdown': True, 'markdown_files': downloaded_files}
            print(f"✅ Downloaded {len(downloaded_files)} markdown files for {handbook_repo}")
            print(f"✅ Downloaded main README for {handbook_repo}")
        else:
            print(f"❌ Failed to download Field Handbook")
            downloaded_content = {}
    
    elif args.no_download:
        print("🔍 Scanning existing external directory...")
        # Build downloaded_content from existing external directory
        downloaded_content = {}
        if os.path.exists(EXTERNAL_DIR):
            for repo_name in os.listdir(EXTERNAL_DIR):
                repo_path = os.path.join(EXTERNAL_DIR, repo_name)
                if os.path.isdir(repo_path):
                    downloaded_content[repo_name] = {'main': False, 'subdirs': []}
                    
                    # Check for main README
                    main_readme = os.path.join(repo_path, "README.md")
                    if os.path.exists(main_readme):
                        downloaded_content[repo_name]['main'] = True
                    
                    # Check for subdirectories with READMEs
                    for item in os.listdir(repo_path):
                        subdir_path = os.path.join(repo_path, item)
                        if os.path.isdir(subdir_path):
                            subdir_readme = os.path.join(subdir_path, "README.md")
                            if os.path.exists(subdir_readme):
                                downloaded_content[repo_name]['subdirs'].append(item)
                    
                    # Special handling for Field Handbook - check for flat markdown files
                    if repo_name == "2FP-Field-Handbook":
                        markdown_files = get_flat_markdown_files(repo_path)
                        if markdown_files:
                            downloaded_content[repo_name]['flat_markdown'] = True
        
        print(f"📚 Found {len(downloaded_content)} existing repositories with content")
        print(f"\n📁 Using existing external directory structure...")
    else:
        print("🔍 Fetching repositories from GitHub organization...")
        repos = get_all_repos()
        print(f"📚 Found {len(repos)} repositories: {repos}")
        print(f"\n📁 Creating external directory structure with subdirectories...")
        downloaded_content = create_external_structure(repos, no_download=args.no_download)
    
    # Fix image paths in all READMEs regardless of mode
    print(f"\n🔧 Fixing image paths in all READMEs...")
    for repo_name in downloaded_content:
        repo_path = os.path.join(EXTERNAL_DIR, repo_name)
        if os.path.exists(repo_path):
            # Fix main README
            main_readme = os.path.join(repo_path, "README.md")
            if os.path.exists(main_readme):
                fix_readme_image_paths(main_readme, repo_name)
            
            # Fix subdirectory READMEs
            for subdir in downloaded_content[repo_name]['subdirs']:
                subdir_readme = os.path.join(repo_path, subdir, "README.md")
                if os.path.exists(subdir_readme):
                    fix_readme_image_paths(subdir_readme, repo_name, subdir)
    
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
    
    if args.handbook:
        print("ℹ️  Ran in handbook-only mode - only the Field Handbook was downloaded.")
    elif args.no_download:
        print("ℹ️  Ran in no-download mode - subdirectories were not discovered.")
        print("ℹ️  Run without --no-download flag to discover subdirectories when API limits reset.")
    
    print("\n📄 Generated sidebar:")
    print(sidebar_content)
