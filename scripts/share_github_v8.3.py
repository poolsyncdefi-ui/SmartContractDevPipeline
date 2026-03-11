#!/usr/bin/env python3
"""
Share GitHub V9.8 - Version ULTRA SIMPLIFIÉE
Génération de PROJECT_SHARE.txt et upload vers GitHub Gists
Affichage minimal
"""

import json
import os
import sys
import datetime
import math
import fnmatch
import subprocess
from pathlib import Path
import requests

# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    def __init__(self):
        current_dir = Path.cwd()
        
        # Déterminer les chemins
        if current_dir.name == "SmartContractDevPipeline":
            self.project_root = current_dir
            self.parent_dir = current_dir.parent
        else:
            self.project_root = current_dir / "SmartContractDevPipeline"
            self.parent_dir = current_dir
        
        # Chercher la config dans le dossier parent
        self.config_path = self.parent_dir / "project_config.json"
        self.config = self.load_config()
    
    def load_config(self):
        """Charge la configuration depuis project_config.json"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                return config
            except Exception:
                pass
        
        # Configuration par défaut minimale
        return {
            "PROJECT_NAME": "SmartContractDevPipeline",
            "GITHUB_TOKEN": "",
            "PROJECT_PATH": str(self.project_root),
            "MAX_GIST_SIZE_MB": 45,
            "EXCLUDE_PATTERNS": [
                "node_modules/*", ".git/*", "__pycache__/*", ".venv/*", "venv/*", "env/*",
                "dist/*", "build/*", ".next/*", ".nuxt/*", "target/*", ".gradle/*",
                ".vscode/*", ".idea/*", ".vs/*", ".pytest_cache/*", ".mypy_cache/*",
                ".coverage/*", ".tox/*", "logs/*", ".cache/*", ".tmp/*", "temp/*",
                ".yarn/*", ".npm/*", "bower_components/*", "jspm_packages/*",
                ".serverless/*", ".webpack/*", ".angular/*", ".vuepress/*", ".docusaurus/*",
                ".sapper/*", ".gatsby/*", ".gridsome/*", ".quasar/*", ".ionic/*", ".expo/*",
                ".react-native/*", ".meteor/*", ".electron/*", ".github/*", ".gitlab/*",
                ".circleci/*", ".travis/*", ".appveyor/*", ".DS_Store", "Thumbs.db",
                "desktop.ini", "Icon", "$RECYCLE.BIN/*", "System Volume Information/*",
                ".Spotlight-V100/*", ".Trashes/*", ".TemporaryItems/*", ".fseventsd/*",
                ".DocumentRevisions-V100/*", "package-lock.json", "yarn.lock",
                "pnpm-lock.yaml", "shrinkwrap.json", "*.log", "*.tmp", "*.cache",
                "*.pyc", "*.pyo", "*.pyd", "*.so", "*.dylib", "*.dll", "*.exe",
                "*.class", "*.jar", "*.o", "*.obj", ".env*", "*.key", "*.pem",
                "*.crt", "*.cert", "*.p12", "*.pfx", "*.keystore",
                "PROJECT_SHARE.txt"
            ],
            "EXCLUDE_DIRS": [
                "node_modules", ".git", ".vscode", ".idea", ".vs", "__pycache__",
                ".pytest_cache", ".mypy_cache", ".coverage", ".tox", "venv",
                ".venv", "env", "virtualenv", "env.bak", "dist", "build", "out",
                ".next", ".nuxt", "target", ".gradle", ".settings", "coverage",
                ".nyc_output", "logs", ".cache", ".tmp", "temp", "tmp", ".yarn",
                ".npm", "bower_components", "jspm_packages", ".serverless",
                ".webpack", ".angular", ".vuepress", ".docusaurus", ".sapper",
                ".gatsby", ".gridsome", ".quasar", ".ionic", ".expo",
                ".react-native", ".meteor", ".electron", ".github", ".gitlab",
                ".circleci", ".travis", ".appveyor", "$RECYCLE.BIN",
                "System Volume Information", ".Spotlight-V100", ".Trashes",
                ".TemporaryItems", ".fseventsd", ".DocumentRevisions-V100",
                ".gists", "gists", "github_gists", "test_gists", "gist_test",
                ".gist_cache", ".github_cache"
            ],
            "INCLUDE_PATTERNS": [
                "*.py", "*.js", "*.ts", "*.sol", "*.rs", "*.go", "*.java",
                "*.cpp", "*.h", "*.hpp", "*.c", "*.cs", "*.rb", "*.php",
                "*.swift", "*.kt", "*.kts", "*.scala", "*.md", "*.txt",
                "*.json", "*.yaml", "*.yml", "*.toml", "*.ini", "*.cfg",
                "*.conf", "*.html", "*.css", "*.scss", "*.sass", "*.less",
                "*.mermaid", "*.svg", "*.sh", "*.bat", "*.ps1", "*.dockerfile",
                "Dockerfile*", "docker-compose*", "Makefile", "Gemfile",
                "Cargo.toml", "go.mod", "package.json", "requirements.txt",
                "pyproject.toml", "setup.py", "*.sql", "*.graphql", "*.gql"
            ]
        }
    
    def get(self, key, default=None):
        return self.config.get(key, default)
    
    def save_token(self, token):
        self.config["GITHUB_TOKEN"] = token
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
            return True
        except:
            return False


# ============================================================================
# FILTRAGE
# ============================================================================

def should_exclude(path, config):
    path_str = str(path)
    path_parts = path.parts
    
    exclude_dirs = config.get("EXCLUDE_DIRS", [])
    for part in path_parts:
        if part in exclude_dirs:
            return True
    
    exclude_patterns = config.get("EXCLUDE_PATTERNS", [])
    for pattern in exclude_patterns:
        if pattern.endswith('/*'):
            dir_pattern = pattern[:-2]
            if f"{dir_pattern}{os.sep}" in path_str or f"{dir_pattern}/" in path_str:
                return True
        elif fnmatch.fnmatch(path.name, pattern):
            return True
        elif fnmatch.fnmatch(path_str, pattern):
            return True
    
    return False

def should_include(path, config):
    if path.is_dir():
        return False
    
    include_patterns = config.get("INCLUDE_PATTERNS", ["*"])
    for pattern in include_patterns:
        if fnmatch.fnmatch(path.name, pattern):
            return True
    
    return False

def collect_files(project_path, config):
    all_files = []
    project_root = Path(project_path)
    
    if not project_root.exists():
        return []
    
    for root, dirs, files in os.walk(project_root):
        dirs[:] = [d for d in dirs if not should_exclude(Path(root) / d, config)]
        
        for file in files:
            file_path = Path(root) / file
            
            if should_exclude(file_path, config):
                continue
            
            if should_include(file_path, config):
                all_files.append(file_path)
    
    return sorted(all_files)


# ============================================================================
# LECTURE DE FICHIERS
# ============================================================================

def read_file_with_line_numbers(file_path):
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                lines = f.readlines()
            
            numbered_lines = []
            for i, line in enumerate(lines, 1):
                line = line.rstrip('\n\r')
                numbered_lines.append(f"   {i:4d}: {line}")
            
            return numbered_lines
        except:
            continue
    
    return [f"   [FICHIER BINAIRE]"]


# ============================================================================
# GÉNÉRATION DE PROJECT_SHARE.txt
# ============================================================================

def create_full_share(config):
    print("\n" + "="*50)
    print("GÉNÉRATION PROJECT_SHARE.txt")
    
    project_path = config.get("PROJECT_PATH")
    if not project_path:
        print("✗ PROJECT_PATH non défini")
        return False
    
    project_root = Path(project_path)
    if not project_root.exists():
        print(f"✗ Chemin introuvable")
        return False
    
    files = collect_files(project_path, config)
    
    if not files:
        print("✗ Aucun fichier")
        return False
    
    output_file = project_root / "PROJECT_SHARE.txt"
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    with open(output_file, 'w', encoding='utf-8') as out_f:
        out_f.write(f"PROJECT: {config.get('PROJECT_NAME')}\n")
        out_f.write(f"DATE: {timestamp}\n")
        out_f.write(f"FILES: {len(files)}\n")
        out_f.write("=" * 80 + "\n\n")
        
        for file_path in files:
            out_f.write(f"FICHIER : {file_path}\n")
            
            numbered_lines = read_file_with_line_numbers(file_path)
            for line in numbered_lines:
                out_f.write(line + '\n')
            
            out_f.write('\n')
    
    if output_file.exists():
        file_size = output_file.stat().st_size
        file_size_mb = file_size / (1024 * 1024)
        print(f"✅ {len(files)} fichiers - {file_size_mb:.2f} MB")
        return True
    else:
        print("❌ Échec")
        return False


# ============================================================================
# FONCTIONS POUR GISTS
# ============================================================================

def estimate_gist_size(content):
    return len(content.encode('utf-8'))

def split_files_into_gists(project_root, config):
    all_files = collect_files(project_root, config)
    all_files = [f for f in all_files if f.name != "PROJECT_SHARE.txt"]
    
    max_size_bytes = config.get("MAX_GIST_SIZE_MB", 45) * 1024 * 1024
    
    file_sizes = []
    for file_path in all_files:
        content = '\n'.join(read_file_with_line_numbers(file_path))
        size = estimate_gist_size(content)
        file_sizes.append({
            "path": str(file_path),
            "name": file_path.name,
            "size": size,
            "content": content
        })
    
    file_sizes.sort(key=lambda x: x["size"], reverse=True)
    
    gist_parts = []
    current_gist = {"index": 1, "files": [], "size": 0}
    
    for file_info in file_sizes:
        if current_gist["size"] + file_info["size"] > max_size_bytes and current_gist["files"]:
            gist_parts.append(current_gist)
            current_gist = {"index": len(gist_parts) + 1, "files": [], "size": 0}
        
        current_gist["files"].append(file_info)
        current_gist["size"] += file_info["size"]
    
    if current_gist["files"]:
        gist_parts.append(current_gist)
    
    return gist_parts

def create_gist_content(gist_data, part_index, total_parts, project_name):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    content = []
    content.append("=" * 80)
    content.append(f"PROJECT_SHARE - PARTIE {part_index}/{total_parts}")
    content.append(f"Projet: {project_name}")
    content.append(f"Date: {timestamp}")
    content.append(f"Fichiers: {len(gist_data['files'])}")
    content.append("=" * 80)
    content.append("")
    
    for file_info in gist_data["files"]:
        content.append("")
        content.append(f"FICHIER : {file_info['path']}")
        content.extend(file_info["content"].split('\n'))
        content.append("")
    
    return '\n'.join(content)

def upload_gists_to_github(gist_parts, config, project_root):
    print("\n" + "="*50)
    print("UPLOAD GISTS")
    
    github_token = config.get("GITHUB_TOKEN")
    if not github_token:
        github_token = input("Token GitHub: ").strip()
        if not github_token:
            print("✗ Token requis")
            return None
        config.save_token(github_token)
    
    headers = {"Authorization": f"token {github_token}"}
    
    try:
        test_response = requests.get("https://api.github.com/user", headers=headers)
        if test_response.status_code != 200:
            print("✗ Token invalide")
            return None
    except:
        print("✗ Erreur connexion")
        return None
    
    uploaded_gists = []
    
    for i, gist_data in enumerate(gist_parts):
        part_index = i + 1
        total_parts = len(gist_parts)
        size_mb = gist_data["size"] / (1024 * 1024)
        
        content = create_gist_content(gist_data, part_index, total_parts, config.get('PROJECT_NAME'))
        filename = f"PROJECT_PART{part_index:02d}_of_{total_parts:02d}.txt"
        
        data = {
            "description": f"{config.get('PROJECT_NAME')} - Partie {part_index}/{total_parts}",
            "public": True,
            "files": {filename: {"content": content}}
        }
        
        try:
            response = requests.post("https://api.github.com/gists", headers=headers, json=data, timeout=120)
            
            if response.status_code == 201:
                gist_response = response.json()
                gist_url = gist_response["html_url"]
                
                print(f"  ✅ {gist_url} ({size_mb:.2f} MB)")
                
                uploaded_gists.append({
                    "part": part_index,
                    "url": gist_url,
                    "size_mb": round(size_mb, 2)
                })
                
            else:
                print(f"  ❌ Erreur part {part_index}")
        except Exception as e:
            print(f"  ❌ Exception part {part_index}")
    
    return uploaded_gists

def save_gist_index(uploaded_gists, config, project_root):
    if not uploaded_gists:
        return
    
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    index_file = project_root / "GISTS_INDEX.txt"
    
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write(f"GISTS - {config.get('PROJECT_NAME')}\n")
        f.write(f"Date: {timestamp}\n")
        f.write(f"Total: {len(uploaded_gists)}\n")
        f.write("-"*40 + "\n\n")
        
        for gist in sorted(uploaded_gists, key=lambda x: x['part']):
            f.write(f"Partie {gist['part']:02d}: {gist['url']}\n")
    
    print(f"\n📄 Index: {index_file.name}")

def share_to_github_gists(config, project_root):
    print("\n" + "="*50)
    print("SHARE TO GISTS")
    
    gist_parts = split_files_into_gists(str(project_root), config)
    
    if not gist_parts:
        print("✗ Aucun fichier")
        return False
    
    total_files = sum(len(p['files']) for p in gist_parts)
    total_size = sum(p['size'] for p in gist_parts) / (1024 * 1024)
    
    print(f"📊 {total_files} fichiers - {total_size:.2f} MB - {len(gist_parts)} Gist(s)")
    
    uploaded = upload_gists_to_github(gist_parts, config, project_root)
    
    if uploaded:
        save_gist_index(uploaded, config, project_root)
        print("\n✅ Terminé")
        return True
    else:
        print("\n❌ Échec")
        return False


# ============================================================================
# GIT COMMIT + PUSH
# ============================================================================

def git_commit_push_publish(config, project_root):
    print("\n" + "="*50)
    print("GIT COMMIT + PUSH")
    
    try:
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, cwd=project_root)
        
        if not status.stdout.strip():
            print("ℹ Aucun changement")
            return True
        
        files_changed = len(status.stdout.strip().split('\n'))
        print(f"📝 {files_changed} fichier(s)")
        
        default_msg = f"Màj {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
        commit_msg = input(f"Message (défaut): ").strip() or default_msg
        
        subprocess.run(["git", "add", "."], cwd=project_root, check=True)
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=project_root, check=True)
        
        branch = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True, cwd=project_root)
        current_branch = branch.stdout.strip() or "main"
        
        result = subprocess.run(["git", "push", "origin", current_branch], capture_output=True, text=True, cwd=project_root)
        
        if result.returncode == 0:
            print("✓ Push OK")
            return True
        else:
            print("✗ Push échec")
            return False
            
    except Exception:
        print("✗ Erreur Git")
        return False


# ============================================================================
# MENU PRINCIPAL
# ============================================================================

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def main_menu(config, project_root):
    while True:
        clear_screen()
        print("\n" + "="*50)
        print(f"SHARE GITHUB V9.8 - {config.get('PROJECT_NAME')}")
        print("="*50)
        print("1. GÉNÉRER PROJECT_SHARE.txt")
        print("2. GIT COMMIT + PUSH")
        print("3. SHARE TO GITHUB GISTS")
        print("4. EXIT")
        print("-"*50)
        
        choice = input("Choix: ").strip()
        
        if choice == "1":
            create_full_share(config)
        elif choice == "2":
            git_commit_push_publish(config, project_root)
        elif choice == "3":
            share_to_github_gists(config, project_root)
        elif choice == "4":
            print("\nAu revoir!")
            break
        
        input("\nAppuyez sur ENTER...")


# ============================================================================
# POINT D'ENTRÉE
# ============================================================================

if __name__ == "__main__":
    config = Config()
    
    try:
        main_menu(config, config.project_root)
    except KeyboardInterrupt:
        print("\n\nInterrompu.")
    except Exception as e:
        print(f"\n✗ Erreur: {e}")