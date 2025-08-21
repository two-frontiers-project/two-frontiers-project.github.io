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

def set_github_token(token):
    """Set the GitHub token globally for API calls."""
    global GITHUB_TOKEN
    GITHUB_TOKEN = token

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
    "2FP-Field-Handbook": "2FP Field Handbook and Standards"
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
    """Fetch all PUBLIC repositories from the GitHub organization.
    
    Note: This only accesses public repositories. Private repositories are not accessible
    even with a token unless the token has explicit access to them.
    """
    repos = []
    page = 1
    while True:
        headers = {}
        if GITHUB_TOKEN:
            headers['Authorization'] = f'token {GITHUB_TOKEN}'
            print(f"🔑 Using token for API call: {GITHUB_TOKEN[:8]}...")
        else:
            print("⚠️  No token available for API call")
        
        # This endpoint only returns PUBLIC repositories by default
        r = requests.get(f"https://api.github.com/orgs/{ORG}/repos?page={page}&per_page=100", headers=headers)
        r.raise_for_status()
        page_repos = r.json()
        if not page_repos:
            break
        
        # Filter to ensure we only get public repos
        public_repos = [repo["name"] for repo in page_repos if not repo.get("private", False)]
        repos.extend(public_repos)
        page += 1
    
    filtered_repos = sorted([r for r in repos if r not in EXCLUDE])
    print(f"🔒 Found {len(filtered_repos)} public repositories")
    return filtered_repos

def get_repo_structure(repo, branch='main'):
    """Get the directory structure of a repository."""
    try:
        # Try main branch first, then master
        branches_to_try = ['main', 'master'] if branch == 'main' else [branch]
        
        for br in branches_to_try:
            url = f"https://api.github.com/repos/{ORG}/{repo}/contents?ref={br}"
            headers = {}
            if GITHUB_TOKEN:
                headers['Authorization'] = f'token {GITHUB_TOKEN}'
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                contents = response.json()
                
                # Find directories and check if they have READMEs
                subdirs = []
                for item in contents:
                    if item['type'] == 'dir':
                        # Check if this directory has a README
                        readme_url = f"https://api.github.com/repos/{ORG}/{repo}/contents/{item['name']}/README.md?ref={br}"
                        headers = {}
                        if GITHUB_TOKEN:
                            headers['Authorization'] = f'token {GITHUB_TOKEN}'
                        readme_response = requests.get(readme_url, headers=headers)
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
            if item['type'] == 'file' and item['name'].endswith('.md') and item['name'] not in ['README.md', '_sidebar.md']:
                # Download the markdown file
                file_url = f"https://raw.githubusercontent.com/{ORG}/{repo}/{branch}/{item['name']}"
                file_response = requests.get(file_url)
                if file_response.status_code == 200:
                    # Create repo directory
                    repo_dir = os.path.join(EXTERNAL_DIR, repo)
                    os.makedirs(repo_dir, exist_ok=True)
                    
                    # Check if file already exists and is the same
                    file_path = os.path.join(repo_dir, item['name'])
                    should_write = True
                    if os.path.exists(file_path):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            existing_content = f.read()
                        if existing_content == file_response.text:
                            should_write = False
                            print(f"⏭️  {item['name']} is up to date")
                    
                    if should_write:
                        # Write the markdown file
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(file_response.text)
                        print(f"📄 Updated: {item['name']}")
                    else:
                        print(f"📄 Skipped: {item['name']} (no changes)")
                    
                    downloaded_files.append(item['name'])
            
            # Also download media files (images, etc.)
            elif item['type'] == 'file' and any(item['name'].lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.pdf']):
                # Download media file
                file_url = f"https://raw.githubusercontent.com/{ORG}/{repo}/{branch}/{item['name']}"
                file_response = requests.get(file_url)
                if file_response.status_code == 200:
                    # Create repo directory
                    repo_dir = os.path.join(EXTERNAL_DIR, repo)
                    os.makedirs(repo_dir, exist_ok=True)
                    
                    # Check if file already exists and is the same
                    file_path = os.path.join(repo_dir, item['name'])
                    should_write = True
                    if os.path.exists(file_path):
                        # For binary files, check file size instead of content
                        if os.path.getsize(file_path) == len(file_response.content):
                            should_write = False
                            print(f"⏭️  {item['name']} is up to date")
                    
                    if should_write:
                        # Write the media file as binary
                        with open(file_path, 'wb') as f:
                            f.write(file_response.content)
                        print(f"🖼️  Updated: {item['name']}")
                    else:
                        print(f"🖼️  Skipped: {item['name']} (no changes)")
                    
                    downloaded_files.append(item['name'])
            
            # Download media directories (like 'media' folder)
            elif item['type'] == 'dir' and item['name'] in ['media', 'images', 'img']:
                print(f"📁 Found media directory: {item['name']}")
                # Download contents of media directory
                media_url = f"https://api.github.com/repos/{ORG}/{repo}/contents/{item['name']}?ref={branch}"
                media_response = requests.get(media_url, headers=headers)
                if media_response.status_code == 200:
                    media_contents = media_response.json()
                    for media_item in media_contents:
                        if media_item['type'] == 'file' and any(media_item['name'].lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.pdf']):
                            # Download media file
                            media_file_url = f"https://raw.githubusercontent.com/{ORG}/{repo}/{branch}/{item['name']}/{media_item['name']}"
                            media_file_response = requests.get(media_file_url)
                            if media_file_response.status_code == 200:
                                # Create media directory
                                repo_dir = os.path.join(EXTERNAL_DIR, repo)
                                media_dir = os.path.join(repo_dir, item['name'])
                                os.makedirs(media_dir, exist_ok=True)
                                
                                # Check if file already exists and is the same
                                media_file_path = os.path.join(media_dir, media_item['name'])
                                should_write = True
                                if os.path.exists(media_file_path):
                                    if os.path.getsize(media_file_path) == len(media_file_response.content):
                                        should_write = False
                                        print(f"⏭️  {item['name']}/{media_item['name']} is up to date")
                                
                                if should_write:
                                    # Write the media file as binary
                                    with open(media_file_path, 'wb') as f:
                                        f.write(media_file_response.content)
                                    print(f"🖼️  Updated: {item['name']}/{media_item['name']}")
                                else:
                                    print(f"🖼️  Skipped: {item['name']}/{media_item['name']} (no changes)")
                                
                                downloaded_files.append(f"{item['name']}/{media_item['name']}")
        
        return downloaded_files
        
    except Exception as e:
        print(f"⚠️  Could not download Field Handbook files for {repo}: {e}")
        return []

def create_external_structure(repos, no_download=False):
    """Create the external directory structure and download READMEs."""
    # Create external directory (don't delete existing content)
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
                
                # Check if README already exists and is the same
                readme_path = os.path.join(repo_dir, "README.md")
                should_write = True
                if os.path.exists(readme_path):
                    with open(readme_path, 'r', encoding='utf-8') as f:
                        existing_content = f.read()
                    if existing_content == main_content:
                        should_write = False
                        print(f"⏭️  README for {repo} is up to date")
                
                if should_write:
                    # Write main README.md
                    with open(readme_path, 'w', encoding='utf-8') as f:
                        f.write(main_content)
                    print(f"✅ Updated README for {repo}")
                
                # Special handling for Field Handbook - download all markdown files
                if repo == "2FP-Field-Handbook":
                    print(f"📥 Checking markdown files for {repo}...")
                    downloaded_files = download_field_handbook_files(repo, branch='main')
                    downloaded_content[repo] = {'main': True, 'subdirs': [], 'flat_markdown': True, 'markdown_files': downloaded_files}
                    print(f"✅ Processed {len(downloaded_files)} markdown files for {repo}")
                else:
                    downloaded_content[repo] = {'main': True, 'subdirs': []}
                
                if should_write:
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
                    title = 'About This Handbook'
                elif title.startswith('02 '):
                    title = 'Expedition Planning'
                elif title.startswith('03 '):
                    title = 'Sample Identifiers and Site Metadata'
                elif title.startswith('04 '):
                    title = 'Preparation for Sample Collection'
                elif title.startswith('05 '):
                    title = 'Setting Up a Field Processing Lab'
                elif title.startswith('06 '):
                    title = 'Sample Collection'
                elif title.startswith('07 '):
                    title = 'Sample Check-in'
                elif title.startswith('08 '):
                    title = 'Sample Processing and Preservation'
                elif title.startswith('09 '):
                    title = 'Sample Transportation'
                elif title.startswith('10 '):
                    title = 'Post-Sampling Reset and Team Debrief'
                
                markdown_files.append({
                    'filename': item,
                    'title': title
                })
    return sorted(markdown_files, key=lambda x: x['filename'])

def generate_sidebar(downloaded_content):
    """Generate the sidebar markdown with simple categorization."""
    lines = [
        '<img src="images/2FP-Logo-MainLogo-COLOR-2063x500.png" alt="Two Frontiers Project" width="1032" />',
        "",
        '<script>',
        'function toggleHandbookSection(linkElement) {',
        '  // Only handle Field Handbook links',
        '  if (!linkElement.href.includes("2FP-Field-Handbook")) return;',
        '  ',
        '  const listItem = linkElement.parentElement;',
        '  const existingSubsections = listItem.querySelector(".handbook-subsections");',
        '  ',
        '  if (existingSubsections) {',
        '    // Toggle existing subsections',
        '    existingSubsections.style.display = existingSubsections.style.display === "none" ? "block" : "none";',
        '    return;',
        '  }',
        '  ',
        '  // Create subsections container',
        '  const subsectionsDiv = document.createElement("div");',
        '  subsectionsDiv.className = "handbook-subsections";',
        '  subsectionsDiv.style.paddingLeft = "20px";',
        '  subsectionsDiv.style.marginTop = "5px";',
        '  ',
        '  // Add loading indicator',
        '  subsectionsDiv.innerHTML = "Loading subsections...";',
        '  listItem.appendChild(subsectionsDiv);',
        '  ',
        '  // Fetch the markdown file to extract headers',
        '  fetch(linkElement.href)',
        '    .then(response => response.text())',
        '    .then(content => {',
        '      const headers = extractHeadersFromMarkdown(content);',
        '      if (headers.length > 0) {',
        '        const subsectionsList = document.createElement("ul");',
        '        headers.forEach(header => {',
        '          const li = document.createElement("li");',
        '          const anchor = header.text.toLowerCase().replace(/[^a-z0-9]+/g, "-");',
        '          const link = document.createElement("a");',
        '          link.href = linkElement.href + "#" + anchor;',
        '          link.textContent = header.text;',
        '          li.appendChild(link);',
        '          subsectionsList.appendChild(li);',
        '        });',
        '        subsectionsDiv.innerHTML = "";',
        '        subsectionsDiv.appendChild(subsectionsList);',
        '      } else {',
        '        subsectionsDiv.innerHTML = "No subsections found";',
        '      }',
        '    })',
        '    .catch(error => {',
        '      subsectionsDiv.innerHTML = "Error loading subsections";',
        '      console.error("Error:", error);',
        '    });',
        '}',
        '',
        'function extractHeadersFromMarkdown(content) {',
        '  const lines = content.split("\\n");',
        '  const headers = [];',
        '  ',
        '  for (const line of lines) {',
        '    const trimmed = line.trim();',
        '    if (trimmed.startsWith("#")) {',
        '      const level = trimmed.length - trimmed.replace(/^#+/, "").length;',
        '      const text = trimmed.replace(/^#+\\s*/, "").trim();',
        '      if (text.length > 3) {',
        '        headers.push({ level, text });',
        '      }',
        '    }',
        '  }',
        '  ',
        '  return headers;',
        '}',
        '</script>',
        '<style>',
        '.handbook-subsections ul {',
        '  list-style-type: none;',
        '  padding-left: 0;',
        '}',
        '.handbook-subsections li {',
        '  margin: 2px 0;',
        '}',
        '.handbook-subsections a {',
        '  color: #ccc;',
        '  text-decoration: none;',
        '  font-size: 0.9em;',
        '}',
        '.handbook-subsections a:hover {',
        '  color: #fff;',
        '  text-decoration: underline;',
        '}',
        '</style>',
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
                        
                        # Add subdirectory links if they exist (as separate clickable items)
                        if downloaded_content[repo]['subdirs']:
                            for subdir in downloaded_content[repo]['subdirs']:
                                subdir_title = subdir.replace('-', ' ').replace('_', ' ').title()
                                lines.append(f"  - [{subdir_title}](external/{repo}/{subdir}/README.md)")
            
        lines.append("")
    
    return "\n".join(lines)

def standardize_readme_headings(readme_path):
    """Standardize heading levels in README files to prevent navigation conflicts."""
    try:
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Find the highest heading level used
        lines = content.split('\n')
        heading_levels = []
        for line in lines:
            if line.strip().startswith('#'):
                level = len(line) - len(line.lstrip('#'))
                heading_levels.append(level)
        
        if not heading_levels:
            return
        
        min_level = min(heading_levels)
        
        # If the highest level is > 1, normalize to start at 1
        if min_level > 1:
            for i in range(len(lines)):
                if lines[i].strip().startswith('#'):
                    current_level = len(lines[i]) - len(lines[i].lstrip('#'))
                    new_level = current_level - min_level + 1
                    lines[i] = '#' * new_level + lines[i].lstrip('#')
            
            content = '\n'.join(lines)
            
            # Only write if content changed
            if content != original_content:
                with open(readme_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"🔧 Standardized headings in {readme_path}")
        
    except Exception as e:
        print(f"⚠️  Could not standardize headings in {readme_path}: {e}")

def fix_handbook_readme_links(readme_path, repo):
    """Fix internal links in the Field Handbook README to point to local files."""
    try:
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Fix GitHub URLs to point to local files
        # Pattern: [text](https://github.com/two-frontiers-project/2FP-Field-Handbook/blob/main/filename.md)
        github_pattern = r'\[([^\]]+)\]\(https://github\.com/two-frontiers-project/2FP-Field-Handbook/blob/main/([^)]+)\)'
        github_links = re.findall(github_pattern, content)
        
        for link_text, filename in github_links:
            # Create the local path
            local_path = f"external/{repo}/{filename}"
            old_pattern = f'[{re.escape(link_text)}](https://github.com/two-frontiers-project/2FP-Field-Handbook/blob/main/{re.escape(filename)})'
            new_pattern = f'[{link_text}]({local_path})'
            content = content.replace(old_pattern, new_pattern)
            print(f"🔗 Fixed GitHub link: {filename} -> {local_path}")
        
        # Also fix the numbered list links that might have different formatting
        numbered_link_pattern = r'(\d+\.\s*\[[^\]]+\]\(https://github\.com/two-frontiers-project/2FP-Field-Handbook/blob/main/([^)]+)\))'
        numbered_links = re.findall(numbered_link_pattern, content)
        
        for full_match, filename in numbered_links:
            # Create the local path
            local_path = f"external/{repo}/{filename}"
            old_pattern = re.escape(full_match)
            new_match = full_match.replace(f"https://github.com/two-frontiers-project/2FP-Field-Handbook/blob/main/{filename}", local_path)
            new_pattern = re.escape(new_match)
            content = re.sub(old_pattern, new_match, content)
            print(f"🔗 Fixed numbered link: {filename} -> {local_path}")
        
        # Find all internal links to markdown files
        # Pattern: [text](filename.md) or [text](filename)
        link_pattern = r'\[([^\]]+)\]\(([^)]+\.md)\)'
        links = re.findall(link_pattern, content)
        
        for link_text, filename in links:
            # Skip if it's already a full URL or external link
            if filename.startswith('http') or filename.startswith('#'):
                continue
            
            # Create the local path
            local_path = f"external/{repo}/{filename}"
            old_pattern = f'[{re.escape(link_text)}]({re.escape(filename)})'
            new_pattern = f'[{link_text}]({local_path})'
            content = content.replace(old_pattern, new_pattern)
            print(f"🔗 Fixed link: {filename} -> {local_path}")
        
        # Also fix links without .md extension
        link_pattern_no_ext = r'\[([^\]]+)\]\(([^)]+)\)'
        links_no_ext = re.findall(link_pattern_no_ext, content)
        
        for link_text, filename in links_no_ext:
            # Skip if it's already a full URL, external link, or has extension
            if filename.startswith('http') or filename.startswith('#') or '.' in filename:
                continue
            
            # Check if this filename exists as a markdown file
            repo_dir = os.path.join(EXTERNAL_DIR, repo)
            if os.path.exists(os.path.join(repo_dir, f"{filename}.md")):
                local_path = f"external/{repo}/{filename}.md"
                old_pattern = f'[{re.escape(link_text)}]({re.escape(filename)})'
                new_pattern = f'[{link_text}]({local_path})'
                content = content.replace(old_pattern, new_pattern)
                print(f"🔗 Fixed link: {filename} -> {local_path}")
        
        # Only write if content changed
        if content != original_content:
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"🔧 Fixed internal links in {readme_path}")
        else:
            print(f"ℹ️  No internal links to fix in {readme_path}")
        
    except Exception as e:
        print(f"⚠️  Could not fix internal links in {readme_path}: {e}")

def extract_handbook_headers(markdown_file_path):
    """Extract headers from a Field Handbook markdown file for custom navigation."""
    try:
        with open(markdown_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        headers = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('#'):
                # Count the # symbols to get the level
                level = len(line) - len(line.lstrip('#'))
                # Extract the header text (remove # symbols and clean up)
                header_text = line.lstrip('#').strip()
                
                # Skip if it's just a title or very short
                if len(header_text) > 3:
                    headers.append({
                        'level': level,
                        'text': header_text,
                        'anchor': header_text.lower().replace(' ', '-').replace(':', '').replace(',', '').replace('.', '')
                    })
        
        return headers
        
    except Exception as e:
        print(f"⚠️  Could not extract headers from {markdown_file_path}: {e}")
        return []

def remove_table_of_contents(readme_path):
    """Remove table of contents sections from READMEs to prevent duplication with sidebar."""
    try:
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Remove common table of contents patterns
        # Pattern 1: Lines starting with - or * followed by text and links
        lines = content.split('\n')
        filtered_lines = []
        in_toc = False
        
        for line in lines:
            stripped = line.strip()
            
            # Check if we're entering a TOC section
            if any(keyword in stripped.lower() for keyword in ['table of contents', 'contents', 'sections', 'chapters']):
                in_toc = True
                continue
            
            # Check if we're exiting a TOC section (hit a header or end of list)
            if in_toc and (stripped.startswith('#') or (stripped and not stripped.startswith('-') and not stripped.startswith('*'))):
                in_toc = False
            
            # Skip lines that are part of TOC
            if in_toc and (stripped.startswith('-') or stripped.startswith('*')):
                continue
            
            # Keep the line if not in TOC
            if not in_toc:
                filtered_lines.append(line)
        
        # Join lines back together
        content = '\n'.join(filtered_lines)
        
        # Only write if content changed
        if content != original_content:
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"🔧 Removed table of contents from {readme_path}")
        
    except Exception as e:
        print(f"⚠️  Could not remove table of contents from {readme_path}: {e}")

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
        set_github_token(args.token)
        print(f"🔑 Using provided GitHub token: {args.token[:8]}...")
    else:
        print("⚠️  No GitHub token provided - using unauthenticated API (60 req/hour limit)")
    
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
            
            # Fix internal links in the README
            print(f"🔧 Fixing internal links in README...")
            fix_handbook_readme_links(readme_path, handbook_repo)
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
    
    # Fix image paths and standardize headings in all READMEs
    print(f"\n🔧 Processing all READMEs...")
    for repo_name in downloaded_content:
        repo_path = os.path.join(EXTERNAL_DIR, repo_name)
        if os.path.exists(repo_path):
            # Process main README
            main_readme = os.path.join(repo_path, "README.md")
            if os.path.exists(main_readme):
                fix_readme_image_paths(main_readme, repo_name)
                standardize_readme_headings(main_readme)
                remove_table_of_contents(main_readme)
            
            # Process subdirectory READMEs
            for subdir in downloaded_content[repo_name]['subdirs']:
                subdir_readme = os.path.join(repo_path, subdir, "README.md")
                if os.path.exists(subdir_readme):
                    fix_readme_image_paths(subdir_readme, repo_name, subdir)
                    standardize_readme_headings(subdir_readme)
                    remove_table_of_contents(subdir_readme)
    
    # Fix internal links in the Field Handbook README
    if "2FP-Field-Handbook" in downloaded_content:
        handbook_repo_path = os.path.join(EXTERNAL_DIR, "2FP-Field-Handbook")
        if os.path.exists(handbook_repo_path):
            handbook_readme = os.path.join(handbook_repo_path, "README.md")
            if os.path.exists(handbook_readme):
                fix_handbook_readme_links(handbook_readme, "2FP-Field-Handbook")
    
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
